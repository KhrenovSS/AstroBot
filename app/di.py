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
from app.infra.astro_model.prompt_engineered import PromptEngineeredAstroModel
from app.infra.crypto.aes_cipher import AESCipher
from app.infra.db.repositories import (
    SqlAlchemyMemoryRepository,
    SqlAlchemySessionRepository,
    SqlAlchemyTransactionRepository,
    SqlAlchemyUserRepository,
)
from app.infra.geo.nominatim_client import NominatimClient
from app.infra.llm.anthropic_client import AnthropicClient
from app.services.chat_service import ChatService
from app.services.conception_service import ConceptionService
from app.services.memory_resolver import MemoryResolver
from app.services.onboarding_service import OnboardingService
from app.services.session_service import SessionService


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
    session_service: SessionService | None = None
    memory_resolver: MemoryResolver | None = None
    chat_service: ChatService | None = None


def build_container(settings: Settings) -> Container:
    """Собрать и вернуть DI-контейнер (Build and return the DI container).

    Спринт 4: добавлены LLM, AstroModel, SessionService, MemoryResolver, ChatService.
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

    # LLM и AstroModel (LLM and AstroModel)
    llm_provider: LLMProvider | None = None
    astro_model: AstroModelProvider | None = None
    if settings.anthropic_api_key:
        llm_provider = AnthropicClient(settings)
        astro_model = PromptEngineeredAstroModel(llm_provider)

    # Сервисы сессий и памяти (Session and memory services)
    session_service: SessionService | None = None
    memory_resolver: MemoryResolver | None = None
    if llm_provider:
        session_service = SessionService(
            session_repo=session_repo,
            llm_provider=llm_provider,
            settings=settings,
        )
        memory_resolver = MemoryResolver(
            memory_repo=memory_repo,
            user_repo=user_repo,
            llm_provider=llm_provider,
        )

    # Онбординг (Onboarding)
    onboarding_service: OnboardingService | None = None
    if geo_provider and aes_cipher:
        onboarding_service = OnboardingService(
            user_repo=user_repo,
            geo_provider=geo_provider,
            aes_cipher=aes_cipher,
            conception_service=conception_service,
            settings=settings,
        )

    # Чат-сервис (Chat service)
    chat_service: ChatService | None = None
    if llm_provider and astro_model and session_service and memory_resolver:
        chat_service = ChatService(
            user_repo=user_repo,
            session_service=session_service,
            astro_model=astro_model,
            llm_provider=llm_provider,
            memory_resolver=memory_resolver,
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
        llm_provider=llm_provider,
        astro_model=astro_model,
        session_service=session_service,
        memory_resolver=memory_resolver,
        chat_service=chat_service,
    )
