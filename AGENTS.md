# Контекст проекта AstroBot

## Суть
Telegram-бот «предиктивный астролог» на основе момента зачатия. «Программист-математик» создал математическую модель предсказаний; LLM интерпретирует структурированные данные модели.

## Стек
Python 3.12 + FastAPI + Aiogram 3 + SQLAlchemy 2.0 (async) + PostgreSQL 16 + Redis 7 + Celery.
Docker Compose — 5 контейнеров (app, worker, beat, postgres, redis).
Архитектура — Clean Architecture (4 слоя), ручной DI (`app/di.py`).

## Документация для разработки

**Перед написанием кода прочитай соответствующий раздел:**

| Задача | Документация |
|--------|--------------|
| Общие правила написания кода | [`docs/CODE_GUIDELINES.md`](docs/CODE_GUIDELINES.md) |
| Архитектура и структура проекта | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Как писать API endpoints | [`docs/API_ROUTES_GUIDE.md`](docs/API_ROUTES_GUIDE.md) |
| Обработка ошибок | [`docs/ERROR_HANDLING.md`](docs/ERROR_HANDLING.md) |
| Соглашения об именовании | [`docs/NAMING_CONVENTIONS.md`](docs/NAMING_CONVENTIONS.md) |
| Как писать тесты | [`docs/TESTING.md`](docs/TESTING.md) |
| Логирование и аудит | [`docs/LOGGING.md`](docs/LOGGING.md) |
| Дизайн AstroModelProvider | [`docs/ASTRO_MODEL_DESIGN.md`](docs/ASTRO_MODEL_DESIGN.md) |
| Code review / самопроверка | [`docs/CHECKLIST_FEATURE.md`](docs/CHECKLIST_FEATURE.md) |
| Миграции БД | [`docs/CHECKLIST_MIGRATION.md`](docs/CHECKLIST_MIGRATION.md) |

## Золотые правила (кратко)

1. **Clean Architecture** — `domain/` не импортирует `infra/`, `services/` импортирует только интерфейсы, `bot/handlers/` не содержит бизнес-логики.
2. **Интерфейсы** — все модули через ABC в `domain/interfaces/`. Реализация подставляется через DI (`app/di.py`).
3. **DI** — `Container` создаётся ровно один раз при старте в `main.py`. Никогда не создавать репозитории/провайдеры внутри хендлеров.
4. **Ошибки** — используй `app/exceptions.py`. Запрещён `except: pass`.
5. **API** — тонкие роуты: валидация → сервис → ответ.
6. **База данных** — миграции только через Alembic; параметризованные запросы.
7. **Логирование** — `logger` из `app/utils/logger.py`, не `print()`.
8. **Комментарии** — bilingual (RU/EN), сразу.
9. **Тесты** — unit для `services/` (с fake-реализациями интерфейсов), integration для `infra/` (testcontainers).
10. **CHANGELOG** — обновляй в том же коммите.
11. **PII-безопасность** — `encrypted_birth_data` никогда не логировать и не передавать в Celery-таски сырым (только `user_id`).
12. **Идемпотентность платежей** — `UNIQUE` constraint на `transactions(provider_transaction_id)`.

## Структура файлов

```
astrobot/
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── alembic.ini
├── pyproject.toml
├── app/
│   ├── main.py                   # entrypoint FastAPI + webhook route
│   ├── config.py                 # Settings (pydantic-settings)
│   ├── di.py                     # Container, build_container()
│   ├── domain/
│   │   ├── entities/             # User, ChatSession, AstroMatrix, Plan...
│   │   └── interfaces/           # AstroModelProvider, LLMProvider, PaymentProvider...
│   ├── services/                 # OnboardingService, ChatService, MemoryService...
│   ├── infra/
│   │   ├── db/                   # SQLAlchemy models, session, repositories
│   │   ├── crypto/               # AES-256-GCM cipher
│   │   ├── geo/                  # Nominatim geocoding client
│   │   ├── astro_model/          # PromptEngineeredAstroModel, EphemerisBasedAstroModel
│   │   ├── llm/                  # AnthropicLLMProvider, WhisperClient
│   │   ├── payments/             # CryptoBotProvider, TelegramStarsProvider, FiatProvider
│   │   ├── rate_limit/           # RedisRateLimiter
│   │   └── notify/              # TelegramBroadcast
│   ├── bot/                      # PRESENTATION (Telegram)
│   │   ├── fsm/                  # onboarding_states.py
│   │   ├── handlers/             # onboarding, chat, billing, feedback
│   │   ├── middlewares/          # DI middleware, rate limit middleware
│   │   └── keyboards.py
│   └── admin/                    # PRESENTATION (Admin API)
│       ├── routers/              # stats, users, broadcast
│       └── auth.py
├── worker/                       # Celery worker
│   ├── celery_app.py
│   └── tasks/                    # memory_tasks, session_tasks, payment_tasks
├── beat/                         # Celery beat
│   └── schedule.py
├── alembic/
│   └── versions/
└── tests/
    ├── unit/                     # мокаем domain/interfaces/*
    └── integration/              # testcontainers: postgres + redis
```

