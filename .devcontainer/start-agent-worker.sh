#!/usr/bin/env bash
set -euo pipefail

RUNTIME_URL="${AGENT_RUNTIME_URL:-https://jlvozmgxxojvljxuhywv.supabase.co/functions/v1/agent-runtime}"
WORKER_ID="${AGENT_WORKER_ID:-github-codespace}"
DATA_DIR="${AGENT_DATA_DIR:-$HOME/.local/share/nb-agent}"
ENV_FILE="$DATA_DIR/worker.env"
PID_FILE="$DATA_DIR/worker.pid"
LOG_FILE="$DATA_DIR/worker.log"

mkdir -p "$DATA_DIR"
chmod 700 "$DATA_DIR"

if [[ -f "$PID_FILE" ]]; then
  pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    echo "agent worker already running (pid $pid)"
    exit 0
  fi
  rm -f "$PID_FILE"
fi

if [[ ! -f "$ENV_FILE" ]]; then
  if [[ -n "${AGENT_ENROLLMENT_CODE:-}" ]]; then
    AGENT_RUNTIME_URL="$RUNTIME_URL" \
    AGENT_WORKER_ID="$WORKER_ID" \
    AGENT_DATA_DIR="$DATA_DIR" \
      node agent-runtime/enroll-worker.mjs
    unset AGENT_ENROLLMENT_CODE || true
  else
    echo "agent worker is not enrolled yet."
    echo "Run: bash agent-runtime/codespace-enroll.sh"
    exit 0
  fi
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

nohup node agent-runtime/worker.mjs >>"$LOG_FILE" 2>&1 &
pid=$!
printf '%s\n' "$pid" >"$PID_FILE"
chmod 600 "$PID_FILE"

sleep 1
if kill -0 "$pid" 2>/dev/null; then
  echo "agent worker started (pid $pid, log $LOG_FILE)"
else
  echo "agent worker failed to start; inspect $LOG_FILE" >&2
  exit 1
fi
