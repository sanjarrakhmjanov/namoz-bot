from __future__ import annotations

from datetime import date, datetime, timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.db.crud import get_or_create_user
from bot.keyboards.inline import prayer_times_keyboard
from bot.services.aladhan import AladhanClient, AladhanError
from bot.utils.formatter import format_prayer_times, format_weekly_prayer_times
from bot.utils.i18n import I18n
from bot.utils.time import apply_offset, combine_date_time, parse_time_str

router = Router()


async def _ensure_user(db_user, db, settings, from_user):
    if db_user is not None:
        return db_user
    last = getattr(from_user, "last_name", None)
    full_name = f"{from_user.first_name} {last}".strip() if last else from_user.first_name
    return await get_or_create_user(
        session=db,
        telegram_id=from_user.id,
        username=from_user.username,
        full_name=full_name,
        default_lang=getattr(settings, "DEFAULT_LANG", "uz"),
    )


async def _send_prayer_times(
    action: str,
    i18n: I18n,
    lang: str,
    db_user,
    aladhan: AladhanClient,
    settings,
    send_func,
):
    target_date = date.today() if action == "today" else date.today() + timedelta(days=1)
    try:
        if db_user.city:
            data = await aladhan.get_prayer_times_by_city(
                city=db_user.city,
                country=settings.DEFAULT_COUNTRY,
                method=settings.ALADHAN_METHOD,
                target_date=target_date,
            )
        else:
            data = await aladhan.get_prayer_times_by_coords(
                lat=db_user.lat,
                lon=db_user.lon,
                method=settings.ALADHAN_METHOD,
                target_date=target_date,
            )
    except AladhanError:
        await send_func(i18n.t("api_error", lang))
        return

    timezone = data["data"]["meta"]["timezone"]
    text = format_prayer_times(
        i18n=i18n,
        lang=lang,
        timings=data["data"]["timings"],
        timezone=timezone,
        method_name=AladhanClient.method_name(settings.ALADHAN_METHOD),
        target_date=target_date,
        offset_min=db_user.time_offset_min,
    )
    await send_func(text)


async def _send_nearest_prayer(
    i18n: I18n,
    lang: str,
    db_user,
    aladhan: AladhanClient,
    settings,
    send_func,
) -> None:
    today = date.today()
    try:
        data = await _fetch_times(db_user, aladhan, settings, today)
    except AladhanError:
        await send_func(i18n.t("api_error", lang))
        return

    timezone = data["data"]["meta"]["timezone"]
    timings = data["data"]["timings"]
    now = datetime.now(combine_date_time(today, "00:00", timezone).tzinfo)
    prayers = [
        ("Fajr", "prayer_fajr"),
        ("Dhuhr", "prayer_dhuhr"),
        ("Asr", "prayer_asr"),
        ("Maghrib", "prayer_maghrib"),
        ("Isha", "prayer_isha"),
    ]

    next_prayer = None
    for key, label in prayers:
        base_time = parse_time_str(timings[key])
        run_dt = combine_date_time(today, base_time, timezone) + timedelta(minutes=db_user.time_offset_min)
        if run_dt > now:
            next_prayer = (key, label, run_dt)
            break

    if not next_prayer:
        try:
            tomorrow_data = await _fetch_times(db_user, aladhan, settings, today + timedelta(days=1))
        except AladhanError:
            await send_func(i18n.t("api_error", lang))
            return
        timings = tomorrow_data["data"]["timings"]
        base_time = parse_time_str(timings["Fajr"])
        run_dt = combine_date_time(today + timedelta(days=1), base_time, timezone) + timedelta(
            minutes=db_user.time_offset_min
        )
        next_prayer = ("Fajr", "prayer_fajr", run_dt)

    key, label_key, run_dt = next_prayer
    display_time = apply_offset(parse_time_str(timings[key]), db_user.time_offset_min, timezone, run_dt.date())
    remaining = _format_remaining(run_dt - now)
    text = i18n.t(
        "nearest_prayer_text",
        lang,
        prayer=i18n.t(label_key, lang),
        time=display_time,
        remaining=remaining,
    )
    await send_func(text)


async def _fetch_times(db_user, aladhan: AladhanClient, settings, target_date: date) -> dict:
    if db_user.city:
        return await aladhan.get_prayer_times_by_city(
            city=db_user.city,
            country=settings.DEFAULT_COUNTRY,
            method=settings.ALADHAN_METHOD,
            target_date=target_date,
        )
    return await aladhan.get_prayer_times_by_coords(
        lat=db_user.lat,
        lon=db_user.lon,
        method=settings.ALADHAN_METHOD,
        target_date=target_date,
    )


