from __future__ import annotations

from datetime import date

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.db.crud import update_user_ramadan, update_user_ramadan_offsets
from bot.services.aladhan import AladhanClient, AladhanError
from bot.utils.i18n import I18n
from bot.utils.time import parse_time_str

router = Router()


def _status_text(i18n: I18n, lang: str, db_user) -> str:
    status = i18n.t("ramadan_status_on", lang) if db_user.ramadan_on else i18n.t("ramadan_status_off", lang)
    return i18n.t(
        "ramadan_status_text",
        lang,
        status=status,
        suhoor=db_user.suhoor_offset_min,
        iftar=db_user.iftar_offset_min,
    )


def _format_schedule(i18n: I18n, lang: str, items: list[tuple[str, str, str]]) -> str:
    lines = [i18n.t("ramadan_schedule_title", lang), ""]
    for day, suhoor, iftar in items:
        lines.append(i18n.t("ramadan_schedule_line", lang, day=day, suhoor=suhoor, iftar=iftar))
    return "\n".join(lines)


@router.callback_query(lambda c: c.data == "menu:ramadan")
async def ramadan_menu(callback: CallbackQuery, i18n: I18n, lang: str, db_user) -> None:
    await callback.message.answer(
        "\n\n".join([_status_text(i18n, lang, db_user), i18n.t("ramadan_help_text", lang)])
    )
    await callback.answer()


@router.message(Command("ramadan"))
async def ramadan_command(
    message: Message,
    i18n: I18n,
    lang: str,
    db_user,
    db,
    aladhan: AladhanClient,
    settings,
    scheduler_service,
) -> None:
    args = (message.text or "").split(maxsplit=1)
    if len(args) == 1:
        await message.answer(
            "\n\n".join([_status_text(i18n, lang, db_user), i18n.t("ramadan_help_text", lang)])
        )
        return

    action = args[1].strip().lower()
    if action in ("on", "enable"):
        await update_user_ramadan(db, db_user.id, True)
        db_user.ramadan_on = True
        await scheduler_service.refresh_all()
        await message.answer(i18n.t("ramadan_enabled", lang))
        return
    if action in ("off", "disable"):
        await update_user_ramadan(db, db_user.id, False)
        db_user.ramadan_on = False
        scheduler_service.remove_ramadan_jobs_for_user(db_user.telegram_id)
        await message.answer(i18n.t("ramadan_disabled", lang))
        return
    if action.startswith("offset"):
        parts = action.split()
        if len(parts) != 3:
            await message.answer(i18n.t("ramadan_offset_invalid", lang))
            return
        try:
            suhoor_offset = int(parts[1])
            iftar_offset = int(parts[2])
        except ValueError:
            await message.answer(i18n.t("ramadan_offset_invalid", lang))
            return
        await update_user_ramadan_offsets(db, db_user.id, suhoor_offset, iftar_offset)
        db_user.suhoor_offset_min = suhoor_offset
        db_user.iftar_offset_min = iftar_offset
        await scheduler_service.refresh_all()
        await message.answer(i18n.t("ramadan_offset_saved", lang, suhoor=suhoor_offset, iftar=iftar_offset))
        return
    if action == "month":
        if not (db_user.city or (db_user.lat is not None and db_user.lon is not None)):
            await message.answer(i18n.t("location_missing", lang))
            return
        today = date.today()
        try:
            if db_user.city:
                data = await aladhan.get_calendar_by_city(
                    city=db_user.city,
                    country=settings.DEFAULT_COUNTRY,
                    method=settings.ALADHAN_METHOD,
                    month=today.month,
                    year=today.year,
                )
            else:
                data = await aladhan.get_calendar_by_coords(
                    lat=db_user.lat,
                    lon=db_user.lon,
                    method=settings.ALADHAN_METHOD,
                    month=today.month,
                    year=today.year,
                )
        except AladhanError:
            await message.answer(i18n.t("api_error", lang))
            return

        items = []
        for day_data in data.get("data", []):
            day = day_data["date"]["gregorian"]["day"]
            timings = day_data["timings"]
            suhoor = parse_time_str(timings["Fajr"])
            iftar = parse_time_str(timings["Maghrib"])
            items.append((day, suhoor, iftar))
        await message.answer(_format_schedule(i18n, lang, items))
        return

    await message.answer(i18n.t("ramadan_help_text", lang))
