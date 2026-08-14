import { spawn } from 'node:child_process';
import readline from 'node:readline';

export class McpStdioClient {
  constructor(config) {
    this.config = config;
    this.child = null;
    this.nextId = 1;
    this.pending = new Map();
    this.closed = false;
  }

  async start() {
    if (this.child) return;
    const { command, args = [], cwd, env = {}, stderr = 'inherit' } = this.config;
    if (!command) throw new Error('Config must include `command`.');

    this.child = spawn(command, args, {
      cwd: cwd || process.cwd(),
      env: { ...process.env, ...env },
      stdio: ['pipe', 'pipe', stderr === 'ignore' ? 'ignore' : 'inherit'],
      windowsHide: true,
    });

    this.child.on('error', (err) => this.#failAll(err));
    this.child.on('exit', (code, signal) => {
      if (!this.closed && this.pending.size) {
        this.#failAll(new Error(`MCP server exited early (code=${code}, signal=${signal}).`));
      }
    });

    const rl = readline.createInterface({ input: this.child.stdout });
    rl.on('line', (line) => {
      const trimmed = line.trim();
      if (!trimmed) return;
      let msg;
      try {
        msg = JSON.parse(trimmed);
      } catch {
        return;
      }
      if (Object.hasOwn(msg, 'id')) {
        const entry = this.pending.get(msg.id);
        if (!entry) return;
        this.pending.delete(msg.id);
        clearTimeout(entry.timer);
        if (msg.error) entry.reject(new Error(`MCP error ${msg.error.code}: ${msg.error.message}`));
        else entry.resolve(msg.result);
      }
    });

    const protocolVersion = this.config.protocolVersion || '2025-06-18';
    const init = await this.request('initialize', {
      protocolVersion,
      capabilities: {},
      clientInfo: {
        name: this.config.clientName || 'mcp-ephemeral-runner',
        version: '0.1.0',
      },
    });
    this.notify('notifications/initialized', {});
    return init;
  }

  request(method, params = {}) {
    if (!this.child?.stdin?.writable) throw new Error('MCP server is not running.');
    const id = this.nextId++;
    const timeoutMs = Number(this.config.timeoutMs || 30_000);
    const msg = { jsonrpc: '2.0', id, method, params };
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`Timed out after ${timeoutMs} ms waiting for ${method}.`));
      }, timeoutMs);
      this.pending.set(id, { resolve, reject, timer });
      this.child.stdin.write(`${JSON.stringify(msg)}\n`);
    });
  }

  notify(method, params = {}) {
    if (!this.child?.stdin?.writable) throw new Error('MCP server is not running.');
    this.child.stdin.write(`${JSON.stringify({ jsonrpc: '2.0', method, params })}\n`);
  }

  async listTools() {
    return this.request('tools/list', {});
  }

  async callTool(name, args = {}) {
    return this.request('tools/call', { name, arguments: args });
  }

  async close() {
    this.closed = true;
    this.#failAll(new Error('MCP client closed.'));
    if (!this.child) return;
    if (this.child.stdin.writable) this.child.stdin.end();
    if (!this.child.killed) this.child.kill('SIGTERM');
    await new Promise((resolve) => {
      const timer = setTimeout(resolve, 1500);
      this.child.once('exit', () => {
        clearTimeout(timer);
        resolve();
      });
    });
    if (!this.child.killed) this.child.kill('SIGKILL');
  }

  #failAll(err) {
    for (const [, entry] of this.pending) {
      clearTimeout(entry.timer);
      entry.reject(err);
    }
    this.pending.clear();
  }
}
