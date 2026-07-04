# Руководство по тестированию (Testing Guide)

> Как писать и запускать тесты в AstroBot.

## Два уровня тестов

```
tests/
├── conftest.py              # Фикстуры pytest
├── unit/                    # Быстрые, с моками интерфейсов
│   ├── test_chat_service.py
│   ├── test_onboarding_service.py
│   ├── test_session_lifecycle.py
│   ├── test_memory_service.py
│   └── test_billing_service.py
└── integration/             # С реальной БД (testcontainers)
    ├── test_user_repository.py
    ├── test_session_repository.py
    ├── test_rate_limiter.py
    └── test_encryption.py
```

| Тип | Скорость | БД | Внешние API |
|-----|----------|----|-------------|
| Unit | быстро (< 1 сек) | мок (fake-реализации) | мок |
| Integration | средне (10-60 сек) | testcontainers (Postgres + Redis) | мок |

## Ключевое правило

**Сервисы (`services/`) тестируются с fake-реализациями интерфейсов, без БД и сети.**

```python
# tests/unit/test_chat_service.py
from app.domain.interfaces.llm import LLMProvider
from app.domain.interfaces.repositories import UserRepository


class FakeLLMProvider(LLMProvider):
    """Предсказуемый fake для тестов"""
    async def generate_reply(self, system_prompt, history, user_message) -> str:
        return "Тестовый ответ"

    async def summarize(self, messages) -> dict:
        return {"summary": "test"}

    async def classify_session_end(self, last_messages) -> bool:
        return False


class FakeUserRepository(UserRepository):
    def __init__(self):
        self.users = {}

    async def get_by_tg_id(self, tg_id) -> User | None:
        return self.users.get(tg_id)

    async def save(self, user) -> None:
        self.users[user.tg_id] = user
```

## Тестирование сервиса

```python
# tests/unit/test_chat_service.py
@pytest.mark.asyncio
async def test_handle_message_returns_reply():
    llm = FakeLLMProvider()
    repo = FakeUserRepository()
    rate_limiter = FakeRateLimiter(allowed=True)
    service = ChatService(user_repo=repo, llm_provider=llm, rate_limiter=rate_limiter)

    reply = await service.handle_message(user_id=1, text="Привет")
    assert reply == "Тестовый ответ"
```

## Интеграционные тесты (testcontainers)

```python
# tests/integration/test_user_repository.py
import pytest
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession


@pytest.fixture
async def db_session():
    with PostgresContainer("postgres:16") as postgres:
        engine = create_async_engine(postgres.get_connection_url())
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncSession(engine) as session:
            yield session
```

## Запуск тестов

```bash
# Все тесты
pytest tests/ -v

# Unit только
pytest tests/unit/ -v

# Integration только
pytest tests/integration/ -v

# С coverage
pytest --cov=app tests/ -v

# Быстрый запуск (без integration)
pytest tests/unit/ -v --ignore=tests/integration
```

## Что тестировать

### Unit-тесты (обязательно)
- `ChatService.handle_message()` — корректный вызов LLM, сохранение message, инкремент лимитов
- `SessionLifecycleService.on_message_processed()` — три сигнала конца сессии
- `OnboardingService.finalize()` — геокодинг, генерация conception_time, вызов AstroModelProvider
- `MemoryService.merge_fact_into_summary()` — optimistic lock
- `BillingService.apply_payment()` — идемпотентность

### Integration-тесты (обязательно)
- Репозитории — CRUD, optimistic lock
- `RedisRateLimiter` — три метрики, превышение лимита
- `AESCipher` — шифрование/дешифрование, смена ключа
- `PromptEngineeredAstroModel` — формат AstroMatrix

### Что НЕ тестировать
- Внешние API (Anthropic, CryptoBot, Nominatim) — только мок
- Aiogram-хендлеры (end-to-end тесты — опционально)
- Celery-таски (только бизнес-логику внутри)

---

*Последнее обновление: 04.07.2026*
