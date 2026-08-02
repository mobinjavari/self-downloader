# Development

## Architecture

| File | Responsibility |
| --- | --- |
| `src/config.py` | Loads `.env` into a `Settings` dataclass (`API_ID`, `API_HASH`, paths, `DELETE_MEDIA_AFTER_UPLOAD`, log level); fails with a clear error on missing/placeholder/invalid values |
| `src/db.py` | SQLite schema and CRUD for the `accounts` table |
| `src/messages.py` | Every user-facing string and log template, grouped by module (`ConfigErrors`, `ClientMessages`, `ClientLogs`, `RunnerLogs`, `ConsoleMessages`) — no text literals live in the logic files |
| `src/client.py` | Builds one Telethon `TelegramClient` per account and implements the save flow: forward first, fall back to download + re-upload, then delete the local file per `DELETE_MEDIA_AFTER_UPLOAD`. Normal media gets a caption with full sender info; timed (self-destructing) media is re-uploaded as a spoiler with the sender's name linked to their profile |
| `src/runner.py` | Loads all enabled accounts, connects and authorizes them one at a time, then runs all authorized clients concurrently. A failure in one account (bad session, connection error, crash mid-run) is logged and isolated — it never takes down the others |
| `main.py` | Process entry point, used by the systemd service and the no-root process mode |
| `console.py` | Rich-table CLI to add/edit/delete accounts (selected by numeric ID) and run the interactive Telethon login. Screen clears between actions with a pause so results stay readable |
| `manage.sh` | venv setup plus two independent process-management modes (see below) |

## Process management: two modes

`manage.sh` supports two unrelated ways to keep `main.py` running, picked based on what access you have:

- **systemd** (needs root/sudo) — for a VPS you administer. Installs a proper service with auto-restart.
- **nohup + pidfile** (no root needed) — for shared hosting (e.g. cPanel) where you only have a regular shell account. Launches `main.py` detached in the background and tracks it via a pidfile; pair `cron-watchdog` with a cron job (every few minutes) so it gets relaunched if it ever dies or gets killed by the host's process limits.

Run `./manage.sh` with no arguments for an interactive menu (systemd and no-root options are in separate submenus), or use the subcommands directly:

| Command | Description |
| --- | --- |
| `./manage.sh setup` | Create the venv, install `requirements.txt`, generate `.env` from `.env.example` if missing |
| `./manage.sh accounts` | Open `console.py` to add, edit, or delete accounts and log in |
| **systemd** | |
| `./manage.sh install` | Write and enable the systemd unit (`sudo` required) |
| `./manage.sh start` / `stop` / `restart` | Control the systemd service (installs it first if missing) |
| `./manage.sh status` | Show `systemctl status` for the service |
| `./manage.sh logs` | Follow the service logs (`journalctl -f`) |
| `./manage.sh uninstall` | Stop, disable, and remove the systemd unit |
| **no-root (cron/nohup)** | |
| `./manage.sh cron-start` | Launch `main.py` detached via `nohup`, tracked by `main.pid` |
| `./manage.sh cron-stop` / `cron-restart` | Stop / restart the detached process |
| `./manage.sh cron-status` | Check whether the pidfile's process is alive |
| `./manage.sh cron-logs` | Follow `logs/self-downloader.log` |
| `./manage.sh cron-watchdog` | Start it only if it isn't already running — meant to be called from a cron job |

This logs in via Telethon, saves the resulting session string to the database, and registers the account. Only accounts with a valid stored session are picked up by `runner.py`.

## Running locally without a process manager

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Requirements

- Python 3.9+
- Either a systemd-based Linux host (for the systemd mode) or any host with a regular shell and cron (for the no-root mode)

---
Developed with the help of [Claude](https://claude.com/claude-code).
