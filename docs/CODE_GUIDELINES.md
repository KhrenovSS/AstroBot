# Рекомендации по написанию кода (Code Guidelines)

> Практическое руководство: как писать код в AstroBot.

## Содержание

1. [Константы — никаких magic numbers](#1-константы--никаких-magic-numbers)
2. [Архитектура: где писать код](#2-архитектура-где-писать-код)
3. [API endpoints: тонкие роуты](#3-api-endpoints-тонкие-роуты)
4. [База данных и миграции](#4-база-данных-и-миграции)
5. [Интерфейсы и DI](#5-интерфейсы-и-di)
6. [Обработка ошибок](#6-обработка-ошибок)
7. [Логирование и PII-безопасность](#7-логирование-и-pii-безопасность)
8. [Комментарии и докстринги](#8-комментарии-и-докстринги)
9. [Импорты](#9-импорты)
10. [Асинхронность](#10-асинхронность)

---

## 1. Константы — никаких magic numbers

### Правило
Все числа, строки, URL, пороги — через `from app.config import settings`.

### ❌ До
```python
async def check_rate_limit(user_id: int):
    daily_limit = 50  # magic number
    ...
```

### ✅ После
```python
from app.config import settings

async def check_rate_limit(user_id: int):
    daily_limit = settings.free_trial_messages_daily
    ...
```

### Где брать константы

| Вместо | Используй |
|--------|-----------|
| `50` (лимит сообщений/день) | `settings.free_trial_messages_daily` |
| `1800` (таймаут сессии) | `settings.session_timeout_seconds` |
| `"https://api.anthropic.com"` | `settings.anthropic_api_base` |
| `3.0` (max credible pace для гео) | `settings.geocoding_timeout` |

## 2. Архитектура: где писать код

| Что делаешь | Куда класть | Пример |
|-------------|-------------|--------|
| Новый Aiogram handler | `app/bot/handlers/<domain>.py` | `app/bot/handlers/onboarding.py` |
| Бизнес-логика (use case) | `app/services/<service_name>.py` | `app/services/chat_service.py` |
| ABC-интерфейс | `app/domain/interfaces/<name>.py` | `app/domain/interfaces/llm.py` |
| Pydantic entity | `app/domain/entities/<name>.py` | `app/domain/entities/user.py` |
| Реализация интерфейса | `app/infra/<module>/<implementation>.py` | `app/infra/llm/anthropic_provider.py` |
| SQLAlchemy модель | `app/infra/db/models.py` | |
| Миграция Alembic | `alembic/versions/` | |
| Celery таск | `worker/tasks/<domain>.py` | `worker/tasks/memory_tasks.py` |
| Конфигурация | `app/config.py` | |
| Тест | `tests/unit/` или `tests/integration/` | |

### Принцип тонких хендлеров/роутов

```python
# bot/handlers/chat.py — ПРАВИЛЬНО
@router.message(Command("start"))
async def start_handler(message: Message, service: OnboardingService = Depends(get_service)):
    await service.start(message.from_user.id)
    await message.answer("Добро пожаловать!")

# bot/handlers/chat.py — НЕПРАВИЛЬНО (бизнес-логика в хендлере)
@router.message(Command("start"))
async def start_handler(message: Message):
    user = await db.query(User).filter(...).first()
    if not user:
        user = User(tg_id=message.from_user.id, status="ONBOARDING")
        db.add(user)
    ...
```

## 3. API endpoints: тонкие роуты

Admin API endpoint должен быть коротким:
```python
# admin/routers/stats.py — ПРАВИЛЬНО
@router.get("/admin/stats")
async def get_stats(service: AdminStatsService = Depends(get_admin_service)):
    stats = await service.get_stats()
    return stats
```

## 4. База данных и миграции

- Миграции — только через Alembic (`alembic revision --autogenerate`)
- Параметризованные запросы — никогда не конкатенируй SQL строки
- Индексы — добавляй для часто запрашиваемых полей (GIN на `messages.content`)
- Optimistic lock — `UPDATE ... WHERE memory_summary_version = :version`

## 5. Интерфейсы и DI

- Все ABC в `app/domain/interfaces/`
- `services/` импортирует только ABC, не конкретные классы
- `app/di.py` — единственное место, где ABC связываются с реализациями
- Никогда: `from app.infra.llm.anthropic_provider import AnthropicLLMProvider` внутри сервиса

## 6. Обработка ошибок

- Используй типизированные исключения из `app/exceptions.py` (или `app/domain/exceptions.py`)
- Запрещён `except: pass` — указывай конкретный тип + логируй
- В хендлерах Aiogram — `except` только для обработки пользовательских ошибок (не технических)

## 7. Логирование и PII-безопасность

- Используй `logger` (стандартный `logging.getLogger`)
- **Никогда не логируй**: `encrypted_birth_data`, сырые даты рождения, пароли, токены
- В Celery-таски передавай только `user_id`, не сырые ПДн

## 8. Комментарии и докстринги

**ВАЖНО: комментарии писать СРАЗУ при написании кода.**

bilingual (RU/EN):
```python
# Расчёт псевдослучайного времени зачатия (Derive pseudo-random conception time)
def derive_conception_time(collected_data: dict) -> datetime:
    ...
```

Правила:
- Каждая `def` (включая вложенные, `__init__`, `_private`) — комментарий выше
- Каждый `class` — комментарий выше
- Каждый нетривиальный блок (`for`, `if`, `try`) внутри функции — комментарий
- `pass`, `return`, простые присваивания — без комментария

## 9. Импорты

Порядок: stdlib → third-party → internal → types

```python
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String

from app.domain.entities.user import User
from app.domain.interfaces.llm import LLMProvider

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.services.chat_service import ChatService
```

## 10. Асинхронность

- Все сервисы и репозитории — async (SQLAlchemy 2.0 async)
- Celery-таски — синхронные обёртки, вызывающие async-сервисы через `asyncio.run()`
- LLM-вызовы — async (httpx.AsyncClient)
- Хендлеры Aiogram — async

---

*Последнее обновление: 04.07.2026*
