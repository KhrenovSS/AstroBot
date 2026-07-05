from datetime import datetime, timezone

import pytest

from app.config import Settings
from app.domain.entities.session import ChatSession
from app.domain.interfaces.llm import LLMProvider
from app.domain.interfaces.repositories import SessionRepository
from app.services.session_service import SessionService, EXPLICIT_PHRASE, SEMANTIC, TIMEOUT


class FakeLLMForSession(LLMProvider):
    """Fake LLM для тестов сессий (Fake LLM for session tests)."""

    def __init__(self):
        self.classify_result = False
        self.classify_calls = []

    async def generate_reply(self, system_prompt: str, history: list[dict], user_message: str) -> str:
        return "test"

    async def summarize(self, messages: list[dict]) -> dict:
        return {"summary": "test"}

    async def classify_session_end(self, last_messages: list[dict]) -> bool:
        self.classify_calls.append(last_messages)
        return self.classify_result


class FakeSessionRepo(SessionRepository):
    """Fake session repo for tests."""

    def __init__(self):
        self.sessions: dict[int, ChatSession] = {}
        self._next_id = 1

    async def create(self, session: ChatSession) -> ChatSession:
        session.id = self._next_id
        self._next_id += 1
        self.sessions[session.id] = session
        return session

    async def get_active_by_user_id(self, user_id: int) -> ChatSession | None:
        for s in self.sessions.values():
            if s.user_id == user_id and s.status == "ACTIVE":
                return s
        return None

    async def update(self, session: ChatSession) -> None:
        self.sessions[session.id] = session

    async def find_active_older_than(self, minutes: int) -> list[ChatSession]:
        now = datetime.now(timezone.utc)
        result = []
        for s in self.sessions.values():
            if s.status == "ACTIVE" and s.last_message_at:
                diff = (now - s.last_message_at).total_seconds() / 60
                if diff > minutes:
                    result.append(s)
        return result


@pytest.fixture
def settings():
    return Settings(
        session_timeout_minutes=30,
        semantic_check_interval=3,
        explicit_end_phrases=["пока", "до свидания", "bye"],
    )


@pytest.fixture
def session_repo():
    return FakeSessionRepo()


@pytest.fixture
def llm():
    return FakeLLMForSession()


@pytest.fixture
def service(session_repo, llm, settings):
    return SessionService(session_repo=session_repo, llm_provider=llm, settings=settings)


class TestSessionService:
    """Тесты SessionService (SessionService tests)."""

    async def test_get_or_create_creates_new(self, service, session_repo):
        """Создаёт новую сессию, если нет активной (Creates new if no active)."""
        session = await service.get_or_create(user_id=1)
        assert session is not None
        assert session.status == "ACTIVE"
        assert session.user_id == 1

    async def test_get_or_create_returns_existing(self, service, session_repo):
        """Возвращает существующую активную сессию (Returns existing active session)."""
        session1 = await service.get_or_create(user_id=2)
        session2 = await service.get_or_create(user_id=2)
        assert session1.id == session2.id

    async def test_on_message_explicit_phrase_ends_session(self, service, session_repo):
        """Явная фраза прощания завершает сессию (Explicit phrase ends session)."""
        session = await service.get_or_create(user_id=3)
        session, reason = await service.on_message_processed(session, "ну пока")
        assert reason == EXPLICIT_PHRASE
        assert session.status == f"ENDED_{EXPLICIT_PHRASE}"

    async def test_on_message_normal_does_not_end(self, service, session_repo):
        """Обычное сообщение не завершает сессию (Normal message does not end)."""
        session = await service.get_or_create(user_id=4)
        session, reason = await service.on_message_processed(session, "расскажи о себе")
        assert reason is None
        assert session.status == "ACTIVE"

    async def test_on_message_semantic_check_after_n_messages(self, service, llm):
        """После N сообщений вызывается semantic check (Semantic check after N messages)."""
        llm.classify_result = True
        session = await service.get_or_create(user_id=5)

        # Первые 2 сообщения — без проверки (First 2 messages — no check)
        for i in range(2):
            session, reason = await service.on_message_processed(session, f"msg {i}")
            assert reason is None

        # 3-е сообщение — достигнут лимит, вызывается LLM (3rd message — limit reached)
        session, reason = await service.on_message_processed(session, "msg 3")
        assert reason == SEMANTIC

    async def test_end_session_forcefully(self, service, session_repo):
        """Принудительное завершение сессии (Forceful session end)."""
        session = await service.get_or_create(user_id=6)
        await service.end_session(session, EXPLICIT_PHRASE)
        ended = await session_repo.get_active_by_user_id(6)
        assert ended is None

    async def test_check_timeouts(self, service, session_repo):
        """Проверка таймаутов завершает просроченные сессии (Timeout check ends stale sessions)."""
        session = await service.get_or_create(user_id=7)
        session.last_message_at = datetime.now(timezone.utc).replace(year=2020)
        await session_repo.update(session)

        stale = await service.check_timeouts()
        assert len(stale) >= 1
        assert stale[0].id == session.id
