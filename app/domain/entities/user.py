from datetime import datetime

from pydantic import BaseModel


class User(BaseModel):
    """Пользователь Telegram-бота (Telegram bot user)."""
    id: int | None = None
    tg_id: int
    status: str = "ONBOARDING"
    encrypted_birth_data: str = ""
    memory_summary: str | None = None
    memory_summary_version: int = 0
    talk_seconds: int = 0
    daily_messages: int = 0
    weekly_messages: int = 0
    last_daily_reset: datetime | None = None
    last_weekly_reset: datetime | None = None
    tariff: str = "FREE"
    created_at: datetime | None = None
    updated_at: datetime | None = None
