from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware

from bot.db.crud import get_or_create_user
from bot.utils.i18n import I18n


class I18nMiddleware(BaseMiddleware):
    def __init__(self, i18n: I18n, default_lang: str):
        self._i18n = i18n
        self._default_lang = default_lang

    @staticmethod
    def _extract_from_user(event: Any):
        if getattr(event, "from_user", None):
            return event.from_user
        for attr in (
            "message",
            "callback_query",
            "edited_message",
            "inline_query",
            "chosen_inline_result",
            "shipping_query",
            "pre_checkout_query",
            "my_chat_member",
            "chat_member",
            "chat_join_request",
        ):
            obj = getattr(event, attr, None)
            if obj is not None and getattr(obj, "from_user", None):
                return obj.from_user
        return None

    @staticmethod
    def _map_language(language_code: str | None, default_lang: str) -> str:
        if not language_code:
            return default_lang
        code = language_code.lower()
        if code.startswith("ru"):
            return "ru"
        if code.startswith("en"):
            return "en"
        if code.startswith("uz"):
            return "uz"
        return default_lang

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        lang = self._default_lang
        data["db_user"] = None
        from_user = self._extract_from_user(event)
        if from_user is not None and "db" in data:
            default_lang = self._map_language(from_user.language_code, self._default_lang)
            last = getattr(from_user, "last_name", None)
            full_name = f"{from_user.first_name} {last}".strip() if last else from_user.first_name
            user = await get_or_create_user(
                session=data["db"],
                telegram_id=from_user.id,
                username=from_user.username,
                full_name=full_name,
                default_lang=default_lang,
            )
            data["db_user"] = user
            if user.lang:
                lang = user.lang
        data["lang"] = lang
        return await handler(event, data)
