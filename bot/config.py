from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    BOT_TOKEN: str
    DATABASE_URL: str = ""
    SQLITE_FALLBACK_PATH: str = "./data/dev.db"
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/bot.log"
    TELEGRAM_ADMIN_IDS: str = ""
    ADMIN_USERNAME: str = ""
    DEFAULT_LANG: str = "uz"
    DEFAULT_TIMEZONE: str = "Asia/Tashkent"
    DEFAULT_COUNTRY: str = "Uzbekistan"
    ALADHAN_METHOD: int = 2
    API_TIMEOUT_SEC: int = 10
    CACHE_TTL_SEC: int = 86400
    SCHEDULER_REFRESH_MIN: int = 30
    MOSQUE_RADIUS_KM: int = 10
    MOSQUE_LIMIT: int = 15
    ADHAN_AUDIO_URL: str = ""
    ADHAN_AUDIO_FILE: str = ""

    @property
    def admin_ids(self) -> List[int]:
        if not self.TELEGRAM_ADMIN_IDS:
            return []
        return [int(x.strip()) for x in self.TELEGRAM_ADMIN_IDS.split(",") if x.strip()]

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"sqlite+aiosqlite:///{self.SQLITE_FALLBACK_PATH}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
