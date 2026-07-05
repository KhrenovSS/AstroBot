import json
import logging
from datetime import datetime

from app.domain.entities.astro import AstroMatrix, GeoPoint, PlanetPosition, Aspect
from app.domain.interfaces.astro_model import AstroModelProvider
from app.domain.interfaces.llm import LLMProvider
from app.exceptions import LLMProviderError

logger = logging.getLogger("astrobot")


class PromptEngineeredAstroModel(AstroModelProvider):
    """MVP-реализация AstroModelProvider: через LLM генерирует псевдонаучные
    астрологические данные на основе времени зачатия и гео.
    (MVP implementation: generates pseudo-scientific astrological data via LLM.)"""

    SYSTEM_PROMPT = (
        "Ты — расчётный движок астрологической модели. "
        "Возвращай ТОЛЬКО JSON без пояснений. "
        "Никогда не добавляй текст до или после JSON."
    )

    def __init__(self, llm_provider: LLMProvider):
        self._llm = llm_provider

    async def build_natal_matrix(
        self, conception_dt: datetime, geo: GeoPoint
    ) -> AstroMatrix:
        """Построить натальную матрицу через LLM (Build natal matrix via LLM)."""
        prompt = self._build_prompt(conception_dt, geo)

        raw = await self._llm.generate_reply(
            system_prompt=self.SYSTEM_PROMPT,
            history=[],
            user_message=prompt,
        )

        try:
            data = json.loads(raw)
            return AstroMatrix(
                conception_dt=conception_dt,
                geo=geo,
                sun_sign=data.get("sun_sign", "Неизвестно"),
                moon_sign=data.get("moon_sign", "Неизвестно"),
                rising_sign=data.get("rising_sign", "Неизвестно"),
                planets=[PlanetPosition(**p) for p in data.get("planets", [])],
                houses={int(k): v for k, v in data.get("houses", {}).items()},
                aspects=[Aspect(**a) for a in data.get("aspects", [])],
                dominant_elements=data.get("dominant_elements", {}),
                dominant_qualities=data.get("dominant_qualities", {}),
                lunar_day=data.get("lunar_day", 1),
                season_power=data.get("season_power", 0.5),
            )
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.error("Failed to parse AstroMatrix from LLM output: %s", raw[:200])
            raise LLMProviderError(f"Failed to parse AstroMatrix: {e}") from e

    def _build_prompt(self, conception_dt: datetime, geo: GeoPoint) -> str:
        """Сформировать prompt для LLM (Build prompt for LLM)."""
        return (
            f"Сгенерируй натальную матрицу для момента зачатия: "
            f"{conception_dt.isoformat()} UTC, "
            f"координаты: {geo.lat}, {geo.lon}, "
            f"таймзона: {geo.timezone}.\n\n"
            f"Верни JSON со следующей структурой:\n"
            f"{{\n"
            f'  "sun_sign": "знак солнца",\n'
            f'  "moon_sign": "знак луны",\n'
            f'  "rising_sign": "асцендент",\n'
            f'  "planets": [{{"name": "Солнце", "sign": "Овен", "degree": 15.5, "house": 1, "is_retrograde": false}}],\n'
            f'  "houses": {{"1": "Овен", "2": "Телец", ...}},\n'
            f'  "aspects": [{{"planet1": "Солнце", "planet2": "Луна", "aspect_type": "трин", "orb": 1.5}}],\n'
            f'  "dominant_elements": {{"огонь": 0.3, "земля": 0.4}},\n'
            f'  "dominant_qualities": {{"кардинальный": 0.5}},\n'
            f'  "lunar_day": 12,\n'
            f'  "season_power": 0.7\n'
            f"}}\n\n"
            f"Заполни все поля правдоподобными значениями."
        )
