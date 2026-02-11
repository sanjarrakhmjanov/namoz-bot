from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Reminder, ReminderEvent, Tasbeh, User


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    default_lang: str,
) -> User:
    user = await get_user_by_telegram_id(session, telegram_id)
    if user:
        if username and user.username != username:
            user.username = username
        return user

    user = User(telegram_id=telegram_id, username=username, lang=default_lang)
    session.add(user)
    await session.flush()
    return user


async def update_user_lang(session: AsyncSession, user_id: int, lang: str) -> None:
    await session.execute(update(User).where(User.id == user_id).values(lang=lang))


async def update_user_city(session: AsyncSession, user_id: int, city: str, timezone: str) -> None:
    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(city=city, lat=None, lon=None, timezone=timezone)
    )


async def update_user_coords(
    session: AsyncSession, user_id: int, lat: float, lon: float, timezone: str
) -> None:
    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(city=None, lat=lat, lon=lon, timezone=timezone)
    )


async def update_user_time_offset(session: AsyncSession, user_id: int, offset_min: int) -> None:
    await session.execute(
        update(User).where(User.id == user_id).values(time_offset_min=offset_min)
    )


async def update_user_silent_hours(
    session: AsyncSession, user_id: int, silent_start: str | None, silent_end: str | None
) -> None:
    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(silent_start=silent_start, silent_end=silent_end)
    )


async def update_user_hijri_reminder(session: AsyncSession, user_id: int, enabled: bool) -> None:
    await session.execute(
        update(User).where(User.id == user_id).values(hijri_reminder_on=enabled)
    )


async def update_user_hijri_month(session: AsyncSession, user_id: int, month: int, year: int) -> None:
    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(last_hijri_month=month, last_hijri_year=year)
    )


async def update_user_ramadan(session: AsyncSession, user_id: int, enabled: bool) -> None:
    await session.execute(
        update(User).where(User.id == user_id).values(ramadan_on=enabled)
    )


async def update_user_ramadan_offsets(
    session: AsyncSession, user_id: int, suhoor_offset_min: int, iftar_offset_min: int
) -> None:
    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(suhoor_offset_min=suhoor_offset_min, iftar_offset_min=iftar_offset_min)
    )


async def get_or_create_reminders(session: AsyncSession, user_id: int) -> Reminder:
    result = await session.execute(select(Reminder).where(Reminder.user_id == user_id))
    reminder = result.scalar_one_or_none()
    if reminder:
        return reminder
    reminder = Reminder(user_id=user_id)
    session.add(reminder)
    await session.flush()
    return reminder


async def get_or_create_tasbeh(session: AsyncSession, user_id: int) -> Tasbeh:
    result = await session.execute(select(Tasbeh).where(Tasbeh.user_id == user_id))
    tasbeh = result.scalar_one_or_none()
    if tasbeh:
        return tasbeh
    tasbeh = Tasbeh(user_id=user_id)
    session.add(tasbeh)
    await session.flush()
    return tasbeh


async def list_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User))
    return list(result.scalars().all())


async def get_admin_stats(session: AsyncSession) -> dict:
    total_users = await session.scalar(select(func.count(User.id)))
    reminders_on = await session.scalar(
        select(func.count(Reminder.id)).where(Reminder.enabled == True)  # noqa: E712
    )
    top_cities_result = await session.execute(
        select(User.city, func.count(User.id))
        .where(User.city.is_not(None))
        .group_by(User.city)
        .order_by(func.count(User.id).desc())
        .limit(5)
    )
    top_cities = [(row[0], row[1]) for row in top_cities_result.all()]
    return {
        "total_users": total_users or 0,
        "reminders_on": reminders_on or 0,
        "top_cities": top_cities,
    }


async def add_reminder_event(
    session: AsyncSession, user_id: int, event_type: str, prayer_key: str | None
) -> None:
    session.add(ReminderEvent(user_id=user_id, event_type=event_type, prayer_key=prayer_key))


async def get_weekly_reminder_stats(session: AsyncSession) -> list[tuple[date, int]]:
    start_date = date.today() - timedelta(days=6)
    result = await session.execute(
        select(func.date(ReminderEvent.sent_at), func.count(ReminderEvent.id))
        .where(ReminderEvent.sent_at >= start_date)
        .group_by(func.date(ReminderEvent.sent_at))
        .order_by(func.date(ReminderEvent.sent_at))
    )
    rows = []
    for day_value, count in result.all():
        if isinstance(day_value, str):
            day_value = date.fromisoformat(day_value)
        rows.append((day_value, count))
    return rows
