from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.db.crud import get_or_create_reminders
from bot.handlers.location import _location_status_text
from bot.utils.i18n import I18n

router = Router()


def _reminder_status(i18n: I18n, lang: str, reminder) -> str:
    enabled = []
    if reminder.fajr_on:
        enabled.append(i18n.t("prayer_fajr", lang))
    if reminder.dhuhr_on:
        enabled.append(i18n.t("prayer_dhuhr", lang))
    if reminder.asr_on:
        enabled.append(i18n.t("prayer_asr", lang))
    if reminder.maghrib_on:
        enabled.append(i18n.t("prayer_maghrib", lang))
    if reminder.isha_on:
        enabled.append(i18n.t("prayer_isha", lang))
    if not enabled:
        return i18n.t("profile_reminders_off", lang)
    items = ", ".join(enabled)
    return i18n.t("profile_reminders_on", lang, items=items, offset=reminder.offset_min)


def _silent_text(i18n: I18n, lang: str, db_user) -> str:
    if not db_user.silent_start or not db_user.silent_end:
        return i18n.t("profile_silent_off", lang)
    return i18n.t("profile_silent_on", lang, start=db_user.silent_start, end=db_user.silent_end)


def _enabled_text(i18n: I18n, lang: str, enabled: bool) -> str:
    return i18n.t("status_on", lang) if enabled else i18n.t("status_off", lang)


@router.message(Command("profile"))
async def profile_command(message: Message, i18n: I18n, lang: str, db_user, db) -> None:
    reminder = await get_or_create_reminders(db, db_user.id)
    text = "\n\n".join(
        [
            i18n.t("profile_title", lang),
            _location_status_text(i18n, lang, db_user),
            i18n.t("profile_lang", lang, language=lang),
            i18n.t("profile_timezone", lang, timezone=db_user.timezone or "-"),
            _reminder_status(i18n, lang, reminder),
            _silent_text(i18n, lang, db_user),
            i18n.t("profile_hijri", lang, enabled=_enabled_text(i18n, lang, bool(db_user.hijri_reminder_on))),
            i18n.t("profile_ramadan", lang, enabled=_enabled_text(i18n, lang, bool(db_user.ramadan_on))),
        ]
    )
    await message.answer(text)


@router.callback_query(lambda c: c.data == "menu:profile")
async def profile_menu(callback: CallbackQuery, i18n: I18n, lang: str, db_user, db) -> None:
    reminder = await get_or_create_reminders(db, db_user.id)
    text = "\n\n".join(
        [
            i18n.t("profile_title", lang),
            _location_status_text(i18n, lang, db_user),
            i18n.t("profile_lang", lang, language=lang),
            i18n.t("profile_timezone", lang, timezone=db_user.timezone or "-"),
            _reminder_status(i18n, lang, reminder),
            _silent_text(i18n, lang, db_user),
            i18n.t("profile_hijri", lang, enabled=_enabled_text(i18n, lang, bool(db_user.hijri_reminder_on))),
            i18n.t("profile_ramadan", lang, enabled=_enabled_text(i18n, lang, bool(db_user.ramadan_on))),
        ]
    )
    await callback.message.answer(text)
    await callback.answer()
