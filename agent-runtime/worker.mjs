#!/usr/bin/env node
import { executeJob } from './lib.mjs';

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

async function heartbeat() {
  return call({ action: 'heartbeat', capabilities: { exec: true, gui: process.platform === 'linux', mcp: true }, metadata: { platform: process.platform, arch: process.arch, node: process.version, pid: process.pid } });
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
