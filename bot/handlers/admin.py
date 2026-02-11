from __future__ import annotations

import logging
from datetime import date, timedelta

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from sqlalchemy import text

from bot.db.crud import get_admin_stats, get_weekly_reminder_stats, list_users
from bot.handlers.states import AdminStates
from bot.keyboards.inline import admin_keyboard
from bot.utils.i18n import I18n
from bot.utils.rate_limit import rate_limit_send

router = Router()
logger = logging.getLogger(__name__)


def _is_admin(user_id: int, settings) -> bool:
    return user_id in settings.admin_ids


def _bar(value: int, max_value: int, width: int = 10) -> str:
    if max_value <= 0:
        return ""
    count = max(1, int((value / max_value) * width)) if value else 0
    return "#" * count


@router.message(Command("admin"))
async def admin_menu(message: Message, i18n: I18n, lang: str, settings) -> None:
    if not _is_admin(message.from_user.id, settings):
        return
    await message.answer(i18n.t("admin_title", lang), reply_markup=admin_keyboard(i18n, lang))


@router.callback_query(lambda c: c.data and c.data.startswith("admin:"))
async def admin_action(callback: CallbackQuery, i18n: I18n, lang: str, db, settings, scheduler_service) -> None:
    if not _is_admin(callback.from_user.id, settings):
        await callback.answer()
        return
    action = callback.data.split(":", 1)[1]
    if action == "users":
        stats = await get_admin_stats(db)
        text = i18n.t("admin_users_text", lang, count=stats["total_users"])
    elif action == "reminders":
        stats = await get_admin_stats(db)
        text = i18n.t("admin_reminders_text", lang, count=stats["reminders_on"])
    elif action == "top_cities":
        stats = await get_admin_stats(db)
        if stats["top_cities"]:
            cities = "\n".join([f"{name} - {count}" for name, count in stats["top_cities"]])
        else:
            cities = i18n.t("admin_no_cities", lang)
        text = i18n.t("admin_top_cities_text", lang, cities=cities)
    elif action == "weekly":
        rows = await get_weekly_reminder_stats(db)
        start_day = date.today() - timedelta(days=6)
        counts = {day: count for day, count in rows}
        series = []
        for idx in range(7):
            day = start_day + timedelta(days=idx)
            count = counts.get(day, 0)
            series.append((day, count))
        max_value = max((count for _, count in series), default=0)
        if max_value == 0:
            text = i18n.t("admin_weekly_empty", lang)
        else:
            lines = [i18n.t("admin_weekly_title", lang)]
            for day, count in series:
                label = day.strftime("%d-%m")
                lines.append(f"{label} | {_bar(count, max_value)} {count}")
            text = "\n".join(lines)
    elif action == "cities_chart":
        stats = await get_admin_stats(db)
        if not stats["top_cities"]:
            text = i18n.t("admin_no_cities", lang)
        else:
            max_value = max(count for _, count in stats["top_cities"])
            lines = [i18n.t("admin_cities_chart_title", lang)]
            for name, count in stats["top_cities"]:
                lines.append(f"{name} | {_bar(count, max_value)} {count}")
            text = "\n".join(lines)
    else:
        try:
            await db.execute(text("SELECT 1"))
            db_ok = True
        except Exception:
            db_ok = False
        scheduler_ok = bool(scheduler_service and scheduler_service._scheduler.running)
        text = i18n.t("admin_health_text", lang, db_ok=db_ok, scheduler_ok=scheduler_ok)
    await callback.message.answer(text)
    await callback.answer()


@router.message(Command("broadcast"))
async def broadcast_start(message: Message, i18n: I18n, lang: str, settings, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id, settings):
        return
    await message.answer(i18n.t("broadcast_prompt", lang))
    await state.set_state(AdminStates.waiting_broadcast)


@router.message(AdminStates.waiting_broadcast, F.text)
async def broadcast_send(message: Message, i18n: I18n, lang: str, db, state: FSMContext) -> None:
    await state.clear()
    users = await list_users(db)
    sent = 0
    for user in users:
        try:
            await message.bot.send_message(user.telegram_id, message.text)
            sent += 1
            await rate_limit_send(0.05)
        except Exception:
            logger.exception("Broadcast failed for %s", user.telegram_id)
            await rate_limit_send(0.05)
    await message.answer(i18n.t("broadcast_done", lang, count=sent))
