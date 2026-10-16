#!/usr/bin/env bash
# (Re)installs this project's two crontab entries: a 5-minute watchdog and an
# @reboot start. Idempotent — replaces its own previous entries, not duplicates.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MARKER="# self-downloader-appctl (managed by scripts/install-cron.sh, do not edit by hand)"

mkdir -p "$PROJECT_DIR/storage/logs"

NEW_LINES="$MARKER
*/5 * * * * cd $PROJECT_DIR && bash scripts/appctl.sh watchdog >> storage/logs/watchdog.log 2>&1
@reboot cd $PROJECT_DIR && bash scripts/appctl.sh start >> storage/logs/watchdog.log 2>&1"

{
    # `|| true`: no existing crontab (first install) is normal, not an error.
    crontab -l 2>/dev/null | grep -vF "scripts/appctl.sh" | grep -vF "$MARKER" || true
    echo "$NEW_LINES"
} | crontab -

echo "==> Cron watchdog (every 5m) and @reboot start entry installed."
