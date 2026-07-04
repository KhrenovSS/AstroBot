# PHASE 1 — Скелет проекта и Docker

## Цель
Создать структуру директорий, Docker-инфраструктуру и базовую конфигурацию проекта. Результат Phase 1 — запускаемый `docker compose up` с пустыми сервисами, но готовой архитектурой.

## Перед началом работы
1. Прочитать `AGENTS.md` — правила кодирования, комментарии, коммиты
2. Прочитать `docs/CODE_GUIDELINES.md`
3. Прочитать `README.md` — актуальное состояние проекта

## Статус работ — ✅ ВЫПОЛНЕНО (Sprint 1, 04.07.2026)

- [x] **Шаг 0 — Подготовка**
  - [x] Создать директории: `app/domain/entities/`, `app/domain/interfaces/`, `app/services/`, `app/infra/db/repositories/`, `app/infra/crypto/`, `app/infra/geo/`, `app/infra/astro_model/`, `app/infra/llm/`, `app/infra/payments/`, `app/infra/rate_limit/`, `app/infra/notify/`, `app/bot/fsm/`, `app/bot/handlers/`, `app/bot/middlewares/`, `app/admin/routers/`, `worker/tasks/`, `beat/`, `alembic/versions/`, `tests/unit/`, `tests/integration/`
  - [x] Создать `__init__.py` во всех пакетах (пустые) — 29 файлов
  - [x] Создать `.gitignore`

- [x] **Шаг 1 — Конфигурация и зависимости**
  - [x] 1.1 Создать `pyproject.toml` с зависимостями
  - [x] 1.2 Создать `app/config.py` — `Settings(BaseSettings)`
  - [x] 1.3 Создать `.env.example` со всеми переменными окружения
  - [x] 1.4 Создать `alembic.ini` + `alembic/env.py` + `alembic/script.py.mako`

- [x] **Шаг 2 — Docker**
  - [x] 2.1 Создать `Dockerfile` (multi-stage: app/worker/beat)
  - [x] 2.2 `docker-compose.yml` — 5 сервисов: app, worker, beat, postgres, redis + healthcheck
  - [x] 2.3 `docker-compose.prod.yml` — `deploy.replicas` для app (3) и worker (2)

- [x] **Шаг 3 — Точка входа FastAPI**
  - [x] 3.1 Создать `app/main.py` — create_app() + /health endpoint + lifespan
  - [x] 3.2 Создать `app/di.py` — Container + build_container()
  - [x] 3.3 Создать `app/exceptions.py` — 8 типов ошибок
  - [x] 3.4 Создать `app/utils/logger.py` — корневой логгер

- [x] **Шаг 4 — Celery и воркеры**
  - [x] 4.1 `worker/celery_app.py` — Celery app с конфигурацией
  - [x] 4.2 `worker/tasks/memory_tasks.py` — заглушка summarize_memory
  - [x] 4.3 `worker/tasks/session_tasks.py` — заглушка check_session_timeout
  - [x] 4.4 `beat/schedule.py` — расписание beat

- [x] **Шаг 5 — Тесты**
  - [x] 5.1 `tests/unit/test_di.py` — 2 теста на build_container
  - [x] 5.2 `pytest tests/ -v` — 2 passed

## Критические проверки

- [x] `pytest tests/ -v` — 2 passed
- [ ] ⚠️ `docker compose up -d` — не проверено (нет Docker на машине)
- [ ] ⚠️ `curl localhost:8000/health` — не проверено

## Ошибки и их решения

| Проблема | Решение |
|----------|---------|
| Alembic не видит модели | Проверить `target_metadata = Base.metadata` в `alembic/env.py` |
| Celery не коннектится к Redis | Проверить `CELERY_BROKER_URL` и `CELERY_RESULT_BACKEND` |
| Контейнер worker не стартует | Проверить, что `celery_app.py` импортируется без ошибок |
| PostgreSQL не проходит healthcheck | Проверить POSTGRES_USER/POSTGRES_PASSWORD в `.env` |

## После завершения фазы

```bash
# Проверка структуры
find app worker beat -type f -name "*.py" | sort

# Проверка Docker
docker compose up -d && docker compose ps

# Проверка тестов
pytest tests/ -v

# Финальный коммит
git add -A && git commit -m "Phase 1: project skeleton + Docker infrastructure"
```
