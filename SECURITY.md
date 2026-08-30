# Security

This project intentionally launches external MCP server commands. Treat MCP servers as executable code.

- Prefer containers/sandboxes for untrusted MCP servers.
- Never commit API keys or tokens.
- Review the package/repository before executing it.
- Pass the smallest possible filesystem/network permissions.
- Use short-lived credentials where possible.
- Do not expose the runner as an unauthenticated public execution endpoint.

## Remote HTTP MCPs

A remote MCP endpoint can receive every tool argument sent to it. Treat tool input as data leaving the local trust boundary.

- Never send API keys, passwords, access tokens, private customer data, or confidential source code as tool arguments.
- Inject authentication through environment variables or a secret manager, not committed config.
- Prefer HTTPS endpoints and vendor-owned MCP servers.
- Apply an allowlist before an autonomous agent is permitted to connect to arbitrary remote MCP URLs.
- Log the endpoint, tool name, and non-secret execution metadata for auditability.
