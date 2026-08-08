#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST="${WEB_SERVER_HOST:-127.0.0.1}"
PORT="${WEB_SERVER_PORT:-8080}"
WEBHOOK_PATH="${WEBHOOK_PATH:-/webhook}"
PYTHON_BIN="${PYTHON_BIN:-${PROJECT_DIR}/.venv/bin/python}"

cd "$PROJECT_DIR"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python interpreter not found at $PYTHON_BIN" >&2
  exit 1
fi

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared is not installed or not available in PATH." >&2
  exit 1
fi

BASE_URL="${1:-}"

if [[ -z "$BASE_URL" ]]; then
  LOG_FILE="${TMPDIR:-/tmp}/cloudflared-ismobot.log"
  STDOUT_LOG="${TMPDIR:-/tmp}/cloudflared-ismobot.stdout"
  : > "$LOG_FILE"
  : > "$STDOUT_LOG"

  cloudflared tunnel --url "http://${HOST}:${PORT}" --no-autoupdate --logfile "$LOG_FILE" > "$STDOUT_LOG" 2>&1 &
  CLOUD_PID=$!

  cleanup() {
    if [[ -n "${CLOUD_PID:-}" ]]; then
      kill "$CLOUD_PID" >/dev/null 2>&1 || true
    fi
  }
  trap cleanup EXIT INT TERM

  for _ in $(seq 1 60); do
    if BASE_URL=$(grep -Eo 'https://[-a-zA-Z0-9.]+\.trycloudflare\.com' "$LOG_FILE" | head -n 1 2>/dev/null); then
      if [[ -n "$BASE_URL" ]]; then
        break
      fi
    fi
    sleep 1
  done

  if [[ -z "${BASE_URL:-}" ]]; then
    echo "Could not detect a Cloudflare tunnel URL from the cloudflared logs." >&2
    exit 1
  fi
fi

export BASE_WEBHOOK_URL="$BASE_URL"
export WEBHOOK_URL="${BASE_URL}${WEBHOOK_PATH}"

echo "Using webhook URL: ${WEBHOOK_URL}"
"$PYTHON_BIN" main.py "$BASE_URL"