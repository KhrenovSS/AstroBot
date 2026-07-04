from datetime import datetime

from pydantic import BaseModel


class ChatSession(BaseModel):
    """Сессия чата пользователя (User chat session)."""
    id: int | None = None
    user_id: int
    status: str = "ACTIVE"
    messages_since_last_semantic_check: int = 0
    created_at: datetime | None = None
    ended_at: datetime | None = None
    last_message_at: datetime | None = None
