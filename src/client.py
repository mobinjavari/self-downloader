from __future__ import annotations

import logging
import os
import time
from collections.abc import Awaitable
from datetime import datetime
from typing import Callable

from telethon import Button, TelegramClient, events
from telethon.extensions.markdown import add_surrogate
from telethon.sessions import StringSession
from telethon.tl.custom import Message
from telethon.tl.types import MessageEntityTextUrl, User

from src.config import settings
from src.db import Account
from src.messages import ClientLogs, ClientMessages

logger = logging.getLogger("self-downloader")

EDIT_THROTTLE_SECONDS = 1.0


def is_timed_media(msg: Message) -> bool:
    return bool(getattr(msg.media, "ttl_seconds", None))


def format_full_name(sender: User | None) -> str:
    if sender is None:
        return ClientMessages.SENDER_UNKNOWN_NAME
    full_name = " ".join(part for part in (sender.first_name, sender.last_name) if part)
    return full_name or ClientMessages.SENDER_UNKNOWN_NAME


def format_sender_info(sender: User | None, sender_id: int) -> str:
    full_name = format_full_name(sender)
    username = f"@{sender.username}" if sender and sender.username else ClientMessages.SENDER_NO_USERNAME
    return ClientMessages.SENDER_INFO.format(full_name=full_name, username=username, sender_id=sender_id)


def build_caption(sender_info: str, text: str) -> str:
    if text:
        return ClientMessages.CAPTION_WITH_TEXT.format(sender_info=sender_info, text=text)
    return ClientMessages.CAPTION_WITHOUT_TEXT.format(sender_info=sender_info)


def build_profile_link(sender: User | None, sender_id: int) -> str:
    username = sender.username if sender else None
    if username:
        return ClientMessages.PROFILE_LINK_USERNAME.format(username=username)
    return ClientMessages.PROFILE_LINK_ID.format(sender_id=sender_id)


def build_timed_caption(sender: User | None, sender_id: int) -> tuple[str, list[MessageEntityTextUrl]]:
    prefix = ClientMessages.CAPTION_TIMED_PREFIX
    full_name = format_full_name(sender)
    text = f"{prefix}{full_name}"
    # Offsets/lengths must be UTF-16 code units (Telegram's entity format), not Python
    # character counts, so names containing emoji don't misplace the link.
    offset = len(add_surrogate(prefix))
    length = len(add_surrogate(full_name))
    link = build_profile_link(sender, sender_id)
    return text, [MessageEntityTextUrl(offset=offset, length=length, url=link)]


def build_client(account: Account) -> TelegramClient:
    download_dir = settings.download_dir / account.label
    download_dir.mkdir(parents=True, exist_ok=True)

    client = TelegramClient(StringSession(account.session_string), settings.api_id, settings.api_hash)

    def make_progress_callback(status_msg: Message, action: str) -> Callable[[int, int], Awaitable[None]]:
        last_edit_time = 0.0

        async def progress_callback(current: int, total: int) -> None:
            nonlocal last_edit_time
            now = time.monotonic()
            if now - last_edit_time < EDIT_THROTTLE_SECONDS:
                return
            last_edit_time = now
            percent = current / total * 100
            try:
                await status_msg.edit(ClientMessages.PROGRESS.format(action=action, percent=percent))
            except Exception:
                logger.debug(ClientLogs.PROGRESS_EDIT_FAILED, account.label)

        return progress_callback

    async def process_media(msg: Message, status_msg: Message | None = None) -> None:
        sender_id = msg.sender_id
        media_type = ClientMessages.MEDIA_TYPE_VIDEO if msg.video else ClientMessages.MEDIA_TYPE_PHOTO
        timestamp = datetime.now().strftime("%H:%M:%S")
        timed = is_timed_media(msg)

        if status_msg is None:
            status_msg = await client.send_message(
                "me",
                ClientMessages.INCOMING_MEDIA.format(media_type=media_type, sender_id=sender_id, timestamp=timestamp),
            )

        file_path = None
        try:
            file_path = await msg.download_media(
                file=str(download_dir),
                progress_callback=make_progress_callback(status_msg, ClientMessages.ACTION_DOWNLOADING),
            )
            if not file_path:
                raise RuntimeError(ClientMessages.DOWNLOAD_NO_PATH)

            sender = await msg.get_sender()
            upload_progress = make_progress_callback(status_msg, ClientMessages.ACTION_UPLOADING)

            if timed:
                caption, entities = build_timed_caption(sender, sender_id)
                # send_file() has no spoiler= kwarg in this Telethon version, so the
                # upload media is built manually and the spoiler flag set on it directly.
                _, media, _ = await client._file_to_media(file_path, progress_callback=upload_progress)
                media.spoiler = True
                await client.send_file("me", media, caption=caption, formatting_entities=entities)
            else:
                caption = build_caption(format_sender_info(sender, sender_id), msg.text)
                await client.send_file("me", file_path, caption=caption, progress_callback=upload_progress)

            await status_msg.delete()

        except Exception as e:
            logger.exception(ClientLogs.PROCESS_FAILED, account.label, sender_id)
            buttons = [[Button.inline(ClientMessages.RETRY_BUTTON, data=f"retry|{msg.chat_id}|{msg.id}")]]
            await status_msg.edit(ClientMessages.OPERATION_FAILED.format(error=e), buttons=buttons)

        finally:
            if settings.delete_media_after_upload and file_path and os.path.exists(file_path):
                os.remove(file_path)

    async def save_media(event: events.NewMessage.Event) -> None:
        if not event.is_private:
            return

        msg = event.message
        if not (msg.photo or msg.video):
            return

        if is_timed_media(msg):
            if not account.save_timed_media:
                return
        elif not account.save_normal_media:
            return

        try:
            await msg.forward_to("me")
            logger.info(ClientLogs.FORWARDED, account.label, msg.sender_id)
            return
        except Exception as e:
            logger.warning(ClientLogs.FORWARD_FAILED, account.label, e)

        await process_media(msg)

    async def retry_button_handler(event: events.CallbackQuery.Event) -> None:
        chat_id = int(event.pattern_match.group(1))
        msg_id = int(event.pattern_match.group(2))

        await event.message.delete()

        try:
            original_msg = await client.get_messages(chat_id, msg_id)
            await process_media(original_msg)
        except Exception:
            logger.exception(ClientLogs.RETRY_FAILED, account.label)
            await event.answer(ClientMessages.RETRY_FAILED_ALERT, alert=True)

    client.add_event_handler(save_media, events.NewMessage(incoming=True))
    client.add_event_handler(retry_button_handler, events.CallbackQuery(pattern=r"retry\|(.+)\|(.+)"))

    return client
