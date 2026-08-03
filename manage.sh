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

if [ -t 1 ]; then
    C_RESET=$'\033[0m'
    C_BOLD=$'\033[1m'
    C_DIM=$'\033[2m'
    C_RED=$'\033[31m'
    C_GREEN=$'\033[32m'
    C_YELLOW=$'\033[33m'
    C_CYAN=$'\033[36m'
else
    C_RESET='' C_BOLD='' C_DIM='' C_RED='' C_GREEN='' C_YELLOW='' C_CYAN=''
fi

info()    { echo "${C_CYAN}${*}${C_RESET}"; }
success() { echo "${C_GREEN}${*}${C_RESET}"; }
warn()    { echo "${C_YELLOW}${*}${C_RESET}"; }
fail()    { echo "${C_RED}${*}${C_RESET}" >&2; }

# Draws a bordered table with a title row and one row per "key::label" entry.
# The key gets its own color (red for "0", green otherwise) so exit/back options stand out.
draw_menu() {
    local title="$1"; shift
    local entries=("$@")

    local maxlen=${#title}
    local key label content
    local -a contents=() colors=()
    for entry in "${entries[@]}"; do
        key="${entry%%::*}"
        label="${entry#*::}"
        content="$(printf '%s) %s' "$key" "$label")"
        contents+=("$content")
        if [ "$key" = "0" ]; then
            colors+=("$C_RED")
        else
            colors+=("$C_GREEN")
        fi
        (( ${#content} > maxlen )) && maxlen=${#content}
    done

    local width=$((maxlen + 2))
    local border
    border="$(printf -- '-%.0s' $(seq 1 $((width + 2))))"

    echo "${C_CYAN}+${border}+${C_RESET}"
    printf "${C_CYAN}|${C_RESET} ${C_BOLD}%-*s${C_RESET} ${C_CYAN}|${C_RESET}\n" "$width" "$title"
    echo "${C_CYAN}+${border}+${C_RESET}"
    for i in "${!contents[@]}"; do
        printf "${C_CYAN}|${C_RESET} %s%-*s${C_RESET} ${C_CYAN}|${C_RESET}\n" "${colors[$i]}" "$width" "${contents[$i]}"
    done
    echo "${C_CYAN}+${border}+${C_RESET}"
}

check_venv() {
    if [ ! -f "$VENV_DIR/bin/python" ]; then
        fail "Virtual environment not found. Run '$0 setup' first."
        exit 1
    fi
}

check_env() {
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        fail "Error: .env not found. Run '$0 setup' first, then edit .env with your API_ID/API_HASH."
        exit 1
    fi
    if grep -qE "API_ID=your_api_id|API_HASH=your_api_hash" "$PROJECT_DIR/.env"; then
        fail "Error: .env still has placeholder API_ID/API_HASH. Edit $PROJECT_DIR/.env with your real credentials from my.telegram.org."
        exit 1
    fi
}

setup() {
    if [ ! -d "$VENV_DIR" ]; then
        info "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
    info "Installing requirements..."
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
        warn "Created .env from .env.example — edit it with your API_ID/API_HASH before starting."
    fi
    success "Setup complete."
}

install_service() {
    check_venv

    info "Writing systemd unit to $SERVICE_FILE (requires sudo)..."
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
    success "Service installed and enabled."
}

ensure_service_installed() {
    if [ ! -f "$SERVICE_FILE" ]; then
        warn "Service not installed yet. Installing now..."
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
    success "Service uninstalled."
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
        warn "Already running (pid $(cat "$PID_FILE"))."
        return
    fi
    nohup "$VENV_DIR/bin/python" "$PROJECT_DIR/main.py" >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    disown
    success "Started (pid $(cat "$PID_FILE")). Logs: $LOG_FILE"
}

cron_stop() {
    if is_cron_process_running; then
        kill "$(cat "$PID_FILE")"
        success "Stopped."
    else
        warn "Not running."
    fi
    rm -f "$PID_FILE"
}

cron_restart() {
    cron_stop
    cron_start
}

cron_status() {
    if is_cron_process_running; then
        success "Running (pid $(cat "$PID_FILE"))."
    else
        warn "Not running."
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
    echo "${C_CYAN}${C_BOLD}"
    cat <<'BANNER'
███████╗███████╗██╗     ███████╗
██╔════╝██╔════╝██║     ██╔════╝
███████╗█████╗  ██║     █████╗
╚════██║██╔══╝  ██║     ██╔══╝
███████║███████╗███████╗██║
╚══════╝╚══════╝╚══════╝╚═╝

██████╗  ██████╗ ██╗    ██╗███╗   ██╗██╗      ██████╗  █████╗ ██████╗ ███████╗██████╗
██╔══██╗██╔═══██╗██║    ██║████╗  ██║██║     ██╔═══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
██║  ██║██║   ██║██║ █╗ ██║██╔██╗ ██║██║     ██║   ██║███████║██║  ██║█████╗  ██████╔╝
██║  ██║██║   ██║██║███╗██║██║╚██╗██║██║     ██║   ██║██╔══██║██║  ██║██╔══╝  ██╔══██╗
██████╔╝╚██████╔╝╚███╔███╔╝██║ ╚████║███████╗╚██████╔╝██║  ██║██████╔╝███████╗██║  ██║
╚═════╝  ╚═════╝  ╚══╝╚══╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝
BANNER
    echo "${C_RESET}"
    echo "${C_DIM}~> github.com/mobinjavari/self-downloader${C_RESET}"
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
    draw_menu "Systemd Service (root / VPS)" \
        "1::Install/update service" \
        "2::Start" \
        "3::Stop" \
        "4::Restart" \
        "5::Status" \
        "6::Logs" \
        "7::Uninstall" \
        "0::Back"
    read -rp "${C_YELLOW}Choose an option: ${C_RESET}" choice
    case "$choice" in
        1) install_service; pause ;;
        2) start_service; pause ;;
        3) stop_service; pause ;;
        4) restart_service; pause ;;
        5) show_status; pause ;;
        6) show_logs ;;
        7) uninstall_service; pause ;;
        0) return 1 ;;
        *) fail "Invalid option."; pause ;;
    esac
}

