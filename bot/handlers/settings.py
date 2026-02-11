from __future__ import annotations

import re

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.db.crud import update_user_hijri_reminder, update_user_lang, update_user_silent_hours, update_user_time_offset
from bot.handlers.states import SettingsStates, SilentHoursStates
from bot.keyboards.inline import language_keyboard, settings_keyboard, settings_offset_keyboard
from bot.utils.i18n import I18n
from bot.utils.time import parse_hhmm_time

router = Router()


@router.callback_query(lambda c: c.data == "menu:settings")
async def settings_menu(callback: CallbackQuery, i18n: I18n, lang: str, db_user) -> None:
    await callback.message.edit_text(
        i18n.t("settings_title", lang),
        reply_markup=settings_keyboard(i18n, lang, db_user),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "settings:lang")
async def settings_lang(callback: CallbackQuery, i18n: I18n, lang: str) -> None:
    await callback.message.answer(i18n.t("choose_language", lang), reply_markup=language_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data == "settings:offset")
async def settings_offset_menu(callback: CallbackQuery, i18n: I18n, lang: str) -> None:
    await callback.message.answer(i18n.t("settings_offset_choose", lang), reply_markup=settings_offset_keyboard(i18n, lang))
    await callback.answer()


@router.callback_query(lambda c: c.data == "settings:silent")
async def settings_silent_menu(callback: CallbackQuery, i18n: I18n, lang: str, state: FSMContext) -> None:
    await callback.message.answer(i18n.t("silent_hours_prompt", lang))
    await state.set_state(SilentHoursStates.waiting_hours)
    await callback.answer()


@router.callback_query(lambda c: c.data == "settings:hijri_toggle")
async def settings_hijri_toggle(callback: CallbackQuery, i18n: I18n, lang: str, db_user, db) -> None:
    enabled = not bool(db_user.hijri_reminder_on)
    await update_user_hijri_reminder(db, db_user.id, enabled)
    db_user.hijri_reminder_on = enabled
    message = i18n.t("hijri_reminder_on", lang) if enabled else i18n.t("hijri_reminder_off", lang)
    await callback.message.answer(message)
    await callback.message.edit_reply_markup(reply_markup=settings_keyboard(i18n, lang, db_user))
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("settings:offset:"))
async def settings_offset_set(callback: CallbackQuery, i18n: I18n, lang: str, db_user, db, scheduler_service, state: FSMContext) -> None:
    value = callback.data.split(":", 2)[2]
    if value == "custom":
        await callback.message.answer(i18n.t("settings_offset_custom", lang))
        await state.set_state(SettingsStates.waiting_offset)
    else:
        await update_user_time_offset(db, db_user.id, int(value))
        await callback.message.answer(i18n.t("settings_offset_saved", lang, value=value))
        await scheduler_service.refresh_all()
    await callback.answer()


@router.message(SettingsStates.waiting_offset, F.text)
async def settings_offset_custom(message: Message, i18n: I18n, lang: str, db_user, db, scheduler_service, state: FSMContext) -> None:
    try:
        value = int(message.text.strip())
    except ValueError:
        await message.answer(i18n.t("settings_offset_invalid", lang))
        return
    await update_user_time_offset(db, db_user.id, value)
    await scheduler_service.refresh_all()
    await state.clear()
    await message.answer(i18n.t("settings_offset_saved", lang, value=value))


@router.message(Command("silent"))
async def silent_hours_command(message: Message, i18n: I18n, lang: str, state: FSMContext) -> None:
    await message.answer(i18n.t("silent_hours_prompt", lang))
    await state.set_state(SilentHoursStates.waiting_hours)


@router.message(SilentHoursStates.waiting_hours, F.text)
async def silent_hours_set(message: Message, i18n: I18n, lang: str, db_user, db, state: FSMContext) -> None:
    text = message.text.strip().lower()
    if text in ("off", "disable", "0"):
        await update_user_silent_hours(db, db_user.id, None, None)
        await state.clear()
        await message.answer(i18n.t("silent_hours_off", lang))
        return

    match = re.match(r"^(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})$", text)
    if not match:
        await message.answer(i18n.t("silent_hours_invalid", lang))
        return

    try:
        start = parse_hhmm_time(match.group(1))
        end = parse_hhmm_time(match.group(2))
    except ValueError:
        await message.answer(i18n.t("silent_hours_invalid", lang))
        return

    await update_user_silent_hours(db, db_user.id, start.strftime("%H:%M"), end.strftime("%H:%M"))
    await state.clear()
    await message.answer(
        i18n.t("silent_hours_saved", lang, start=start.strftime("%H:%M"), end=end.strftime("%H:%M"))
    )
