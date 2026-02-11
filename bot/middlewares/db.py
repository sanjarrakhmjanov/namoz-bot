from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


logger = logging.getLogger(__name__)


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, sessionmaker: async_sessionmaker):
        self._sessionmaker = sessionmaker

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        async with self._sessionmaker() as session:  # type: AsyncSession
            data["db"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                logger.exception("DB session rolled back due to error")
                raise
