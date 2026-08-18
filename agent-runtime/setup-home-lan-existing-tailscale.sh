#!/usr/bin/env bash
set -euo pipefail

RUNTIME_URL="${AGENT_RUNTIME_URL:-https://jlvozmgxxojvljxuhywv.supabase.co/functions/v1/agent-runtime}"
WORKER_ID="${AGENT_WORKER_ID:-home-lan}"
ENROLLMENT_CODE="${AGENT_ENROLLMENT_CODE:-}"
INSTALL_GUI="${INSTALL_GUI:-1}"
INSTALL_DIR="${AGENT_INSTALL_DIR:-/opt/mcp-ephemeral-runner}"
SERVICE_USER="${AGENT_SERVICE_USER:-agent-worker}"

if [[ ${EUID} -ne 0 ]]; then
  echo "Run as root: sudo -E bash $0" >&2
  exit 2
fi
if [[ -z "$ENROLLMENT_CODE" ]]; then
  echo "AGENT_ENROLLMENT_CODE is required" >&2
  exit 2
fi
if ! command -v tailscale >/dev/null 2>&1; then
  echo "Tailscale is not installed. This bootstrap is for an existing Tailscale node." >&2
  exit 3
fi
TS_IP="$(tailscale ip -4 2>/dev/null | head -n1 || true)"
if [[ -z "$TS_IP" ]]; then
  echo "Tailscale is installed but this node is not connected to a tailnet." >&2
  exit 3
fi

echo "Existing Tailscale node detected: $TS_IP"

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git curl ca-certificates nodejs npm openssl python3 python3-venv
if [[ "$INSTALL_GUI" == "1" ]]; then
  apt-get install -y -qq xvfb openbox chromium x11vnc websockify scrot || true
  apt-get install -y -qq novnc || true
fi

NODE_MAJOR="$(node -p "Number(process.versions.node.split('.')[0])")"
if (( NODE_MAJOR < 18 )); then
  echo "Node.js >=18 is required; installed version is $(node --version)." >&2
  exit 4
fi

if id "$SERVICE_USER" >/dev/null 2>&1; then
  :
else
  useradd --system --create-home --home-dir /var/lib/agent-runtime --shell /usr/sbin/nologin "$SERVICE_USER"
fi

if [[ -d "$INSTALL_DIR/.git" ]]; then
  git -C "$INSTALL_DIR" fetch origin main
  git -C "$INSTALL_DIR" checkout main
  git -C "$INSTALL_DIR" pull --ff-only origin main
else
  rm -rf "$INSTALL_DIR"
  git clone --depth 1 https://github.com/agentpixelated/mcp-ephemeral-runner.git "$INSTALL_DIR"
fi

if [[ "$INSTALL_GUI" == "1" ]]; then
  python3 -m venv "$INSTALL_DIR/.agent-runtime-venv"
  "$INSTALL_DIR/.agent-runtime-venv/bin/pip" install --quiet --upgrade pip pyautogui pillow python-xlib
fi

WORKER_TOKEN="arw_$(openssl rand -hex 32)"
TOKEN_SHA="$(printf '%s' "$WORKER_TOKEN" | sha256sum | awk '{print $1}')"
ENROLL_JSON="$(python3 - "$WORKER_ID" "$ENROLLMENT_CODE" "$TOKEN_SHA" <<'PY'
import json, sys
print(json.dumps({
  'action': 'enroll',
  'worker_id': sys.argv[1],
  'enrollment_code': sys.argv[2],
  'token_sha256': sys.argv[3],
}))
PY
)"
ENROLL_RESPONSE="$(curl --fail-with-body --silent --show-error \
  -H 'content-type: application/json' \
  --data "$ENROLL_JSON" \
  "$RUNTIME_URL")"
python3 - "$ENROLL_RESPONSE" <<'PY'
import json, sys
obj=json.loads(sys.argv[1])
if obj.get('ok') is not True:
    raise SystemExit(f"Enrollment failed: {obj}")
print(f"Enrolled worker: {obj.get('worker_id')}")
PY

install -d -m 700 /etc/agent-runtime
umask 077
cat >/etc/agent-runtime/home-lan.env <<EOF
AGENT_RUNTIME_URL=$RUNTIME_URL
AGENT_WORKER_ID=$WORKER_ID
AGENT_WORKER_TOKEN=$WORKER_TOKEN
AGENT_POLL_MS=3000
AGENT_PYTHON=$INSTALL_DIR/.agent-runtime-venv/bin/python
EOF
chmod 600 /etc/agent-runtime/home-lan.env

chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
install -d -o "$SERVICE_USER" -g "$SERVICE_USER" -m 750 /var/lib/agent-runtime

cat >/etc/systemd/system/agent-home-lan.service <<EOF
[Unit]
Description=Universal Agent Runtime home-lan worker
After=network-online.target tailscaled.service
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=/etc/agent-runtime/home-lan.env
ExecStart=/usr/bin/node $INSTALL_DIR/agent-runtime/worker.mjs
Restart=always
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
UMask=0077

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now agent-home-lan.service
sleep 2
systemctl --no-pager --full status agent-home-lan.service || true

echo
echo "home-lan installed."
echo "Tailscale IPv4: $TS_IP"
echo "Service: agent-home-lan.service"
echo "No Tailscale login, routes, SSH settings, or tailnet ACLs were modified."
echo "Logs: journalctl -u agent-home-lan -f"
