import logging
import os
import time
from datetime import datetime

from telethon import Button, TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.custom import Message

from src.config import settings
from src.db import Account

logger = logging.getLogger("self-downloader")

EDIT_THROTTLE_SECONDS = 1.0


def is_timed_media(msg: Message) -> bool:
    return bool(getattr(msg.media, "ttl_seconds", None))


def build_client(account: Account) -> TelegramClient:
    download_dir = settings.download_dir / account.label
    download_dir.mkdir(parents=True, exist_ok=True)

    client = TelegramClient(StringSession(account.session_string), settings.api_id, settings.api_hash)
    last_edit_time = {"value": 0.0}

    def make_progress_callback(status_msg: Message, action: str):
        async def progress_callback(current: int, total: int) -> None:
            now = time.monotonic()
            if now - last_edit_time["value"] < EDIT_THROTTLE_SECONDS:
                return
            last_edit_time["value"] = now
            percent = current / total * 100
            try:
                await status_msg.edit(f"{action}: {percent:.1f}% complete")
            except Exception:
                pass

        return progress_callback

    async def process_media(msg: Message, status_msg: Message | None = None) -> None:
        sender_id = msg.sender_id
        media_type = "video" if msg.video else "photo"
        timestamp = datetime.now().strftime("%H:%M:%S")

        if status_msg is None:
            status_msg = await client.send_message(
                "me",
                f"Incoming {media_type} from `{sender_id}` at {timestamp}\nDownloading/uploading...",
            )

        file_path = None
        try:
            file_path = await msg.download_media(
                file=str(download_dir),
                progress_callback=make_progress_callback(status_msg, "Downloading"),
            )
            if not file_path:
                raise RuntimeError("Download returned no file path")

            await client.send_file(
                "me",
                file_path,
                caption=msg.text or "",
                progress_callback=make_progress_callback(status_msg, "Uploading"),
            )
            await status_msg.edit(f"{media_type.capitalize()} from `{sender_id}` saved to Saved Messages.")

        except Exception as e:
            logger.exception("[%s] Failed to process media from %s", account.label, sender_id)
            buttons = [[Button.inline("Retry", data=f"retry|{msg.chat_id}|{msg.id}")]]
            await status_msg.edit(f"Operation failed:\n\n`{e}`", buttons=buttons)

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
            logger.info("[%s] Forwarded media from %s", account.label, msg.sender_id)
            return
        except Exception as e:
            logger.warning("[%s] Forward failed (%s), falling back to download/upload", account.label, e)

        await process_media(msg)

    async def retry_button_handler(event: events.CallbackQuery.Event) -> None:
        chat_id = int(event.pattern_match.group(1))
        msg_id = int(event.pattern_match.group(2))

        await event.message.delete()

        try:
            original_msg = await client.get_messages(chat_id, msg_id)
            await process_media(original_msg)
        except Exception:
            logger.exception("[%s] Retry failed", account.label)
            await event.answer("Retry failed", alert=True)

    client.add_event_handler(save_media, events.NewMessage(incoming=True))
    client.add_event_handler(retry_button_handler, events.CallbackQuery(pattern=r"retry\|(.+)\|(.+)"))

    return client
