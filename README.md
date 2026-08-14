# MCP Ephemeral Runner

Run a local/stdio MCP server **temporarily**, inspect its tools, call one or more tools, then tear it down.

The project implements the workflow used in the Playwright MCP experiment:

```text
config / package / command
          ↓
spawn temporary MCP server
          ↓
initialize
          ↓
notifications/initialized
          ↓
tools/list
          ↓
tools/call (one or many)
          ↓
collect JSON results
          ↓
terminate MCP process
```

## Why this exists

Many MCP servers are distributed as `npx`, `uvx`, Python, Docker, or other stdio commands. An AI agent should not need to permanently install every server. This runner lets an orchestrator treat an MCP server as an **ephemeral task dependency**.

The runner itself has **zero npm dependencies** and uses Node.js standard library only.

## Requirements

- Node.js >= 20
- Whatever runtime the target MCP requires (`npx`, `uvx`, Docker, Python, etc.)
- Network access if the MCP/package/site needs it

## Quick proof without internet

```bash
npm test
```

Expected:

```text
PASS: initialize -> tools/list -> tools/call -> persistent session -> teardown
```

Inspect the included mock MCP:

```bash
node src/cli.mjs inspect examples/mock.json
```

Run a multi-step workflow while keeping one MCP process alive:

```bash
node src/cli.mjs workflow examples/mock.json workflows/mock-proof.json
```

The counter returns `2` and then `5`, proving that state persists across tool calls in one session.

## Use Playwright MCP

`examples/playwright.json`:

```json
{
  "command": "npx",
  "args": ["-y", "@playwright/mcp", "--headless"],
  "timeoutMs": 60000
}
```

Inspect its available tools:

```bash
node src/cli.mjs inspect examples/playwright.json
```

Navigate and snapshot in the same browser session:

```bash
node src/cli.mjs workflow examples/playwright.json workflows/playwright-proof.json
```

## Call any MCP tool

```bash
node src/cli.mjs call <config.json> <tool-name> '<arguments-json>'
```

Example:

```bash
node src/cli.mjs call examples/mock.json echo '{"text":"hello"}'
```

## Generic MCP config

```json
{
  "command": "npx",
  "args": ["-y", "some-mcp-package"],
  "cwd": "/optional/working/directory",
  "timeoutMs": 30000,
  "env": {
    "SOME_SETTING": "value"
  }
}
```

The process receives the host environment plus config-specific variables.

> Do not put real secrets in committed JSON config. Pass them through the environment or a secret manager.

## Agent integration pattern

An AI-agent harness can generate a config and workflow at runtime:

```text
User task
   ↓
Agent discovers suitable MCP
   ↓
Security/compatibility check
   ↓
Generate ephemeral config
   ↓
MCP Ephemeral Runner
   ↓
structured tool results
   ↓
Agent reasons / verifies
```

This is useful for:

- Playwright MCP for browser automation
- Filesystem MCP for bounded file access
- GitHub MCP inside a controlled environment
- database MCPs
- domain-specific MCPs such as marketplace/search adapters

## Isolation model

This runner starts processes on the host by default. For untrusted MCP servers, make the **command itself** an isolation boundary, for example Docker:

```json
{
  "command": "docker",
  "args": ["run", "-i", "--rm", "your-mcp-image"]
}
```

A production agent should add:

- package/repository allowlists
- container or microVM isolation
- network policy
- filesystem mounts scoped read-only where possible
- tool-level approval policy
- max runtime and resource limits
- secret injection with short-lived credentials
- execution audit log

## Current scope

MVP supports **stdio MCP servers**, because that is the execution method used by many local MCP packages and matches the Playwright experiment. Remote Streamable HTTP support can be added as a second transport.

### Environment-variable substitution

Config strings can reference host environment variables safely:

```json
{
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
  }
}
```

The value is resolved only at runtime. The secret itself never needs to be committed.
