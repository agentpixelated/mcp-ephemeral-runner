#!/usr/bin/env node
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { executeJob } from './lib.mjs';

const file = process.argv[2];
if (!file) throw new Error('Usage: node agent-runtime/run-job-file.mjs <job.json>');
const root = process.cwd();
const job = JSON.parse(await readFile(file, 'utf8'));
const started_at = new Date().toISOString();
let output;
try {
  const result = await executeJob(job, root);
  output = { id: job.id || path.basename(file, '.json'), status: 'succeeded', started_at, finished_at: new Date().toISOString(), result };
} catch (err) {
  output = { id: job.id || path.basename(file, '.json'), status: 'failed', started_at, finished_at: new Date().toISOString(), error: String(err?.stack || err) };
  process.exitCode = 1;
}
await mkdir('agent-runtime/results', { recursive: true });
const resultFile = `agent-runtime/results/${output.id}.json`;
await writeFile(resultFile, JSON.stringify(output, null, 2) + '\n');
console.log(JSON.stringify({ ...output, result_file: resultFile }, null, 2));
