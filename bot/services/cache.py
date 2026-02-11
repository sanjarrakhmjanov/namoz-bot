from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheItem:
    value: Any
    expires_at: float


class AsyncTTLCache:
    def __init__(self, default_ttl: int = 86400) -> None:
        self._default_ttl = default_ttl
        self._data: dict[str, CacheItem] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            item = self._data.get(key)
            if not item:
                return None
            if item.expires_at < time.time():
                self._data.pop(key, None)
                return None
            return item.value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        async with self._lock:
            expires_at = time.time() + (ttl or self._default_ttl)
            self._data[key] = CacheItem(value=value, expires_at=expires_at)
