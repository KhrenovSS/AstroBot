# Чеклист новой фичи

Перед коммитом проверь каждый пункт (Check each item before commit):

## Архитектура (Architecture)

- [ ] DRY — нет дублирования кода
- [ ] Код организован по слоям (PRESENTATION → APPLICATION → DOMAIN → INFRASTRUCTURE)
- [ ] Файл не больше ~500 строк (если больше — вынести)
- [ ] Нет циклических импортов
- [ ] Новый интерфейс (ABC) добавлен в `app/domain/interfaces/`
- [ ] Реализация — в `app/infra/<module>/`
- [ ] Бизнес-логика — в `app/services/`, не в хендлере/роуте

## Константы (Constants)

- [ ] Нет hardcoded значений — используются из `settings`
- [ ] Новые настройки добавлены в `app/config.py`
- [ ] Магические числа заменены на именованные константы

## Код (Code)

- [ ] Комментарии bilingual (RU/EN), написаны сразу
- [ ] Docstring для каждой функции/класса
- [ ] Типизация (type hints) для аргументов и return
- [ ] Нет `print()` — используется `logger`
- [ ] Нет `except: pass` — указаны конкретные типы
- [ ] Асинхронные функции — async/await

## PII-безопасность (PII Security)

- [ ] `encrypted_birth_data` не передаётся в Celery-таски сырым (только user_id)
- [ ] ПДн не логируются и не попадают в Sentry breadcrumbs
- [ ] Шифрование AES-256-GCM перед сохранением ПДн

## Обработка ошибок (Error handling)

- [ ] Используются типизированные исключения
- [ ] Ошибки логируются с контекстом
- [ ] User-friendly сообщения (не stack traces)

## Тесты (Tests)

- [ ] Unit-тесты для бизнес-логики (fake-реализации интерфейсов)
- [ ] Edge cases покрыты
- [ ] Тесты проходят: `pytest tests/unit/ -v`

## Документация (Documentation)

- [ ] CHANGELOG.md обновлён
- [ ] AGENTS.md обновлён (структура файлов, статус)
- [ ] README.md обновлён (features, roadmap)
- [ ] Если новый endpoint — docs/API_ROUTES_GUIDE.md обновлён

---

*Последнее обновление: 04.07.2026*
