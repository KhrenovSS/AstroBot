# Changelog — AstroBot

All notable changes to this project are tracked here.

## [04.07.2026] — Initial scaffold (Phase 1)

### Added
- **Документация проекта**: README.md, AGENTS.md, CHANGELOG.md, TECH_DEBT.md, PHASE_1_PLAN.md
- **docs/**: ARCHITECTURE.md, CODE_GUIDELINES.md, API_ROUTES_GUIDE.md, ERROR_HANDLING.md, NAMING_CONVENTIONS.md, TESTING.md, LOGGING.md, CHECKLIST_API.md, CHECKLIST_FEATURE.md, CHECKLIST_MIGRATION.md, DEVELOPMENT_GUIDELINES.md, ASTRO_MODEL_DESIGN.md
- **Концепция**: Clean Architecture (4 слоя), модульный монолит с чёткими границами через ABC-интерфейсы
- **Архитектура зафиксирована**: 5 Docker-контейнеров (app, worker, beat, postgres, redis), ручной DI в `app/di.py`, трёхсигнальная модель завершения сессии
- **Интерфейсы**: AstroModelProvider, LLMProvider, PaymentProvider, UserRepository, RateLimiter — с точными сигнатурами

## [04.07.2026] — Sprint 1: скелет проекта и Docker-инфраструктура

### Added
- **Структура директорий**: 29 пакетов с `__init__.py` по Clean Architecture (4 слоя)
- **Конфигурация**: `pyproject.toml` с зависимостями, `app/config.py` (pydantic-settings), `.env.example`
- **Docker**: `Dockerfile` (multi-stage: app/worker/beat), `docker-compose.yml` (5 контейнеров с healthcheck), `docker-compose.prod.yml` (replicas)
- **FastAPI entrypoint**: `app/main.py` — create_app() + `/health` endpoint + lifespan (DI, logger)
- **DI-контейнер**: `app/di.py` — `Container` dataclass + `build_container(settings)`
- **Базовые исключения**: `app/exceptions.py` — 8 типизированных классов ошибок
- **Логгер**: `app/utils/logger.py` — настройка корневого логгера
- **Celery**: `worker/celery_app.py` + задачи-заглушки (`memory_tasks`, `session_tasks`)
- **Beat**: `beat/schedule.py` — расписание периодических задач
- **Alembic**: `alembic.ini` + `alembic/env.py` (async online/offline) + `alembic/script.py.mako`
- **SQLAlchemy Base**: `app/infra/db/models.py` — `DeclarativeBase`
- **Тесты**: `tests/unit/test_di.py` — проверка сборки контейнера
- **.gitignore**: `__pycache__/`, `.env`, `*.egg-info/`

## [04.07.2026] — Sprint 2: БД + AES + ABC-интерфейсы

### Added
- **Domain entities**: `app/domain/entities/user.py`, `session.py`, `memory.py`, `payment.py`, `astro.py` — Pydantic-модели предметной области
- **ABC-интерфейсы**: `app/domain/interfaces/repositories.py` (UserRepository, SessionRepository, MemoryRepository, TransactionRepository), `astro_model.py`, `llm.py`, `payment.py`, `rate_limiter.py`
- **SQLAlchemy модели**: `app/infra/db/models.py` — User, ChatSession, MemorySummary, Transaction с enum-статусами, FK, индексами, unique-constraints
- **AES-256-GCM шифрование**: `app/infra/crypto/aes_cipher.py` — AESCipher с encrypt/decrypt, генерацией ключа, защитой от подмены
- **Репозитории**: `app/infra/db/repositories.py` — SQLAlchemy-реализации всех 4 репозиториев с optimistic lock для memory_summary
- **DI-контейнер**: `app/di.py` — добавлены db_session_factory, user_repo, session_repo, memory_repo, transaction_repo, aes_cipher
- **Alembic миграция**: `alembic/versions/0001_initial_schema.py` — создание всех 4 таблиц
- **Исключения**: `app/exceptions.py` — добавлены AuthenticationError, SessionEndError, MemoryConflictError
- **Тесты**: 27 unit-тестов (DI, AES-шифрование, репозитории)

## [05.07.2026] — Sprint 3: онбординг, FSM, геокодинг, conception_time

### Added
- **FSM состояния**: `app/bot/fsm/onboarding_states.py` — Aiogram StatesGroup (ASK_BIRTH_DATE → ASK_BIRTH_PLACE → ASK_BIRTH_TIME → CONFIRM_DATA → COMPLETE)
- **BirthData entity**: `app/domain/entities/birth_data.py` — Pydantic-модель для сбора ПДн (дата/место/время рождения, данные родителей)
- **GeoProvider interface**: `app/domain/interfaces/geo.py` — ABC-контракт для геокодинга
- **NominatimClient**: `app/infra/geo/nominatim_client.py` — реализация GeoProvider через Nominatim (OpenStreetMap) с определением таймзоны
- **ConceptionService**: `app/services/conception_service.py` — детерминированная генерация conception_time (SHA-256 seed → offset в диапазоне 266–287 дней до рождения)
- **OnboardingService**: `app/services/onboarding_service.py` — use-case онбординга: создание пользователя, сбор ПДн, геокодинг, шифрование (AES-256-GCM), генерация conception_time, переключение в ACTIVE
- **Onboarding handler**: `app/bot/handlers/onboarding.py` — Aiogram-хендлеры для /start и FSM-шагов онбординга
- **DI-контейнер**: `app/di.py` — добавлены GeoProvider (NominatimClient), ConceptionService, OnboardingService
- **Конфигурация**: `app/config.py` — настройки Nominatim (url, user_agent, timeout)
- **Тесты**: 9 unit-тестов (5 для ConceptionService, 4 для OnboardingService)

## [05.07.2026] — Sprint 4: LLM, память, сессии, Celery

### Added
- **AnthropicClient**: `app/infra/llm/anthropic_client.py` — реализация LLMProvider через Anthropic Claude API (generate_reply, summarize, classify_session_end)
- **PromptEngineeredAstroModel**: `app/infra/astro_model/prompt_engineered.py` — MVP AstroModelProvider, генерация AstroMatrix через LLM
- **EphemerisBasedAstroModel**: `app/infra/astro_model/ephemeris_based.py` — заглушка для будущей swisseph-реализации
- **MemoryResolver**: `app/services/memory_resolver.py` — суммаризация диалогов, конфликт-резолюция через optimistic lock
- **SessionService**: `app/services/session_service.py` — lifecycle сессий (get_or_create, on_message_processed с детектором конца сессии, end_session, check_timeouts)
- **ChatService**: `app/services/chat_service.py` — полная оркестрация чата: user → session → astro_matrix → LLM → reply → session_end_check
- **Celery tasks**: `worker/tasks/memory_tasks.py` (summarize_memory) и `worker/tasks/session_tasks.py` (check_session_timeout) — реальная реализация через asyncio.run + DI
- **Chat handler**: `app/bot/handlers/chat.py` — Aiogram-хендлеры /help, /new, обработка сообщений
- **DI-контейнер**: `app/di.py` — добавлены AnthropicClient, PromptEngineeredAstroModel, SessionService, MemoryResolver, ChatService
- **Конфигурация**: `app/config.py` — anthropic_model, anthropic_max_tokens, anthropic_temperature, anthropic_api_base, semantic_check_interval, n_system_prompt, explicit_end_phrases
- **Тесты**: 12 новых unit-тестов (ChatService — 5, SessionService — 7, PromptEngineeredAstroModel — 3)

## [05.07.2026] — Sprint 4 (hotfix): Anthropic/Groq → локальный Ollama

### Changed
- **Миграция LLM**: Anthropic Claude → Groq (не заработал) → **Ollama локально**
- `app/config.py` — `anthropic_*` / `groq_*` → `ollama_*` (api_base, model, timeout)
- `app/di.py` — `AnthropicClient` / `GroqClient` → `OllamaClient`
- `app/infra/llm/anthropic_client.py` / `groq_client.py` → `app/infra/llm/ollama_client.py`
- `.env` / `.env.example` — все ключи API удалены, LLM работает локально без ключей

### Added
- **Ollama установлен** (v0.31.1), модель `qwen2.5:0.5b` (494MB) скачана
- `app/infra/llm/ollama_client.py` — реализация LLMProvider через локальный Ollama API (`POST /api/chat`)
- Инструкция по запуску Ollama в `AGENTS.md`

### Removed
- Зависимость от внешних API-ключей (Anthropic, Groq) — проект полностью автономен
- `app/infra/llm/anthropic_client.py` — удалён из импортов (файл сохранён для истории)

---

*Версия: 0.4.1*
