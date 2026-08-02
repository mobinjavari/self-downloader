import asyncio
import logging

from src.client import build_client
from src.config import settings
from src.db import Account, init_db, list_enabled_accounts
from src.messages import RunnerLogs

logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("self-downloader")


async def _run_until_disconnected(client, label: str) -> None:
    try:
        await client.run_until_disconnected()
    except Exception as e:
        logger.error(RunnerLogs.CLIENT_CRASHED, label, e)


async def _start_client(account: Account):
    try:
        client = build_client(account)
        await client.connect()
        if not await client.is_user_authorized():
            logger.error(RunnerLogs.NOT_AUTHORIZED, account.label)
            await client.disconnect()
            return None
        logger.info(RunnerLogs.CLIENT_STARTED, account.label)
        return client
    except Exception as e:
        logger.error(RunnerLogs.CLIENT_START_FAILED, account.label, e)
        return None


async def run() -> None:
    init_db()
    settings.download_dir.mkdir(parents=True, exist_ok=True)

    accounts = list_enabled_accounts()
    if not accounts:
        logger.error(RunnerLogs.NO_ENABLED_ACCOUNTS)
        return

    started = []
    for account in accounts:
        client = await _start_client(account)
        if client is not None:
            started.append((account, client))

    if not started:
        logger.error(RunnerLogs.NO_AUTHORIZED_ACCOUNTS)
        return

    await asyncio.gather(*(_run_until_disconnected(client, account.label) for account, client in started))


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
