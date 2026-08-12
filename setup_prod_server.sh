#!/usr/bin/env bash
set -euo pipefail

# Usage: sudo ./setup_prod_server.sh [--target /opt/ismobot] [--user ismobot]

TARGET_DIR="/opt/ismobot"
SERVICE_NAME="ismobot"
SERVICE_FILE_SOURCE="$(pwd)/ismobot.service"
SYSTEM_SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SYSTEM_USER="ismogroup"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET_DIR="$2"; shift 2;;
    --user) SYSTEM_USER="$2"; shift 2;;
    --service-file) SERVICE_FILE_SOURCE="$2"; shift 2;;
    --help|-h) echo "Usage: sudo $0 [--target DIR] [--user NAME]"; exit 0;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root (sudo)." >&2
  exit 1
fi

set -x

# Create system user if it doesn't exist
if ! id -u "$SYSTEM_USER" >/dev/null 2>&1; then
  useradd --system --create-home --home-dir "$TARGET_DIR" --shell /usr/sbin/nologin "$SYSTEM_USER"
fi

# Copy project to target
rm -rf "$TARGET_DIR/.deploy_tmp" || true
mkdir -p "$TARGET_DIR/.deploy_tmp"
rsync -a --delete --exclude='.venv' ./ "$TARGET_DIR/.deploy_tmp/"
mkdir -p "$TARGET_DIR"
chown -R "$SYSTEM_USER":"$SYSTEM_USER" "$TARGET_DIR/.deploy_tmp"
mv "$TARGET_DIR/.deploy_tmp"/* "$TARGET_DIR" || true
rm -rf "$TARGET_DIR/.deploy_tmp"

# Create virtualenv and install dependencies
python3 -m venv "$TARGET_DIR/venv"
"$TARGET_DIR/venv/bin/pip" install --upgrade pip
if [[ -f "$TARGET_DIR/requirements.txt" ]]; then
  "$TARGET_DIR/venv/bin/pip" install -r "$TARGET_DIR/requirements.txt"
fi

# Ensure scripts are executable
chmod +x "$TARGET_DIR/run_bot_prod.sh"

# Copy systemd unit file (use the provided template)
cp "$SERVICE_FILE_SOURCE" "$SYSTEM_SERVICE_FILE"
sed -i "s|WorkingDirectory=.*|WorkingDirectory=${TARGET_DIR}|" "$SYSTEM_SERVICE_FILE"
sed -i "s|ExecStart=.*|ExecStart=${TARGET_DIR}/run_bot_prod.sh|" "$SYSTEM_SERVICE_FILE"
sed -i "s|User=.*|User=${SYSTEM_USER}|" "$SYSTEM_SERVICE_FILE"

# Create log directory
mkdir -p /var/log/ismobot
chown -R "$SYSTEM_USER":"$SYSTEM_USER" /var/log/ismobot

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME".service

echo "Deployment complete. Service: $SYSTEM_SERVICE_FILE"
set +x
