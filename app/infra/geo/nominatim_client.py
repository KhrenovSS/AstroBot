import httpx
from httpx import AsyncClient

from app.config import Settings
from app.domain.entities.astro import GeoPoint
from app.domain.interfaces.geo import GeoProvider
from app.exceptions import GeocodingError


class NominatimClient(GeoProvider):
    """Реализация GeoProvider через Nominatim (OpenStreetMap) API."""

    def __init__(self, settings: Settings):
        self._base_url = settings.nominatim_url.rstrip("/")
        self._user_agent = settings.nominatim_user_agent
        self._timeout = settings.geocoding_timeout

    async def geocode(self, place: str) -> GeoPoint:
        """Геокодировать название места (Geocode a place string to GeoPoint)."""
        url = f"{self._base_url}/search"
        params = {
            "q": place,
            "format": "json",
            "limit": 1,
            "addressdetails": 0,
        }
        headers = {
            "User-Agent": self._user_agent,
        }

        async with AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
            except httpx.TimeoutException:
                raise GeocodingError(place, "Nominatim request timed out")
            except httpx.HTTPStatusError as e:
                raise GeocodingError(place, f"HTTP {e.response.status_code}")
            except httpx.RequestError as e:
                raise GeocodingError(place, str(e))

        results = response.json()
        if not results:
            raise GeocodingError(place, "No results found")

        result = results[0]
        lat = float(result["lat"])
        lon = float(result["lon"])

        # Определение таймзоны по координатам (Timezone lookup via Nominatim reverse)
        tz = await self._resolve_timezone(lat, lon)

        return GeoPoint(lat=lat, lon=lon, timezone=tz)

    async def _resolve_timezone(self, lat: float, lon: float) -> str:
        """Определить часовой пояс по координатам (Resolve timezone from coordinates)."""
        url = f"{self._base_url}/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
        }
        headers = {
            "User-Agent": self._user_agent,
        }

        async with AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
            except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError):
                return "UTC"

        data = response.json()
        tz = data.get("properties", {}).get("timezone", {}).get("name", "UTC")
        return tz if tz else "UTC"
