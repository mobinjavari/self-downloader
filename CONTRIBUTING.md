# Contributing

We'd love for you to get involved in developing this repository.

## Setup Workflow

| Command | Description |
| --- | --- |
| `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt` | Create the virtualenv and install dependencies (dev extras included) |
| `cp .env.example .env` | Copy the env template, then fill in API_ID/API_HASH from my.telegram.org |
| `.venv/bin/python console.py` | Add, edit, or delete accounts and log them in |
| `.venv/bin/python main.py` | Run the downloader locally |
| `ruff check --fix . && ruff format .` | Lint and format |

Requires Python 3.9+. There's no automated test suite yet — verify changes by running the affected flow through `main.py`/`console.py` locally.

## Schema Workflow

- `src/config.py` loads and validates settings from the environment.
- `src/db.py` persists accounts in SQLite.
- `src/messages.py` centralizes every user-facing string and log template so the logic files stay free of text literals.
- `src/client.py` builds a Telethon client per account and implements the media-saving flow.
- `src/runner.py` starts all enabled accounts and keeps them running concurrently, isolating failures per account.
- `main.py` is the process entry point.
- `console.py` is the interactive CLI for managing accounts and logging in.
- `scripts/` deploys and supervises the process on shared hosting without root access: `deploy.sh` (full deploy, called by `.cpanel.yml`), `appctl.sh` (start/stop/restart/watchdog/status via a PID file), `install-cron.sh` (installs the watchdog and boot-start cron entries).

## Contribution Workflow

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/). Branch off `main` and open a pull request for review.