show_cron_menu() {
    clear_screen
    print_banner
    draw_menu "No-root Process (cPanel / shared hosting)" \
        "1::Start" \
        "2::Stop" \
        "3::Restart" \
        "4::Status" \
        "5::Logs" \
        "0::Back"
    read -rp "${C_YELLOW}Choose an option: ${C_RESET}" choice
    case "$choice" in
        1) cron_start; pause ;;
        2) cron_stop; pause ;;
        3) cron_restart; pause ;;
        4) cron_status; pause ;;
        5) cron_logs ;;
        0) return 1 ;;
        *) fail "Invalid option."; pause ;;
    esac
}

show_menu() {
    clear_screen
    print_banner
    draw_menu "Self-Downloader Manager" \
        "1::Setup (venv + requirements)" \
        "2::Manage accounts" \
        "3::Systemd service (root / VPS) >" \
        "4::No-root process (cPanel / shared hosting) >" \
        "0::Exit"
    read -rp "${C_YELLOW}Choose an option: ${C_RESET}" choice
    case "$choice" in
        1) setup; pause ;;
        2) manage_accounts ;;
        3) while show_systemd_menu; do :; done ;;
        4) while show_cron_menu; do :; done ;;
        0) exit 0 ;;
        *) fail "Invalid option."; pause ;;
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
        fail "Usage: $0 {setup|install|start|stop|restart|status|logs|uninstall|accounts|cron-start|cron-restart|cron-stop|cron-status|cron-logs|cron-watchdog}"
        exit 1
        ;;
esac
