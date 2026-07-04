from datetime import datetime

from pydantic import BaseModel


class MemorySummary(BaseModel):
    """Сводка памяти пользователя для LLM (User memory summary for LLM)."""
    id: int | None = None
    user_id: int
    summary: str
    version: int = 1
    created_at: datetime | None = None
    updated_at: datetime | None = None
