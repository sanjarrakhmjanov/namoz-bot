from datetime import date

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.db.crud import update_user_hijri_reminder
from bot.services.aladhan import AladhanClient, AladhanError
from bot.utils.i18n import I18n

router = Router()


@router.callback_query(lambda c: c.data == "menu:hijri")
async def hijri_menu(callback: CallbackQuery, i18n: I18n, lang: str, aladhan: AladhanClient) -> None:
    try:
        data = await aladhan.get_hijri_date(date.today())
        hijri = data["data"]["hijri"]
        greg = data["data"]["gregorian"]
    except AladhanError:
        await callback.message.answer(i18n.t("api_error", lang))
        await callback.answer()
        return

    weekday_key_map = {
        "Monday": "weekday_mon",
        "Tuesday": "weekday_tue",
        "Wednesday": "weekday_wed",
        "Thursday": "weekday_thu",
        "Friday": "weekday_fri",
        "Saturday": "weekday_sat",
        "Sunday": "weekday_sun",
    }
    weekday_key = weekday_key_map.get(greg["weekday"]["en"], "weekday_mon")
    weekday = i18n.t(weekday_key, lang)

    text = i18n.t(
        "hijri_text",
        lang,
        hijri=f"{hijri['day']} {hijri['month']['en']} {hijri['year']}",
        greg=f"{greg['day']} {greg['month']['en']} {greg['year']}",
        weekday=weekday,
    )
    await callback.message.answer(text)
    await callback.answer()


@router.message(Command("hijri_remind"))
async def hijri_reminder_command(message: Message, i18n: I18n, lang: str, db_user, db) -> None:
    text = (message.text or "").strip().lower()
    if text.endswith(" on") or text.endswith(" enable"):
        enabled = True
    elif text.endswith(" off") or text.endswith(" disable"):
        enabled = False
    else:
        status = i18n.t("hijri_reminder_on", lang) if db_user.hijri_reminder_on else i18n.t("hijri_reminder_off", lang)
        await message.answer(i18n.t("hijri_reminder_usage", lang, status=status))
        return

    await update_user_hijri_reminder(db, db_user.id, enabled)
    db_user.hijri_reminder_on = enabled
    message_text = i18n.t("hijri_reminder_on", lang) if enabled else i18n.t("hijri_reminder_off", lang)
    await message.answer(message_text)
