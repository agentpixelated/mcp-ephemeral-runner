import assert from 'node:assert/strict';
import http from 'node:http';
import { McpHttpClient } from '../src/mcp-http-client.mjs';

let counter = 0;
const sessionId = 'test-session-1';
const server = http.createServer(async (req, res) => {
  if (req.method === 'DELETE') {
    res.writeHead(204);
    res.end();
    return;
  }
  if (req.method !== 'POST') {
    res.writeHead(405);
    res.end();
    return;
  }

  let body = '';
  for await (const chunk of req) body += chunk;
  const msg = JSON.parse(body || '{}');

  if (msg.method !== 'initialize') {
    assert.equal(req.headers['mcp-session-id'], sessionId);
  }

  if (!Object.hasOwn(msg, 'id')) {
    res.writeHead(202, { 'Mcp-Session-Id': sessionId });
    res.end();
    return;
  }

  let result;
  if (msg.method === 'initialize') {
    result = {
      protocolVersion: '2025-06-18',
      capabilities: { tools: {} },
      serverInfo: { name: 'mock-http-mcp', version: '1.0.0' },
    };
  } else if (msg.method === 'tools/list') {
    result = {
      tools: [
        { name: 'counter_increment', description: 'increment counter', inputSchema: { type: 'object' } },
      ],
    };
  } else if (msg.method === 'tools/call') {
    counter += Number(msg.params?.arguments?.by || 1);
    result = { content: [{ type: 'text', text: String(counter) }] };
  } else {
    res.writeHead(200, { 'content-type': 'application/json', 'Mcp-Session-Id': sessionId });
    res.end(JSON.stringify({ jsonrpc: '2.0', id: msg.id, error: { code: -32601, message: 'Method not found' } }));
    return;
  }

  res.writeHead(200, {
    'content-type': 'application/json',
    'Mcp-Session-Id': sessionId,
  });
  res.end(JSON.stringify({ jsonrpc: '2.0', id: msg.id, result }));
});

await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const address = server.address();
const client = new McpHttpClient({
  transport: 'http',
  url: `http://127.0.0.1:${address.port}/mcp`,
  timeoutMs: 3000,
});

try {
  const init = await client.start();
  assert.equal(init.serverInfo.name, 'mock-http-mcp');
  const tools = await client.listTools();
  assert.deepEqual(tools.tools.map((t) => t.name), ['counter_increment']);
  const a = await client.callTool('counter_increment', { by: 4 });
  const b = await client.callTool('counter_increment', { by: 6 });
  assert.equal(a.content[0].text, '4');
  assert.equal(b.content[0].text, '10');
  assert.equal(client.sessionId, sessionId);
  console.log('PASS: HTTP initialize -> session -> tools/list -> tools/call -> teardown');
} finally {
  await client.close();
  await new Promise((resolve) => server.close(resolve));
}
