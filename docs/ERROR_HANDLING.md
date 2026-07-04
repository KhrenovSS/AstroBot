# Обработка ошибок (Error Handling)

> Как правильно обрабатывать исключения в AstroBot.

## Главные правила

1. **Запрещён `except: pass`** — всегда указывай тип исключения.
2. **Логируй ошибки** с контекстом (но без ПДн).
3. **Используй типизированные исключения**.
4. **Возвращай user-friendly сообщения**, не stack traces.
5. **Не лови Exception без причины** — лови только то, что можешь обработать.
6. **Верификация webhook** до чтения payload как доверенного.
7. **PII никогда не должна попадать в исключение** или в его лог.

## Иерархия исключений

```
Exception
  └── AppError (базовое)
        ├── NotFoundError            # 404 — пользователь/сессия не найдены
        ├── ValidationError          # 400 — невалидные данные
        ├── AuthenticationError      # 401 — неверный API-ключ админки
        ├── LLMError                 # 502 — ошибка Anthropic API
        ├── PaymentError             # 502 — ошибка платёжного провайдера
        ├── GeoCodingError           # 502 — ошибка геокодинга
        ├── RateLimitError           # 429 — превышен лимит
        ├── SessionEndError          # — ошибка при завершении сессии
        └── MemoryConflictError      # — ошибка при разрешении конфликта памяти
```

## Исключения проекта

| Исключение | Статус | Когда использовать |
|------------|--------|-------------------|
| `NotFoundError(resource, id)` | 404 | Ресурс не найден в БД |
| `ValidationError(field, reason)` | 400 | Невалидные входные данные |
| `AuthenticationError(reason)` | 401 | Неверный API-ключ или токен |
| `LLMError(endpoint, status, detail)` | 502 | Ошибка Anthropic/LLM API |
| `PaymentError(provider, reason)` | 502 | Ошибка CryptoBot/Stars API |
| `GeoCodingError(place, reason)` | 502 | Не удалось геокодировать место |
| `RateLimitError(metric, limit)` | 429 | Превышен лимит сообщений/времени |
| `SessionEndError(session_id)` | 500 | Ошибка при закрытии сессии |
| `MemoryConflictError(user_id)` | 500 | Ошибка при разрешении конфликта памяти |

## Примеры

### ❌ Неправильно
```python
try:
    result = await llm.generate_reply(...)
except Exception:
    pass  # ошибка проглочена, пользователь не получит ответ
```

### ✅ Правильно
```python
from app.domain.exceptions import LLMError

try:
    result = await llm.generate_reply(...)
except LLMError as e:
    logger.error("LLM API error: %s", e)
    await message.answer("Извините, не удалось обработать запрос. Попробуйте позже.")
```

### Платёжный webhook
```python
# Обязательно: верификация ДО обработки
try:
    payment_result = await payment_provider.verify_webhook(raw_body, headers)
    if not payment_result.valid:
        logger.warning("Invalid payment webhook signature")
        return {"status": "ignored"}
except PaymentError as e:
    logger.error("Payment verification error: %s", e)
    return {"status": "error"}, 500

# Только после верификации — бизнес-логика
await billing_service.apply_payment(payment_result)
```

### Celery-таски
```python
@app.task(bind=True, max_retries=3, default_retry_delay=60)
def summarize_session(self, session_id: int):
    try:
        memory_service = get_memory_service()
        asyncio.run(memory_service.summarize(session_id))
    except MemoryConflictError as e:
        logger.warning("Memory conflict for session %s: %s", session_id, e)
        self.retry(exc=e)
    except Exception as e:
        logger.error("Unexpected error summarizing session %s: %s", session_id, e)
        raise
```

## Логирование ошибок

- Логируй `error_id` (UUID) — можно показать пользователю для поддержки
- **Никогда не логируй**: `encrypted_birth_data`, conception_time, пароли, токены
- В Aiogram-хендлерах используй `message.answer("...")` для user-friendly сообщения

---

*Последнее обновление: 04.07.2026*
