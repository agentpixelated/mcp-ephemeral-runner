import { McpStdioClient } from './mcp-client.mjs';
import { McpHttpClient } from './mcp-http-client.mjs';

export function createMcpClient(config) {
  const transport = config.transport || (config.url ? 'http' : 'stdio');
  if (transport === 'http' || transport === 'streamable-http') return new McpHttpClient(config);
  if (transport === 'stdio') return new McpStdioClient(config);
  throw new Error(`Unsupported MCP transport: ${transport}`);
}
