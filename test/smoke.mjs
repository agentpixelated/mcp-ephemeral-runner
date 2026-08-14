import assert from 'node:assert/strict';
import { McpStdioClient } from '../src/mcp-client.mjs';

const client = new McpStdioClient({
  command: 'node',
  args: ['mock/server.mjs'],
  timeoutMs: 3000,
});

try {
  const init = await client.start();
  assert.equal(init.serverInfo.name, 'mock-mcp');
  const listed = await client.listTools();
  assert.deepEqual(listed.tools.map(t => t.name), ['echo', 'counter_increment']);
  const echo = await client.callTool('echo', { text: 'works' });
  assert.equal(echo.content[0].text, 'works');
  const a = await client.callTool('counter_increment', { by: 2 });
  const b = await client.callTool('counter_increment', { by: 3 });
  assert.equal(a.content[0].text, '2');
  assert.equal(b.content[0].text, '5');
  console.log('PASS: initialize -> tools/list -> tools/call -> persistent session -> teardown');
} finally {
  await client.close();
}
