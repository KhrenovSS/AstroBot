from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.domain.interfaces.astro_model import AstroModelProvider
from app.domain.interfaces.geo import GeoProvider
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
from app.infra.geo.nominatim_client import NominatimClient
from app.services.conception_service import ConceptionService
from app.services.onboarding_service import OnboardingService


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
    geo_provider: GeoProvider | None = None
    conception_service: ConceptionService | None = None
    onboarding_service: OnboardingService | None = None
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

    geo_provider = NominatimClient(settings) if settings.nominatim_url else None
    conception_service = ConceptionService()

    onboarding_service: OnboardingService | None = None
    if geo_provider and aes_cipher:
        onboarding_service = OnboardingService(
            user_repo=user_repo,
            geo_provider=geo_provider,
            aes_cipher=aes_cipher,
            conception_service=conception_service,
            settings=settings,
        )

    return Container(
        settings=settings,
        db_session_factory=session_factory,
        user_repo=user_repo,
        session_repo=session_repo,
        memory_repo=memory_repo,
        transaction_repo=transaction_repo,
        aes_cipher=aes_cipher,
        geo_provider=geo_provider,
        conception_service=conception_service,
        onboarding_service=onboarding_service,
    )
