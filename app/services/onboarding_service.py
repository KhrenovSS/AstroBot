from datetime import date, time

from app.config import Settings
from app.domain.entities.birth_data import BirthData, ParentData
from app.domain.entities.user import User
from app.domain.interfaces.geo import GeoProvider
from app.domain.interfaces.repositories import UserRepository
from app.infra.crypto.aes_cipher import AESCipher
from app.services.conception_service import ConceptionService


class OnboardingService:
    """Use-case: онбординг нового пользователя (User onboarding flow)."""

    def __init__(
        self,
        user_repo: UserRepository,
        geo_provider: GeoProvider,
        aes_cipher: AESCipher,
        conception_service: ConceptionService,
        settings: Settings,
    ):
        self._user_repo = user_repo
        self._geo_provider = geo_provider
        self._aes_cipher = aes_cipher
        self._conception_service = conception_service
        self._settings = settings

    async def start(self, tg_id: int) -> User:
        """Создать пользователя со статусом ONBOARDING (Create user with ONBOARDING status)."""
        existing = await self._user_repo.get_by_tg_id(tg_id)
        if existing:
            return existing

        user = User(tg_id=tg_id, status="ONBOARDING")
        created = await self._user_repo.create(user)
        return created

    async def save_birth_date(self, user_id: int, birth_date: date) -> None:
        """Сохранить дату рождения в pending-данные (Save birth date to pending data)."""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            return
        # Birth data is accumulated in memory during FSM, finalized at the end.
        # This method is a hook for future in-memory accumulation.

    async def save_birth_place(self, user_id: int, place: str) -> None:
        """Сохранить место рождения (Save birth place)."""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            return

    async def finalize(
        self,
        tg_id: int,
        birth_date: date,
        birth_place: str,
        birth_time: time | None = None,
        parents: list[ParentData] | None = None,
    ) -> User:
        """Финализировать онбординг: геокодинг, шифрование, conception_time (Finalize onboarding).

        1. Геокодировать место рождения
        2. Собрать BirthData, зашифровать
        3. Вычислить conception_time
        4. Сохранить пользователя со статусом ACTIVE
        """
        # Геокодинг места рождения (Geocode birth place)
        await self._geo_provider.geocode(birth_place)

        # Сбор и шифрование ПДн (Collect and encrypt PII)
        birth_data = BirthData(
            birth_date=birth_date,
            birth_place=birth_place,
            birth_time=birth_time,
            parents=parents or [],
        )
        birth_data_json = birth_data.model_dump_json()
        encrypted = self._aes_cipher.encrypt(birth_data_json)

        # Вычисление времени зачатия (Derive conception time)
        self._conception_service.derive(tg_id, birth_data)

        # Обновление пользователя (Update user)
        user = await self._user_repo.get_by_tg_id(tg_id)
        if not user:
            user = User(tg_id=tg_id)
            user = await self._user_repo.create(user)

        user.status = "ACTIVE"
        user.encrypted_birth_data = encrypted

        await self._user_repo.save(user)

        return user
