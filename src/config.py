import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from src.messages import ConfigErrors

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"

PLACEHOLDER_VALUES = {"your_api_id", "your_api_hash"}


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    api_id: int
    api_hash: str
    delete_media_after_upload: bool
    db_path: Path
    download_dir: Path
    log_level: str


def load_settings() -> Settings:
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")

    if not api_id or not api_hash:
        raise RuntimeError(ConfigErrors.MISSING_CREDENTIALS)

    if api_id in PLACEHOLDER_VALUES or api_hash in PLACEHOLDER_VALUES:
        raise RuntimeError(ConfigErrors.PLACEHOLDER_CREDENTIALS)

    try:
        api_id_int = int(api_id)
    except ValueError:
        raise RuntimeError(ConfigErrors.INVALID_API_ID.format(value=api_id)) from None

    db_filename = Path(os.getenv("DB_FILENAME", "selfdownloader.db")).name

    return Settings(
        api_id=api_id_int,
        api_hash=api_hash,
        delete_media_after_upload=_env_bool("DELETE_MEDIA_AFTER_UPLOAD", True),
        db_path=STORAGE_DIR / db_filename,
        download_dir=STORAGE_DIR / "downloads",
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


settings = load_settings()
