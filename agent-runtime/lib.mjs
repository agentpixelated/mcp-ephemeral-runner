import { spawn } from 'node:child_process';
import { access, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';

const MAX_DEFAULT = 2 * 1024 * 1024;

export async function runProcess(argv, options = {}) {
  if (!Array.isArray(argv) || argv.length < 1 || argv.some(x => typeof x !== 'string')) {
    throw new Error('payload.argv must be a non-empty string array');
  }
  const timeoutMs = Math.min(Math.max(Number(options.timeoutMs || 600000), 1000), 6 * 60 * 60 * 1000);
  const maxBytes = Math.min(Math.max(Number(options.maxBytes || MAX_DEFAULT), 4096), 16 * 1024 * 1024);
  const env = { ...process.env, ...(options.env || {}) };
  const started = Date.now();

  return await new Promise((resolve, reject) => {
    const child = spawn(argv[0], argv.slice(1), {
      cwd: options.cwd || process.cwd(),
      env,
      shell: false,
      detached: process.platform !== 'win32',
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    const out = [];
    const err = [];
    let outBytes = 0;
    let errBytes = 0;
    let truncated = false;
    const collect = (bucket, which) => chunk => {
      let remaining = maxBytes - (which === 'out' ? outBytes : errBytes);
      if (remaining <= 0) { truncated = true; return; }
      const buf = Buffer.from(chunk);
      const sliced = buf.length > remaining ? buf.subarray(0, remaining) : buf;
      bucket.push(sliced);
      if (which === 'out') outBytes += sliced.length; else errBytes += sliced.length;
      if (sliced.length < buf.length) truncated = true;
    };
    child.stdout.on('data', collect(out, 'out'));
    child.stderr.on('data', collect(err, 'err'));
    child.on('error', reject);

    const timer = setTimeout(() => {
      try { process.kill(-child.pid, 'SIGTERM'); } catch { try { child.kill('SIGTERM'); } catch {} }
      setTimeout(() => { try { process.kill(-child.pid, 'SIGKILL'); } catch { try { child.kill('SIGKILL'); } catch {} } }, 3000).unref();
    }, timeoutMs);

    child.on('close', (code, signal) => {
      clearTimeout(timer);
      resolve({
        exit_code: code,
        signal,
        duration_ms: Date.now() - started,
        stdout: Buffer.concat(out).toString('utf8'),
        stderr: Buffer.concat(err).toString('utf8'),
        truncated,
      });
    });
  });
}

function safeEnv(extra = {}) {
  const blocked = /^(AGENT_WORKER_TOKEN|SUPABASE_|GITHUB_TOKEN$|ACTIONS_ID_TOKEN_REQUEST_)/i;
  const out = {};
  for (const [k, v] of Object.entries(extra || {})) {
    if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(k)) continue;
    if (blocked.test(k)) continue;
    out[k] = String(v);
  }
  return out;
}

async function commandExists(name) {
  const r = await runProcess(['sh', '-c', `command -v "$1" >/dev/null 2>&1`, 'sh', name], { timeoutMs: 5000 });
  return r.exit_code === 0;
}

async function findDisplay() {
  for (let n = 88; n <= 109; n++) {
    try {
      await readFile(`/tmp/.X${n}-lock`);
    } catch {
      return `:${n}`;
    }
  }
  throw new Error('No free X display found');
}

export async function startTemporaryGui(spec = {}) {
  if (process.platform !== 'linux') throw new Error('Temporary GUI currently requires Linux');
  if (!(await commandExists('Xvfb'))) throw new Error('Xvfb is not installed');
  const display = await findDisplay();
  const n = display.slice(1);
  const width = Math.min(Math.max(Number(spec.width || 1365), 640), 3840);
  const height = Math.min(Math.max(Number(spec.height || 768), 480), 2160);
  const dir = await mkdtemp(path.join(tmpdir(), 'agent-gui-'));
  const xauth = path.join(dir, '.Xauthority');
  await writeFile(xauth, '');
  const procs = [];

  const xvfb = spawn('Xvfb', [display, '-screen', '0', `${width}x${height}x24`, '-nolisten', 'tcp', '-ac'], {
    detached: true, stdio: 'ignore', env: { ...process.env, XAUTHORITY: xauth },
  });
  procs.push(xvfb);
  await new Promise(r => setTimeout(r, 500));

  if (await commandExists('openbox')) {
    const p = spawn('openbox', [], { detached: true, stdio: 'ignore', env: { ...process.env, DISPLAY: display, XAUTHORITY: xauth } });
    procs.push(p);
  }

  let browser = null;
  if (spec.browser) {
    const browserCmd = (await commandExists('chromium')) ? 'chromium' : ((await commandExists('google-chrome')) ? 'google-chrome' : null);
    if (browserCmd) {
      const profile = path.join(dir, 'browser-profile');
      const args = ['--no-sandbox', '--disable-dev-shm-usage', `--user-data-dir=${profile}`, '--new-window'];
      if (spec.url) args.push(String(spec.url));
      browser = spawn(browserCmd, args, { detached: true, stdio: 'ignore', env: { ...process.env, DISPLAY: display, XAUTHORITY: xauth } });
      procs.push(browser);
    }
  }

  let novnc = null;
  if (spec.novnc && await commandExists('x11vnc') && await commandExists('websockify')) {
    const vncPort = Number(spec.vnc_port || 5900);
    const webPort = Number(spec.web_port || 6080);
    const vnc = spawn('x11vnc', ['-display', display, '-localhost', '-rfbport', String(vncPort), '-nopw', '-forever', '-shared'], {
      detached: true, stdio: 'ignore', env: { ...process.env, DISPLAY: display, XAUTHORITY: xauth },
    });
    procs.push(vnc);
    const webRoot = spec.novnc_web_root || '/usr/share/novnc';
    const ws = spawn('websockify', [`127.0.0.1:${webPort}`, `127.0.0.1:${vncPort}`, '--web', webRoot], {
      detached: true, stdio: 'ignore', env: { ...process.env, DISPLAY: display, XAUTHORITY: xauth },
    });
    procs.push(ws);
    novnc = { local_url: `http://127.0.0.1:${webPort}/vnc.html`, vnc_port: vncPort, web_port: webPort };
  }

  async function screenshot() {
    const file = path.join(dir, 'screenshot.png');
    if (await commandExists('scrot')) {
      const r = await runProcess(['scrot', file], { env: { DISPLAY: display, XAUTHORITY: xauth }, timeoutMs: 10000 });
      if (r.exit_code !== 0) throw new Error(`scrot failed: ${r.stderr}`);
    } else {
      const r = await runProcess(['import', '-window', 'root', file], { env: { DISPLAY: display, XAUTHORITY: xauth }, timeoutMs: 10000 });
      if (r.exit_code !== 0) throw new Error(`screenshot failed: ${r.stderr}`);
    }
    const bytes = await readFile(file);
    return { bytes, file };
  }

  async function stop() {
    for (const p of procs.reverse()) {
      try { process.kill(-p.pid, 'SIGTERM'); } catch { try { p.kill('SIGTERM'); } catch {} }
    }
    await new Promise(r => setTimeout(r, 250));
    await rm(dir, { recursive: true, force: true });
  }

  return { display, xauth, dir, browser_pid: browser?.pid || null, novnc, screenshot, stop };
}

export async function executeJob(job, repoRoot = process.cwd()) {
  const payload = job?.payload || {};
  const kind = String(job?.kind || 'exec');
  const cwd = payload.cwd ? path.resolve(repoRoot, String(payload.cwd)) : repoRoot;
  const env = safeEnv(payload.env);
  const timeoutMs = payload.timeout_ms || 600000;

  if (kind === 'exec' || kind === 'mcp') {
    const result = await runProcess(payload.argv, { cwd, env, timeoutMs, maxBytes: payload.max_output_bytes });
    return { kind, ...result };
  }

  if (kind === 'gui') {
    const gui = await startTemporaryGui(payload.gui || {});
    try {
      const guiEnv = { ...env, DISPLAY: gui.display, XAUTHORITY: gui.xauth };
      let actionResult = null;
      if (Array.isArray(payload.actions) && payload.actions.length) {
        const controlPath = path.join(repoRoot, 'agent-runtime', 'gui', 'control.py');
        let python = process.env.AGENT_PYTHON || 'python3';
        if (!process.env.AGENT_PYTHON) {
          const venvPython = path.join(repoRoot, '.agent-runtime-venv', 'bin', 'python');
          try { await access(venvPython); python = venvPython; } catch {}
        }
        actionResult = await runProcess([python, controlPath, JSON.stringify(payload.actions)], { cwd, env: guiEnv, timeoutMs });
      }
      let processResult = null;
      if (Array.isArray(payload.argv) && payload.argv.length) {
        processResult = await runProcess(payload.argv, { cwd, env: guiEnv, timeoutMs, maxBytes: payload.max_output_bytes });
      }
      let shot = null;
      if (payload.screenshot !== false) {
        const { bytes } = await gui.screenshot();
        const cap = Math.min(Number(payload.max_screenshot_bytes || 2 * 1024 * 1024), 4 * 1024 * 1024);
        shot = bytes.length <= cap ? bytes.toString('base64') : null;
      }
      return { kind, display: gui.display, novnc: gui.novnc, actions: actionResult, process: processResult, screenshot_png_base64: shot };
    } finally {
      await gui.stop();
    }
  }

  throw new Error(`Unsupported job kind: ${kind}`);
}
