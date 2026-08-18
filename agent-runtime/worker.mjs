#!/usr/bin/env node
import os from 'node:os';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { executeJob } from './lib.mjs';

const execFileAsync = promisify(execFile);
const URL = process.env.AGENT_RUNTIME_URL;
const TOKEN = process.env.AGENT_WORKER_TOKEN;
const WORKER_ID = process.env.AGENT_WORKER_ID || 'worker';
const POLL_MS = Math.max(Number(process.env.AGENT_POLL_MS || 5000), 1000);
const ONCE = process.argv.includes('--once');

if (!URL || !TOKEN) {
  console.error('AGENT_RUNTIME_URL and AGENT_WORKER_TOKEN are required');
  process.exit(2);
}

async function call(body) {
  const r = await fetch(URL, {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'authorization': `Bearer ${TOKEN}` },
    body: JSON.stringify(body),
  });
  const text = await r.text();
  let data;
  try { data = text ? JSON.parse(text) : {}; } catch { data = { raw: text }; }
  if (!r.ok) throw new Error(`agent-runtime HTTP ${r.status}: ${JSON.stringify(data)}`);
  return data;
}

function lanAddresses() {
  const addresses = [];
  for (const [name, rows] of Object.entries(os.networkInterfaces())) {
    if (name === 'tailscale0' || !rows) continue;
    for (const row of rows) {
      if (row.family === 'IPv4' && !row.internal) addresses.push({ interface: name, address: row.address });
    }
  }
  return addresses;
}

async function tailscaleMetadata() {
  try {
    const { stdout } = await execFileAsync('tailscale', ['ip', '-4'], { timeout: 5000 });
    const ipv4 = stdout.trim().split(/\s+/)[0] || null;
    return { available: Boolean(ipv4), ipv4 };
  } catch {
    return { available: false, ipv4: null };
  }
}

async function heartbeat() {
  const tailscale = await tailscaleMetadata();
  return call({
    action: 'heartbeat',
    capabilities: { exec: true, gui: process.platform === 'linux', mcp: true, lan: true, tailscale: tailscale.available },
    metadata: {
      platform: process.platform,
      arch: process.arch,
      node: process.version,
      pid: process.pid,
      hostname: os.hostname(),
      tailscale,
      lan_ipv4: lanAddresses(),
    },
  });
}

async function handle(job) {
  await call({ action: 'start', job_id: job.id });
  try {
    const result = await executeJob(job, process.cwd());
    await call({ action: 'complete', job_id: job.id, result });
    console.log(JSON.stringify({ job_id: job.id, status: 'succeeded' }));
  } catch (err) {
    const error = String(err?.stack || err);
    try { await call({ action: 'fail', job_id: job.id, error }); } catch (reportErr) { console.error('report failure', reportErr); }
    console.error(JSON.stringify({ job_id: job.id, status: 'failed', error }));
  }
}

await heartbeat();
console.error(`agent worker ${WORKER_ID} online`);

while (true) {
  try {
    const { job } = await call({ action: 'poll' });
    if (job) await handle(job);
    else if (ONCE) break;
  } catch (err) {
    console.error(String(err?.stack || err));
    if (ONCE) process.exitCode = 1;
  }
  if (ONCE) break;
  await new Promise(r => setTimeout(r, POLL_MS));
}
