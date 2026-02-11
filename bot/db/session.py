from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from bot.config import Settings


def get_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)


def get_sessionmaker(engine: AsyncEngine) -> async_sessionmaker:
    return async_sessionmaker(engine, expire_on_commit=False)
