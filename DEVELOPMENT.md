# Development

## Architecture

| File | Responsibility |
| --- | --- |
| `src/config.py` | Loads `.env` into a `Settings` dataclass (`API_ID`, `API_HASH`, paths, `DELETE_MEDIA_AFTER_UPLOAD`, log level) |
| `src/db.py` | SQLite schema and CRUD for the `accounts` table |
| `src/client.py` | Builds one Telethon `TelegramClient` per account and implements the save flow: forward first, fall back to download + re-upload, then delete the local file per `DELETE_MEDIA_AFTER_UPLOAD` |
| `src/runner.py` | Loads all enabled, authorized accounts and runs their clients concurrently in one asyncio loop |
| `main.py` | Process entry point, used by the systemd service |
| `console.py` | Rich-table CLI to add/edit/delete accounts and run the interactive Telethon login |
| `manage.sh` | venv setup and systemd service lifecycle |

All accounts share one `API_ID`/`API_HASH` app registration from `.env`; what distinguishes accounts is their own Telethon session, stored as a `StringSession` string directly in the `accounts` table (no session files on disk). Treat the SQLite file as a secret — it holds live login credentials.

## Commands

All commands run through `manage.sh` at the project root. With no argument it opens the same options as an interactive menu.

| Command | Description |
| --- | --- |
| `./manage.sh setup` | Create the venv, install `requirements.txt`, generate `.env` from `.env.example` if missing |
| `./manage.sh accounts` | Open `console.py` to add, edit, or delete accounts and log in |
| `./manage.sh install` | Write and enable the systemd unit (`sudo` required) |
| `./manage.sh start` | Start the service (installs it first if missing) |
| `./manage.sh stop` | Stop the service |
| `./manage.sh restart` | Restart the service (installs it first if missing) |
| `./manage.sh status` | Show `systemctl status` for the service |
| `./manage.sh logs` | Follow the service logs (`journalctl -f`) |
| `./manage.sh uninstall` | Stop, disable, and remove the systemd unit |

`./manage.sh accounts` logs in via Telethon, saves the resulting session string to the database, and registers the account. Only accounts with a valid stored session are picked up by `runner.py`.

## Running locally without systemd

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main.py
```

---
Developed with the help of [Claude](https://claude.com/claude-code).
