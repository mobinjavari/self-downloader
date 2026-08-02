#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="self-downloader"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SERVICE_USER="$(whoami)"
PID_FILE="$PROJECT_DIR/main.pid"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/self-downloader.log"

check_venv() {
    if [ ! -f "$VENV_DIR/bin/python" ]; then
        echo "Virtual environment not found. Run '$0 setup' first." >&2
        exit 1
    fi
}

check_env() {
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        echo "Error: .env not found. Run '$0 setup' first, then edit .env with your API_ID/API_HASH." >&2
        exit 1
    fi
    if grep -qE "API_ID=your_api_id|API_HASH=your_api_hash" "$PROJECT_DIR/.env"; then
        echo "Error: .env still has placeholder API_ID/API_HASH. Edit $PROJECT_DIR/.env with your real credentials from my.telegram.org." >&2
        exit 1
    fi
}

setup() {
    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
    echo "Installing requirements..."
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
        echo "Created .env from .env.example — edit it with your API_ID/API_HASH before starting."
    fi
    echo "Setup complete."
}

install_service() {
    check_venv

    echo "Writing systemd unit to $SERVICE_FILE (requires sudo)..."
    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Self Downloader - Telegram self-account media saver
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
WorkingDirectory=${PROJECT_DIR}
EnvironmentFile=${PROJECT_DIR}/.env
ExecStart=${VENV_DIR}/bin/python ${PROJECT_DIR}/main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"
    echo "Service installed and enabled."
}

ensure_service_installed() {
    if [ ! -f "$SERVICE_FILE" ]; then
        echo "Service not installed yet. Installing now..."
        install_service
    fi
}

start_service() {
    check_venv
    check_env
    ensure_service_installed
    sudo systemctl start "$SERVICE_NAME"
    show_status
}

stop_service() {
    sudo systemctl stop "$SERVICE_NAME"
    show_status
}

restart_service() {
    check_venv
    check_env
    ensure_service_installed
    sudo systemctl restart "$SERVICE_NAME"
    show_status
}

show_status() {
    sudo systemctl status "$SERVICE_NAME" --no-pager || true
}

show_logs() {
    sudo journalctl -u "$SERVICE_NAME" -f --no-pager
}

uninstall_service() {
    sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    sudo systemctl disable "$SERVICE_NAME" 2>/dev/null || true
    sudo rm -f "$SERVICE_FILE"
    sudo systemctl daemon-reload
    echo "Service uninstalled."
}

manage_accounts() {
    check_venv
    check_env
    "$VENV_DIR/bin/python" "$PROJECT_DIR/console.py"
}

is_cron_process_running() {
    [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

cron_start() {
    check_venv
    check_env
    mkdir -p "$LOG_DIR"
    if is_cron_process_running; then
        echo "Already running (pid $(cat "$PID_FILE"))."
        return
    fi
    nohup "$VENV_DIR/bin/python" "$PROJECT_DIR/main.py" >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    disown
    echo "Started (pid $(cat "$PID_FILE")). Logs: $LOG_FILE"
}

cron_stop() {
    if is_cron_process_running; then
        kill "$(cat "$PID_FILE")"
        echo "Stopped."
    else
        echo "Not running."
    fi
    rm -f "$PID_FILE"
}

cron_restart() {
    cron_stop
    cron_start
}

cron_status() {
    if is_cron_process_running; then
        echo "Running (pid $(cat "$PID_FILE"))."
    else
        echo "Not running."
    fi
}

cron_logs() {
    tail -n 100 -f "$LOG_FILE"
}

cron_watchdog() {
    check_venv
    check_env
    if ! is_cron_process_running; then
        cron_start
    fi
}

print_banner() {
    cat <<'BANNER'
 __      _  _
(_  _ |_|_ | \ _     ._ | _  _. _| _ ._
__)(/_| |  |_/(_)\/\/| ||(_)(_|(_|(/_|
BANNER
    echo "github.com/mobinjavari/self-downloader"
    echo ""
}

pause() {
    read -rp "Press Enter to continue..." _ || true
}

clear_screen() {
    clear 2>/dev/null || true
}

show_systemd_menu() {
    clear_screen
    print_banner
    echo "===== Systemd Service (root / VPS) ====="
    echo "1) Install/update service"
    echo "2) Start"
    echo "3) Stop"
    echo "4) Restart"
    echo "5) Status"
    echo "6) Logs"
    echo "7) Uninstall"
    echo "0) Back"
    echo "=========================================="
    read -rp "Choose an option: " choice
    case "$choice" in
        1) install_service; pause ;;
        2) start_service; pause ;;
        3) stop_service; pause ;;
        4) restart_service; pause ;;
        5) show_status; pause ;;
        6) show_logs ;;
        7) uninstall_service; pause ;;
        0) return 1 ;;
        *) echo "Invalid option."; pause ;;
    esac
}

show_cron_menu() {
    clear_screen
    print_banner
    echo "===== No-root Process (cPanel / shared hosting) ====="
    echo "1) Start"
    echo "2) Stop"
    echo "3) Restart"
    echo "4) Status"
    echo "5) Logs"
    echo "0) Back"
    echo "======================================================="
    read -rp "Choose an option: " choice
    case "$choice" in
        1) cron_start; pause ;;
        2) cron_stop; pause ;;
        3) cron_restart; pause ;;
        4) cron_status; pause ;;
        5) cron_logs ;;
        0) return 1 ;;
        *) echo "Invalid option."; pause ;;
    esac
}

show_menu() {
    clear_screen
    print_banner
    echo "===== Self-Downloader Manager ====="
    echo "1) Setup (venv + requirements)"
    echo "2) Manage accounts"
    echo "3) Systemd service (root / VPS) >"
    echo "4) No-root process (cPanel / shared hosting) >"
    echo "0) Exit"
    echo "===================================="
    read -rp "Choose an option: " choice
    case "$choice" in
        1) setup; pause ;;
        2) manage_accounts ;;
        3) while show_systemd_menu; do :; done ;;
        4) while show_cron_menu; do :; done ;;
        0) exit 0 ;;
        *) echo "Invalid option."; pause ;;
    esac
}

case "${1:-}" in
    setup) setup ;;
    install) install_service ;;
    start) start_service ;;
    stop) stop_service ;;
    restart) restart_service ;;
    status) show_status ;;
    logs) show_logs ;;
    uninstall) uninstall_service ;;
    accounts) manage_accounts ;;
    cron-start) cron_start ;;
    cron-restart) cron_restart ;;
    cron-stop) cron_stop ;;
    cron-status) cron_status ;;
    cron-logs) cron_logs ;;
    cron-watchdog) cron_watchdog ;;
    "")
        while true; do
            show_menu
        done
        ;;
    *)
        echo "Usage: $0 {setup|install|start|stop|restart|status|logs|uninstall|accounts|cron-start|cron-restart|cron-stop|cron-status|cron-logs|cron-watchdog}"
        exit 1
        ;;
esac
