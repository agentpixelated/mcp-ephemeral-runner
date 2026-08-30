function parseSse(text) {
  const events = text.split(/\r?\n\r?\n/);
  for (const event of events) {
    const dataLines = event
      .split(/\r?\n/)
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.slice(5).trim());
    if (!dataLines.length) continue;
    const data = dataLines.join('\n');
    if (!data || data === '[DONE]') continue;
    try {
      return JSON.parse(data);
    } catch {
      // Keep scanning events until a JSON-RPC message is found.
    }
  }
  throw new Error('Streamable HTTP response did not contain a JSON-RPC message.');
}

export class McpHttpClient {
  constructor(config) {
    this.config = config;
    this.nextId = 1;
    this.sessionId = null;
    this.started = false;
    this.closed = false;
  }

  async start() {
    if (this.started) return this.initializeResult;
    if (!this.config.url) throw new Error('HTTP MCP config must include `url`.');

    const protocolVersion = this.config.protocolVersion || '2025-06-18';
    const init = await this.request('initialize', {
      protocolVersion,
      capabilities: {},
      clientInfo: {
        name: this.config.clientName || 'mcp-ephemeral-runner',
        version: '0.2.0',
      },
    });
    await this.notify('notifications/initialized', {});
    this.started = true;
    this.initializeResult = init;
    return init;
  }

  async request(method, params = {}) {
    if (this.closed) throw new Error('MCP HTTP client is closed.');
    const id = this.nextId++;
    const message = { jsonrpc: '2.0', id, method, params };
    const response = await this.#post(message);
    if (!response || typeof response !== 'object') {
      throw new Error(`Invalid MCP response for ${method}.`);
    }
    if (response.error) {
      throw new Error(`MCP error ${response.error.code}: ${response.error.message}`);
    }
    return response.result;
  }

  async notify(method, params = {}) {
    if (this.closed) throw new Error('MCP HTTP client is closed.');
    await this.#post({ jsonrpc: '2.0', method, params }, { notification: true });
  }

  async listTools() {
    return this.request('tools/list', {});
  }

  async callTool(name, args = {}) {
    return this.request('tools/call', { name, arguments: args });
  }

  async close() {
    if (this.closed) return;
    this.closed = true;
    if (!this.sessionId || !this.config.url) return;
    const timeoutMs = Math.min(Number(this.config.timeoutMs || 30_000), 3000);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      await fetch(this.config.url, {
        method: 'DELETE',
        headers: this.#headers(),
        signal: controller.signal,
      });
    } catch {
      // Session termination is best-effort.
    } finally {
      clearTimeout(timer);
    }
  }

  #headers() {
    const headers = {
      accept: 'application/json, text/event-stream',
      'content-type': 'application/json',
      ...(this.config.headers || {}),
    };
    if (this.sessionId) headers['Mcp-Session-Id'] = this.sessionId;
    if (this.config.protocolVersion) headers['MCP-Protocol-Version'] = this.config.protocolVersion;
    return headers;
  }

  async #post(message, { notification = false } = {}) {
    const timeoutMs = Number(this.config.timeoutMs || 30_000);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    let res;
    try {
      res = await fetch(this.config.url, {
        method: 'POST',
        headers: this.#headers(),
        body: JSON.stringify(message),
        signal: controller.signal,
      });
    } catch (error) {
      if (error?.name === 'AbortError') {
        throw new Error(`Timed out after ${timeoutMs} ms waiting for HTTP MCP response.`);
      }
      throw error;
    } finally {
      clearTimeout(timer);
    }

    const sessionId = res.headers.get('mcp-session-id');
    if (sessionId) this.sessionId = sessionId;

    if (notification && (res.status === 202 || res.status === 204)) return null;
    if (!res.ok) {
      const body = await res.text().catch(() => '');
      throw new Error(`HTTP MCP request failed (${res.status}): ${body.slice(0, 1000)}`);
    }
    if (res.status === 202 || res.status === 204) return null;

    const contentType = res.headers.get('content-type') || '';
    if (contentType.includes('application/json')) return res.json();
    const text = await res.text();
    if (contentType.includes('text/event-stream')) return parseSse(text);
    try {
      return JSON.parse(text);
    } catch {
      throw new Error(`Unsupported MCP response content-type: ${contentType || 'unknown'}`);
    }
  }
}
