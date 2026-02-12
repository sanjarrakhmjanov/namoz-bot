from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.db.models import Reminder
from bot.utils.i18n import I18n


def language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang:uz"),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
    )
    builder.adjust(1)
    return builder.as_markup()


def main_menu_keyboard(i18n: I18n, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    buttons = [
        ("menu:prayer_times", i18n.t("menu_prayer_times", lang)),
        ("menu:location", i18n.t("menu_location", lang)),
        ("menu:mosques", i18n.t("menu_mosques", lang)),
        ("menu:reminders", i18n.t("menu_reminders", lang)),
        ("menu:qibla", i18n.t("menu_qibla", lang)),
        ("menu:hijri", i18n.t("menu_hijri", lang)),
        ("menu:ramadan", i18n.t("menu_ramadan", lang)),
        ("menu:duas", i18n.t("menu_duas", lang)),
        ("menu:tasbeh", i18n.t("menu_tasbeh", lang)),
        ("menu:profile", i18n.t("menu_profile", lang)),
        ("menu:settings", i18n.t("menu_settings", lang)),
        ("menu:help", i18n.t("menu_help", lang)),
    ]
    for cb, text in buttons:
        builder.add(InlineKeyboardButton(text=text, callback_data=cb))
    builder.adjust(2)
    return builder.as_markup()


def prayer_times_keyboard(i18n: I18n, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text=i18n.t("btn_today", lang), callback_data="prayer:today"),
        InlineKeyboardButton(text=i18n.t("btn_tomorrow", lang), callback_data="prayer:tomorrow"),
        InlineKeyboardButton(text=i18n.t("btn_week", lang), callback_data="prayer:week"),
        InlineKeyboardButton(text=i18n.t("btn_nearest", lang), callback_data="prayer:nearest"),
    )
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data="menu:back"))
    return builder.as_markup()


def reminders_keyboard(i18n: I18n, lang: str, reminder: Reminder) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    def toggle_text(key: str, enabled: bool) -> str:
        return f"{'✅' if enabled else '❌'} {i18n.t(key, lang)}"

    builder.add(
        InlineKeyboardButton(text=toggle_text("prayer_fajr", reminder.fajr_on), callback_data="rem:toggle:fajr"),
        InlineKeyboardButton(text=toggle_text("prayer_dhuhr", reminder.dhuhr_on), callback_data="rem:toggle:dhuhr"),
        InlineKeyboardButton(text=toggle_text("prayer_asr", reminder.asr_on), callback_data="rem:toggle:asr"),
        InlineKeyboardButton(text=toggle_text("prayer_maghrib", reminder.maghrib_on), callback_data="rem:toggle:maghrib"),
        InlineKeyboardButton(text=toggle_text("prayer_isha", reminder.isha_on), callback_data="rem:toggle:isha"),
    )
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text=i18n.t("btn_all_on", lang), callback_data="rem:all_on"),
        InlineKeyboardButton(text=i18n.t("btn_all_off", lang), callback_data="rem:all_off"),
    )
    builder.row(
        InlineKeyboardButton(text=i18n.t("btn_quick_on", lang), callback_data="rem:quick_on"),
    )
    builder.row(
        InlineKeyboardButton(text=i18n.t("btn_offset", lang), callback_data="rem:offset"),
    )
    builder.row(InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data="menu:back"))
    return builder.as_markup()


def reminders_offset_keyboard(i18n: I18n, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for value in (5, 10, 15):
        builder.add(
            InlineKeyboardButton(text=i18n.t("btn_offset_value", lang, value=value), callback_data=f"rem:offset:{value}")
        )
    builder.add(InlineKeyboardButton(text=i18n.t("btn_offset_custom", lang), callback_data="rem:offset:custom"))
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data="menu:back"))
    return builder.as_markup()


def tasbeh_keyboard(i18n: I18n, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text=i18n.t("btn_plus_one", lang), callback_data="tasbeh:inc:1"),
        InlineKeyboardButton(text=i18n.t("btn_plus_ten", lang), callback_data="tasbeh:inc:10"),
        InlineKeyboardButton(text=i18n.t("btn_reset", lang), callback_data="tasbeh:reset"),
    )
    builder.row(InlineKeyboardButton(text=i18n.t("btn_goal", lang), callback_data="tasbeh:goal"))
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data="menu:back"))
    return builder.as_markup()


def tasbeh_goal_keyboard(i18n: I18n, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for value in (33, 99, 100):
        builder.add(
            InlineKeyboardButton(text=i18n.t("btn_goal_value", lang, value=value), callback_data=f"tasbeh:goal:{value}")
        )
    builder.add(InlineKeyboardButton(text=i18n.t("btn_goal_custom", lang), callback_data="tasbeh:goal:custom"))
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data="menu:back"))
    return builder.as_markup()


def settings_keyboard(i18n: I18n, lang: str, db_user) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    hijri_text = (
        i18n.t("btn_hijri_reminder_off", lang)
        if getattr(db_user, "hijri_reminder_on", False)
        else i18n.t("btn_hijri_reminder_on", lang)
    )
    builder.add(
        InlineKeyboardButton(text=i18n.t("btn_change_lang", lang), callback_data="settings:lang"),
        InlineKeyboardButton(text=i18n.t("btn_time_offset", lang), callback_data="settings:offset"),
        InlineKeyboardButton(text=i18n.t("btn_silent_hours", lang), callback_data="settings:silent"),
        InlineKeyboardButton(text=hijri_text, callback_data="settings:hijri_toggle"),
    )
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data="menu:back"))
    return builder.as_markup()


def settings_offset_keyboard(i18n: I18n, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for value in (-10, -5, 0, 5, 10):
        builder.add(
            InlineKeyboardButton(text=i18n.t("btn_offset_value", lang, value=value), callback_data=f"settings:offset:{value}")
        )
    builder.add(InlineKeyboardButton(text=i18n.t("btn_offset_custom", lang), callback_data="settings:offset:custom"))
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data="menu:back"))
    return builder.as_markup()


def admin_keyboard(i18n: I18n, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text=i18n.t("admin_users", lang), callback_data="admin:users"),
        InlineKeyboardButton(text=i18n.t("admin_users_list", lang), callback_data="admin:users_list"),
        InlineKeyboardButton(text=i18n.t("admin_reminders", lang), callback_data="admin:reminders"),
        InlineKeyboardButton(text=i18n.t("admin_top_cities", lang), callback_data="admin:top_cities"),
        InlineKeyboardButton(text=i18n.t("admin_weekly", lang), callback_data="admin:weekly"),
        InlineKeyboardButton(text=i18n.t("admin_cities_chart", lang), callback_data="admin:cities_chart"),
        InlineKeyboardButton(text=i18n.t("admin_health", lang), callback_data="admin:health"),
    )
    builder.adjust(2)
    return builder.as_markup()


def duas_keyboard(i18n: I18n, lang: str, index: int, total: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    prev_index = (index - 1) % total
    next_index = (index + 1) % total
    builder.add(
        InlineKeyboardButton(text=i18n.t("btn_prev", lang), callback_data=f"dua:idx:{prev_index}"),
        InlineKeyboardButton(text=i18n.t("btn_next", lang), callback_data=f"dua:idx:{next_index}"),
    )
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data="menu:back"))
    return builder.as_markup()
