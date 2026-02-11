from aiogram import Router
from aiogram.types import CallbackQuery

from bot.services.qibla import bearing_to_compass, qibla_bearing
from bot.utils.i18n import I18n

router = Router()


@router.callback_query(lambda c: c.data == "menu:qibla")
async def qibla_menu(callback: CallbackQuery, i18n: I18n, lang: str, db_user) -> None:
    if db_user.lat is None or db_user.lon is None:
        await callback.message.answer(i18n.t("location_missing", lang))
        await callback.answer()
        return
    bearing = qibla_bearing(db_user.lat, db_user.lon)
    compass = bearing_to_compass(bearing)
    map_url = (
        "https://www.google.com/maps/dir/?api=1"
        f"&origin={db_user.lat},{db_user.lon}"
        "&destination=21.4225,39.8262"
        "&travelmode=walking"
    )
    await callback.message.answer(
        "\n".join(
            [
                i18n.t("qibla_text", lang, degree=round(bearing), compass=compass),
                i18n.t("qibla_map_link", lang, url=map_url),
            ]
        )
    )
    await callback.answer()