def _format_remaining(delta: timedelta) -> str:
    total_minutes = int(delta.total_seconds() // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


@router.callback_query(lambda c: c.data == "menu:prayer_times")
async def prayer_times_menu(callback: CallbackQuery, i18n: I18n, lang: str) -> None:
    await callback.message.edit_text(i18n.t("prayer_times_choose", lang), reply_markup=prayer_times_keyboard(i18n, lang))
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("prayer:"))
async def prayer_times_action(
    callback: CallbackQuery,
    i18n: I18n,
    lang: str,
    db,
    aladhan: AladhanClient,
    settings,
    db_user=None,
) -> None:
    db_user = await _ensure_user(db_user, db, settings, callback.from_user)
    if not (db_user.city or (db_user.lat is not None and db_user.lon is not None)):
        await callback.message.answer(i18n.t("location_missing", lang))
        await callback.answer()
        return

    action = callback.data.split(":", 1)[1]

    if action in ("today", "tomorrow"):
        await _send_prayer_times(action, i18n, lang, db_user, aladhan, settings, callback.message.answer)
    elif action == "nearest":
        await _send_nearest_prayer(i18n, lang, db_user, aladhan, settings, callback.message.answer)
    else:
        week_data = []
        for day in range(7):
            day_date = date.today() + timedelta(days=day)
            if db_user.city:
                day_data = await aladhan.get_prayer_times_by_city(
                    city=db_user.city,
                    country=settings.DEFAULT_COUNTRY,
                    method=settings.ALADHAN_METHOD,
                    target_date=day_date,
                )
            else:
                day_data = await aladhan.get_prayer_times_by_coords(
                    lat=db_user.lat,
                    lon=db_user.lon,
                    method=settings.ALADHAN_METHOD,
                    target_date=day_date,
                )
            week_data.append((day_date, day_data["data"]["timings"]))
        timezone = db_user.timezone or settings.DEFAULT_TIMEZONE
        text = format_weekly_prayer_times(i18n, lang, week_data, timezone, db_user.time_offset_min)
        await callback.message.answer(text)
    await callback.answer()


@router.message(Command("today"))
async def today_command(message: Message, i18n: I18n, lang: str, db, db_user, aladhan: AladhanClient, settings) -> None:
    db_user = await _ensure_user(db_user, db, settings, message.from_user)
    if not (db_user.city or (db_user.lat is not None and db_user.lon is not None)):
        await message.answer(i18n.t("location_missing", lang))
        return
    await _send_prayer_times("today", i18n, lang, db_user, aladhan, settings, message.answer)


@router.message(Command("tomorrow"))
async def tomorrow_command(message: Message, i18n: I18n, lang: str, db, db_user, aladhan: AladhanClient, settings) -> None:
    db_user = await _ensure_user(db_user, db, settings, message.from_user)
    if not (db_user.city or (db_user.lat is not None and db_user.lon is not None)):
        await message.answer(i18n.t("location_missing", lang))
        return
    await _send_prayer_times("tomorrow", i18n, lang, db_user, aladhan, settings, message.answer)


@router.message(Command("week"))
async def week_command(message: Message, i18n: I18n, lang: str, db, db_user, aladhan: AladhanClient, settings) -> None:
    db_user = await _ensure_user(db_user, db, settings, message.from_user)
    if not (db_user.city or (db_user.lat is not None and db_user.lon is not None)):
        await message.answer(i18n.t("location_missing", lang))
        return
    week_data = []
    for day in range(7):
        day_date = date.today() + timedelta(days=day)
        day_data = await _fetch_times(db_user, aladhan, settings, day_date)
        week_data.append((day_date, day_data["data"]["timings"]))
    timezone = db_user.timezone or settings.DEFAULT_TIMEZONE
    text = format_weekly_prayer_times(i18n, lang, week_data, timezone, db_user.time_offset_min)
    await message.answer(text)


@router.message(Command("nearest"))
async def nearest_command(message: Message, i18n: I18n, lang: str, db, db_user, aladhan: AladhanClient, settings) -> None:
    db_user = await _ensure_user(db_user, db, settings, message.from_user)
    if not (db_user.city or (db_user.lat is not None and db_user.lon is not None)):
        await message.answer(i18n.t("location_missing", lang))
        return

    await _send_nearest_prayer(i18n, lang, db_user, aladhan, settings, message.answer)
