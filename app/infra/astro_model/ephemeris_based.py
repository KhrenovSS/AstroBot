from datetime import datetime

from app.domain.entities.astro import AstroMatrix, GeoPoint
from app.domain.interfaces.astro_model import AstroModelProvider


class EphemerisBasedAstroModel(AstroModelProvider):
    """Заглушка: будущая реализация через swisseph (Stub: future swisseph implementation)."""

    async def build_natal_matrix(
        self, conception_dt: datetime, geo: GeoPoint
    ) -> AstroMatrix:
        raise NotImplementedError("EphemerisBasedAstroModel is not implemented yet")
