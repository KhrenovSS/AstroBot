from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.memory import MemorySummary
from app.domain.entities.payment import Transaction
from app.domain.entities.session import ChatSession
from app.domain.entities.user import User
from app.domain.interfaces.repositories import (
    MemoryRepository,
    SessionRepository,
    TransactionRepository,
    UserRepository,
)
from app.exceptions import MemoryConflictError, NotFoundError
from app.infra.db import models as m


class SqlAlchemyUserRepository(UserRepository):
    """SQLAlchemy user repository implementation."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self._session.execute(
            select(m.User).where(m.User.id == user_id)
        )
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def get_by_tg_id(self, tg_id: int) -> User | None:
        result = await self._session.execute(
            select(m.User).where(m.User.tg_id == tg_id)
        )
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def create(self, user: User) -> User:
        orm_user = m.User(
            tg_id=user.tg_id,
            status=user.status,
            encrypted_birth_data=user.encrypted_birth_data,
            tariff=user.tariff,
        )
        self._session.add(orm_user)
        await self._session.flush()
        return self._to_domain(orm_user)

    async def save(self, user: User) -> None:
        stmt = (
            update(m.User)
            .where(m.User.id == user.id)
            .values(
                status=user.status,
                encrypted_birth_data=user.encrypted_birth_data,
                memory_summary=user.memory_summary,
                memory_summary_version=user.memory_summary_version,
                talk_seconds=user.talk_seconds,
                daily_messages=user.daily_messages,
                weekly_messages=user.weekly_messages,
                last_daily_reset=user.last_daily_reset,
                last_weekly_reset=user.last_weekly_reset,
                tariff=user.tariff,
            )
        )
        result = await self._session.execute(stmt)
        if result.rowcount == 0:
            raise NotFoundError(f"User {user.id} not found")

    async def update_memory_summary(self, user_id: int, summary: str, version: int) -> None:
        # Оптимистичная блокировка: обновляем только если версия совпадает (Optimistic lock)
        stmt = (
            update(m.User)
            .where(m.User.id == user_id, m.User.memory_summary_version == version)
            .values(memory_summary=summary, memory_summary_version=version + 1)
        )
        result = await self._session.execute(stmt)
        if result.rowcount == 0:
            raise MemoryConflictError(
                f"Memory summary conflict for user {user_id}, version {version}"
            )

    def _to_domain(self, orm: m.User) -> User:
        return User(
            id=orm.id,
            tg_id=orm.tg_id,
            status=orm.status.value if hasattr(orm.status, "value") else orm.status,
            encrypted_birth_data=orm.encrypted_birth_data,
            memory_summary=orm.memory_summary,
            memory_summary_version=orm.memory_summary_version,
            talk_seconds=orm.talk_seconds,
            daily_messages=orm.daily_messages,
            weekly_messages=orm.weekly_messages,
            last_daily_reset=orm.last_daily_reset,
            last_weekly_reset=orm.last_weekly_reset,
            tariff=orm.tariff.value if hasattr(orm.tariff, "value") else orm.tariff,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )


class SqlAlchemySessionRepository(SessionRepository):
    """SQLAlchemy реализация репозитория сессий (SQLAlchemy session repository implementation)."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, session: ChatSession) -> ChatSession:
        orm_session = m.ChatSession(
            user_id=session.user_id,
            status=session.status,
        )
        self._session.add(orm_session)
        await self._session.flush()
        return self._to_domain(orm_session)

    async def get_active_by_user_id(self, user_id: int) -> ChatSession | None:
        result = await self._session.execute(
            select(m.ChatSession).where(
                m.ChatSession.user_id == user_id,
                m.ChatSession.status == m.SessionStatus.ACTIVE,
            )
        )
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def update(self, session: ChatSession) -> None:
        stmt = (
            update(m.ChatSession)
            .where(m.ChatSession.id == session.id)
            .values(
                status=session.status,
                messages_since_last_semantic_check=session.messages_since_last_semantic_check,
                ended_at=session.ended_at,
                last_message_at=session.last_message_at,
            )
        )
        result = await self._session.execute(stmt)
        if result.rowcount == 0:
            raise NotFoundError(f"ChatSession {session.id} not found")

    async def find_active_older_than(self, minutes: int) -> list[ChatSession]:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        result = await self._session.execute(
            select(m.ChatSession).where(
                m.ChatSession.status == m.SessionStatus.ACTIVE,
                m.ChatSession.last_message_at < cutoff,
            )
        )
        return [self._to_domain(row) for row in result.scalars().all()]

    def _to_domain(self, orm: m.ChatSession) -> ChatSession:
        return ChatSession(
            id=orm.id,
            user_id=orm.user_id,
            status=orm.status.value if hasattr(orm.status, "value") else orm.status,
            messages_since_last_semantic_check=orm.messages_since_last_semantic_check,
            created_at=orm.created_at,
            ended_at=orm.ended_at,
            last_message_at=orm.last_message_at,
        )


class SqlAlchemyMemoryRepository(MemoryRepository):
    """SQLAlchemy реализация репозитория памяти (SQLAlchemy memory repository implementation)."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_user_id(self, user_id: int) -> MemorySummary | None:
        result = await self._session.execute(
            select(m.MemorySummary).where(m.MemorySummary.user_id == user_id)
        )
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def save(self, memory: MemorySummary) -> MemorySummary:
        orm = m.MemorySummary(
            user_id=memory.user_id,
            summary=memory.summary,
            version=memory.version,
        )
        self._session.add(orm)
        await self._session.flush()
        return self._to_domain(orm)

    def _to_domain(self, orm: m.MemorySummary) -> MemorySummary:
        return MemorySummary(
            id=orm.id,
            user_id=orm.user_id,
            summary=orm.summary,
            version=orm.version,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )


class SqlAlchemyTransactionRepository(TransactionRepository):
    """SQLAlchemy transaction repository implementation."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, transaction: Transaction) -> Transaction:
        orm = m.Transaction(
            user_id=transaction.user_id,
            provider=transaction.provider,
            provider_transaction_id=transaction.provider_transaction_id,
            amount=transaction.amount,
            currency=transaction.currency,
            status=transaction.status,
            plan=transaction.plan,
        )
        self._session.add(orm)
        await self._session.flush()
        return self._to_domain(orm)

    async def get_by_provider_tx_id(self, provider_tx_id: str) -> Transaction | None:
        result = await self._session.execute(
            select(m.Transaction).where(
                m.Transaction.provider_transaction_id == provider_tx_id
            )
        )
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def get_by_user_id(self, user_id: int) -> list[Transaction]:
        result = await self._session.execute(
            select(m.Transaction)
            .where(m.Transaction.user_id == user_id)
            .order_by(m.Transaction.created_at.desc())
        )
        return [self._to_domain(row) for row in result.scalars().all()]

    def _to_domain(self, orm: m.Transaction) -> Transaction:
        return Transaction(
            id=orm.id,
            user_id=orm.user_id,
            provider=orm.provider,
            provider_transaction_id=orm.provider_transaction_id,
            amount=orm.amount,
            currency=orm.currency,
            status=orm.status.value if hasattr(orm.status, "value") else orm.status,
            plan=orm.plan,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
