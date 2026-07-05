import logging
from datetime import datetime, timezone

from app.config import Settings
from app.domain.entities.session import ChatSession
from app.domain.interfaces.llm import LLMProvider
from app.domain.interfaces.repositories import SessionRepository

logger = logging.getLogger("astrobot")

EXPLICIT_PHRASE = "EXPLICIT"
SEMANTIC = "SEMANTIC"
TIMEOUT = "TIMEOUT"


class SessionService:
    """Управление жизненным циклом сессий чата (Chat session lifecycle management)."""

    def __init__(
        self,
        session_repo: SessionRepository,
        llm_provider: LLMProvider,
        settings: Settings,
    ):
        self._session_repo = session_repo
        self._llm = llm_provider
        self._settings = settings

    async def get_or_create(self, user_id: int) -> ChatSession:
        """Получить активную сессию или создать новую (Get active session or create new)."""
        existing = await self._session_repo.get_active_by_user_id(user_id)
        if existing:
            return existing

        session = ChatSession(user_id=user_id, status="ACTIVE")
        return await self._session_repo.create(session)

    async def on_message_processed(
        self, session: ChatSession, last_user_text: str
    ) -> tuple[ChatSession, str | None]:
        """Обработать сообщение: проверить конец сессии (Process message: check session end).

        Возвращает (session, end_reason) — если сессия завершена, end_reason не None.
        Returns (session, end_reason) — if session ended, end_reason is not None.
        """
        # Проверка явной фразы прощания (Check explicit farewell phrase)
        if self._matches_explicit_phrase(last_user_text):
            await self._end_session(session, EXPLICIT_PHRASE)
            return session, EXPLICIT_PHRASE

        # Проверка по счётчику сообщений (Check by message counter)
        session.messages_since_last_semantic_check += 1
        await self._session_repo.update(session)

        if session.messages_since_last_semantic_check >= self._settings.semantic_check_interval:
            is_ending = await self._llm.classify_session_end(
                self._build_recent_context(session)
            )
            if is_ending:
                await self._end_session(session, SEMANTIC)
                return session, SEMANTIC

        return session, None

    async def end_session(self, session: ChatSession, reason: str = EXPLICIT_PHRASE) -> None:
        """Принудительно завершить сессию (Forcefully end session)."""
        await self._end_session(session, reason)

    async def check_timeouts(self) -> list[ChatSession]:
        """Найти и завершить просроченные сессии (Find and end stale sessions)."""
        stale = await self._session_repo.find_active_older_than(
            self._settings.session_timeout_minutes
        )
        for s in stale:
            await self._end_session(s, TIMEOUT)
        return stale

    def _matches_explicit_phrase(self, text: str) -> bool:
        """Проверить, содержит ли текст явную фразу прощания (Check for explicit farewell)."""
        text_lower = text.strip().lower()
        for phrase in self._settings.explicit_end_phrases:
            if phrase in text_lower:
                return True
        return False

    def _build_recent_context(self, session: ChatSession) -> list[dict]:
        """Построить контекст последних сообщений для классификации
        (Build recent message context for classification).

        В MVP возвращает заглушку — в реальном приложении загружается из БД.
        """
        return [{"role": "user", "content": "(последние сообщения)"}]

    async def _end_session(self, session: ChatSession, reason: str) -> None:
        """Завершить сессию с указанной причиной (End session with given reason)."""
        session.status = f"ENDED_{reason}"
        session.ended_at = datetime.now(timezone.utc)
        await self._session_repo.update(session)
        logger.info("Session %d ended: %s", session.id, reason)
