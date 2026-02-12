from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

from bot.keyboards.inline import main_menu_keyboard
from bot.utils.i18n import I18n

router = Router()

MENU_BUTTON_TEXTS = {"🏠 Menyu", "🏠 Меню", "🏠 Menu"}


def _admin_contact_text(i18n: I18n, lang: str, settings) -> str:
    admin_username = getattr(settings, "ADMIN_USERNAME", "") if settings else ""
    if admin_username:
        return i18n.t("help_admin", lang, admin=admin_username)
    admin_ids = getattr(settings, "admin_ids", []) if settings else []
    if not admin_ids:
        return i18n.t("help_admin_not_set", lang)
    admin_links = [f"<a href=\"tg://user?id={admin_id}\">Admin</a>" for admin_id in admin_ids]
    return i18n.t("help_admin", lang, admin=", ".join(admin_links))


def _help_text(i18n: I18n, lang: str, settings) -> str:
    return "\n\n".join(
        [
            i18n.t("help_text", lang),
            i18n.t("help_commands", lang),
            _admin_contact_text(i18n, lang, settings),
        ]
    )


@router.message(Command("menu"))
async def menu_command(message: Message, i18n: I18n, lang: str) -> None:
    await message.answer(i18n.t("main_menu", lang), reply_markup=main_menu_keyboard(i18n, lang))


@router.message(F.text.in_(MENU_BUTTON_TEXTS))
async def menu_button_text(message: Message, i18n: I18n, lang: str) -> None:
    await message.answer(i18n.t("main_menu", lang), reply_markup=main_menu_keyboard(i18n, lang))


@router.message(Command("back"))
async def back_command(message: Message, i18n: I18n, lang: str) -> None:
    await message.answer(i18n.t("main_menu", lang), reply_markup=main_menu_keyboard(i18n, lang))


@router.message(Command("help"))
async def help_command(message: Message, i18n: I18n, lang: str, settings) -> None:
    await message.answer(
        _help_text(i18n, lang, settings),
        reply_markup=main_menu_keyboard(i18n, lang),
    )


@router.callback_query(lambda c: c.data == "menu:help")
async def help_menu(callback: CallbackQuery, i18n: I18n, lang: str, settings) -> None:
    try:
        await callback.message.edit_text(
            _help_text(i18n, lang, settings),
            reply_markup=main_menu_keyboard(i18n, lang),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise
    await callback.answer()


@router.callback_query(lambda c: c.data == "menu:back")
async def back_menu(callback: CallbackQuery, i18n: I18n, lang: str) -> None:
    try:
        await callback.message.edit_text(
            i18n.t("main_menu", lang),
            reply_markup=main_menu_keyboard(i18n, lang),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise
    await callback.answer()
