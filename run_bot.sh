#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-${PROJECT_DIR}/.venv/bin/python}"
STATE_FILE="${XDG_STATE_HOME:-$HOME/.local/state}/ismobot/base_webhook_url"

cd "$PROJECT_DIR"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python interpreter not found at $PYTHON_BIN" >&2
  exit 1
fi

if [[ ! -f "$STATE_FILE" ]]; then
  echo "Cloudflare tunnel URL file not found: $STATE_FILE" >&2
  echo "Start the tunnel service first." >&2
  exit 1
fi

BASE_URL="$(<"$STATE_FILE")"
if [[ -z "$BASE_URL" ]]; then
  echo "Cloudflare tunnel URL file is empty: $STATE_FILE" >&2
  exit 1
fi

export BASE_WEBHOOK_URL="$BASE_URL"
echo "Starting bot with webhook URL: ${BASE_WEBHOOK_URL}"
exec "$PYTHON_BIN" main.py "$BASE_URL"