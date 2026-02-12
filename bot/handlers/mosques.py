from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.db.crud import get_or_create_user, update_user_coords
from bot.handlers.states import MosquesStates
from bot.keyboards.reply import location_request_keyboard, remove_reply_keyboard
from bot.services.aladhan import AladhanClient, AladhanError
from bot.services.overpass import OverpassClient, OverpassError
from bot.utils.i18n import I18n

router = Router()


def _format_mosques(i18n: I18n, lang: str, items: list[dict], radius_km: int) -> str:
    if not items:
        return i18n.t("mosques_none", lang)
    lines = [i18n.t("mosques_title", lang, radius=radius_km), ""]
    for idx, item in enumerate(items, start=1):
        distance = f"{item['distance_km']:.2f}"
        url = None
        if item.get("lat") is not None and item.get("lon") is not None:
            url = f"https://maps.google.com/?q={item['lat']},{item['lon']}"
        if item.get("address"):
            line = i18n.t(
                "mosques_item_addr",
                lang,
                index=idx,
                name=item["name"],
                distance=distance,
                address=item["address"],
                url=url or "",
            )
        else:
            line = i18n.t(
                "mosques_item",
                lang,
                index=idx,
                name=item["name"],
                distance=distance,
                url=url or "",
            )
        lines.append(line)
    return "\n".join(lines)


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


@router.callback_query(lambda c: c.data == "menu:mosques")
async def mosques_menu(callback: CallbackQuery, i18n: I18n, lang: str, db, db_user, settings, state: FSMContext) -> None:
    db_user = await _ensure_user(db_user, db, settings, callback.from_user)
    if db_user.lat is None or db_user.lon is None:
        await callback.message.answer(
            i18n.t("mosques_location_needed", lang),
            reply_markup=location_request_keyboard(i18n.t("btn_send_location", lang)),
        )
        await state.set_state(MosquesStates.waiting_location)
        await callback.answer()
        return
    await _send_mosques(callback.message.answer, i18n, lang, db_user, settings)
    await callback.answer()


@router.message(Command("mosques"))
async def mosques_command(message: Message, i18n: I18n, lang: str, db, db_user, settings, state: FSMContext) -> None:
    db_user = await _ensure_user(db_user, db, settings, message.from_user)
    if db_user.lat is None or db_user.lon is None:
        await message.answer(
            i18n.t("mosques_location_needed", lang),
            reply_markup=location_request_keyboard(i18n.t("btn_send_location", lang)),
        )
        await state.set_state(MosquesStates.waiting_location)
        return
    await _send_mosques(message.answer, i18n, lang, db_user, settings)


@router.message(MosquesStates.waiting_location, F.location)
async def mosques_location_received(
    message: Message,
    i18n: I18n,
    lang: str,
    db,
    db_user,
    settings,
    aladhan: AladhanClient,
    state: FSMContext,
) -> None:
    db_user = await _ensure_user(db_user, db, settings, message.from_user)
    lat = message.location.latitude
    lon = message.location.longitude
    try:
        data = await aladhan.get_prayer_times_by_coords(
            lat, lon, method=settings.ALADHAN_METHOD, target_date=message.date.date()
        )
        timezone = data["data"]["meta"]["timezone"]
    except AladhanError:
        timezone = settings.DEFAULT_TIMEZONE
    db_user.lat = lat
    db_user.lon = lon
    db_user.timezone = timezone
    await update_user_coords(db, db_user.id, lat, lon, timezone)
    await state.clear()
    await _send_mosques(message.answer, i18n, lang, db_user, settings)
    await message.answer(i18n.t("location_saved", lang), reply_markup=remove_reply_keyboard())


async def _send_mosques(send_func, i18n: I18n, lang: str, db_user, settings) -> None:
    client = OverpassClient()
    try:
        items = await client.find_mosques(
            lat=db_user.lat,
            lon=db_user.lon,
            radius_km=settings.MOSQUE_RADIUS_KM,
            limit=settings.MOSQUE_LIMIT,
        )
    except OverpassError:
        await send_func(i18n.t("mosques_error", lang))
        return
    text = _format_mosques(i18n, lang, items, settings.MOSQUE_RADIUS_KM)
    await send_func(text)
