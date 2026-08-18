# Universal Agent Runtime

This directory turns the ephemeral MCP runner into a general execution substrate. It is intentionally project-agnostic.

## Components

- **Supabase control plane:** persistent jobs, workers, events and key/value state.
- **Edge Function:** public health endpoint plus authenticated worker polling/reporting.
- **Local/LAN worker:** outbound-only polling; no inbound Internet port is required.
- **Temporary GUI:** Xvfb + Openbox, optional Chromium and local-only noVNC; mouse/keyboard actions use PyAutoGUI.
- **GitHub Actions worker:** long-running, secret-free jobs are dispatched by adding a JSON file under `agent-runtime/dispatch/`.
- **Existing MCP runner:** MCP servers remain ephemeral tools and can be invoked from normal `exec` jobs.

## Job format

### CLI / compute

```json
{
  "kind": "exec",
  "payload": {
    "argv": ["python3", "-c", "print(6*7)"],
    "cwd": ".",
    "timeout_ms": 60000
  }
}
```

Commands are spawned with `shell: false`. A shell can still be requested explicitly with `argv: ["bash", "-lc", "..."]`.

### GUI

```json
{
  "kind": "gui",
  "payload": {
    "gui": {"browser": true, "url": "https://example.com", "width": 1365, "height": 768},
    "actions": [
      {"op": "sleep", "seconds": 2},
      {"op": "hotkey", "keys": ["ctrl", "l"]},
      {"op": "type", "text": "https://example.com"},
      {"op": "key", "key": "enter"},
      {"op": "sleep", "seconds": 2}
    ],
    "screenshot": true
  }
}
```

The X server is created only for the job and is torn down afterwards. noVNC, when enabled, binds to loopback only; use SSH/Tailscale port forwarding rather than exposing unauthenticated VNC publicly.

## LAN worker

Install dependencies on a Debian-family host:

```bash
./agent-runtime/bootstrap-debian.sh
```

Run:

```bash
export AGENT_RUNTIME_URL='https://<project>.supabase.co/functions/v1/agent-runtime'
export AGENT_WORKER_ID='home-lan'
export AGENT_WORKER_TOKEN='...'
node agent-runtime/worker.mjs
```

The worker makes outbound HTTPS requests to the control plane. A job executed by this worker can therefore reach services on the same LAN without opening the LAN to inbound Internet traffic.

## Security model

- Worker tokens are never committed; only SHA-256 hashes are stored server-side.
- Supabase tables have RLS enabled and `anon`/`authenticated` table privileges revoked.
- GitHub long-job workflow receives no repository secrets and checks out with persisted credentials disabled.
- Job payload environment variables cannot override worker/Supabase/GitHub credential variables.
- Temporary VNC is local-only by default.
- Treat workers as privileged compute. Register only machines you control and rotate a worker token if it is exposed.
