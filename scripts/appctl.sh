#!/usr/bin/env bash
# Start/stop/restart/watchdog control for main.py via a PID file — used by
# scripts/deploy.sh and the cron watchdog.
#
# Usage: scripts/appctl.sh {start|stop|restart|watchdog|status}

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
RUN_DIR="$PROJECT_DIR/run"
LOG_DIR="$PROJECT_DIR/logs"
LOCK_DIR="$RUN_DIR/appctl.lock.d"
PID_FILE="$RUN_DIR/main.pid"
LOG_FILE="$LOG_DIR/main.log"

mkdir -p "$RUN_DIR" "$LOG_DIR"

_acquire_lock() {
    # mkdir is atomic on every filesystem (including NFS); a plain lockfile or
    # flock isn't reliably so. Self-heals a stale lock left by a holder that
    # died without cleaning up, by checking whether its recorded pid is alive.
    if mkdir "$LOCK_DIR" 2>/dev/null; then
        echo $$ >"$LOCK_DIR/pid"
        trap 'rm -rf "$LOCK_DIR"' EXIT
        return 0
    fi
    local holder
    holder="$(cat "$LOCK_DIR/pid" 2>/dev/null || true)"
    if [[ -n "$holder" ]] && kill -0 "$holder" 2>/dev/null; then
        return 1
    fi
    rm -rf "$LOCK_DIR" 2>/dev/null || true
    if mkdir "$LOCK_DIR" 2>/dev/null; then
        echo $$ >"$LOCK_DIR/pid"
        trap 'rm -rf "$LOCK_DIR"' EXIT
        return 0
    fi
    return 1
}

_is_running() {
    [[ -f "$PID_FILE" ]] || return 1
    kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

_start() {
    if _is_running; then
        echo "==> main already running (pid $(cat "$PID_FILE"))"
        return 0
    fi
    if [[ ! -x "$VENV_DIR/bin/python" ]]; then
        echo "!! $VENV_DIR/bin/python not found — run scripts/deploy.sh first." >&2
        return 1
    fi
    # Our own pidfile says nothing is running, but that only tracks what WE
    # started — a stray instance started outside appctl.sh (manual testing, an
    # old pre-appctl deploy) wouldn't be in it. Starting blind on top of one
    # means two clients polling the same Telegram sessions at once.
    local stray
    stray="$(pgrep -f "$VENV_DIR/bin/python $PROJECT_DIR/main.py" || true)"
    if [[ -n "$stray" ]]; then
        echo "!! main already running untracked (pid(s): $stray, not in $PID_FILE) — kill it first." >&2
        return 1
    fi
    echo "==> Starting main..."
    PYTHONUNBUFFERED=1 nohup "$VENV_DIR/bin/python" "$PROJECT_DIR/main.py" >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
}

_stop() {
    _is_running || { echo "==> main not running"; return 0; }
    local pid
    pid="$(cat "$PID_FILE")"
    echo "==> Stopping main (pid $pid)..."
    kill -TERM "$pid" 2>/dev/null || true
    for _ in $(seq 1 10); do
        kill -0 "$pid" 2>/dev/null || break
        sleep 1
    done
    if kill -0 "$pid" 2>/dev/null; then
        kill -KILL "$pid" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
}

cmd="${1:-}"

case "$cmd" in
    start|stop|restart|watchdog)
        _acquire_lock || { echo "==> Another appctl run is in progress, skipping"; exit 0; }
        case "$cmd" in
            start)    _start ;;
            stop)     _stop ;;
            restart)  _stop; _start ;;
            watchdog) _is_running || _start ;;
        esac
        ;;
    status)
        if _is_running; then
            echo "main: running (pid $(cat "$PID_FILE"))"
        else
            echo "main: stopped"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|watchdog|status}" >&2
        exit 1
        ;;
esac
