from abc import ABC, abstractmethod

from app.domain.entities.memory import MemorySummary
from app.domain.entities.payment import Transaction
from app.domain.entities.session import ChatSession
from app.domain.entities.user import User


class UserRepository(ABC):
    """Интерфейс репозитория пользователей (User repository interface)."""

    @abstractmethod
    async def get_by_id(self, user_id: int) -> User | None:
        ...

    @abstractmethod
    async def get_by_tg_id(self, tg_id: int) -> User | None:
        ...

    @abstractmethod
    async def create(self, user: User) -> User:
        ...

    @abstractmethod
    async def save(self, user: User) -> None:
        ...

    @abstractmethod
    async def update_memory_summary(self, user_id: int, summary: str, version: int) -> None:
        ...


class SessionRepository(ABC):
    """Интерфейс репозитория сессий (Session repository interface)."""

    @abstractmethod
    async def create(self, session: ChatSession) -> ChatSession:
        ...

    @abstractmethod
    async def get_active_by_user_id(self, user_id: int) -> ChatSession | None:
        ...

    @abstractmethod
    async def update(self, session: ChatSession) -> None:
        ...

    @abstractmethod
    async def find_active_older_than(self, minutes: int) -> list[ChatSession]:
        ...


class MemoryRepository(ABC):
    """Интерфейс репозитория памяти (Memory repository interface)."""

    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> MemorySummary | None:
        ...

    @abstractmethod
    async def save(self, memory: MemorySummary) -> MemorySummary:
        ...


class TransactionRepository(ABC):
    """Интерфейс репозитория транзакций (Transaction repository interface)."""

    @abstractmethod
    async def create(self, transaction: Transaction) -> Transaction:
        ...

    @abstractmethod
    async def get_by_provider_tx_id(self, provider_tx_id: str) -> Transaction | None:
        ...

    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> list[Transaction]:
        ...
