# AstroBot — Предиктивный астролог в Telegram

Telegram-бот в роли «предиктивного астролога». Позиционирование: «программист-математик» создал математическую модель предсказаний на основе **момента зачатия** (а не даты/времени/места рождения, как в классической астрологии).

---

## Реализованные возможности

- **🧬 Онбординг и геокодинг** — сбор даты, места, времени рождения; геокодинг → координаты + таймзона (Nominatim/OpenStreetMap)
- **🔮 Псевдослучайное время зачатия** — детерминированная генерация (SHA-256 seed → offset 266–287 дней до рождения)
- **🤖 LLM-генерация ответов** — персонализированные предсказания на основе `AstroMatrix` + `memory_summary`; локальный Ollama (qwen2.5:0.5b), без внешних API-ключей
- **🧠 Память пользователя** — сырая история сообщений, Celery-суммаризация, конфликт-резолюция (optimistic lock)
- **⏱️ Определение конца сессии** — три сигнала: явные стоп-фразы, таймаут, семантическая LLM-проверка (по счётчику)
- **🔐 Шифрование ПДн** — AES-256-GCM

### Планируется (Sprint 5)
- Голосовые сообщения (Whisper API)
- Лимиты бесплатного триала (Redis-счётчики: сообщений/день, сообщений/неделю, суммарное время)
- Монетизация (CryptoBot USDT, Telegram Stars, Fiat RUB)
- Admin API (статистика, управление пользователями, рассылка)
- Обратная связь (оценка сессии 0–10, адаптация communication_style)

---

## Архитектура

### Стек
- **Backend**: Python 3.12, FastAPI, Aiogram 3, SQLAlchemy 2.0 (async)
- **Очереди**: Celery + Redis (broker)
- **БД**: PostgreSQL 16, Redis 7 (FSM, кэш, счётчики, брокер)
- **LLM**: Ollama (локально, модель `qwen2.5:0.5b`) — **без внешних API-ключей**
- **Платежи**: не подключены (Sprint 5)
- **Инфраструктура**: Docker Compose (5 контейнеров) или локальный запуск (Ubuntu 24.04)

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

### Контейнеры (Docker) / Сервисы (локально)

| Сервис | Назначение |
|--------|-----------|
| `astrobot-app` | FastAPI + Aiogram 3 polling, Admin API, FSM, оркестрация LLM |
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
| `status` | ENUM(ONBOARDING, ACTIVE, BLOCKED) | Статус пользователя |
| `encrypted_birth_data` | TEXT | AES-256 зашифрованные ПДн |
| `memory_summary` | TEXT | Суммаризированная память |
| `memory_summary_version` | INTEGER | Для optimistic lock |
| `talk_seconds` | INTEGER | Секунд в триале |
| `daily_messages` | INTEGER | Сообщений за день |
| `weekly_messages` | INTEGER | Сообщений за неделю |
| `last_daily_reset` | TIMESTAMPTZ | Сброс дневного лимита |
| `last_weekly_reset` | TIMESTAMPTZ | Сброс недельного лимита |
| `tariff` | ENUM(FREE, PREMIUM_MONTHLY, PREMIUM_YEARLY) | Тариф |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### `chat_sessions`
| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | INTEGER PK | |
| `user_id` | INTEGER FK → users.id | |
| `status` | ENUM(ACTIVE, ENDED_EXPLICIT, ENDED_SEMANTIC, ENDED_TIMEOUT) | |
| `messages_since_last_semantic_check` | INTEGER | Счётчик сообщений для LLM-проверки |
| `created_at` | TIMESTAMPTZ | |
| `ended_at` | TIMESTAMPTZ | |
| `last_message_at` | TIMESTAMPTZ | |

### `memory_summaries`
| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | INTEGER PK | |
| `user_id` | INTEGER FK → users.id (UNIQUE) | |
| `summary` | TEXT | Суммаризированная память |
| `version` | INTEGER | Для optimistic lock |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

### `transactions`
| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | INTEGER PK | |
| `user_id` | INTEGER FK → users.id | |
| `provider` | VARCHAR(30) | crypto_bot / telegram_stars / fiat |
| `provider_transaction_id` | VARCHAR(255) UNIQUE | Идемпотентность |
| `plan` | VARCHAR(30) | free/weekly/monthly/consultation |
| `amount` | NUMERIC(12,2) | |
| `currency` | VARCHAR(10) | USDT / STARS / RUB |
| `status` | ENUM(PENDING, COMPLETED, FAILED) | |
| `created_at` | TIMESTAMPTZ | |
| `updated_at` | TIMESTAMPTZ | |

---

## Структура проекта

