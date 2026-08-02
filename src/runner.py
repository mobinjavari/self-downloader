import asyncio
import logging

from src.client import build_client
from src.config import settings
from src.db import init_db, list_enabled_accounts

logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("self-downloader")


async def run() -> None:
    init_db()
    settings.download_dir.mkdir(parents=True, exist_ok=True)

    accounts = list_enabled_accounts()
    if not accounts:
        logger.error("No enabled accounts found. Add one with: python console.py")
        return

    clients = []
    for account in accounts:
        client = build_client(account)
        await client.connect()
        if not await client.is_user_authorized():
            logger.error("[%s] Session not authorized. Log in first with: python console.py", account.label)
            await client.disconnect()
            continue
        logger.info("[%s] Client started", account.label)
        clients.append(client)

    if not clients:
        logger.error("No authorized accounts to run. Exiting.")
        return

    await asyncio.gather(*(client.run_until_disconnected() for client in clients))


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
