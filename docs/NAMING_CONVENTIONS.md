# Соглашения об именовании (Naming Conventions)

> Как называть файлы, классы, функции, переменные в AstroBot.

## Таблица соглашений

| Элемент | Стиль | Пример |
|---------|-------|--------|
| Файлы и модули | `snake_case` | `chat_service.py`, `onboarding_states.py` |
| Классы | `PascalCase` | `ChatService`, `OnboardingStates` |
| Функции и методы | `snake_case` | `derive_conception_time()`, `handle_message()` |
| Переменные | `snake_case` | `memory_summary`, `conception_dt` |
| Константы | `UPPER_SNAKE_CASE` | `SESSION_TIMEOUT_SECONDS`, `MAX_MESSAGES_DAILY` |
| Приватные методы/переменные | `_prefix` | `_derive_seed()`, `_cached_geo` |
| Pydantic модели | `PascalCase` | `AstroMatrix`, `GeoPoint`, `RateLimitDecision` |
| SQLAlchemy модели | `PascalCase` | `User`, `ChatSession`, `Transaction` |
| ABC-интерфейсы | `PascalCase` | `AstroModelProvider`, `LLMProvider` |
| Реализации интерфейсов | `PascalCase` | `PromptEngineeredAstroModel`, `AnthropicLLMProvider` |
| Celery-таски | `snake_case` | `summarize_session`, `resolve_memory_conflict` |
| Тестовые файлы | `test_*.py` | `test_chat_service.py` |
| Тестовые классы | `TestPascalCase` | `TestChatService` |
| Фикстуры pytest | `snake_case` | `db_session`, `sample_user` |

## Примеры

### Файлы

```
✅ app/services/chat_service.py
✅ app/domain/interfaces/llm.py
✅ app/infra/llm/anthropic_provider.py
✅ worker/tasks/memory_tasks.py
✅ tests/unit/test_chat_service.py

❌ app/services/ChatService.py
❌ app/domain/interfaces/LLMProvider.py
❌ app/infra/llm/AnthropicProvider.py
```

### Классы

```python
# ✅
class ChatService:
    pass

class PromptEngineeredAstroModel(AstroModelProvider):
    pass

# ❌
class chat_service:
    pass

class prompt_engineered_model:
    pass
```

### Функции и переменные

```python
# ✅
async def handle_message(user_id: int, text: str) -> str: ...
conception_time = derive_conception_time(collected_data)

# ❌
async def HandleMessage(UserId, Text): ...
ConceptionTime = DeriveConceptionTime(CollectedData)
```

### Константы и env-переменные

```python
# ✅ app/config.py
session_timeout_seconds: int = 1800
free_trial_messages_daily: int = 50

# ✅ .env.example
SESSION_TIMEOUT_SECONDS=1800
FREE_TRIAL_MESSAGES_DAILY=50
```

### Модули

```
app/
├── domain/
│   ├── entities/       # сущности предметной области
│   └── interfaces/     # ABC-контракты
├── services/           # use-case сервисы
├── infra/              # реализации
│   ├── db/             # БД
│   ├── llm/            # LLM провайдеры
│   └── payments/       # платёжные провайдеры
├── bot/
│   ├── handlers/       # хендлеры Aiogram
│   ├── middlewares/    # middleware
│   └── fsm/            # состояния FSM
└── admin/
    └── routers/        # админ-роуты
```

---

*Последнее обновление: 04.07.2026*
