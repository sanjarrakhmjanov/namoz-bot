from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from bot.utils.geo import haversine_km


logger = logging.getLogger(__name__)


class OverpassError(RuntimeError):
    pass


class OverpassClient:
    def __init__(self, timeout: int = 20) -> None:
        self._timeout = timeout
        self._urls = [
            "https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
            "https://overpass.nchc.org.tw/api/interpreter",
            "https://overpass.osm.ch/api/interpreter",
            "https://overpass.openstreetmap.ru/api/interpreter",
        ]

    async def find_mosques(
        self, lat: float, lon: float, radius_km: int, limit: int
    ) -> list[dict[str, Any]]:
        payload = await self._fetch_with_fallback(lat, lon, radius_km)

        items = []
        for element in payload.get("elements", []):
            elem_lat = element.get("lat") or (element.get("center") or {}).get("lat")
            elem_lon = element.get("lon") or (element.get("center") or {}).get("lon")
            if elem_lat is None or elem_lon is None:
                continue
            tags = element.get("tags", {})
            name = tags.get("name") or "Masjid"
            addr = self._format_address(tags)
            distance = haversine_km(lat, lon, elem_lat, elem_lon)
            items.append(
                {
                    "name": name,
                    "distance_km": distance,
                    "lat": elem_lat,
                    "lon": elem_lon,
                    "address": addr,
                }
            )

        items.sort(key=lambda x: x["distance_km"])
        return items[:limit]

    async def _fetch_with_fallback(self, lat: float, lon: float, radius_km: int) -> dict[str, Any]:
        radius_options = [radius_km, max(1, radius_km // 2), max(1, radius_km // 3)]
        last_error: Exception | None = None
        timeout = aiohttp.ClientTimeout(total=self._timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for radius in radius_options:
                query = self._build_query(lat, lon, radius)
                for url in self._urls:
                    for attempt in range(2):
                        try:
                            async with session.post(url, data={"data": query}) as resp:
                                if resp.status != 200:
                                    text = await resp.text()
                                    logger.error("Overpass error %s: %s", resp.status, text)
                                    last_error = OverpassError("Overpass API error")
                                    if resp.status in (429, 504, 502, 503):
                                        await asyncio.sleep(1 + attempt)
                                        continue
                                    raise last_error
                                return await resp.json()
                        except aiohttp.ClientError as exc:
                            logger.exception("Overpass request failed")
                            last_error = exc
                            await asyncio.sleep(1 + attempt)
                            continue
        raise OverpassError("Overpass API unavailable") from last_error

    @staticmethod
    def _build_query(lat: float, lon: float, radius_km: int) -> str:
        radius_m = radius_km * 1000
        return (
            "[out:json][timeout:25];"
            "(node['amenity'='place_of_worship']['religion'='muslim'](around:{r},{lat},{lon});"
            "way['amenity'='place_of_worship']['religion'='muslim'](around:{r},{lat},{lon});"
            "relation['amenity'='place_of_worship']['religion'='muslim'](around:{r},{lat},{lon}););"
            "out center;"
        ).format(r=radius_m, lat=lat, lon=lon)

    @staticmethod
    def _format_address(tags: dict[str, Any]) -> str | None:
        street = tags.get("addr:street")
        house = tags.get("addr:housenumber")
        city = tags.get("addr:city")
        parts = [p for p in [street, house, city] if p]
        if not parts:
            return None
        return ", ".join(parts)
