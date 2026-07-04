from datetime import datetime

from pydantic import BaseModel


class GeoPoint(BaseModel):
    """Географические координаты (Geographic coordinates)."""
    lat: float
    lon: float
    timezone: str


class PlanetPosition(BaseModel):
    """Позиция планеты в натальной карте (Planet position in natal chart)."""
    name: str
    sign: str
    degree: float
    house: int
    is_retrograde: bool = False


class Aspect(BaseModel):
    """Аспект между планетами (Planetary aspect)."""
    planet1: str
    planet2: str
    aspect_type: str
    orb: float


class AstroMatrix(BaseModel):
    """Структурированные данные астрологической модели (Structured astrological model data)."""
    conception_dt: datetime
    geo: GeoPoint
    sun_sign: str
    moon_sign: str
    rising_sign: str
    planets: list[PlanetPosition]
    houses: dict[int, str]
    aspects: list[Aspect]
    dominant_elements: dict[str, float]
    dominant_qualities: dict[str, float]
    lunar_day: int
    season_power: float
    additional: dict = {}
