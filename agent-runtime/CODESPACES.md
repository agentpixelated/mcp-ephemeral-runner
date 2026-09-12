# GitHub Codespaces worker

This repository can run a Codespace as an outbound-only worker for the existing Supabase `agent-runtime` control plane.

## Security model

- No GitHub personal access token is committed to this repository.
- The long-lived worker token is generated inside the Codespace by `agent-runtime/enroll-worker.mjs`.
- Supabase stores only the SHA-256 hash of that worker token.
- The one-time enrollment code is removed server-side after a successful enrollment.
- Worker state is stored with mode `0600` under `$HOME/.local/share/nb-agent/worker.env`.
- The worker opens no inbound port. It polls the Supabase Edge Function over HTTPS.

## First boot

Open this repository in a GitHub Codespace. The devcontainer starts automatically, but the worker remains idle until it has been enrolled.

Run:

```bash
bash agent-runtime/codespace-enroll.sh
```

Paste the one-time enrollment code when prompted. The script generates the durable worker credential locally and starts the worker.

## Later starts

`.devcontainer/start-agent-worker.sh` is run by the Codespace `postStartCommand`. Once enrolled, stopping and starting the same Codespace automatically restarts the worker.

## Inspect

```bash
cat "$HOME/.local/share/nb-agent/worker.pid"
tail -n 100 "$HOME/.local/share/nb-agent/worker.log"
```

Do not print or commit `worker.env`.
