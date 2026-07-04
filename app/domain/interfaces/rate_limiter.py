from abc import ABC, abstractmethod

from pydantic import BaseModel


class RateLimitDecision(BaseModel):
    """Решение лимитера (Rate limiter decision)."""
    allowed: bool
    remaining: int
    retry_after: int | None = None


class RateLimiter(ABC):
    """Интерфейс лимитера запросов (Rate limiter interface)."""

    @abstractmethod
    async def check_and_increment(
        self, user_id: int, event: str
    ) -> RateLimitDecision:
        ...
