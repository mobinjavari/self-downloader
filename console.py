import asyncio
import sys

from rich.console import Console
from rich.table import Table
from telethon import TelegramClient
from telethon.sessions import StringSession

from src.messages import ConsoleMessages

console = Console()

try:
    from src.config import settings
    from src.db import (
        add_account,
        delete_account,
        get_account,
        init_db,
        list_accounts,
        update_account,
    )
except RuntimeError as e:
    console.print(ConsoleMessages.CONFIG_ERROR.format(error=e))
    sys.exit(1)


def render_accounts() -> None:
    accounts = list_accounts()
    table = Table(title=ConsoleMessages.TABLE_TITLE, show_lines=True)
    table.add_column(ConsoleMessages.COLUMN_ID, justify="right")
    table.add_column(ConsoleMessages.COLUMN_LABEL)
    table.add_column(ConsoleMessages.COLUMN_ENABLED, justify="center")
    table.add_column(ConsoleMessages.COLUMN_NORMAL_MEDIA, justify="center")
    table.add_column(ConsoleMessages.COLUMN_TIMED_MEDIA, justify="center")
    table.add_column(ConsoleMessages.COLUMN_UPDATED_AT)

    if not accounts:
        console.print(ConsoleMessages.NO_ACCOUNTS)
        return

    for account in accounts:
        table.add_row(
            str(account.id),
            account.label,
            ConsoleMessages.YES if account.is_enabled else ConsoleMessages.NO,
            ConsoleMessages.YES if account.save_normal_media else ConsoleMessages.NO,
            ConsoleMessages.YES if account.save_timed_media else ConsoleMessages.NO,
            account.updated_at,
        )
    console.print(table)


def prompt_bool(question: str, default: bool = True) -> bool:
    suffix = ConsoleMessages.SUFFIX_DEFAULT_YES if default else ConsoleMessages.SUFFIX_DEFAULT_NO
    answer = console.input(ConsoleMessages.PROMPT_BOOL.format(question=question, suffix=suffix)).strip().lower()
    if not answer:
        return default
    return answer in {"y", "yes"}


async def login_account() -> str:
    client = TelegramClient(StringSession(), settings.api_id, settings.api_hash)
    await client.start()
    me = await client.get_me()
    console.print(ConsoleMessages.LOGIN_SUCCESS.format(name=me.first_name, user_id=me.id))
    session_string = client.session.save()
    await client.disconnect()
    return session_string


def add_account_flow() -> None:
    label = console.input(ConsoleMessages.PROMPT_LABEL).strip()
    if not label:
        console.print(ConsoleMessages.LABEL_EMPTY)
        return
    if get_account(label):
        console.print(ConsoleMessages.LABEL_EXISTS)
        return

    save_normal_media = prompt_bool(ConsoleMessages.ASK_SAVE_NORMAL_MEDIA, True)
    save_timed_media = prompt_bool(ConsoleMessages.ASK_SAVE_TIMED_MEDIA, True)

    console.print(ConsoleMessages.STARTING_LOGIN)
    try:
        session_string = asyncio.run(login_account())
    except Exception as e:
        console.print(ConsoleMessages.LOGIN_FAILED.format(error=e))
        return

    add_account(
        label,
        session_string=session_string,
        save_normal_media=save_normal_media,
        save_timed_media=save_timed_media,
    )
    console.print(ConsoleMessages.ACCOUNT_ADDED)


def edit_account_flow() -> None:
    render_accounts()
    label = console.input(ConsoleMessages.PROMPT_EDIT_LABEL).strip()
    account = get_account(label)
    if not account:
        console.print(ConsoleMessages.ACCOUNT_NOT_FOUND)
        return

    is_enabled = prompt_bool(ConsoleMessages.ASK_ENABLED, account.is_enabled)
    save_normal_media = prompt_bool(ConsoleMessages.ASK_SAVE_NORMAL_MEDIA, account.save_normal_media)
    save_timed_media = prompt_bool(ConsoleMessages.ASK_SAVE_TIMED_MEDIA, account.save_timed_media)

    update_account(
        label,
        is_enabled=is_enabled,
        save_normal_media=save_normal_media,
        save_timed_media=save_timed_media,
    )
    console.print(ConsoleMessages.ACCOUNT_UPDATED)


def delete_account_flow() -> None:
    render_accounts()
    label = console.input(ConsoleMessages.PROMPT_DELETE_LABEL).strip()
    if not get_account(label):
        console.print(ConsoleMessages.ACCOUNT_NOT_FOUND)
        return
    if prompt_bool(ConsoleMessages.CONFIRM_DELETE.format(label=label), False):
        delete_account(label)
        console.print(ConsoleMessages.ACCOUNT_DELETED)


def main() -> None:
    init_db()

    actions = {
        "1": render_accounts,
        "2": add_account_flow,
        "3": edit_account_flow,
        "4": delete_account_flow,
    }

    while True:
        console.print(ConsoleMessages.MENU)
        choice = console.input(ConsoleMessages.CHOOSE_OPTION).strip()
        if choice == "0":
            break
        action = actions.get(choice)
        if action is None:
            console.print(ConsoleMessages.INVALID_OPTION)
            continue
        try:
            action()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            console.print(ConsoleMessages.UNEXPECTED_ERROR.format(error=e))


if __name__ == "__main__":
    main()
