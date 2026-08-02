import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


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
        raise RuntimeError("API_ID and API_HASH must be set in the .env file")

    return Settings(
        api_id=int(api_id),
        api_hash=api_hash,
        delete_media_after_upload=_env_bool("DELETE_MEDIA_AFTER_UPLOAD", True),
        db_path=BASE_DIR / os.getenv("DB_PATH", "selfdownloader.db"),
        download_dir=BASE_DIR / os.getenv("DOWNLOAD_DIR", "downloads"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


settings = load_settings()
