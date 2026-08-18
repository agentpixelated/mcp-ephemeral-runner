#!/usr/bin/env sh
set -eu

RUNTIME_URL="${AGENT_RUNTIME_URL:-https://jlvozmgxxojvljxuhywv.supabase.co/functions/v1/agent-runtime}"
WORKER_ID="${AGENT_WORKER_ID:-home-lan}"
ENROLLMENT_CODE="${AGENT_ENROLLMENT_CODE:-}"
APP_DIR="${AGENT_APP_DIR:-/DATA/AppData/agent-home-lan}"
IMAGE="${AGENT_IMAGE:-agent-home-lan:local}"
CONTAINER="${AGENT_CONTAINER_NAME:-agent-home-lan}"
VOLUME="${AGENT_DATA_VOLUME:-agent-home-lan-data}"

if [ -z "$ENROLLMENT_CODE" ]; then
  echo "AGENT_ENROLLMENT_CODE is required" >&2
  exit 2
fi
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. This setup is intended for ZimaOS." >&2
  exit 3
fi

mkdir -p "$APP_DIR"
rm -rf "$APP_DIR/repo"

echo "Fetching universal agent runtime without installing Git on ZimaOS..."
docker run --rm \
  -v "$APP_DIR:/work" \
  alpine/git:latest clone --depth 1 https://github.com/agentpixelated/mcp-ephemeral-runner.git /work/repo

echo "Building isolated home-lan worker image..."
docker build \
  -t "$IMAGE" \
  -f "$APP_DIR/repo/agent-runtime/Dockerfile.zimaos" \
  "$APP_DIR/repo"

docker volume create "$VOLUME" >/dev/null

TS_IP=""
if command -v tailscale >/dev/null 2>&1; then
  TS_IP="$(tailscale ip -4 2>/dev/null | head -n1 || true)"
fi

echo "Enrolling worker. Plaintext worker token will only be written to Docker volume $VOLUME..."
docker run --rm \
  --network host \
  -e "AGENT_RUNTIME_URL=$RUNTIME_URL" \
  -e "AGENT_WORKER_ID=$WORKER_ID" \
  -e "AGENT_ENROLLMENT_CODE=$ENROLLMENT_CODE" \
  -e "AGENT_TAILSCALE_IP=$TS_IP" \
  -v "$VOLUME:/data" \
  "$IMAGE" \
  node agent-runtime/enroll-worker.mjs

docker rm -f "$CONTAINER" >/dev/null 2>&1 || true

echo "Starting persistent worker container..."
docker run -d \
  --name "$CONTAINER" \
  --restart unless-stopped \
  --init \
  --network host \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  --shm-size 1g \
  -v "$VOLUME:/data" \
  "$IMAGE" >/dev/null

sleep 3

echo
echo "Container status:"
docker ps --filter "name=^/${CONTAINER}$" --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'
echo
echo "Recent worker logs:"
docker logs --tail 20 "$CONTAINER" 2>&1 || true

echo
echo "home-lan Docker worker installed."
echo "Container: $CONTAINER"
echo "Data volume: $VOLUME"
[ -n "$TS_IP" ] && echo "Detected Tailscale IPv4: $TS_IP"
echo "No Docker socket or host filesystem is mounted into the worker."
echo "No Tailscale login, routes, SSH settings, or ACLs were modified."
