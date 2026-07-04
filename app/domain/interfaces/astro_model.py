from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.entities.astro import AstroMatrix, GeoPoint


class AstroModelProvider(ABC):
    """Интерфейс провайдера астрологической модели (Astrological model provider interface)."""

    @abstractmethod
    async def build_natal_matrix(
        self, conception_dt: datetime, geo: GeoPoint
    ) -> AstroMatrix:
        """Возвращает структурированные 'данные модели' (JSON), которые
        далее интерпретирует LLM. Не должен содержать текст ответа."""
        ...
