from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class Transaction(BaseModel):
    """Платёжная транзакция (Payment transaction)."""
    id: int | None = None
    user_id: int
    provider: str
    provider_transaction_id: str
    amount: Decimal
    currency: str = "USD"
    status: str = "PENDING"
    plan: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Invoice(BaseModel):
    """Счёт для оплаты (Payment invoice)."""
    id: str
    amount: Decimal
    currency: str
    pay_url: str | None = None
    status: str = "PENDING"
