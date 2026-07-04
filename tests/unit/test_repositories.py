from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.entities.session import ChatSession
from app.domain.entities.user import User
from app.exceptions import MemoryConflictError, NotFoundError
from app.infra.db.repositories import (
    SqlAlchemyMemoryRepository,
    SqlAlchemySessionRepository,
    SqlAlchemyTransactionRepository,
    SqlAlchemyUserRepository,
)


@pytest.fixture
def mock_session():
    session = AsyncMock(spec_set=[
        "execute", "flush", "add",
    ])
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session


class TestSqlAlchemyUserRepository:
    async def test_get_by_tg_id_returns_user(self, mock_session):
        orm_user = MagicMock()
        orm_user.id = 1
        orm_user.tg_id = 12345
        orm_user.status = MagicMock(value="ACTIVE")
        orm_user.encrypted_birth_data = "encrypted"
        orm_user.memory_summary = "summary"
        orm_user.memory_summary_version = 2
        orm_user.talk_seconds = 100
        orm_user.daily_messages = 5
        orm_user.weekly_messages = 20
        orm_user.last_daily_reset = None
        orm_user.last_weekly_reset = None
        orm_user.tariff = MagicMock(value="FREE")
        orm_user.created_at = None
        orm_user.updated_at = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = orm_user
        mock_session.execute.return_value = mock_result

        repo = SqlAlchemyUserRepository(mock_session)
        user = await repo.get_by_tg_id(12345)

        assert user is not None
        assert user.tg_id == 12345
        assert user.status == "ACTIVE"
        assert user.tariff == "FREE"

    async def test_get_by_tg_id_returns_none(self, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = SqlAlchemyUserRepository(mock_session)
        user = await repo.get_by_tg_id(99999)

        assert user is None

    async def test_create_user(self, mock_session):
        repo = SqlAlchemyUserRepository(mock_session)

        orm_user = MagicMock()
        orm_user.id = 1
        orm_user.tg_id = 12345
        orm_user.status = MagicMock(value="ONBOARDING")
        orm_user.encrypted_birth_data = ""
        orm_user.memory_summary = None
        orm_user.memory_summary_version = 0
        orm_user.talk_seconds = 0
        orm_user.daily_messages = 0
        orm_user.weekly_messages = 0
        orm_user.last_daily_reset = None
        orm_user.last_weekly_reset = None
        orm_user.tariff = MagicMock(value="FREE")
        orm_user.created_at = None
        orm_user.updated_at = None

        with patch.object(repo, '_to_domain', return_value=User(tg_id=12345, id=1)):
            user_in = User(tg_id=12345)
            result = await repo.create(user_in)

        assert result is not None
        mock_session.add.assert_called_once()

    async def test_save_updates_user(self, mock_session):
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        repo = SqlAlchemyUserRepository(mock_session)
        user = User(id=1, tg_id=12345, status="ACTIVE")

        await repo.save(user)
        mock_session.execute.assert_awaited_once()

    async def test_save_not_found_raises_error(self, mock_session):
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        repo = SqlAlchemyUserRepository(mock_session)
        user = User(id=999, tg_id=12345)

        with pytest.raises(NotFoundError):
            await repo.save(user)

    async def test_update_memory_summary_success(self, mock_session):
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        repo = SqlAlchemyUserRepository(mock_session)
        await repo.update_memory_summary(user_id=1, summary="new summary", version=2)
        mock_session.execute.assert_awaited_once()

    async def test_update_memory_summary_conflict_raises_error(self, mock_session):
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        repo = SqlAlchemyUserRepository(mock_session)
        with pytest.raises(MemoryConflictError):
            await repo.update_memory_summary(user_id=1, summary="new summary", version=99)


class TestSqlAlchemySessionRepository:
    async def test_get_active_by_user_id(self, mock_session):
        orm = MagicMock()
        orm.id = 1
        orm.user_id = 1
        orm.status = MagicMock(value="ACTIVE")
        orm.messages_since_last_semantic_check = 0
        orm.created_at = None
        orm.ended_at = None
        orm.last_message_at = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = orm
        mock_session.execute.return_value = mock_result

        repo = SqlAlchemySessionRepository(mock_session)
        session = await repo.get_active_by_user_id(1)

        assert session is not None
        assert session.status == "ACTIVE"

    async def test_get_active_by_user_id_none(self, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = SqlAlchemySessionRepository(mock_session)
        session = await repo.get_active_by_user_id(1)

        assert session is None

    async def test_create_session(self, mock_session):
        repo = SqlAlchemySessionRepository(mock_session)
        session_in = ChatSession(user_id=1)

        with patch.object(repo, '_to_domain', return_value=session_in):
            await repo.create(session_in)

        mock_session.add.assert_called_once()

    async def test_update_session_not_found(self, mock_session):
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        repo = SqlAlchemySessionRepository(mock_session)
        session = ChatSession(id=999, user_id=1)

        with pytest.raises(NotFoundError):
            await repo.update(session)


class TestSqlAlchemyTransactionRepository:
    async def test_get_by_provider_tx_id_found(self, mock_session):
        orm = MagicMock()
        orm.id = 1
        orm.user_id = 1
        orm.provider = "CRYPTO_BOT"
        orm.provider_transaction_id = "tx123"
        orm.amount = 100.0
        orm.currency = "USD"
        orm.status = MagicMock(value="COMPLETED")
        orm.plan = "PREMIUM_MONTHLY"
        orm.created_at = None
        orm.updated_at = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = orm
        mock_session.execute.return_value = mock_result

        repo = SqlAlchemyTransactionRepository(mock_session)
        tx = await repo.get_by_provider_tx_id("tx123")

        assert tx is not None
        assert tx.provider_transaction_id == "tx123"
        assert tx.status == "COMPLETED"

    async def test_get_by_provider_tx_id_not_found(self, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = SqlAlchemyTransactionRepository(mock_session)
        tx = await repo.get_by_provider_tx_id("nonexistent")

        assert tx is None


class TestSqlAlchemyMemoryRepository:
    async def test_get_by_user_id_found(self, mock_session):
        orm = MagicMock()
        orm.id = 1
        orm.user_id = 1
        orm.summary = "memory summary"
        orm.version = 1
        orm.created_at = None
        orm.updated_at = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = orm
        mock_session.execute.return_value = mock_result

        repo = SqlAlchemyMemoryRepository(mock_session)
        memory = await repo.get_by_user_id(1)

        assert memory is not None
        assert memory.summary == "memory summary"
        assert memory.version == 1

    async def test_get_by_user_id_not_found(self, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = SqlAlchemyMemoryRepository(mock_session)
        memory = await repo.get_by_user_id(1)

        assert memory is None
