from datetime import datetime, timezone

import pytest

from app.config import Settings
from app.domain.entities.astro import AstroMatrix, GeoPoint
from app.domain.entities.memory import MemorySummary
from app.domain.entities.session import ChatSession
from app.domain.entities.user import User
from app.domain.interfaces.astro_model import AstroModelProvider
from app.domain.interfaces.llm import LLMProvider
from app.domain.interfaces.repositories import (
    MemoryRepository,
    SessionRepository,
    UserRepository,
)
from app.services.chat_service import ChatService
from app.services.memory_resolver import MemoryResolver
from app.services.session_service import SessionService


class FakeLLMProvider(LLMProvider):
    """Предсказуемый fake для тестов (Predictable fake for tests)."""

    def __init__(self):
        self.last_system_prompt = None
        self.last_history = None
        self.last_user_message = None
        self.reply = "Тестовый ответ астролога"
        self.summary_result = {"summary": "test summary", "key_facts": ["fact1"], "mood": "neutral"}
        self.classify_result = False

    async def generate_reply(self, system_prompt: str, history: list[dict], user_message: str) -> str:
        self.last_system_prompt = system_prompt
        self.last_history = history
        self.last_user_message = user_message
        return self.reply

    async def summarize(self, messages: list[dict]) -> dict:
        return self.summary_result

    async def classify_session_end(self, last_messages: list[dict]) -> bool:
        return self.classify_result


class FakeAstroModel(AstroModelProvider):
    """Fake для тестов (Fake for tests)."""

    def __init__(self):
        self.last_conception_dt = None
        self.last_geo = None

    async def build_natal_matrix(self, conception_dt: datetime, geo: GeoPoint) -> AstroMatrix:
        self.last_conception_dt = conception_dt
        self.last_geo = geo
        return AstroMatrix(
            conception_dt=conception_dt,
            geo=geo,
            sun_sign="Овен",
            moon_sign="Рак",
            rising_sign="Лев",
            planets=[],
            houses={},
            aspects=[],
            dominant_elements={},
            dominant_qualities={},
            lunar_day=1,
            season_power=0.5,
        )


class FakeUserRepository(UserRepository):
    """Fake user repository for tests."""

    def __init__(self):
        self.users: dict[int, User] = {}
        self._next_id = 1

    async def get_by_id(self, user_id: int) -> User | None:
        for u in self.users.values():
            if u.id == user_id:
                return u
        return None

    async def get_by_tg_id(self, tg_id: int) -> User | None:
        return self.users.get(tg_id)

    async def create(self, user: User) -> User:
        user.id = self._next_id
        self._next_id += 1
        self.users[user.tg_id] = user
        return user

    async def save(self, user: User) -> None:
        self.users[user.tg_id] = user

    async def update_memory_summary(self, user_id: int, summary: str, version: int) -> None:
        for u in self.users.values():
            if u.id == user_id:
                u.memory_summary = summary
                u.memory_summary_version = version + 1
                return


class FakeSessionRepository(SessionRepository):
    """Fake session repository for tests."""

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
        return []


class FakeMemoryRepository(MemoryRepository):
    """Fake memory repository for tests."""

    def __init__(self):
        self.memories: dict[int, MemorySummary] = {}

    async def get_by_user_id(self, user_id: int) -> MemorySummary | None:
        return self.memories.get(user_id)

    async def save(self, memory: MemorySummary) -> MemorySummary:
        self.memories[memory.user_id] = memory
        return memory


@pytest.fixture
def settings():
    return Settings(
        ollama_api_base="http://localhost:11434",
        semantic_check_interval=5,
        explicit_end_phrases=["пока", "до свидания"],
        n_system_prompt="Ты — предиктивный астролог.",
        prompt_file="/tmp/nonexistent_prompt_for_tests.md",
    )


@pytest.fixture
def user_repo():
    return FakeUserRepository()


@pytest.fixture
def session_repo():
    return FakeSessionRepository()


@pytest.fixture
def memory_repo():
    return FakeMemoryRepository()


@pytest.fixture
def llm():
    return FakeLLMProvider()


@pytest.fixture
def astro_model():
    return FakeAstroModel()


@pytest.fixture
def session_service(session_repo, llm, settings):
    return SessionService(session_repo=session_repo, llm_provider=llm, settings=settings)


@pytest.fixture
def memory_resolver(memory_repo, user_repo, llm):
    return MemoryResolver(memory_repo=memory_repo, user_repo=user_repo, llm_provider=llm)


@pytest.fixture
def chat_service(user_repo, session_service, astro_model, llm, memory_resolver, settings):
    return ChatService(
        user_repo=user_repo,
        session_service=session_service,
        astro_model=astro_model,
        llm_provider=llm,
        memory_resolver=memory_resolver,
        settings=settings,
    )


class TestChatService:
    """Тесты ChatService (ChatService tests)."""

    async def test_handle_message_returns_reply(self, chat_service, user_repo, tg_id=12345):
        """Обработка сообщения возвращает ответ (Message handling returns a reply)."""
        user = User(tg_id=tg_id, status="ACTIVE")
        await user_repo.create(user)

        reply = await chat_service.handle_message(tg_id=tg_id, text="Привет")
        assert reply == "Тестовый ответ астролога"

    async def test_handle_message_creates_session(self, chat_service, user_repo, session_repo, tg_id=12346):
        """Обработка сообщения создаёт сессию (Message handling creates a session)."""
        user = User(tg_id=tg_id, status="ACTIVE")
        await user_repo.create(user)

        await chat_service.handle_message(tg_id=tg_id, text="Привет")

        session = await session_repo.get_active_by_user_id(user.id)
        assert session is not None
        assert session.status == "ACTIVE"

    async def test_handle_message_without_user_raises(self, chat_service):
        """Обработка сообщения без пользователя вызывает ошибку (No user raises error)."""
        from app.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await chat_service.handle_message(tg_id=99999, text="Привет")

    async def test_handle_message_increments_counters(self, chat_service, user_repo, tg_id=12347):
        """Обработка сообщения увеличивает счётчики (Message handling increments counters)."""
        user = User(tg_id=tg_id, status="ACTIVE")
        await user_repo.create(user)

        await chat_service.handle_message(tg_id=tg_id, text="Привет")
        updated = await user_repo.get_by_tg_id(tg_id)
        assert updated.daily_messages == 1
        assert updated.weekly_messages == 1

    async def test_handle_message_passes_system_prompt(self, chat_service, user_repo, llm, tg_id=12348):
        """Обработка сообщения передаёт system prompt в LLM (Message handling passes system prompt)."""
        user = User(tg_id=tg_id, status="ACTIVE")
        await user_repo.create(user)

        await chat_service.handle_message(tg_id=tg_id, text="Привет")
        assert llm.last_system_prompt is not None
        assert "Ты — предиктивный астролог" in llm.last_system_prompt
