# Архитектура проекта (Project Architecture)

> Где размещать код? Как организован проект? Читай перед созданием новых файлов.

## Текущий стек (Current stack)

- **Backend:** Python 3.12, FastAPI, Aiogram 3
- **БД:** PostgreSQL 16 + SQLAlchemy 2.0 (async) + Alembic
- **Очереди:** Celery + Redis (broker/backend)
- **Кэш/FSM:** Redis
- **LLM:** Anthropic API, Whisper API (голос)
- **Платежи:** CryptoBot API, Telegram Stars
- **Инфраструктура:** Docker Compose (5 контейнеров)

## Чистая архитектура (Clean Architecture) — обязательна

Проект строится по Clean Architecture в 4 слоя. Направление зависимостей — **только внутрь**, никогда наружу и никогда «по диагонали» через слой.

```
┌─────────────────────────────────────────────────────────┐
│ PRESENTATION  (aiogram-хендлеры, FastAPI admin-роуты)    │  знает про Application
│   bot/handlers/*, admin/routers/*                        │
├─────────────────────────────────────────────────────────┤
│ APPLICATION   (use-case сервисы, оркестрация)            │  знает про Domain
│   services/*  (OnboardingService, ChatService, ...)      │
├─────────────────────────────────────────────────────────┤
│ DOMAIN        (интерфейсы/контракты, чистые сущности)    │  ни от кого не знает
│   domain/interfaces/*, domain/entities/*                 │
├─────────────────────────────────────────────────────────┤
│ INFRASTRUCTURE (реализации: Postgres, Redis, LLM API,    │  реализует Domain-интерфейсы
│   Telegram, платёжные провайдеры)                        │
│   infra/db/*, infra/llm/*, infra/payments/*, infra/geo/* │
└─────────────────────────────────────────────────────────┘
```

### Жёсткие правила

1. `domain/` не импортирует НИЧЕГО из `infra/`, `services/`, `bot/`, `admin/`. Только stdlib, pydantic, typing.
2. `services/` импортирует только интерфейсы из `domain/interfaces/`, никогда конкретные классы из `infra/` напрямую. Конкретная реализация подставляется через DI (`app/di.py`).
3. `bot/handlers/*` НЕ содержит бизнес-логики — только: принять апдейт → вызвать `services/*` → отформатировать ответ. Если в хендлере больше 15-20 строк — сигнал утечки.
4. `infra/*` не знает о существовании других `infra/*` модулей. Общение между инфра-модулями — только через `services/`.
5. Celery-таски (`workers/tasks/*`) — тонкие обёртки, вызывающие `services/*`. Бизнес-логика суммаризации/аудита памяти живёт в сервисах, не в тасках.

### Правило для неопределённости

«Если это решение о том, ЧТО делать — это Application (services/); если решение о том, КАК технически это сделать (SQL, HTTP-запрос к LLM, вызов Telegram API) — это Infrastructure (infra/).»

## Dependency Injection (без магии, вручную)

Один файл `app/di.py`, который один раз собирает граф объектов при старте процесса и раздаёт их через aiogram middleware / FastAPI `Depends`.

```python
@dataclass
class Container:
    user_repo: UserRepository
    llm_provider: LLMProvider
    astro_model: AstroModelProvider
    rate_limiter: RateLimiter
    payment_provider: PaymentProvider
    chat_service: ChatService
    onboarding_service: OnboardingService
    billing_service: BillingService

def build_container(settings: Settings) -> Container:
    # ... создание всех реализаций и сервисов ...
```

`Container` создаётся ровно один раз при старте в `main.py`. Никогда не создавать новые экземпляры внутри хендлера или таска.

## Структура репозитория

```
astrobot/
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── alembic.ini
├── pyproject.toml
├── app/
│   ├── main.py
│   ├── config.py                 # Settings (pydantic-settings)
│   ├── di.py                     # Container + build_container
│   ├── domain/
│   │   ├── entities/             # User, ChatSession, AstroMatrix, Plan, Invoice...
│   │   └── interfaces/           # AstroModelProvider, LLMProvider, PaymentProvider...
│   ├── services/                 # OnboardingService, ChatService, SessionLifecycleService...
│   ├── infra/
│   │   ├── db/                   # models, session, repositories
│   │   ├── crypto/               # AES-256-GCM cipher
│   │   ├── geo/                  # Nominatim client
│   │   ├── astro_model/          # PromptEngineeredAstroModel, EphemerisBasedAstroModel
│   │   ├── llm/                  # AnthropicLLMProvider, WhisperClient
│   │   ├── payments/             # CryptoBotProvider, TelegramStarsProvider, FiatProvider
│   │   ├── rate_limit/           # RedisRateLimiter
│   │   └── notify/               # TelegramBroadcast
│   ├── bot/
│   │   ├── fsm/                  # OnboardingStates (aiogram StatesGroup)
│   │   ├── handlers/             # onboarding, chat, billing, feedback
│   │   ├── middlewares/          # DI middleware, rate limit middleware
│   │   └── keyboards.py
│   └── admin/
│       ├── routers/              # stats, users, broadcast
│       └── auth.py
├── worker/
│   ├── celery_app.py
│   └── tasks/                    # memory_tasks, session_tasks, payment_tasks
├── beat/
│   └── schedule.py
├── alembic/
│   └── versions/
└── tests/
    ├── unit/                     # мокаем domain/interfaces/*
    └── integration/              # testcontainers: postgres + redis
```

## Потоки данных (Data flow)

### Онбординг
```
User → /start → bot/handlers/onboarding.py
  → onboarding_service.start(tg_id) → создаёт User со status=ONBOARDING
  → FSM: ASK_BIRTH_DATE → ASK_BIRTH_PLACE → ASK_BIRTH_TIME (опционально)
       → [если время неизвестно] ASK_PARENTS_DATES → ASK_GRANDPARENTS_DATES
  → onboarding_service.finalize(user_id, collected_data)
    → geo_client.geocode(place) → GeoPoint
    → derive_conception_time(collected_data) → datetime (детерминированный seed)
    → astro_model.build_natal_matrix(conception_dt, geo) → AstroMatrix
    → User.status = ACTIVE
```

### Обычное сообщение
```
User message → bot/handlers/chat.py
  → rate_limit_middleware: check_and_increment
  → chat_service.handle_message(user_id, text)
    → repo: сохранить raw message (role=user)
    → system_prompt = render(persona_template, memory_summary, astro_matrix)
    → llm_provider.generate_reply(system_prompt, history, text)
    → сохранить raw message (role=assistant)
    → инкремент talk_seconds
  → session_lifecycle_service.on_message_processed(session_id)
```

### Платежи
```
Webhook (CryptoBot/Telegram Stars) → FastAPI endpoint → 200 OK immediately
  → Celery task: payment_tasks.process_webhook.delay(raw_body)
    → payment_provider.verify_webhook(raw_body, headers)
    → billing_service.apply_payment(result)
      → UNIQUE(provider_transaction_id) — идемпотентность
```

## Важные ограничения

- **Stateless app** — весь state в Postgres/Redis, чтобы можно было поднять несколько реплик.
- **PII-безопасность** — `encrypted_birth_data` никогда в логах/тасках (только `user_id`).
- **Celery tasks не имеют доступа к Telegram API** — только через outbox-таблицу или прямой вызов Bot из `app`.

---

*Последнее обновление: 04.07.2026*
