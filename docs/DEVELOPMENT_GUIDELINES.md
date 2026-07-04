# Development Guidelines — AstroBot

> Единая точка входа для стандартов разработки.

## Обязательно к прочтению

| Задача | Читать |
|--------|--------|
| Начать работу с проектом | [`AGENTS.md`](../AGENTS.md) |
| Общие правила написания кода | [`CODE_GUIDELINES.md`](CODE_GUIDELINES.md) |
| Архитектура и структура проекта | [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| Как писать API endpoints | [`API_ROUTES_GUIDE.md`](API_ROUTES_GUIDE.md) |
| Обработка ошибок и исключения | [`ERROR_HANDLING.md`](ERROR_HANDLING.md) |
| Соглашения об именовании | [`NAMING_CONVENTIONS.md`](NAMING_CONVENTIONS.md) |
| Как писать тесты | [`TESTING.md`](TESTING.md) |
| Логирование и аудит | [`LOGGING.md`](LOGGING.md) |
| Дизайн модели предсказаний | [`ASTRO_MODEL_DESIGN.md`](ASTRO_MODEL_DESIGN.md) |
| Code review / самопроверка | [`CHECKLIST_FEATURE.md`](CHECKLIST_FEATURE.md) |
| Code review API endpoint | [`CHECKLIST_API.md`](CHECKLIST_API.md) |
| Миграции БД | [`CHECKLIST_MIGRATION.md`](CHECKLIST_MIGRATION.md) |

## Золотые правила (кратко)

1. **Clean Architecture** — `domain/` не импортирует `infra/`, `services/` импортирует только интерфейсы.
2. **Интерфейсы** — все модули через ABC в `domain/interfaces/`. Реализация подставляется через DI.
3. **DI** — `Container` создаётся один раз в `main.py`. Никогда не создавать репозитории/провайдеры внутри хендлеров.
4. **Константы** — используй `from app.config import settings`. Никаких magic numbers.
5. **Исключения** — используй `app/domain/exceptions.py`. Запрещён `except: pass`.
6. **API** — тонкие роуты: валидация → сервис → ответ.
7. **База данных** — миграции только через Alembic; параметризованные запросы.
8. **Логирование** — `logger.info()`/`logger.error()` вместо `print()`.
9. **PII-безопасность** — `encrypted_birth_data` никогда в логах/тасках (только `user_id`).
10. **Комментарии** — bilingual (RU/EN), пиши сразу.
11. **Тесты** — unit для `services/` (fake-реализации), integration для `infra/` (testcontainers).
12. **CHANGELOG** — обновляй сразу в том же коммите.

## Быстрые ссылки

- Запуск: `docker compose up -d`
- Локальная разработка: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- Тесты: `pytest tests/ -v`
- Миграции: `alembic revision --autogenerate -m "description"` && `alembic upgrade head`
- Линтер: `ruff check app/ worker/`
- Типчек: `mypy app/ worker/`

---

*Последнее обновление: 04.07.2026*
