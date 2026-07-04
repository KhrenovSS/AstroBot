from app.config import Settings
from app.di import Container, build_container
from app.domain.interfaces.repositories import (
    MemoryRepository,
    SessionRepository,
    TransactionRepository,
    UserRepository,
)


class TestDI:
    """Проверка DI-контейнера (Verify DI container builds correctly)."""

    def test_build_container_returns_container(self):
        settings = Settings()
        container = build_container(settings)
        assert isinstance(container, Container)

    def test_container_holds_settings(self):
        settings = Settings()
        container = build_container(settings)
        assert container.settings is settings

    def test_container_has_repositories(self):
        settings = Settings()
        container = build_container(settings)
        assert isinstance(container.user_repo, UserRepository)
        assert isinstance(container.session_repo, SessionRepository)
        assert isinstance(container.memory_repo, MemoryRepository)
        assert isinstance(container.transaction_repo, TransactionRepository)
