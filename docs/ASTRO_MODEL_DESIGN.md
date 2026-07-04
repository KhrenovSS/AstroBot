# AstroModelProvider — дизайн модуля предсказаний

> Документ описывает архитектуру модуля астрологических расчётов (AstroModelProvider),
> который является ядром «математической модели» предиктивной астрологии по моменту зачатия.

---

## 1. Концепция

«Математическая модель» — это **не hardcoded алгоритм и не prompt-инжиниринг внутри LLM**.
Это отдельный заменяемый модуль за интерфейсом `AstroModelProvider`, у которого есть чёткий
контракт входа/выхода:

```python
from abc import ABC, abstractmethod
from datetime import datetime
from app.domain.entities.astro import AstroMatrix, GeoPoint


class AstroModelProvider(ABC):
    @abstractmethod
    async def build_natal_matrix(
        self, conception_dt: datetime, geo: GeoPoint
    ) -> AstroMatrix:
        """Возвращает структурированные 'данные модели' (JSON), которые
        далее интерпретирует LLM. Не должен содержать текст ответа."""
        ...
```

**Вход:** дата/время зачатия (UTC) + географические координаты
**Выход:** структурированная `AstroMatrix` (JSON-совместимый объект)
**Потребитель:** `ChatService`, который передаёт `AstroMatrix` в system prompt LLM

---

## 2. Реализации

### MVP: `PromptEngineeredAstroModel`

Генерирует псевдонаучные «астрологические координаты» через LLM-запрос.
Не требует эфемерид или астрономических расчётов.

```python
class PromptEngineeredAstroModel(AstroModelProvider):
    """MVP-реализация: через LLM генерирует структурированные
    псевдонаучные данные на основе времени зачатия и гео."""

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def build_natal_matrix(
        self, conception_dt: datetime, geo: GeoPoint
    ) -> AstroMatrix:
        # Формируем prompt, который просит LLM вернуть JSON с
        # определённой структурой (не текст ответа пользователю)
        prompt = self._build_prompt(conception_dt, geo)
        raw = await self.llm.generate_reply(
            system_prompt="Ты — расчётный движок астрологической модели. "
                          "Возвращай ТОЛЬКО JSON.",
            history=[],
            user_message=prompt,
        )
        return AstroMatrix.model_validate_json(raw)
```

### Future: `EphemerisBasedAstroModel`

Реальный расчёт положений планет через swisseph (или аналог).

```python
class EphemerisBasedAstroModel(AstroModelProvider):
    """Заготовка на будущее: реальный расчёт положений планет
    (swisseph и т.д.). Пока NotImplemented."""
    ...
```

---

## 3. Формат AstroMatrix

```python
# app/domain/entities/astro.py
from pydantic import BaseModel


class GeoPoint(BaseModel):
    lat: float
    lon: float
    timezone: str  # IANA timezone, e.g. "Europe/Moscow"


class PlanetPosition(BaseModel):
    name: str        # "Солнце", "Луна", "Меркурий"...
    sign: str        # "Овен", "Телец"...
    degree: float    # 0.0–360.0
    house: int       # 1–12
    is_retrograde: bool = False


 class Aspect(BaseModel):
    planet1: str
    planet2: str
    aspect_type: str   # "трин", "квадрат", "оппозиция"...
    orb: float         # точность аспекта в градусах


class AstroMatrix(BaseModel):
    """Структурированные данные астрологической модели.
    Выход AstroModelProvider, вход для LLM-промта."""

    conception_dt: datetime
    geo: GeoPoint
    sun_sign: str                # Знак Солнца
    moon_sign: str               # Знак Луны
    rising_sign: str             # Асцендент
    planets: list[PlanetPosition]
    houses: dict[int, str]       # {1: "Овен", 2: "Телец", ...}
    aspects: list[Aspect]
    dominant_elements: dict[str, float]   # {"огонь": 0.3, "земля": 0.4, ...}
    dominant_qualities: dict[str, float]  # {"кардинальный": 0.5, ...}
    lunar_day: int               # Лунный день (1–30)
    season_power: float          # 0.0–1.0 — сила сезона
    additional: dict = {}        # для расширения
```

**Правило:** `AstroMatrix` — это данные, а не текст. Текст ответа пользователю строит
`ChatService` через `LLMProvider`, используя `AstroMatrix` как контекст.

---

## 4. Псевдонаучная терминология (для system prompt LLM)

При генерации `AstroMatrix` через `PromptEngineeredAstroModel` используются термины:

- **Матрица зачатия** — совокупность астрологических факторов на момент зачатия
- **Эфемериды зачатия** — расчётные положения тел
- **Квантовые состояния клеток** — метафора влияния момента зачатия на потенциал
- **Натальная матрица** — выходной JSON-объект

**Важно:** LLM должна быть проинструктирована не давать медицинских, юридических и
финансовых советов; при запросах такого рода — мягко переводить разговор в
развлекательный регистр.

---

## 5. Conception Time — детерминированная генерация

Время зачатия = чистая функция (не LLM!), чтобы результат был воспроизводим:

```python
import hashlib
from datetime import timedelta

def derive_conception_time(
    user_id: int, birth_date: date, parents_dates: dict | None = None
) -> datetime:
    """Детерминированная генерация времени зачатия.

    Алгоритм:
    1. seed = sha256(str(user_id) + serialize(collected_dates))
    2. Псевдослучайное смещение от birth_date - 9 месяцев
       в диапазоне conception_window_days (несколько дней)
    3. Псевдослучайное время суток
    """
    seed = hashlib.sha256(
        f"{user_id}:{birth_date}:{parents_dates}".encode()
    ).digest()
    # ... детерминированный расчёт ...
```

**Важно:** генерация conception_time — без побочных эффектов и без вызова LLM.
LLM подключается только на этапе интерпретации (генерации текста ответа).

---

## 6. План развития

| Этап | Что делаем | Статус |
|------|-----------|--------|
| 0 | Определить `AstroModelProvider` интерфейс | Готово |
| 1 | `PromptEngineeredAstroModel` — MVP через LLM | Phase 4 |
| 2 | `EphemerisBasedAstroModel` — заглушка NotImplemented | Phase 4 |
| 3 | Полноценный расчёт через swisseph | Будущее |

---

*Версия: 1.0 · Дата: 04.07.2026*
