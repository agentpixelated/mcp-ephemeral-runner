#!/bin/sh
set -eu
ENV_FILE="${AGENT_DATA_DIR:-/data}/worker.env"
if [ ! -f "$ENV_FILE" ]; then
  echo "Worker is not enrolled: $ENV_FILE is missing" >&2
  exit 2
fi
set -a
. "$ENV_FILE"
set +a
export AGENT_CONTAINERIZED=1
exec node agent-runtime/worker.mjs
