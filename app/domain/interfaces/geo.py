from abc import ABC, abstractmethod

from app.domain.entities.astro import GeoPoint


class GeoProvider(ABC):
    """Интерфейс геокодинга: место → координаты + таймзона (Geocoding interface)."""

    @abstractmethod
    async def geocode(self, place: str) -> GeoPoint:
        """Преобразовать название места в GeoPoint (Geocode place string to coordinates)."""
        ...
