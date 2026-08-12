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

exec "$PYTHON_BIN" main.py 
