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

- `src/` holds the core application logic: settings loading/validation, account persistence, the Telegram client and media-saving flow, the multi-account runner, and the centralized user-facing text/log templates.
- The project root holds the two entry points: the unattended downloader process and the interactive account-management CLI.
- `scripts/` holds the deployment and process-supervision tooling used to run the project on shared hosting without root access.

## Contribution Workflow

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/). Branch off `main` and open a pull request for review.
