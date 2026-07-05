import logging
from datetime import datetime, timezone

from app.config import Settings
from app.domain.entities.astro import AstroMatrix, GeoPoint
from app.domain.interfaces.astro_model import AstroModelProvider
from app.domain.interfaces.llm import LLMProvider
from app.domain.interfaces.repositories import SessionRepository, UserRepository
from app.exceptions import NotFoundError
from app.services.memory_resolver import MemoryResolver
from app.services.session_service import SessionService

logger = logging.getLogger("astrobot")


class ChatService:
    """Оркестрация чата: сообщение → матрица → LLM → ответ
    (Chat orchestration: message → matrix → LLM → reply)."""

    def __init__(
        self,
        user_repo: UserRepository,
        session_service: SessionService,
        astro_model: AstroModelProvider,
        llm_provider: LLMProvider,
        memory_resolver: MemoryResolver,
        settings: Settings,
    ):
        self._user_repo = user_repo
        self._session_service = session_service
        self._astro_model = astro_model
        self._llm = llm_provider
        self._memory_resolver = memory_resolver
        self._settings = settings

    async def handle_message(self, tg_id: int, text: str) -> str:
        """Обработать входящее сообщение пользователя (Process incoming user message).

        1. Получить пользователя
        2. Получить/создать сессию
        3. Получить матрицу (натальную или заглушку)
        4. Получить память
        5. Сформировать system prompt
        6. Вызвать LLM
        7. Проверить конец сессии
        8. Вернуть ответ
        """
        # Шаг 1: Получить пользователя (Get user)
        user = await self._user_repo.get_by_tg_id(tg_id)
        if not user:
            raise NotFoundError(f"User with tg_id {tg_id} not found — please start onboarding via /start")

        # Шаг 2: Получить/создать сессию (Get/create session)
        session = await self._session_service.get_or_create(user.id)

        # Шаг 3: Получить астрологическую матрицу (Get astrological matrix)
        astro_data = await self._load_astro_matrix(user)

        # Шаг 4: Получить память пользователя (Get user memory)
        memory = await self._memory_resolver.get_or_create_summary(user.id)
        memory_context = memory.summary if memory else ""

        # Шаг 5: Сформировать system prompt (Build system prompt)
        system_prompt = self._build_system_prompt(astro_data, memory_context)

        # Шаг 6: Загрузить историю сессии (в MVP — заглушка) (Load session history — stub in MVP)
        history = []

        # Шаг 7: Вызвать LLM (Call LLM)
        reply = await self._llm.generate_reply(
            system_prompt=system_prompt,
            history=history,
            user_message=text,
        )

        # Шаг 8: Проверить конец сессии (Check session end)
        session, end_reason = await self._session_service.on_message_processed(session, text)
        if end_reason:
            reply += "\n\n⚠️ Сессия завершена. Напишите что-нибудь, чтобы начать новый разговор."

        # Шаг 9: Обновить счётчики пользователя (Update user counters)
        user.daily_messages += 1
        user.weekly_messages += 1
        user.last_daily_reset = user.last_daily_reset or datetime.now(timezone.utc)
        user.last_weekly_reset = user.last_weekly_reset or datetime.now(timezone.utc)
        await self._user_repo.save(user)

        return reply

    async def _load_astro_matrix(self, user) -> AstroMatrix | None:
        """Загрузить астрологическую матрицу пользователя (Load user astrological matrix).

        Расшифровывает birth_data, получает conception_time,
        строит натальную матрицу через AstroModelProvider.
        """
        # MVP: возвращаем заглушку, пока нет полного пайплайна расшифровки
        # (MVP: return stub until full decryption pipeline is ready)
        return None

    def _build_system_prompt(
        self, astro_data: AstroMatrix | None, memory_context: str
    ) -> str:
        """Сформировать system prompt для LLM (Build system prompt for LLM)."""
        parts = [self._settings.n_system_prompt]

        if astro_data:
            parts.append(f"\n\nДанные натальной матрицы:\n{astro_data.model_dump_json(indent=2)}")

        if memory_context:
            parts.append(f"\n\nКонтекст памяти пользователя:\n{memory_context}")

        return "\n".join(parts)
