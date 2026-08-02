#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="self-downloader"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SERVICE_USER="$(whoami)"

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
    if [ ! -f "$VENV_DIR/bin/python" ]; then
        echo "Virtual environment not found. Run '$0 setup' first."
        exit 1
    fi

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
    ensure_service_installed
    sudo systemctl start "$SERVICE_NAME"
    show_status
}

stop_service() {
    sudo systemctl stop "$SERVICE_NAME"
    show_status
}

restart_service() {
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
    "$VENV_DIR/bin/python" "$PROJECT_DIR/console.py"
}

show_menu() {
    echo ""
    echo "===== Self-Downloader Manager ====="
    echo "1) Setup (venv + requirements)"
    echo "2) Install/update systemd service"
    echo "3) Start service"
    echo "4) Stop service"
    echo "5) Restart service"
    echo "6) Show status"
    echo "7) Show logs"
    echo "8) Uninstall service"
    echo "9) Manage accounts"
    echo "0) Exit"
    echo "===================================="
    read -rp "Choose an option: " choice
    case "$choice" in
        1) setup ;;
        2) install_service ;;
        3) start_service ;;
        4) stop_service ;;
        5) restart_service ;;
        6) show_status ;;
        7) show_logs ;;
        8) uninstall_service ;;
        9) manage_accounts ;;
        0) exit 0 ;;
        *) echo "Invalid option." ;;
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
    "")
        while true; do
            show_menu
        done
        ;;
    *)
        echo "Usage: $0 {setup|install|start|stop|restart|status|logs|uninstall|accounts}"
        exit 1
        ;;
esac
