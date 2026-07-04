# Контекст проекта AstroBot

## Суть
Telegram-бот «предиктивный астролог» на основе момента зачатия. «Программист-математик» создал математическую модель предсказаний; LLM интерпретирует структурированные данные модели.

## Стек
Python 3.12 + FastAPI + Aiogram 3 + SQLAlchemy 2.0 (async) + PostgreSQL 16 + Redis 7 + Celery.
Docker Compose — 5 контейнеров (app, worker, beat, postgres, redis).
Архитектура — Clean Architecture (4 слоя), ручной DI (`app/di.py`).

## Окружение (local dev)

| Параметр | Значение |
|----------|----------|
| ОС | Ubuntu 24.04 LTS |
| Python | 3.12.3 (`/usr/bin/python3`) |
| Установка зависимостей | `pip install --break-system-packages -e ".[dev]"` |
| Запуск тестов | `pytest tests/ -v` (после добавления `~/.local/bin` в PATH) |
| PATH для утилит | `export PATH="$HOME/.local/bin:$PATH"` |

### Sudo
Пароль sudo сохранён в `.env` (в `.gitignore`, не коммитится):
```
SUDO_PASSWORD=<пароль>
```
Для команд, требующих sudo, используется паттерн:
```bash
printf '%s\n' "$SUDO_PASSWORD" | sudo -S <command>
```
Где `SUDO_PASSWORD` читается из `config.sudo_password` или напрямую из `.env`.

Уже настроено NOPASSWD для: `apt`, `apt-get`, `dpkg` (через `/etc/sudoers.d/astrobot`).
Docker НЕ установлен — будет добавлен при необходимости (потребуется sudo и `apt install docker.io`).

### Текущий статус
- **Sprint 1 завершён (04.07.2026)**: скелет проекта, Docker-инфраструктура, конфигурация, базовая архитектура
- **Sprint 2 завершён (04.07.2026)**: SQLAlchemy модели, Alembic миграция (0001), AES-256-GCM шифрование, ABC-интерфейсы, репозитории (User, Session, Memory, Transaction), DI-контейнер расширен, 27 unit-тестов
- **Sprint 3 — не начат**: Онбординг, геокодинг, FSM
- **Sprint 4 — не начат**: LLM, память, сессии, Celery
- **Sprint 5 — не начат**: Лимиты, тарифы, платежи, Admin API

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

## Структура файлов (актуальная, Sprint 1)

```
astrobot/
├── .env.example
├── .env                        # НЕ КОММИТИТСЯ (в .gitignore)
├── .gitignore
├── Dockerfile                  # multi-stage: app / worker / beat
├── docker-compose.yml          # 5 сервисов + healthcheck
├── docker-compose.prod.yml     # replicas
├── pyproject.toml
├── alembic.ini
├── CHANGELOG.md
├── PHASE_1_PLAN.md
├── TECH_DEBT.md
├── docs/                       # 12 файлов документации
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI + /health + lifespan
│   ├── config.py               # Settings (pydantic-settings) + sudo_password
│   ├── di.py                   # Container dataclass, build_container()
│   ├── exceptions.py           # 11 типизированных исключений (Phase 2: +AuthenticationError, SessionEndError, MemoryConflictError)
│   ├── utils/
│   │   └── logger.py           # корневой логгер astrobot
│   ├── domain/
│   │   ├── entities/           # User, ChatSession, MemorySummary, Transaction, AstroMatrix (Phase 2)
│   │   └── interfaces/         # UserRepository, SessionRepository, MemoryRepository, TransactionRepository, AstroModelProvider, LLMProvider, PaymentProvider, RateLimiter (Phase 2)
│   ├── services/               # пусто (Phase 3)
│   ├── infra/
│   │   ├── db/models.py        # User, ChatSession, MemorySummary, Transaction (Phase 2)
│   │   ├── db/repositories.py  # SQLAlchemy реализации репозиториев (Phase 2)
│   │   ├── crypto/aes_cipher.py   # AES-256-GCM (Phase 2)
│   │   ├── geo/                # пусто
│   │   ├── astro_model/        # пусто
│   │   ├── llm/                # пусто
│   │   ├── payments/           # пусто
│   │   ├── rate_limit/         # пусто
│   │   └── notify/             # пусто
│   ├── bot/                    # пусто (Phase 3)
│   │   ├── fsm/
│   │   ├── handlers/
│   │   └── middlewares/
│   └── admin/                  # пусто (Phase 5)
│       └── routers/
├── worker/
│   ├── celery_app.py           # Celery app + configure
│   └── tasks/
│       ├── memory_tasks.py     # заглушка
│       └── session_tasks.py    # заглушка
├── beat/
│   └── schedule.py             # Celery beat schedule
├── alembic/
│   ├── env.py                  # async online + offline mode
│   ├── script.py.mako
│   └── versions/               # 0001_initial_schema.py (Phase 2)
└── tests/
    ├── conftest.py
    ├── unit/
    │   ├── test_di.py          # 3 теста (Phase 2)
    │   ├── test_aes_cipher.py  # 9 тестов (Phase 2)
    │   └── test_repositories.py # 15 тестов (Phase 2)
    └── integration/            # пусто
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

## Спринты (план)

| Спринт | Статус | Что делаем |
|--------|--------|------------|
| **1** — Скелет + Docker | ✅ **Завершён** | Структура, docker-compose, FastAPI entrypoint, config, DI, celery, beat, alembic, тесты |
| **2** — БД + AES + интерфейсы | ✅ **Завершён** | SQLAlchemy models, Alembic миграции, AES-256-GCM, ABC интерфейсы, репозитории |
| **3** — Онбординг + FSM | ⏳ Ожидает | Aiogram FSM, геокодинг (Nominatim), генерация conception_time, Whisper |
| **4** — LLM + память + сессии | ⏳ Ожидает | Anthropic LLM, суммаризация, конфликт-резолюция, сессия lifecycle, Celery tasks |
| **5** — Лимиты + платежи + Admin | ⏳ Ожидает | Redis-лимиты, тарифы, CryptoBot, Telegram Stars, Admin API |

**Следующий шаг:** Sprint 3 — начать с онбординга, FSM (Aiogram), геокодинга (Nominatim), генерации conception_time.

---

**Если сессия прервана:** прочитать `AGENTS.md` и `README.md`.
