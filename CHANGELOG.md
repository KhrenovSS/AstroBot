# Changelog — AstroBot

All notable changes to this project are tracked here.

## [04.07.2026] — Initial scaffold (Phase 1)

### Added
- **Документация проекта**: README.md, AGENTS.md, CHANGELOG.md, TECH_DEBT.md, PHASE_1_PLAN.md
- **docs/**: ARCHITECTURE.md, CODE_GUIDELINES.md, API_ROUTES_GUIDE.md, ERROR_HANDLING.md, NAMING_CONVENTIONS.md, TESTING.md, LOGGING.md, CHECKLIST_API.md, CHECKLIST_FEATURE.md, CHECKLIST_MIGRATION.md, DEVELOPMENT_GUIDELINES.md, ASTRO_MODEL_DESIGN.md
- **Концепция**: Clean Architecture (4 слоя), модульный монолит с чёткими границами через ABC-интерфейсы
- **Архитектура зафиксирована**: 5 Docker-контейнеров (app, worker, beat, postgres, redis), ручной DI в `app/di.py`, трёхсигнальная модель завершения сессии
- **Интерфейсы**: AstroModelProvider, LLMProvider, PaymentProvider, UserRepository, RateLimiter — с точными сигнатурами

---

*Версия: 0.1.0*
