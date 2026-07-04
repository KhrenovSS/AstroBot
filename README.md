# AstroBot — Предиктивный астролог в Telegram

Telegram-бот в роли «предиктивного астролога». Позиционирование: «программист-математик» создал математическую модель предсказаний на основе **момента зачатия** (а не даты/времени/места рождения, как в классической астрологии).

---

## Основные возможности (Features)

- **🧬 Онбординг и геокодинг** — сбор даты, места, времени рождения; геокодинг → координаты + таймзона (Nominatim/Google Geocoding с кэшированием)
- **🔮 Псевдослучайное время зачатия** — детерминированная генерация (seed = hash(user_id + собранные даты), воспроизводимый результат)
- **🤖 LLM-генерация ответов** — персонализированные предсказания на основе `AstroMatrix` + `memory_summary` + `communication_style`
- **🎤 Голосовые сообщения** — транскрибация через Whisper API
- **🧠 Память пользователя** — сырая история сообщений, Celery-суммаризация, конфликт-резолюция, периодический аудит
- **⏱️ Определение конца сессии** — три сигнала: явные стоп-фразы, таймаут, семантическая LLM-проверка
- **📊 Лимиты бесплатного триала** — 3 Redis-счётчика: сообщений/день, сообщений/неделю, суммарное время разговора
- **💰 Монетизация** — Free trial / Weekly / Monthly / Разовая консультация; провайдеры: CryptoBot (USDT), Telegram Stars, Fiat (RUB)
- **⭐ Обратная связь** — оценка сессии (0–10), адаптация `communication_style`
- **🔐 Шифрование ПДн** — AES-256-GCM для даты/места рождения, данных о смерти родственников
- **📈 Admin API** — статистика, управление пользователями, рассылка

---

## Архитектура

### Стек
- **Backend**: Python 3.12, FastAPI, Aiogram 3, SQLAlchemy 2.0 (async)
- **Очереди**: Celery + Redis (broker)
- **БД**: PostgreSQL 16, Redis (FSM state, кэш, счётчики)
- **LLM**: Anthropic API, Whisper API
- **Платежи**: CryptoBot API, Telegram Stars
- **Инфраструктура**: Docker Compose (5 контейнеров)

### Чистая архитектура (Clean Architecture) — 4 слоя

```
┌─────────────────────────────────────────────────────────┐
│ PRESENTATION  (aiogram-хендлеры, FastAPI admin-роуты)    │
│   bot/handlers/*, admin/routers/*                        │
├─────────────────────────────────────────────────────────┤
│ APPLICATION   (use-case сервисы, оркестрация)            │
│   services/*  (OnboardingService, ChatService, ...)      │
├─────────────────────────────────────────────────────────┤
│ DOMAIN        (интерфейсы/контракты, чистые сущности)    │
│   domain/interfaces/*, domain/entities/*                 │
├─────────────────────────────────────────────────────────┤
│ INFRASTRUCTURE (реализации: Postgres, Redis, LLM API,    │
│   Telegram, платёжные провайдеры)                        │
│   infra/db/*, infra/llm/*, infra/payments/*, infra/geo/* │
└─────────────────────────────────────────────────────────┘
```

**Правило**: зависимости — только внутрь. `domain/` не импортирует ничего из `infra/`, `services/` импортирует только интерфейсы из `domain/interfaces/`.

### Контейнеры

| Контейнер | Назначение |
|-----------|-----------|
| `astrobot-app` | FastAPI + Aiogram 3 webhook, Admin API, FSM, оркестрация LLM |
| `astrobot-worker` | Celery worker: суммаризация, conflict resolution, аудит памяти |
| `astrobot-beat` | Celery beat: таймауты сессий, периодический аудит |
| `postgres` | PostgreSQL 16 |
| `redis` | Redis 7 (FSM, кэш, счётчики, брокер) |

---

## Схема базы данных

### `users`
| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | INTEGER PK | |
| `tg_id` | BIGINT UNIQUE | ID Telegram |
| `encrypted_birth_data` | TEXT | AES-256 зашифрованные ПДн |
| `conception_time` | TIMESTAMPTZ | Вычисленное время зачатия |
| `memory_summary` | JSONB | Структурированная память |
| `memory_summary_version` | INTEGER | Для optimistic lock |
| `communication_style` | JSONB | Стиль общения (адаптируется) |
| `free_trial_cumulative_seconds` | FLOAT | Секунд в триале |
| `paid_balance_seconds` | FLOAT | Оплаченные секунды |
| `subscription_status` | VARCHAR | free/weekly/monthly |
| `subscription_expires_at` | TIMESTAMPTZ | |

