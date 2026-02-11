from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.db.crud import get_or_create_reminders
from bot.handlers.states import ReminderStates
from bot.keyboards.inline import reminders_keyboard, reminders_offset_keyboard
from bot.utils.i18n import I18n

router = Router()


@router.callback_query(lambda c: c.data == "menu:reminders")
async def reminders_menu(callback: CallbackQuery, i18n: I18n, lang: str, db_user, db) -> None:
    reminder = await get_or_create_reminders(db, db_user.id)
    await callback.message.edit_text(
        i18n.t("reminders_title", lang),
        reply_markup=reminders_keyboard(i18n, lang, reminder),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("rem:toggle:"))
async def reminders_toggle(callback: CallbackQuery, i18n: I18n, lang: str, db_user, db, scheduler_service) -> None:
    reminder = await get_or_create_reminders(db, db_user.id)
    key = callback.data.split(":", 2)[2]
    mapping = {
        "fajr": "fajr_on",
        "dhuhr": "dhuhr_on",
        "asr": "asr_on",
        "maghrib": "maghrib_on",
        "isha": "isha_on",
    }
    attr = mapping.get(key)
    if attr:
        setattr(reminder, attr, not getattr(reminder, attr))
        reminder.enabled = any(
            [reminder.fajr_on, reminder.dhuhr_on, reminder.asr_on, reminder.maghrib_on, reminder.isha_on]
        )
    await callback.message.edit_reply_markup(reply_markup=reminders_keyboard(i18n, lang, reminder))
    if reminder.enabled:
        await scheduler_service.refresh_all()
    else:
        scheduler_service.remove_jobs_for_user(db_user.telegram_id)
    await callback.answer()


@router.callback_query(lambda c: c.data == "rem:all_on")
async def reminders_all_on(callback: CallbackQuery, i18n: I18n, lang: str, db_user, db, scheduler_service) -> None:
    reminder = await get_or_create_reminders(db, db_user.id)
    reminder.fajr_on = reminder.dhuhr_on = reminder.asr_on = reminder.maghrib_on = reminder.isha_on = True
    reminder.enabled = True
    await callback.message.edit_reply_markup(reply_markup=reminders_keyboard(i18n, lang, reminder))
    await scheduler_service.refresh_all()
    await callback.answer()


@router.callback_query(lambda c: c.data == "rem:quick_on")
async def reminders_quick_on(callback: CallbackQuery, i18n: I18n, lang: str, db_user, db, scheduler_service) -> None:
    reminder = await get_or_create_reminders(db, db_user.id)
    reminder.fajr_on = reminder.dhuhr_on = reminder.asr_on = reminder.maghrib_on = reminder.isha_on = True
    reminder.enabled = True
    await scheduler_service.refresh_all()
    await callback.message.answer(
        i18n.t("reminders_quick_on", lang),
        reply_markup=reminders_offset_keyboard(i18n, lang),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "rem:all_off")
async def reminders_all_off(callback: CallbackQuery, i18n: I18n, lang: str, db_user, db, scheduler_service) -> None:
    reminder = await get_or_create_reminders(db, db_user.id)
    reminder.fajr_on = reminder.dhuhr_on = reminder.asr_on = reminder.maghrib_on = reminder.isha_on = False
    reminder.enabled = False
    await callback.message.edit_reply_markup(reply_markup=reminders_keyboard(i18n, lang, reminder))
    scheduler_service.remove_jobs_for_user(db_user.telegram_id)
    await callback.answer()


@router.callback_query(lambda c: c.data == "rem:offset")
async def reminders_offset_menu(callback: CallbackQuery, i18n: I18n, lang: str) -> None:
    await callback.message.answer(
        i18n.t("reminders_offset_choose", lang),
        reply_markup=reminders_offset_keyboard(i18n, lang),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("rem:offset:"))
async def reminders_offset_set(callback: CallbackQuery, i18n: I18n, lang: str, db_user, db, scheduler_service, state: FSMContext) -> None:
    value = callback.data.split(":", 2)[2]
    if value == "custom":
        await callback.message.answer(i18n.t("reminders_offset_custom", lang))
        await state.set_state(ReminderStates.waiting_offset)
    else:
        reminder = await get_or_create_reminders(db, db_user.id)
        reminder.offset_min = int(value)
        await callback.message.answer(i18n.t("reminders_offset_saved", lang, value=value))
        await scheduler_service.refresh_all()
    await callback.answer()


@router.message(ReminderStates.waiting_offset, F.text)
async def reminders_offset_custom(message: Message, i18n: I18n, lang: str, db_user, db, scheduler_service, state: FSMContext) -> None:
    try:
        value = int(message.text.strip())
    except ValueError:
        await message.answer(i18n.t("reminders_offset_invalid", lang))
        return
    reminder = await get_or_create_reminders(db, db_user.id)
    reminder.offset_min = value
    await scheduler_service.refresh_all()
    await state.clear()
    await message.answer(i18n.t("reminders_offset_saved", lang, value=value))


@router.message(Command("remindertest"))
async def reminder_test_command(message: Message, i18n: I18n, lang: str, scheduler_service) -> None:
    if await scheduler_service.is_in_silent_hours(message.from_user.id):
        await message.answer(i18n.t("reminder_test_blocked", lang))
        return
    run_dt = await scheduler_service.schedule_test_reminder(message.from_user.id, lang)
    await message.answer(i18n.t("reminder_test_scheduled", lang, time=run_dt.strftime("%H:%M")))
