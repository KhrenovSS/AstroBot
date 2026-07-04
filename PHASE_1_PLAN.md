# PHASE 1 — Скелет проекта и Docker

## Цель
Создать структуру директорий, Docker-инфраструктуру и базовую конфигурацию проекта. Результат Phase 1 — запускаемый `docker compose up` с пустыми сервисами, но готовой архитектурой.

## Перед началом работы
1. Прочитать `AGENTS.md` — правила кодирования, комментарии, коммиты
2. Прочитать `docs/CODE_GUIDELINES.md`
3. Прочитать `README.md` — актуальное состояние проекта

## Статус работ

- [ ] **Шаг 0 — Подготовка**
  - [ ] Создать директории: `app/domain/entities/`, `app/domain/interfaces/`, `app/services/`, `app/infra/db/repositories/`, `app/infra/crypto/`, `app/infra/geo/`, `app/infra/astro_model/`, `app/infra/llm/`, `app/infra/payments/`, `app/infra/rate_limit/`, `app/infra/notify/`, `app/bot/fsm/`, `app/bot/handlers/`, `app/bot/middlewares/`, `app/admin/routers/`, `worker/tasks/`, `beat/`, `alembic/versions/`, `tests/unit/`, `tests/integration/`
  - [ ] Создать `__init__.py` во всех пакетах (пустые)
  - [ ] Проверить `git status`

- [ ] **Шаг 1 — Конфигурация и зависимости**
  - [ ] 1.1 Создать `pyproject.toml` с зависимостями (fastapi, aiogram, sqlalchemy, alembic, celery, redis, pydantic-settings, cryptography, httpx)
  - [ ] 1.2 Создать `app/config.py` — `Settings(BaseSettings)` из pydantic-settings
  - [ ] 1.3 Создать `.env.example` со всеми переменными окружения
  - [ ] 1.4 Создать `alembic.ini` + `alembic/env.py` + `alembic/script.py.mako`

- [ ] **Шаг 2 — Docker**
  - [ ] 2.1 Создать `Dockerfile` для `astrobot-app` (Python 3.12-slim, установка зависимостей, копирование кода)
  - [ ] 2.2 Создать `Dockerfile` для `astrobot-worker` (тот же образ, entrypoint = celery worker)
  - [ ] 2.3 Создать `docker-compose.yml` — 5 сервисов: app, worker, beat, postgres, redis
  - [ ] 2.4 Healthcheck для postgres (pg_isready) и redis (redis-cli ping)
  - [ ] 2.5 `docker-compose.prod.yml` — `deploy.replicas` для app и worker

- [ ] **Шаг 3 — Точка входа FastAPI**
  - [ ] 3.1 Создать `app/main.py` — create_app() + uvicorn.run()
  - [ ] 3.2 Создать `app/di.py` — класс `Container` + `build_container(settings)`
  - [ ] 3.3 Проверить: `docker compose up` стартует без ошибок, /health возвращает 200

- [ ] **Шаг 4 — Тестовая заглушка**
  - [ ] 4.1 Написать `tests/unit/test_di.py` — проверить, что build_container() возвращает Container с правильными типами
  - [ ] 4.2 Проверить: `pytest tests/unit/ -v` проходит

## Критические проверки

- [ ] `docker compose up -d` — все 5 контейнеров стартуют
- [ ] `docker compose ps` — все `Up (healthy)`
- [ ] `curl localhost:8000/health` — 200 OK
- [ ] `git status` — нет лишних файлов
- [ ] `pytest tests/ -v` — тесты проходят

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
