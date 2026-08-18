#!/usr/bin/env node
import { createHash, randomBytes } from 'node:crypto';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';

const url = process.env.AGENT_RUNTIME_URL;
const workerId = process.env.AGENT_WORKER_ID || 'home-lan';
const enrollmentCode = process.env.AGENT_ENROLLMENT_CODE;
const dataDir = process.env.AGENT_DATA_DIR || '/data';

if (!url || !enrollmentCode) {
  console.error('AGENT_RUNTIME_URL and AGENT_ENROLLMENT_CODE are required');
  process.exit(2);
}

const token = `arw_${randomBytes(32).toString('hex')}`;
const tokenSha256 = createHash('sha256').update(token).digest('hex');

const response = await fetch(url, {
  method: 'POST',
  headers: { 'content-type': 'application/json' },
  body: JSON.stringify({
    action: 'enroll',
    worker_id: workerId,
    enrollment_code: enrollmentCode,
    token_sha256: tokenSha256,
  }),
});

const text = await response.text();
let body;
try { body = text ? JSON.parse(text) : {}; } catch { body = { raw: text }; }
if (!response.ok || body.ok !== true) {
  throw new Error(`Enrollment failed (${response.status}): ${JSON.stringify(body)}`);
}

await mkdir(dataDir, { recursive: true });
const envPath = path.join(dataDir, 'worker.env');
const env = [
  `AGENT_RUNTIME_URL=${url}`,
  `AGENT_WORKER_ID=${workerId}`,
  `AGENT_WORKER_TOKEN=${token}`,
  `AGENT_POLL_MS=${process.env.AGENT_POLL_MS || '3000'}`,
  process.env.AGENT_TAILSCALE_IP ? `AGENT_TAILSCALE_IP=${process.env.AGENT_TAILSCALE_IP}` : '',
].filter(Boolean).join('\n') + '\n';
await writeFile(envPath, env, { mode: 0o600 });
console.log(JSON.stringify({ ok: true, worker_id: workerId, env_file: envPath }));
