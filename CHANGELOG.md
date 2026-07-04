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

---

*Версия: 0.3.0*
