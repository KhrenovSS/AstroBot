from abc import ABC, abstractmethod

from app.domain.entities.payment import Invoice


class PaymentProvider(ABC):
    """Интерфейс платёжного провайдера (Payment provider interface)."""

    @abstractmethod
    async def create_invoice(self, user_id: int, plan: str) -> Invoice:
        ...

    @abstractmethod
    async def verify_webhook(self, raw_body: bytes, headers: dict) -> dict:
        ...
