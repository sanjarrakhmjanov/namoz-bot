from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.db.crud import get_or_create_user, update_user_city, update_user_coords
from bot.handlers.states import LocationStates
from bot.keyboards.reply import location_request_keyboard, remove_reply_keyboard
from bot.utils.i18n import I18n
from bot.services.aladhan import AladhanClient, AladhanError

router = Router()


@router.callback_query(lambda c: c.data == "menu:location")
async def location_menu(callback: CallbackQuery, i18n: I18n, lang: str, db_user, state: FSMContext) -> None:
    status = _location_status_text(i18n, lang, db_user)
    await callback.message.answer(
        f"{status}\n\n{i18n.t('location_prompt', lang)}",
        reply_markup=location_request_keyboard(i18n.t("btn_send_location", lang)),
    )
    await state.set_state(LocationStates.waiting_city)
    await callback.answer()


@router.message(Command("setcity"))
async def set_city_command(message: Message, i18n: I18n, lang: str, state: FSMContext) -> None:
    await message.answer(i18n.t("setcity_prompt", lang))
    await state.set_state(LocationStates.waiting_city)


@router.message(Command("setlocation"))
async def set_location_command(message: Message, i18n: I18n, lang: str, state: FSMContext) -> None:
    await message.answer(
        i18n.t("setlocation_prompt", lang),
        reply_markup=location_request_keyboard(i18n.t("btn_send_location", lang)),
    )
    await state.set_state(LocationStates.waiting_city)


@router.message(LocationStates.waiting_city, F.location)
async def location_received(message: Message, i18n: I18n, lang: str, db_user, db, aladhan: AladhanClient, settings, scheduler_service, state: FSMContext) -> None:
    if db_user is None:
        last = getattr(message.from_user, "last_name", None)
        full_name = f"{message.from_user.first_name} {last}".strip() if last else message.from_user.first_name
        db_user = await get_or_create_user(
            session=db,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=full_name,
            default_lang=getattr(settings, "DEFAULT_LANG", "uz"),
        )
    lat = message.location.latitude
    lon = message.location.longitude
    try:
        data = await aladhan.get_prayer_times_by_coords(
            lat, lon, method=settings.ALADHAN_METHOD, target_date=message.date.date()
        )
        timezone = data["data"]["meta"]["timezone"]
    except AladhanError:
        await message.answer(i18n.t("api_error", lang))
        return
    await update_user_coords(db, db_user.id, lat, lon, timezone)
    await scheduler_service.refresh_all()
    await state.clear()
    await message.answer(i18n.t("location_saved", lang), reply_markup=remove_reply_keyboard())


@router.message(LocationStates.waiting_city, F.text)
async def city_received(message: Message, i18n: I18n, lang: str, db_user, db, aladhan: AladhanClient, settings, scheduler_service, state: FSMContext) -> None:
    if db_user is None:
        last = getattr(message.from_user, "last_name", None)
        full_name = f"{message.from_user.first_name} {last}".strip() if last else message.from_user.first_name
        db_user = await get_or_create_user(
            session=db,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=full_name,
            default_lang=getattr(settings, "DEFAULT_LANG", "uz"),
        )
    city = message.text.strip()
    if len(city) < 2:
        await message.answer(i18n.t("location_invalid", lang))
        return
    try:
        data = await aladhan.get_prayer_times_by_city(
            city, country=settings.DEFAULT_COUNTRY, method=settings.ALADHAN_METHOD, target_date=message.date.date()
        )
        timezone = data["data"]["meta"]["timezone"]
    except AladhanError:
        await message.answer(i18n.t("api_error", lang))
        return
    await update_user_city(db, db_user.id, city, timezone)
    await scheduler_service.refresh_all()
    await state.clear()
    await message.answer(i18n.t("city_saved", lang, city=city), reply_markup=remove_reply_keyboard())


@router.message(F.location)
async def location_any(message: Message, i18n: I18n, lang: str, db_user, db, aladhan: AladhanClient, settings, scheduler_service, state: FSMContext) -> None:
    if db_user is None:
        last = getattr(message.from_user, "last_name", None)
        full_name = f"{message.from_user.first_name} {last}".strip() if last else message.from_user.first_name
        db_user = await get_or_create_user(
            session=db,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=full_name,
            default_lang=getattr(settings, "DEFAULT_LANG", "uz"),
        )
    lat = message.location.latitude
    lon = message.location.longitude
    try:
        data = await aladhan.get_prayer_times_by_coords(
            lat, lon, method=settings.ALADHAN_METHOD, target_date=message.date.date()
        )
        timezone = data["data"]["meta"]["timezone"]
    except AladhanError:
        await message.answer(i18n.t("api_error", lang))
        return
    await update_user_coords(db, db_user.id, lat, lon, timezone)
    await scheduler_service.refresh_all()
    await state.clear()
    await message.answer(i18n.t("location_saved", lang), reply_markup=remove_reply_keyboard())


def _location_status_text(i18n: I18n, lang: str, db_user) -> str:
    if not db_user or (not db_user.city and db_user.lat is None and db_user.lon is None):
        return i18n.t("location_status_empty", lang)
    if db_user.city:
        return i18n.t("location_status_city", lang, city=db_user.city, timezone=db_user.timezone or "-")
    return i18n.t(
        "location_status_coords",
        lang,
        lat=f"{db_user.lat:.4f}",
        lon=f"{db_user.lon:.4f}",
        timezone=db_user.timezone or "-",
    )
