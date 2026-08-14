#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import { createMcpClient } from './mcp-client-factory.mjs';

function usage() {
  console.log(`\nMCP Ephemeral Runner\n\nUsage:\n  mcp-runner inspect <config.json>\n  mcp-runner call <config.json> <tool-name> [arguments-json]\n  mcp-runner workflow <config.json> <workflow.json>\n\nThe MCP session is started for the command, handshake is performed, tools are used, and the process/session is terminated.\n`);
}

async function readJson(file) {
  const full = path.resolve(file);
  return JSON.parse(await fs.readFile(full, 'utf8'));
}

function print(value) {
  console.log(JSON.stringify(value, null, 2));
}

const [mode, configPath, arg1, arg2] = process.argv.slice(2);
if (!mode || !configPath) {
  usage();
  process.exit(1);
}

function expandEnv(value) {
  if (typeof value === 'string') {
    return value.replace(/\$\{([A-Z0-9_]+)\}/g, (_, name) => {
      if (!(name in process.env)) throw new Error(`Missing environment variable: ${name}`);
      return process.env[name];
    });
  }
  if (Array.isArray(value)) return value.map(expandEnv);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, expandEnv(v)]));
  }
  return value;
}

const config = expandEnv(await readJson(configPath));
const client = createMcpClient(config);

try {
  const init = await client.start();

  if (mode === 'inspect') {
    const tools = await client.listTools();
    print({ initialize: init, tools: tools.tools || tools });
  } else if (mode === 'call') {
    if (!arg1) throw new Error('Missing tool name.');
    const args = arg2 ? JSON.parse(arg2) : {};
    print(await client.callTool(arg1, args));
  } else if (mode === 'workflow') {
    if (!arg1) throw new Error('Missing workflow JSON path.');
    const workflow = await readJson(arg1);
    if (!Array.isArray(workflow)) throw new Error('Workflow must be a JSON array.');
    const results = [];
    for (let i = 0; i < workflow.length; i++) {
      const step = workflow[i];
      if (!step?.tool) throw new Error(`Workflow step ${i + 1} is missing tool.`);
      const result = await client.callTool(step.tool, step.arguments || {});
      results.push({ step: i + 1, tool: step.tool, result });
    }
    print({ initialize: init, results });
  } else {
    usage();
    process.exitCode = 1;
  }
} finally {
  await client.close();
}
