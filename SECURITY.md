# Security

This project intentionally launches external MCP server commands. Treat MCP servers as executable code.

- Prefer containers/sandboxes for untrusted MCP servers.
- Never commit API keys or tokens.
- Review the package/repository before executing it.
- Pass the smallest possible filesystem/network permissions.
- Use short-lived credentials where possible.
- Do not expose the runner as an unauthenticated public execution endpoint.
