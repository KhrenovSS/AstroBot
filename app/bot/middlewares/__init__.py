from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.di import Container


class DIMiddleware(BaseMiddleware):
    """Middleware, внедряющий зависимости из DI-контейнера в хендлеры."""

    def __init__(self, container: Container) -> None:
        self.container = container

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if self.container.onboarding_service:
            data["onboarding_service"] = self.container.onboarding_service
        if self.container.chat_service:
            data["chat_service"] = self.container.chat_service
        return await handler(event, data)
