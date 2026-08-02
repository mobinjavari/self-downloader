import asyncio

from rich.console import Console
from rich.table import Table
from telethon import TelegramClient
from telethon.sessions import StringSession

from src.config import settings
from src.db import (
    add_account,
    delete_account,
    get_account,
    init_db,
    list_accounts,
    update_account,
)

console = Console()


def render_accounts() -> None:
    accounts = list_accounts()
    table = Table(title="Self-Downloader Accounts", show_lines=True)
    table.add_column("ID", justify="right")
    table.add_column("Label")
    table.add_column("Enabled", justify="center")
    table.add_column("Normal media", justify="center")
    table.add_column("Timed media", justify="center")
    table.add_column("Updated at")

    if not accounts:
        console.print("[yellow]No accounts yet.[/yellow]")
        return

    for account in accounts:
        table.add_row(
            str(account.id),
            account.label,
            "Yes" if account.is_enabled else "No",
            "Yes" if account.save_normal_media else "No",
            "Yes" if account.save_timed_media else "No",
            account.updated_at,
        )
    console.print(table)


def prompt_bool(question: str, default: bool = True) -> bool:
    suffix = "Y/n" if default else "y/N"
    answer = console.input(f"{question} [{suffix}]: ").strip().lower()
    if not answer:
        return default
    return answer in {"y", "yes"}


async def login_account() -> str:
    client = TelegramClient(StringSession(), settings.api_id, settings.api_hash)
    await client.start()
    me = await client.get_me()
    console.print(f"[green]Logged in as {me.first_name} ({me.id})[/green]")
    session_string = client.session.save()
    await client.disconnect()
    return session_string


def add_account_flow() -> None:
    label = console.input("Account label (unique, e.g. main): ").strip()
    if not label:
        console.print("[red]Label cannot be empty.[/red]")
        return
    if get_account(label):
        console.print("[red]An account with this label already exists.[/red]")
        return

    save_normal_media = prompt_bool("Save normal media?", True)
    save_timed_media = prompt_bool("Save timed (self-destructing) media?", True)

    console.print("Starting Telegram login...")
    session_string = asyncio.run(login_account())

    add_account(
        label,
        session_string=session_string,
        save_normal_media=save_normal_media,
        save_timed_media=save_timed_media,
    )
    console.print("[green]Account added.[/green]")


def edit_account_flow() -> None:
    render_accounts()
    label = console.input("Label of the account to edit: ").strip()
    account = get_account(label)
    if not account:
        console.print("[red]Account not found.[/red]")
        return

    is_enabled = prompt_bool("Enabled?", account.is_enabled)
    save_normal_media = prompt_bool("Save normal media?", account.save_normal_media)
    save_timed_media = prompt_bool("Save timed media?", account.save_timed_media)

    update_account(
        label,
        is_enabled=is_enabled,
        save_normal_media=save_normal_media,
        save_timed_media=save_timed_media,
    )
    console.print("[green]Account updated.[/green]")


def delete_account_flow() -> None:
    render_accounts()
    label = console.input("Label of the account to delete: ").strip()
    if not get_account(label):
        console.print("[red]Account not found.[/red]")
        return
    if prompt_bool(f"Delete '{label}'? This cannot be undone.", False):
        delete_account(label)
        console.print("[green]Account deleted.[/green]")


MENU = """
[bold cyan]Self-Downloader Account Manager[/bold cyan]
1) List accounts
2) Add account (and log in)
3) Edit account
4) Delete account
0) Exit
"""


def main() -> None:
    init_db()

    actions = {
        "1": render_accounts,
        "2": add_account_flow,
        "3": edit_account_flow,
        "4": delete_account_flow,
    }

    while True:
        console.print(MENU)
        choice = console.input("Choose an option: ").strip()
        if choice == "0":
            break
        action = actions.get(choice)
        if action is None:
            console.print("[red]Invalid option.[/red]")
            continue
        action()


if __name__ == "__main__":
    main()
