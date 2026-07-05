from datetime import datetime, timezone

import pytest

from app.domain.entities.astro import GeoPoint
from app.domain.interfaces.llm import LLMProvider
from app.infra.astro_model.prompt_engineered import PromptEngineeredAstroModel


class FakeLLMForAstro(LLMProvider):
    """Fake LLM для тестов астро-модели (Fake LLM for astro model tests)."""

    def __init__(self):
        self.last_system_prompt = None
        self.last_message = None

    async def generate_reply(self, system_prompt: str, history: list[dict], user_message: str) -> str:
        self.last_system_prompt = system_prompt
        self.last_message = user_message
        return (
            '{"sun_sign": "Овен", "moon_sign": "Рак", "rising_sign": "Лев", '
            '"planets": [{"name": "Солнце", "sign": "Овен", "degree": 15.5, "house": 1, "is_retrograde": false}], '
            '"houses": {"1": "Овен"}, '
            '"aspects": [{"planet1": "Солнце", "planet2": "Луна", "aspect_type": "трин", "orb": 1.5}], '
            '"dominant_elements": {"огонь": 0.3, "земля": 0.4}, '
            '"dominant_qualities": {"кардинальный": 0.5}, '
            '"lunar_day": 12, "season_power": 0.7}'
        )

    async def summarize(self, messages: list[dict]) -> dict:
        return {"summary": "test"}

    async def classify_session_end(self, last_messages: list[dict]) -> bool:
        return False


class TestPromptEngineeredAstroModel:
    """Тесты PromptEngineeredAstroModel (PromptEngineeredAstroModel tests)."""

    @pytest.fixture
    def llm(self):
        return FakeLLMForAstro()

    @pytest.fixture
    def model(self, llm):
        return PromptEngineeredAstroModel(llm_provider=llm)

    async def test_build_natal_matrix_returns_astromatrix(self, model, llm):
        """Построение натальной матрицы возвращает AstroMatrix (Build returns AstroMatrix)."""
        dt = datetime(2020, 6, 15, 12, 0, tzinfo=timezone.utc)
        geo = GeoPoint(lat=55.75, lon=37.62, timezone="Europe/Moscow")

        matrix = await model.build_natal_matrix(dt, geo)
        assert matrix.sun_sign == "Овен"
        assert matrix.moon_sign == "Рак"
        assert matrix.rising_sign == "Лев"
        assert len(matrix.planets) == 1
        assert matrix.planets[0].name == "Солнце"
        assert matrix.lunar_day == 12
        assert matrix.season_power == 0.7

    async def test_build_natal_matrix_passes_correct_prompt(self, model, llm):
        """Построение матрицы передаёт корректный prompt (Build passes correct prompt)."""
        dt = datetime(2020, 6, 15, 12, 0, tzinfo=timezone.utc)
        geo = GeoPoint(lat=55.75, lon=37.62, timezone="Europe/Moscow")

        await model.build_natal_matrix(dt, geo)
        assert llm.last_system_prompt is not None
        assert "ТОЛЬКО JSON" in llm.last_system_prompt
        assert "2020-06-15" in llm.last_message
        assert "55.75" in llm.last_message

    async def test_build_natal_matrix_invalid_json_raises(self, llm):
        """Некорректный JSON от LLM вызывает ошибку (Invalid JSON raises error)."""
        async def fake_reply(system_prompt, history, user_message):
            return "not valid json"
        llm.generate_reply = fake_reply

        model = PromptEngineeredAstroModel(llm_provider=llm)
        from app.exceptions import LLMProviderError

        with pytest.raises(LLMProviderError):
            dt = datetime(2020, 6, 15, 12, 0, tzinfo=timezone.utc)
            geo = GeoPoint(lat=55.75, lon=37.62, timezone="Europe/Moscow")
            await model.build_natal_matrix(dt, geo)
