# Логирование и аудит (Logging and Audit)

## Уровни наблюдаемости (Observability levels)

Проект реализует **Level 1 Standard observability** на старте, с планом перехода на Level 2:

- Структурированные логи приложения
- Логи HTTP-запросов (Admin API)
- Аудит-события ключевых операций (в БД + файл)
- PII-безопасность: encrypted_birth_data никогда не логируется

## Переменные окружения (Environment variables)

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `LOG_LEVEL` | `info` | Уровень логирования: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FORMAT` | `text` | Формат: `text` (читаемый) или `json` (для анализа) |
| `LOGS_DIR` | `logs` | Директория для лог-файлов |
| `SLOW_REQUEST_MS` | `1000` | Порог медленного запроса в мс |

## Файлы логов (Log files)

Все файлы ротируются ежедневно в полночь UTC. Хранятся 30 дней.

```
logs/
├── app_YYYY-MM-DD.log          # Логи приложения
├── requests_YYYY-MM-DD.log     # Логи HTTP-запросов (Admin API)
└── audit_YYYY-MM-DD.log        # Аудит-события (дублирование БД)
```

## Как получить логгер (How to get a logger)

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Session started", extra={"user_id": user_id, "session_id": session_id})
```

## Важные правила PII-безопасности

### ❌ Никогда не логировать
```python
# ПЛОХО: encrypted_birth_data в логе
logger.info("User birth data: %s", user.encrypted_birth_data)

# ПЛОХО: сырое conception_time пользователя
logger.info("Conception time for user %s: %s", user_id, conception_dt)

# ПЛОХО: ПДн в extra
logger.info("Processing", extra={"birth_date": birth_date})
```

### ✅ Правильно
```python
# OK: user_id без ПДн
logger.info("Onboarding completed for user %s", user_id)

# OK: метрики без ПДн
logger.info("LLM call: %d tokens, %2f seconds", tokens, elapsed)

# OK: технические события
logger.info("Session %s ended, reason=%s", session_id, end_reason.value)
```

## Аудит-события (Audit events)

Ключевые операции записываются в таблицу `memory_audit_log` (в БД) и дублируются в файл:

| Событие | Описание |
|---------|----------|
| `user.onboarding_completed` | Пользователь закончил онбординг |
| `session.explicit_end` | Пользователь явно завершил сессию |
| `session.timeout_end` | Сессия закрыта по таймауту |
| `session.semantic_end` | Сессия закрыта по семантике |
| `memory.summary_updated` | Обновлён memory_summary |
| `memory.conflict_resolved` | Разрешён конфликт памяти |
| `memory.audit_completed` | Периодический аудит памяти выполнен |
| `payment.invoice_created` | Создан счёт на оплату |
| `payment.webhook_received` | Получен вебхук оплаты |
| `payment.completed` | Платёж подтверждён |
| `admin.stats_viewed` | Просмотр статистики админом |
| `admin.broadcast_sent` | Рассылка выполнена |

### Формат записи аудита
```python
{
    "user_id": 123,
    "event": "session.explicit_end",
    "details": {"session_id": 456, "end_reason": "explicit_phrase"},
    "ip_address": None,
    "created_at": "2026-07-04T12:00:00+00:00"
}
```

---

*Последнее обновление: 04.07.2026*
