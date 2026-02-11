from __future__ import annotations

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.db.crud import get_or_create_tasbeh
from bot.handlers.states import TasbehStates
from bot.keyboards.inline import tasbeh_goal_keyboard, tasbeh_keyboard
from bot.utils.i18n import I18n

router = Router()


def _tasbeh_text(i18n: I18n, lang: str, count: int, goal: int) -> str:
    return i18n.t("tasbeh_text", lang, count=count, goal=goal)


@router.callback_query(lambda c: c.data == "menu:tasbeh")
async def tasbeh_menu(callback: CallbackQuery, i18n: I18n, lang: str, db_user, db) -> None:
    tasbeh = await get_or_create_tasbeh(db, db_user.id)
    await callback.message.edit_text(
        _tasbeh_text(i18n, lang, tasbeh.count, tasbeh.goal),
        reply_markup=tasbeh_keyboard(i18n, lang),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("tasbeh:inc:"))
async def tasbeh_increment(callback: CallbackQuery, i18n: I18n, lang: str, db_user, db) -> None:
    tasbeh = await get_or_create_tasbeh(db, db_user.id)
    inc = int(callback.data.split(":", 2)[2])
    tasbeh.count += inc
    await callback.message.edit_text(
        _tasbeh_text(i18n, lang, tasbeh.count, tasbeh.goal),
        reply_markup=tasbeh_keyboard(i18n, lang),
    )
    if tasbeh.count >= tasbeh.goal:
        await callback.message.answer(i18n.t("tasbeh_goal_reached", lang))
    await callback.answer()


@router.callback_query(lambda c: c.data == "tasbeh:reset")
async def tasbeh_reset(callback: CallbackQuery, i18n: I18n, lang: str, db_user, db) -> None:
    tasbeh = await get_or_create_tasbeh(db, db_user.id)
    tasbeh.count = 0
    await callback.message.edit_text(
        _tasbeh_text(i18n, lang, tasbeh.count, tasbeh.goal),
        reply_markup=tasbeh_keyboard(i18n, lang),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "tasbeh:goal")
async def tasbeh_goal_menu(callback: CallbackQuery, i18n: I18n, lang: str) -> None:
    await callback.message.answer(i18n.t("tasbeh_goal_choose", lang), reply_markup=tasbeh_goal_keyboard(i18n, lang))
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("tasbeh:goal:"))
async def tasbeh_goal_set(callback: CallbackQuery, i18n: I18n, lang: str, db_user, db, state: FSMContext) -> None:
    value = callback.data.split(":", 2)[2]
    if value == "custom":
        await callback.message.answer(i18n.t("tasbeh_goal_custom", lang))
        await state.set_state(TasbehStates.waiting_goal)
    else:
        tasbeh = await get_or_create_tasbeh(db, db_user.id)
        tasbeh.goal = int(value)
        tasbeh.count = 0
        await callback.message.answer(i18n.t("tasbeh_goal_saved", lang, value=value))
    await callback.answer()


@router.message(TasbehStates.waiting_goal, F.text)
async def tasbeh_goal_custom(message: Message, i18n: I18n, lang: str, db_user, db, state: FSMContext) -> None:
    try:
        value = int(message.text.strip())
    except ValueError:
        await message.answer(i18n.t("tasbeh_goal_invalid", lang))
        return
    tasbeh = await get_or_create_tasbeh(db, db_user.id)
    tasbeh.goal = value
    tasbeh.count = 0
    await state.clear()
    await message.answer(i18n.t("tasbeh_goal_saved", lang, value=value))
