import readline from 'node:readline';

let counter = 0;
const tools = [
  {
    name: 'echo',
    description: 'Echo input text.',
    inputSchema: { type: 'object', properties: { text: { type: 'string' } }, required: ['text'] },
  },
  {
    name: 'counter_increment',
    description: 'Increment persistent in-process state.',
    inputSchema: { type: 'object', properties: { by: { type: 'number' } } },
  },
];

const rl = readline.createInterface({ input: process.stdin });
rl.on('line', (line) => {
  let m;
  try { m = JSON.parse(line); } catch { return; }
  if (!Object.hasOwn(m, 'id')) return;
  let result;
  if (m.method === 'initialize') {
    result = {
      protocolVersion: '2025-06-18',
      capabilities: { tools: {} },
      serverInfo: { name: 'mock-mcp', version: '0.1.0' },
    };
  } else if (m.method === 'tools/list') {
    result = { tools };
  } else if (m.method === 'tools/call') {
    if (m.params.name === 'echo') {
      result = { content: [{ type: 'text', text: String(m.params.arguments?.text ?? '') }] };
    } else if (m.params.name === 'counter_increment') {
      counter += Number(m.params.arguments?.by ?? 1);
      result = { content: [{ type: 'text', text: String(counter) }] };
    } else {
      process.stdout.write(`${JSON.stringify({ jsonrpc: '2.0', id: m.id, error: { code: -32601, message: 'Tool not found' } })}\n`);
      return;
    }
  } else {
    process.stdout.write(`${JSON.stringify({ jsonrpc: '2.0', id: m.id, error: { code: -32601, message: 'Method not found' } })}\n`);
    return;
  }
  process.stdout.write(`${JSON.stringify({ jsonrpc: '2.0', id: m.id, result })}\n`);
});
