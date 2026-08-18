#!/usr/bin/env bash
set -euo pipefail
if [[ $EUID -ne 0 ]]; then SUDO=sudo; else SUDO=; fi
$SUDO apt-get update
$SUDO apt-get install -y xvfb openbox chromium x11vnc websockify scrot python3 python3-venv nodejs npm
$SUDO apt-get install -y novnc || true
python3 -m venv .agent-runtime-venv
.agent-runtime-venv/bin/pip install --upgrade pip pyautogui pillow python-xlib
printf '%s\n' 'Agent runtime dependencies installed.'
