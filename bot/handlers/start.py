from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from bot.db.crud import get_or_create_user, update_user_lang
from bot.keyboards.inline import language_keyboard, main_menu_keyboard
from bot.utils.i18n import I18n

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, i18n: I18n, lang: str) -> None:
    text = i18n.t("welcome", lang)
    await message.answer(text, reply_markup=language_keyboard())


@router.callback_query(lambda c: c.data and c.data.startswith("lang:"))
async def set_language_handler(
    callback: CallbackQuery,
    i18n: I18n,
    lang: str,
    db,
    settings=None,
    db_user=None,
) -> None:
    new_lang = callback.data.split(":", 1)[1]
    user = db_user
    if user is None:
        user = await get_or_create_user(
            session=db,
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            default_lang=getattr(settings, "DEFAULT_LANG", "uz"),
        )
    await update_user_lang(db, user.id, new_lang)
    await callback.message.edit_text(i18n.t("language_set", new_lang))
    await callback.message.answer(
        i18n.t("main_menu", new_lang),
        reply_markup=main_menu_keyboard(i18n, new_lang),
    )
    await callback.answer()
