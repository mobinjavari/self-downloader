#!/usr/bin/env bash
# Full deploy: stop, install deps, (re)install the cron watchdog, start again.
# Called by .cpanel.yml. Safe to re-run any number of times.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

cd "$PROJECT_DIR"

echo "==> Stopping any running process..."
bash scripts/appctl.sh stop

if [[ ! -f .env ]]; then
    if [[ -f .env.example ]]; then
        cp .env.example .env
        echo "!! .env was missing, created it from .env.example — fill in API_ID/API_HASH before the app can start: $PROJECT_DIR/.env"
    else
        echo "!! Neither .env nor .env.example exists." >&2
        exit 1
    fi
fi

if [[ ! -d "$VENV_DIR" ]]; then
    echo "==> Creating virtualenv..."
    python3 -m venv "$VENV_DIR"
fi

echo "==> Installing/updating dependencies..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r requirements.txt

echo "==> Installing the cron watchdog..."
bash scripts/install-cron.sh

echo "==> Starting main..."
bash scripts/appctl.sh start

echo "==> Deploy finished. Check status with: bash scripts/appctl.sh status"