```
astrobot/
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .env                        # НЕ КОММИТИТСЯ
├── alembic.ini
├── pyproject.toml
├── CHANGELOG.md
├── AGENTS.md
├── start_bot.sh                # Скрипт локального запуска
├── app/
│   ├── main.py                 # FastAPI + lifespan + Aiogram polling
│   ├── config.py               # Settings (pydantic-settings)
│   ├── di.py                   # Container dataclass, build_container()
│   ├── exceptions.py           # 11 типизированных исключений
│   ├── utils/
│   │   └── logger.py           # Корневой логгер astrobot
│   ├── domain/
│   │   ├── entities/           # User, ChatSession, MemorySummary, Transaction, AstroMatrix, BirthData
│   │   └── interfaces/         # AstroModelProvider, LLMProvider, GeoProvider, PaymentProvider, RateLimiter, 4 репозитория
│   ├── services/               # ConceptionService, OnboardingService, ChatService, SessionService, MemoryResolver
│   ├── infra/
│   │   ├── db/
│   │   │   ├── models.py       # SQLAlchemy модели (User, ChatSession, MemorySummary, Transaction)
│   │   │   └── repositories.py # SQLAlchemy реализации репозиториев
│   │   ├── crypto/
│   │   │   └── aes_cipher.py   # AES-256-GCM шифрование
│   │   ├── geo/
│   │   │   └── nominatim_client.py  # Геокодинг (OpenStreetMap)
│   │   ├── astro_model/
│   │   │   ├── prompt_engineered.py # MVP AstroModelProvider
│   │   │   └── ephemeris_based.py   # Заглушка (будущая swisseph)
│   │   ├── llm/
│   │   │   ├── ollama_client.py     # Активная реализация LLMProvider
│   │   │   ├── anthropic_client.py  # Не используется (история)
│   │   │   └── groq_client.py       # Не используется (история)
│   │   ├── payments/           # Пусто (Sprint 5)
│   │   ├── rate_limit/         # Пусто (Sprint 5)
│   │   └── notify/             # Пусто (Sprint 5)
│   ├── bot/
│   │   ├── __init__.py         # setup_dispatcher()
│   │   ├── fsm/                # OnboardingStates
│   │   ├── handlers/           # onboarding.py, chat.py
│   │   └── middlewares/        # DIMiddleware
│   └── admin/                  # Пусто (Sprint 5)
├── worker/
│   ├── celery_app.py
│   └── tasks/                  # memory_tasks, session_tasks
├── beat/
│   └── schedule.py
├── alembic/
│   ├── env.py
│   └── versions/               # 0001_initial_schema.py
└── tests/
    ├── conftest.py
    ├── unit/                   # 8 файлов, 52 теста
    └── integration/            # Пусто
```

---

## Запуск

### Требования
- Python 3.12
- PostgreSQL 16 + Redis 7 (локально или через Docker)
- Ollama (локально) с моделью `qwen2.5:0.5b`

### Переменные окружения (`.env`)

Полный список — в `.env.example`:
```
TELEGRAM_BOT_TOKEN=
OLLAMA_API_BASE=http://localhost:11434
OLLAMA_MODEL=qwen2.5:0.5b
OLLAMA_TIMEOUT=120
DATABASE_URL=postgresql+asyncpg://astrobot:astrobot_password@localhost:5432/astrobot
DATABASE_URL_SYNC=postgresql://astrobot:astrobot_password@localhost:5432/astrobot
REDIS_URL=redis://localhost:6379/0
AES_ENCRYPTION_KEY=
NOMINATIM_URL=https://nominatim.openstreetmap.org
LOG_LEVEL=info
```

### Локальный запуск (Ubuntu 24.04)

```bash
# 1. PostgreSQL и Redis
sudo systemctl start postgresql redis-server

# 2. Ollama (если не запущен)
ollama serve &>/tmp/ollama_serve.log &

# 3. Скопировать .env.example → .env и заполнить
cp .env.example .env

# 4. Накатить миграции
alembic upgrade head

# 5. Запустить бота
./start_bot.sh
```

### Запуск через Docker Compose

```bash
docker compose up -d
```

---

## План реализации (Sprint roadmap)

| Sprint | Статус | Описание |
|--------|--------|----------|
| **1** — Скелет + Docker | ✅ **Завершён** | Структура, docker-compose, FastAPI, DI, Celery, Beat, Alembic, тесты |
| **2** — БД + AES + интерфейсы | ✅ **Завершён** | SQLAlchemy, AES-256-GCM, ABC-интерфейсы, репозитории, 27 тестов |
| **3** — Онбординг + FSM | ✅ **Завершён** | Aiogram FSM, геокодинг (Nominatim), conception_time, 9 тестов |
| **4** — LLM + память + сессии | ✅ **Завершён** | Ollama, суммаризация, сессия lifecycle, Celery tasks, 52 теста |
| **5** — Лимиты + платежи + Admin | ⏳ **Ожидает** | Redis-лимиты, тарифы, CryptoBot, Telegram Stars, Admin API |

---

## Лицензия

Проект разрабатывается как развлекательный/спиритуальный сервис. Не является медицинской, психологической или финансовой консультацией.

---

## Ссылки
- **Telegram Bot API**: https://core.telegram.org/bots/api
- **Aiogram 3**: https://docs.aiogram.dev/
- **Ollama**: https://ollama.ai/
- **Crypto Bot API**: https://help.cryptobot.bot/

---

*Последнее обновление: 05.07.2026 — Sprint 4 hotfix + devops*
