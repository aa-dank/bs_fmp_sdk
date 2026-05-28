from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(slots=True)
class FileMakerConfig:
    """Connection and request settings for the FileMaker Data API."""

    host: str
    user: str
    password: str
    database: str = "UCPPC"
    fetch_limit: int = 100_000
    timeout: int = 300
    verify_ssl: bool = False
    api_version: str = "v1"
    default_layout: str | None = None


def load_config(env_file: str | Path | None = None) -> FileMakerConfig:
    """Load FileMaker configuration from environment variables and .env."""
    if env_file is None:
        env_file = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_file, override=False)

    return FileMakerConfig(
        host=_require("FM_HOST"),
        user=_require("FM_USER"),
        password=_require("FM_PASSWORD"),
        database=os.environ.get("FM_DATABASE", "UCPPC"),
        fetch_limit=int(os.environ.get("FM_FETCH_LIMIT", "100000")),
        timeout=int(os.environ.get("FM_TIMEOUT", "300")),
        verify_ssl=os.environ.get("FM_VERIFY_SSL", "false").lower() == "true",
        api_version=os.environ.get("FM_API_VERSION", "v1"),
        default_layout=os.environ.get("FM_DEFAULT_LAYOUT"),
    )


def _require(key: str) -> str:
    """Return a required environment variable or raise a clear error."""
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"Required environment variable '{key}' is not set.")
    return value