## Ключевые интерфейсы

```python
# app/domain/interfaces/astro_model.py
class AstroModelProvider(ABC):
    @abstractmethod
    async def build_natal_matrix(self, conception_dt: datetime, geo: GeoPoint) -> AstroMatrix: ...

# app/domain/interfaces/llm.py
class LLMProvider(ABC):
    @abstractmethod
    async def generate_reply(self, system_prompt, history, user_message) -> str: ...
    @abstractmethod
    async def summarize(self, messages) -> dict: ...
    @abstractmethod
    async def classify_session_end(self, last_messages) -> bool: ...

# app/domain/interfaces/payment.py
class PaymentProvider(ABC):
    @abstractmethod
    async def create_invoice(self, user_id, plan) -> Invoice: ...
    @abstractmethod
    async def verify_webhook(self, raw_body, headers) -> PaymentResult: ...

# app/domain/interfaces/repositories.py
class UserRepository(ABC):
    @abstractmethod
    async def get_by_tg_id(self, tg_id) -> User | None: ...
    @abstractmethod
    async def save(self, user) -> None: ...
    @abstractmethod
    async def update_memory_summary(self, user_id, summary, version) -> None: ...

# app/domain/interfaces/rate_limiter.py
class RateLimiter(ABC):
    @abstractmethod
    async def check_and_increment(self, user_id, event) -> RateLimitDecision: ...
```

**Реализации подставляются в `app/di.py`. Выбор `AstroModelProvider` — исключительно там, не `if model_type` в сервисах.**

## Определение конца сессии — алгоритм

```python
async def on_message_processed(self, session, last_user_text):
    if self._matches_explicit_phrase(last_user_text):       # классификатор намерений
        await self._end_session(session, EXPLICIT_PHRASE)
        return
    session.messages_since_last_semantic_check += 1
    if session.messages_since_last_semantic_check >= N:     # по счётчику
        is_ending = await self.llm_provider.classify_session_end(session.last_n_messages(6))
        if is_ending:
            await self._end_session(session, SEMANTIC)

# отдельно, в beat:
async def check_timeouts(self):
    stale = await self.session_repo.find_active_older_than(TIMEOUT_MINUTES)
    for s in stale:
        await self._end_session(s, TIMEOUT)
```

## Платежи — идемпотентность

```python
def apply_payment(result):
    # UNIQUE(provider_transaction_id) — повторный webhook = no-op
    INSERT ... ON CONFLICT (provider_transaction_id) DO NOTHING
```

## Жёсткие анти-правила

1. **Не вызывать Telegram Bot API из `worker/tasks/`** — только через outbox-таблицу.
2. **Не логировать `encrypted_birth_data`** — ни в логах, ни в Celery-задачах.
3. **Не создавать соединения с БД/Redis внутри хендлеров** — через DI пул.
4. **Не смешивать верификацию webhook с бизнес-логикой** — проверка подписи до чтения payload.
5. **Не вызывать `classify_session_end` на каждое сообщение** — только по счётчику.
6. **Не писать бизнес-правила в `bot/handlers/` или `admin/routers/`**.
7. **Не заменять `AstroModelProvider` условным `if` внутри `ChatService`**.

## Фазы реализации

**PHASE 1** — `docker-compose.yml`, `Dockerfile`, `pyproject.toml`, `app/config.py`, пустые пакеты.
**PHASE 2** — `infra/db/models.py`, `alembic/`, `infra/crypto/aes_cipher.py`, `domain/interfaces/*`.
**PHASE 3** — `bot/fsm/`, `bot/handlers/onboarding.py`, `services/onboarding_service.py`, `infra/geo/`, `infra/llm/whisper_client.py`.
**PHASE 4** — `infra/llm/anthropic_provider.py`, `infra/astro_model/`, `services/chat_service.py`, `services/session_lifecycle_service.py`, `services/memory_service.py`, `worker/tasks/`.
**PHASE 5** — `infra/rate_limit/`, `services/billing_service.py`, `domain/entities/billing.py`, `infra/payments/`, `admin/routers/`.

---

**Если сессия прервана:** прочитать `AGENTS.md` и `README.md`.
