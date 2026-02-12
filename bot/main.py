import asyncio
import os

from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import get_settings
from bot.logging_config import setup_logging
from bot.db.session import get_engine, get_sessionmaker
from bot.middlewares.db import DbSessionMiddleware
from bot.middlewares.i18n import I18nMiddleware
from bot.services.aladhan import AladhanClient
from bot.services.cache import AsyncTTLCache
from bot.services.scheduler import SchedulerService
from bot.utils.i18n import I18n
from bot.handlers import (
    start,
    menu,
    prayer_times,
    location,
    reminders,
    qibla,
    hijri,
    duas,
    tasbeh,
    settings,
    admin,
    mosques,
    ramadan,
    profile,
    errors,
)


async def _start_health_server() -> web.AppRunner | None:
    port_value = os.getenv("PORT")
    if not port_value:
        return None
    app = web.Application()

    async def health(_request: web.Request) -> web.Response:
        return web.Response(text="ok")

    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(port_value))
    await site.start()
    return runner


async def main() -> None:
    app_settings = get_settings()
    setup_logging(app_settings.LOG_LEVEL, app_settings.LOG_FILE)

    bot = Bot(
        token=app_settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Start"),
            BotCommand(command="menu", description="Main menu"),
            BotCommand(command="help", description="Help"),
            BotCommand(command="back", description="Back to menu"),
            BotCommand(command="setcity", description="Set city"),
            BotCommand(command="setlocation", description="Set location"),
            BotCommand(command="today", description="Today prayer times"),
            BotCommand(command="tomorrow", description="Tomorrow prayer times"),
            BotCommand(command="week", description="Weekly prayer times"),
            BotCommand(command="nearest", description="Nearest prayer time"),
            BotCommand(command="mosques", description="Nearby mosques"),
            BotCommand(command="silent", description="Set quiet hours"),
            BotCommand(command="remindertest", description="Test reminder"),
            BotCommand(command="hijri_remind", description="Hijri month reminder"),
            BotCommand(command="ramadan", description="Ramadan mode"),
            BotCommand(command="profile", description="User profile"),
            BotCommand(command="dua", description="Dua search"),
        ]
    )
    dp = Dispatcher(storage=MemoryStorage())

    i18n = I18n("locales")
    engine = get_engine(app_settings)
    sessionmaker = get_sessionmaker(engine)
    cache = AsyncTTLCache(default_ttl=app_settings.CACHE_TTL_SEC)
    aladhan = AladhanClient(cache=cache, timeout=app_settings.API_TIMEOUT_SEC)
    scheduler_service = SchedulerService(
        bot=bot,
        settings=app_settings,
        aladhan=aladhan,
        i18n=i18n,
        sessionmaker=sessionmaker,
    )

    dp["scheduler_service"] = scheduler_service
    dp["aladhan"] = aladhan
    dp["settings"] = app_settings
    dp["i18n"] = i18n
    dp["sessionmaker"] = sessionmaker

    dp.update.middleware(DbSessionMiddleware(sessionmaker=sessionmaker))
    dp.update.middleware(I18nMiddleware(i18n=i18n, default_lang=app_settings.DEFAULT_LANG))

    dp.include_routers(
        start.router,
        menu.router,
        prayer_times.router,
        location.router,
        reminders.router,
        qibla.router,
        hijri.router,
        duas.router,
        tasbeh.router,
        settings.router,
        admin.router,
        mosques.router,
        ramadan.router,
        profile.router,
        errors.router,
    )

    await scheduler_service.start()
    runner = await _start_health_server()
    try:
        await dp.start_polling(bot)
    finally:
        if runner:
            await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
