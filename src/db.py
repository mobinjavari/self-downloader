from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator

from src.config import settings


@dataclass
class Account:
    id: int
    label: str
    session_string: str
    is_enabled: bool
    save_normal_media: bool
    save_timed_media: bool
    created_at: str
    updated_at: str


SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL UNIQUE,
    session_string TEXT NOT NULL,
    is_enabled INTEGER NOT NULL DEFAULT 1,
    save_normal_media INTEGER NOT NULL DEFAULT 1,
    save_timed_media INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(settings.db_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as connection:
        connection.execute(SCHEMA)


def _row_to_account(row: sqlite3.Row) -> Account:
    return Account(
        id=row["id"],
        label=row["label"],
        session_string=row["session_string"],
        is_enabled=bool(row["is_enabled"]),
        save_normal_media=bool(row["save_normal_media"]),
        save_timed_media=bool(row["save_timed_media"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def list_accounts() -> list[Account]:
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM accounts ORDER BY id").fetchall()
    return [_row_to_account(row) for row in rows]


def list_enabled_accounts() -> list[Account]:
    return [account for account in list_accounts() if account.is_enabled]


def get_account(label: str) -> Account | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM accounts WHERE label = ?", (label,)).fetchone()
    return _row_to_account(row) if row else None


def add_account(
    label: str,
    session_string: str,
    save_normal_media: bool = True,
    save_timed_media: bool = True,
) -> Account:
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO accounts "
            "(label, session_string, is_enabled, save_normal_media, save_timed_media, created_at, updated_at) "
            "VALUES (?, ?, 1, ?, ?, ?, ?)",
            (label, session_string, int(save_normal_media), int(save_timed_media), now, now),
        )
    account = get_account(label)
    assert account is not None
    return account


def update_account(label: str, **fields: bool | str) -> None:
    if not fields:
        return
    now = datetime.now().isoformat(timespec="seconds")
    assignments = ", ".join(f"{key} = ?" for key in fields)
    values = [int(value) if isinstance(value, bool) else value for value in fields.values()]
    with get_connection() as connection:
        connection.execute(
            f"UPDATE accounts SET {assignments}, updated_at = ? WHERE label = ?",
            (*values, now, label),
        )


def delete_account(label: str) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM accounts WHERE label = ?", (label,))
