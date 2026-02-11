from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import duas_keyboard
from bot.utils.duas import DUA_CATEGORIES, DUA_ITEMS
from bot.utils.i18n import I18n

router = Router()


def _dua_text(i18n: I18n, lang: str, index: int) -> str:
    dua = DUA_ITEMS[index]
    title = i18n.t(dua["title"], lang)
    text = i18n.t(dua["text"], lang)
    return f"<b>{title}</b>\n\n{text}"


def _category_name(i18n: I18n, lang: str, key: str) -> str:
    return i18n.t(f"dua_cat_{key}", lang)


@router.callback_query(lambda c: c.data == "menu:duas")
async def duas_menu(callback: CallbackQuery, i18n: I18n, lang: str) -> None:
    await callback.message.edit_text(
        _dua_text(i18n, lang, 0),
        reply_markup=duas_keyboard(i18n, lang, 0, len(DUA_ITEMS)),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("dua:idx:"))
async def duas_change(callback: CallbackQuery, i18n: I18n, lang: str) -> None:
    index = int(callback.data.split(":", 2)[2])
    await callback.message.edit_text(
        _dua_text(i18n, lang, index),
        reply_markup=duas_keyboard(i18n, lang, index, len(DUA_ITEMS)),
    )
    await callback.answer()


@router.message(Command("dua"))
async def dua_search(message: Message, i18n: I18n, lang: str) -> None:
    args = (message.text or "").split(maxsplit=1)
    if len(args) == 1:
        categories = ", ".join(_category_name(i18n, lang, key) for key in DUA_CATEGORIES)
        await message.answer(i18n.t("dua_usage", lang, categories=categories))
        return

    query = args[1].strip()
    if query.isdigit():
        index = int(query) - 1
        if index < 0 or index >= len(DUA_ITEMS):
            await message.answer(i18n.t("dua_not_found", lang))
            return
        await message.answer(_dua_text(i18n, lang, index))
        return

    normalized = query.lower()
    localized_map = {
        _category_name(i18n, lang, key).lower(): key for key in DUA_CATEGORIES
    }
    if normalized in DUA_CATEGORIES:
        matches = [
            (idx, item)
            for idx, item in enumerate(DUA_ITEMS)
            if item.get("category") == normalized
        ]
    elif normalized in localized_map:
        category_key = localized_map[normalized]
        matches = [
            (idx, item)
            for idx, item in enumerate(DUA_ITEMS)
            if item.get("category") == category_key
        ]
    else:
        matches = []
        for idx, item in enumerate(DUA_ITEMS):
            title = i18n.t(item["title"], lang).lower()
            text = i18n.t(item["text"], lang).lower()
            if normalized in title or normalized in text:
                matches.append((idx, item))

    if not matches:
        await message.answer(i18n.t("dua_not_found", lang))
        return

    lines = [i18n.t("dua_search_results", lang)]
    for idx, item in matches[:5]:
        title = i18n.t(item["title"], lang)
        lines.append(f"{idx + 1}. {title}")
    lines.append(i18n.t("dua_search_hint", lang))
    await message.answer("\n".join(lines))
