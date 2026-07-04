from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.domain.interfaces.astro_model import AstroModelProvider
from app.domain.interfaces.llm import LLMProvider
from app.domain.interfaces.payment import PaymentProvider
from app.domain.interfaces.rate_limiter import RateLimiter
from app.domain.interfaces.repositories import (
    MemoryRepository,
    SessionRepository,
    TransactionRepository,
    UserRepository,
)
from app.infra.crypto.aes_cipher import AESCipher
from app.infra.db.repositories import (
    SqlAlchemyMemoryRepository,
    SqlAlchemySessionRepository,
    SqlAlchemyTransactionRepository,
    SqlAlchemyUserRepository,
)


@dataclass
class Container:
    """DI-контейнер: содержит все зависимости приложения (Dependency injection container)."""
    settings: Settings
    db_session_factory: async_sessionmaker[AsyncSession]
    user_repo: UserRepository
    session_repo: SessionRepository
    memory_repo: MemoryRepository
    transaction_repo: TransactionRepository
    aes_cipher: AESCipher
    llm_provider: LLMProvider | None = None
    astro_model: AstroModelProvider | None = None
    rate_limiter: RateLimiter | None = None
    payment_provider: PaymentProvider | None = None


def build_container(settings: Settings) -> Container:
    """Собрать и вернуть DI-контейнер (Build and return the DI container).

    В Phase 1 — только settings. Репозитории и провайдеры добавляются в Phase 2.
    """
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    session: AsyncSession = session_factory()

    aes_cipher = AESCipher(settings.aes_encryption_key) if settings.aes_encryption_key else None

    user_repo = SqlAlchemyUserRepository(session)
    session_repo = SqlAlchemySessionRepository(session)
    memory_repo = SqlAlchemyMemoryRepository(session)
    transaction_repo = SqlAlchemyTransactionRepository(session)

    return Container(
        settings=settings,
        db_session_factory=session_factory,
        user_repo=user_repo,
        session_repo=session_repo,
        memory_repo=memory_repo,
        transaction_repo=transaction_repo,
        aes_cipher=aes_cipher,
    )
