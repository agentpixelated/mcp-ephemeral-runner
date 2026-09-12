#!/usr/bin/env bash
set -euo pipefail

export AGENT_RUNTIME_URL="${AGENT_RUNTIME_URL:-https://jlvozmgxxojvljxuhywv.supabase.co/functions/v1/agent-runtime}"
export AGENT_WORKER_ID="${AGENT_WORKER_ID:-github-codespace}"
export AGENT_DATA_DIR="${AGENT_DATA_DIR:-$HOME/.local/share/nb-agent}"

if [[ -f "$AGENT_DATA_DIR/worker.env" ]]; then
  echo "worker is already enrolled at $AGENT_DATA_DIR/worker.env"
  exit 0
fi

read -rsp "One-time enrollment code: " AGENT_ENROLLMENT_CODE
echo
export AGENT_ENROLLMENT_CODE

node agent-runtime/enroll-worker.mjs
unset AGENT_ENROLLMENT_CODE

bash .devcontainer/start-agent-worker.sh
