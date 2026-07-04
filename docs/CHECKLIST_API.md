# Чеклист нового API endpoint (Admin API)

Перед коммитом проверь каждый пункт (Check each item before commit):

## Структура (Structure)

- [ ] Роут создан в `admin/routers/<domain>.py`
- [ ] Используется `APIRouter` с `prefix="/admin"` и `tags`
- [ ] Функция имеет docstring (bilingual RU/EN)
- [ ] Путь endpoint логичен: `/admin/stats`, `/admin/users/{id}`, `/admin/broadcast`

## Валидация (Validation)

- [ ] Входные данные валидируются через Pydantic модель
- [ ] Используется `response_model=` для типизации ответа
- [ ] Query параметры имеют типы и ограничения (`Field(ge=, le=)`)
- [ ] Path параметры валидируются (тип, диапазон)

## Бизнес-логика (Business logic)

- [ ] Логика вынесена в `app/services/*.py`
- [ ] Роут тонкий: валидация → вызов сервиса → возврат
- [ ] Нет SQL-запросов напрямую в роуте
- [ ] Нет hardcoded значений — используются константы из `app/config.py`

## Безопасность (Security)

- [ ] Эндпоинт защищён `Depends(verify_admin_key)`
- [ ] Верификация платёжного webhook ДО обработки данных
- [ ] Нет утечки PII (encrypted_birth_data) в ответе
- [ ] Используется `UNIQUE(provider_transaction_id)` для идемпотентности платежей

## Обработка ошибок (Error handling)

- [ ] Используются типизированные исключения
- [ ] `HTTPException` с понятным `detail` для клиента
- [ ] Нет `except: pass` — указаны конкретные типы
- [ ] Ошибки логируются с контекстом (без ПДн)

## Логирование (Logging)

- [ ] Ключевые события аудита записываются в `memory_audit_log`
- [ ] Нет ПДн в логах (encrypted_birth_data, conception_time)
- [ ] `logger.info` для успешных операций
- [ ] `logger.error` для ошибок с контекстом

## Тесты (Tests)

- [ ] Unit-тесты для сервиса (fake-реализации интерфейсов)
- [ ] Тесты на ошибки и граничные случаи
- [ ] Тесты проходят: `pytest tests/unit/ -v`

---

*Последнее обновление: 04.07.2026*
