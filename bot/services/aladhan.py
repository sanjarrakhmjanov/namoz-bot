from __future__ import annotations

import logging
from datetime import date
from typing import Any

import aiohttp

from bot.services.cache import AsyncTTLCache


logger = logging.getLogger(__name__)


METHODS = {
    1: "University of Islamic Sciences, Karachi",
    2: "Islamic Society of North America",
    3: "Muslim World League",
    4: "Umm Al-Qura University, Makkah",
    5: "Egyptian General Authority of Survey",
    7: "Institute of Geophysics, University of Tehran",
    8: "Gulf Region",
    9: "Kuwait",
    10: "Qatar",
    11: "Majlis Ugama Islam Singapura, Singapore",
    12: "Union Organization islamic de France",
    13: "Diyanet İşleri Başkanlığı, Turkey",
    14: "Spiritual Administration of Muslims of Russia",
}


class AladhanError(RuntimeError):
    pass


class AladhanClient:
    def __init__(self, cache: AsyncTTLCache, timeout: int = 10) -> None:
        self._cache = cache
        self._timeout = timeout
        self._base_url = "https://api.aladhan.com/v1"

    async def _get_json(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        try:
            timeout = aiohttp.ClientTimeout(total=self._timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error("Aladhan error %s: %s", resp.status, text)
                        raise AladhanError("Aladhan API error")
                    return await resp.json()
        except aiohttp.ClientError as exc:
            logger.exception("Aladhan request failed")
            raise AladhanError("Aladhan API unavailable") from exc

    async def get_prayer_times_by_city(
        self, city: str, country: str, method: int, target_date: date
    ) -> dict[str, Any]:
        cache_key = f"city:{city}:{country}:{method}:{target_date.isoformat()}"
        cached = await self._cache.get(cache_key)
        if cached:
            return cached
        params = {
            "city": city,
            "country": country,
            "method": method,
            "date": target_date.strftime("%d-%m-%Y"),
        }
        data = await self._get_json("/timingsByCity", params)
        await self._cache.set(cache_key, data)
        return data

    async def get_prayer_times_by_coords(
        self, lat: float, lon: float, method: int, target_date: date
    ) -> dict[str, Any]:
        cache_key = f"coords:{lat:.4f}:{lon:.4f}:{method}:{target_date.isoformat()}"
        cached = await self._cache.get(cache_key)
        if cached:
            return cached
        params = {
            "latitude": lat,
            "longitude": lon,
            "method": method,
            "date": target_date.strftime("%d-%m-%Y"),
        }
        data = await self._get_json("/timings", params)
        await self._cache.set(cache_key, data)
        return data

    async def get_hijri_date(self, target_date: date) -> dict[str, Any]:
        cache_key = f"hijri:{target_date.isoformat()}"
        cached = await self._cache.get(cache_key)
        if cached:
            return cached
        params = {"date": target_date.strftime("%d-%m-%Y")}
        data = await self._get_json("/gToH", params)
        await self._cache.set(cache_key, data)
        return data

    async def get_calendar_by_city(
        self, city: str, country: str, method: int, month: int, year: int
    ) -> dict[str, Any]:
        cache_key = f"calendar:city:{city}:{country}:{method}:{month}:{year}"
        cached = await self._cache.get(cache_key)
        if cached:
            return cached
        params = {
            "city": city,
            "country": country,
            "method": method,
            "month": month,
            "year": year,
        }
        data = await self._get_json("/calendarByCity", params)
        await self._cache.set(cache_key, data)
        return data

    async def get_calendar_by_coords(
        self, lat: float, lon: float, method: int, month: int, year: int
    ) -> dict[str, Any]:
        cache_key = f"calendar:coords:{lat:.4f}:{lon:.4f}:{method}:{month}:{year}"
        cached = await self._cache.get(cache_key)
        if cached:
            return cached
        params = {
            "latitude": lat,
            "longitude": lon,
            "method": method,
            "month": month,
            "year": year,
        }
        data = await self._get_json("/calendar", params)
        await self._cache.set(cache_key, data)
        return data

    @staticmethod
    def method_name(method: int) -> str:
        return METHODS.get(method, "Unknown")