### `sessions`
| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | INTEGER PK | |
| `user_id` | INTEGER FK | |
| `is_active` | BOOLEAN | |
| `started_at` | TIMESTAMPTZ | |
| `ended_at` | TIMESTAMPTZ | |
| `end_reason` | ENUM | explicit_phrase / timeout / semantic |
| `total_tokens` | INTEGER | |
| `topic_tags` | JSONB | Для админ-статистики |

### `messages`
| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | INTEGER PK | |
| `session_id` | INTEGER FK | |
| `role` | VARCHAR | user / assistant |
| `content` | TEXT | GIN-индекс |
| `created_at` | TIMESTAMPTZ | |

### `transactions`
| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | INTEGER PK | |
| `user_id` | INTEGER FK | |
| `provider` | VARCHAR | crypto_bot / telegram_stars / fiat |
| `plan_code` | VARCHAR | free/weekly/monthly/consultation |
| `amount` | FLOAT | |
| `currency` | VARCHAR | USDT / STARS / RUB |
| `status` | VARCHAR | |
| `raw_webhook_data` | JSONB | |

### `feedback`
| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | INTEGER PK | |
| `session_id` | INTEGER FK | |
| `user_id` | INTEGER FK | |
| `rating` | INTEGER | 0–10 |
| `comment` | TEXT | |
| `created_at` | TIMESTAMPTZ | |

### `memory_audit_log`
| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | INTEGER PK | |
| `user_id` | INTEGER FK | |
| `diff` | JSONB | История изменений summary |
| `created_at` | TIMESTAMPTZ | |

---

## Структура проекта

```
astrobot/
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── alembic.ini
├── pyproject.toml
├── app/
│   ├── main.py
│   ├── config.py
│   ├── di.py
│   ├── domain/
│   │   ├── entities/        # User, Session, AstroMatrix, Plan...
│   │   └── interfaces/      # AstroModelProvider, LLMProvider, PaymentProvider...
│   ├── services/            # OnboardingService, ChatService, MemoryService...
│   ├── infra/
│   │   ├── db/              # models, session, repositories
│   │   ├── crypto/          # aes_cipher
│   │   ├── geo/             # nominatim_client
│   │   ├── astro_model/     # prompt_engineered_model, ephemeris_model
│   │   ├── llm/             # anthropic_provider, whisper_client
│   │   ├── payments/        # crypto_bot, telegram_stars, fiat
│   │   ├── rate_limit/      # redis_rate_limiter
│   │   └── notify/          # telegram_broadcast
│   ├── bot/                 # fsm, handlers, middlewares, keyboards
│   └── admin/               # routers, auth
├── worker/
│   ├── celery_app.py
│   └── tasks/               # memory_tasks, session_tasks, payment_tasks
├── beat/
│   └── schedule.py
├── alembic/
│   └── versions/
└── tests/
    ├── unit/                # тесты services с моками интерфейсов
    └── integration/         # тесты infra с testcontainers
```

---

## Запуск

### Требования
- Docker + Docker Compose
- Python 3.12 (для локальной разработки)

### Переменные окружения (`.env`)
```
TELEGRAM_BOT_TOKEN=
ANTHROPIC_API_KEY=
OPENAI_API_KEY=              # для Whisper
DATABASE_URL=postgresql://astrobot:...@postgres:5432/astrobot
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
AES_ENCRYPTION_KEY=          # 256-bit key для AES-256-GCM
CRYPTO_BOT_TOKEN=
SECRET_KEY=                  # для Admin API auth
LOG_LEVEL=info
```

### Запуск через Docker Compose
```bash
docker compose up -d
```

### Локальная разработка
```bash
docker compose up postgres redis -d
cp .env.example .env
# отредактировать .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## План реализации (Roadmap)

**PHASE 1** — Скелет проекта и Docker
- [ ] Структура директорий, docker-compose.yml, Dockerfile, requirements.txt, .env.example

**PHASE 2** — БД, безопасность, интерфейсы
- [ ] SQLAlchemy-модели, AES-256 шифрование, Alembic-миграции, ABC-интерфейсы

**PHASE 3** — Бот и FSM (Aiogram 3)
- [ ] Онбординг, геокодинг, генерация conception_time, Whisper

**PHASE 4** — LLM-движок, память, Celery
- [ ] LLMProvider, суммаризация, conflict resolution, SessionLifecycleService

**PHASE 5** — Лимиты, тарифы, платежи, Admin API
- [ ] Redis-лимиты, тарифные планы, CryptoBot, Admin API

---

## Лицензия

Проект разрабатывается как развлекательный/спиритуальный сервис. Не является медицинской, психологической или финансовой консультацией.

---

## Ссылки
- **Telegram Bot API**: https://core.telegram.org/bots/api
- **Aiogram 3**: https://docs.aiogram.dev/
- **Anthropic API**: https://docs.anthropic.com/
- **Crypto Bot API**: https://help.cryptobot.bot/

---

*Последнее обновление: 04.07.2026 — Initial scaffold*
