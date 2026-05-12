from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str
    allowed_telegram_user_id: int | None
    llm_base_url: str
    llm_model: str
    llm_vision_model: str
    database_path: Path
    timezone: str


def load_config() -> Config:
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing. Add it to .env.")

    allowed_user = os.getenv("ALLOWED_TELEGRAM_USER_ID", "").strip()
    return Config(
        telegram_bot_token=token,
        allowed_telegram_user_id=int(allowed_user) if allowed_user else None,
        llm_base_url=os.getenv("LLM_BASE_URL", "http://127.0.0.1:1234").strip(),
        llm_model=os.getenv("LLM_MODEL", "google/gemma-4-e2b").strip(),
        llm_vision_model=os.getenv("LLM_VISION_MODEL", "").strip()
        or os.getenv("LLM_MODEL", "google/gemma-4-e2b").strip(),
        database_path=Path(os.getenv("DATABASE_PATH", "data/agent.sqlite3")),
        timezone=os.getenv("TIMEZONE", "Europe/Bucharest").strip(),
    )
