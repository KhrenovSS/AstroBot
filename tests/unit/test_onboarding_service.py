from unittest.mock import AsyncMock

import pytest

from app.config import Settings
from app.domain.entities.astro import GeoPoint
from app.domain.entities.birth_data import BirthData
from app.domain.entities.user import User
from app.infra.crypto.aes_cipher import AESCipher
from app.services.conception_service import ConceptionService
from app.services.onboarding_service import OnboardingService


@pytest.fixture
def aes_cipher():
    key = AESCipher.generate_key()
    return AESCipher(key)


@pytest.fixture
def settings():
    return Settings()


@pytest.fixture
def fake_user_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def fake_geo_provider():
    provider = AsyncMock()
    provider.geocode.return_value = GeoPoint(lat=55.7558, lon=37.6173, timezone="Europe/Moscow")
    return provider


@pytest.fixture
def onboarding_service(fake_user_repo, fake_geo_provider, aes_cipher, settings):
    conception_service = ConceptionService()
    return OnboardingService(
        user_repo=fake_user_repo,
        geo_provider=fake_geo_provider,
        aes_cipher=aes_cipher,
        conception_service=conception_service,
        settings=settings,
    )


class TestOnboardingService:
    """Тесты OnboardingService (Onboarding service tests)."""

    async def test_start_creates_new_user(self, onboarding_service, fake_user_repo):
        """start создаёт пользователя, если его нет (Start creates user if not exists)."""
        fake_user_repo.get_by_tg_id.return_value = None
        fake_user_repo.create.return_value = User(tg_id=12345, id=1, status="ONBOARDING")

        user = await onboarding_service.start(tg_id=12345)

        assert user is not None
        assert user.status == "ONBOARDING"
        fake_user_repo.create.assert_awaited_once()

    async def test_start_returns_existing_user(self, onboarding_service, fake_user_repo):
        """start возвращает существующего пользователя (Start returns existing user)."""
        existing = User(tg_id=12345, id=1, status="ACTIVE")
        fake_user_repo.get_by_tg_id.return_value = existing

        user = await onboarding_service.start(tg_id=12345)

        assert user is existing
        assert user.status == "ACTIVE"
        fake_user_repo.create.assert_not_called()

    async def test_finalize_sets_active_status(
        self, onboarding_service, fake_user_repo, fake_geo_provider, aes_cipher
    ):
        """finalize переключает пользователя в ACTIVE (Finalize sets ACTIVE status)."""
        from datetime import date

        fake_user_repo.get_by_tg_id.return_value = User(tg_id=12345, id=1, status="ONBOARDING")

        user = await onboarding_service.finalize(
            tg_id=12345,
            birth_date=date(1990, 5, 15),
            birth_place="Москва",
        )

        assert user.status == "ACTIVE"
        assert user.encrypted_birth_data != ""
        fake_geo_provider.geocode.assert_awaited_once_with("Москва")
        fake_user_repo.save.assert_awaited_once()

    async def test_finalize_encrypts_birth_data(
        self, onboarding_service, fake_user_repo, aes_cipher
    ):
        """finalize шифрует данные обратимо (Finalize encrypts data reversibly)."""
        from datetime import date

        fake_user_repo.get_by_tg_id.return_value = User(tg_id=12345, id=1, status="ONBOARDING")

        user = await onboarding_service.finalize(
            tg_id=12345,
            birth_date=date(1990, 5, 15),
            birth_place="Москва",
        )

        decrypted = aes_cipher.decrypt(user.encrypted_birth_data)
        parsed = BirthData.model_validate_json(decrypted)
        assert parsed.birth_date == date(1990, 5, 15)
        assert parsed.birth_place == "Москва"

    async def test_finalize_geocoding_error(
        self, onboarding_service, fake_user_repo, fake_geo_provider
    ):
        """Ошибка геокодинга пробрасывается наверх (Geocoding error propagates)."""
        from datetime import date

        from app.exceptions import GeocodingError

        fake_geo_provider.geocode.side_effect = GeocodingError("invalid", "Not found")
        fake_user_repo.get_by_tg_id.return_value = User(tg_id=12345, id=1, status="ONBOARDING")

        with pytest.raises(GeocodingError):
            await onboarding_service.finalize(
                tg_id=12345,
                birth_date=date(1990, 5, 15),
                birth_place="NonexistentPlace12345",
            )
