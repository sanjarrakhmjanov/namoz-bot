from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiogram.types import FSInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from bot.config import Settings
from bot.db.crud import add_reminder_event
from bot.db.models import Reminder, User
from bot.services.aladhan import AladhanClient
from bot.utils.formatter import format_reminder_text
from bot.utils.time import combine_date_time, is_time_in_range, parse_hhmm_time, parse_time_str
from bot.utils.i18n import I18n


logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(
        self,
        bot,
        settings: Settings,
        aladhan: AladhanClient,
        i18n: I18n,
        sessionmaker: async_sessionmaker,
    ) -> None:
        self._bot = bot
        self._settings = settings
        self._aladhan = aladhan
        self._i18n = i18n
        self._sessionmaker = sessionmaker
        self._scheduler = AsyncIOScheduler()
        self._job_keys: set[str] = set()

    async def start(self) -> None:
        self._scheduler.add_job(self.refresh_all, "interval", minutes=self._settings.SCHEDULER_REFRESH_MIN)
        self._scheduler.add_job(self.check_hijri_reminders, "interval", hours=12)
        self._scheduler.start()
        await self.refresh_all()

    async def refresh_all(self) -> None:
        async with self._sessionmaker() as session:
            result = await session.execute(
                select(User, Reminder).join(Reminder, Reminder.user_id == User.id)
            )
            for user, reminder in result.all():
                if not reminder.enabled:
                    continue
                if not self._user_has_location(user):
                    continue
                await self._schedule_for_user(user, reminder)
            ramadan_result = await session.execute(select(User).where(User.ramadan_on == True))
            ramadan_users = ramadan_result.scalars().all()
        for user in ramadan_users:
            if not self._user_has_location(user):
                continue
            await self._schedule_ramadan_for_user(user)

    async def _schedule_for_user(self, user: User, reminder: Reminder) -> None:
        today = date.today()
        for day_offset in (0, 1):
            target_date = today + timedelta(days=day_offset)
            try:
                data = await self._get_times_for_user(user, target_date)
            except Exception:
                logger.exception("Failed to fetch prayer times for reminders")
                continue
            timings = data["data"]["timings"]
            for prayer_key in ("Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"):
                if not self._is_prayer_enabled(reminder, prayer_key):
                    continue
                time_str = parse_time_str(timings[prayer_key])
                run_dt = combine_date_time(target_date, time_str, user.timezone or self._settings.DEFAULT_TIMEZONE)
                run_dt = run_dt + timedelta(minutes=reminder.offset_min + user.time_offset_min)
                if run_dt <= datetime.now(run_dt.tzinfo):
                    continue
                if self._is_in_silent_hours(user, run_dt):
                    continue
                job_id = f"{user.telegram_id}:{prayer_key}:{target_date.isoformat()}"
                if job_id in self._job_keys:
                    continue
                self._job_keys.add(job_id)
                self._scheduler.add_job(
                    self._send_reminder,
                    trigger=DateTrigger(run_date=run_dt),
                    id=job_id,
                    args=[job_id, user.telegram_id, prayer_key, user.lang],
                    replace_existing=True,
                )

    async def _get_times_for_user(self, user: User, target_date: date) -> dict:
        if user.city:
            return await self._aladhan.get_prayer_times_by_city(
                city=user.city,
                country=self._settings.DEFAULT_COUNTRY,
                method=self._settings.ALADHAN_METHOD,
                target_date=target_date,
            )
        return await self._aladhan.get_prayer_times_by_coords(
            lat=user.lat,
            lon=user.lon,
            method=self._settings.ALADHAN_METHOD,
            target_date=target_date,
        )

    async def _send_reminder(self, job_id: str, telegram_id: int, prayer_key: str, lang: str) -> None:
        try:
            if await self._should_skip_reminder(telegram_id):
                return
            text = format_reminder_text(self._i18n, prayer_key, lang)
            await self._send_with_optional_audio(telegram_id, text)
            await self._log_event(telegram_id, "prayer", prayer_key)
        except Exception:
            logger.exception("Failed to send reminder to %s", telegram_id)
        finally:
            self._job_keys.discard(job_id)

    async def _send_ramadan_reminder(
        self, job_id: str, telegram_id: int, reminder_key: str, lang: str
    ) -> None:
        try:
            if await self._should_skip_reminder(telegram_id):
                return
            text = self._i18n.t(reminder_key, lang)
            await self._bot.send_message(telegram_id, text)
            await self._log_event(telegram_id, "ramadan", reminder_key)
        except Exception:
            logger.exception("Failed to send ramadan reminder to %s", telegram_id)
        finally:
            self._job_keys.discard(job_id)

    async def schedule_test_reminder(self, telegram_id: int, lang: str) -> datetime:
        async with self._sessionmaker() as session:
            result = await session.execute(select(User).where(User.telegram_id == telegram_id))
            user = result.scalar_one_or_none()
        timezone = user.timezone if user and user.timezone else self._settings.DEFAULT_TIMEZONE
        run_dt = datetime.now(tz=self._get_timezone(timezone)) + timedelta(minutes=1)
        job_id = f"test:{telegram_id}:{int(run_dt.timestamp())}"
        self._job_keys.add(job_id)
        self._scheduler.add_job(
            self._send_test_reminder,
            trigger=DateTrigger(run_date=run_dt),
            id=job_id,
            args=[job_id, telegram_id, lang],
            replace_existing=True,
        )
        return run_dt

    async def _send_test_reminder(self, job_id: str, telegram_id: int, lang: str) -> None:
        try:
            if await self._should_skip_reminder(telegram_id):
                return
            text = self._i18n.t("reminder_test_text", lang)
            await self._bot.send_message(telegram_id, text)
        except Exception:
            logger.exception("Failed to send test reminder to %s", telegram_id)
        finally:
            self._job_keys.discard(job_id)

    async def check_hijri_reminders(self) -> None:
        async with self._sessionmaker() as session:
            result = await session.execute(select(User).where(User.hijri_reminder_on == True))
            users = result.scalars().all()

        for user in users:
            try:
                timezone = user.timezone or self._settings.DEFAULT_TIMEZONE
                tz = self._get_timezone(timezone)
                today = datetime.now(tz).date()
                data = await self._aladhan.get_hijri_date(today)
                hijri = data["data"]["hijri"]
                month = int(hijri["month"]["number"])
                year = int(hijri["year"])
                if user.last_hijri_month == month and user.last_hijri_year == year:
                    continue
                await self._bot.send_message(
                    user.telegram_id,
                    self._i18n.t(
                        "hijri_month_reminder",
                        user.lang,
                        month=hijri["month"]["en"],
                        year=year,
                    ),
                )
                async with self._sessionmaker() as session:
                    await session.execute(
                        User.__table__.update()
                        .where(User.id == user.id)
                        .values(last_hijri_month=month, last_hijri_year=year)
                    )
                    await session.commit()
            except Exception:
                logger.exception("Failed to send hijri reminder to %s", user.telegram_id)

    @staticmethod
    def _is_prayer_enabled(reminder: Reminder, prayer_key: str) -> bool:
        mapping = {
            "Fajr": reminder.fajr_on,
            "Dhuhr": reminder.dhuhr_on,
            "Asr": reminder.asr_on,
            "Maghrib": reminder.maghrib_on,
            "Isha": reminder.isha_on,
        }
        return mapping.get(prayer_key, False)

    @staticmethod
    def _user_has_location(user: User) -> bool:
        return bool(user.city or (user.lat is not None and user.lon is not None))

    def remove_jobs_for_user(self, telegram_id: int) -> None:
        jobs = [job for job in self._scheduler.get_jobs() if job.id.startswith(f"{telegram_id}:")]
        for job in jobs:
            self._scheduler.remove_job(job.id)
            self._job_keys.discard(job.id)

    def remove_ramadan_jobs_for_user(self, telegram_id: int) -> None:
        prefix = f"{telegram_id}:ramadan:"
        jobs = [job for job in self._scheduler.get_jobs() if job.id.startswith(prefix)]
        for job in jobs:
            self._scheduler.remove_job(job.id)
            self._job_keys.discard(job.id)

    async def _schedule_ramadan_for_user(self, user: User) -> None:
        today = date.today()
        for day_offset in (0, 1):
            target_date = today + timedelta(days=day_offset)
            try:
                data = await self._get_times_for_user(user, target_date)
            except Exception:
                logger.exception("Failed to fetch prayer times for ramadan reminders")
                continue
            timings = data["data"]["timings"]
            timezone = data["data"]["meta"]["timezone"]
            items = [
                ("ramadan_suhoor_reminder", "Fajr", user.suhoor_offset_min),
                ("ramadan_iftar_reminder", "Maghrib", user.iftar_offset_min),
            ]
            for reminder_key, prayer_key, offset in items:
                time_str = parse_time_str(timings[prayer_key])
                run_dt = combine_date_time(target_date, time_str, timezone)
                run_dt = run_dt + timedelta(minutes=offset + user.time_offset_min)
                if run_dt <= datetime.now(run_dt.tzinfo):
                    continue
                if self._is_in_silent_hours(user, run_dt):
                    continue
                job_id = f"{user.telegram_id}:ramadan:{reminder_key}:{target_date.isoformat()}"
                if job_id in self._job_keys:
                    continue
                self._job_keys.add(job_id)
                self._scheduler.add_job(
                    self._send_ramadan_reminder,
                    trigger=DateTrigger(run_date=run_dt),
                    id=job_id,
                    args=[job_id, user.telegram_id, reminder_key, user.lang],
                    replace_existing=True,
                )

    def _is_in_silent_hours(self, user: User, run_dt: datetime) -> bool:
        if not user.silent_start or not user.silent_end:
            return False
        try:
            start = parse_hhmm_time(user.silent_start)
            end = parse_hhmm_time(user.silent_end)
        except ValueError:
            return False
        return is_time_in_range(run_dt.time(), start, end)

    async def _should_skip_reminder(self, telegram_id: int) -> bool:
        async with self._sessionmaker() as session:
            result = await session.execute(select(User).where(User.telegram_id == telegram_id))
            user = result.scalar_one_or_none()
        if not user:
            return False
        timezone = user.timezone or self._settings.DEFAULT_TIMEZONE
        now = datetime.now(self._get_timezone(timezone))
        return self._is_in_silent_hours(user, now)

    async def is_in_silent_hours(self, telegram_id: int) -> bool:
        return await self._should_skip_reminder(telegram_id)

    async def _send_with_optional_audio(self, telegram_id: int, text: str) -> None:
        audio_file = self._settings.ADHAN_AUDIO_FILE
        audio_url = self._settings.ADHAN_AUDIO_URL
        if audio_file:
            await self._bot.send_audio(telegram_id, FSInputFile(audio_file), caption=text)
            return
        if audio_url:
            await self._bot.send_audio(telegram_id, audio_url, caption=text)
            return
        await self._bot.send_message(telegram_id, text)

    async def _log_event(self, telegram_id: int, event_type: str, prayer_key: str | None) -> None:
        async with self._sessionmaker() as session:
            result = await session.execute(select(User).where(User.telegram_id == telegram_id))
            user = result.scalar_one_or_none()
            if not user:
                return
            await add_reminder_event(session, user.id, event_type, prayer_key)
            await session.commit()

    @staticmethod
    def _get_timezone(timezone: str) -> ZoneInfo:
        try:
            return ZoneInfo(timezone)
        except ZoneInfoNotFoundError:
            return ZoneInfo("UTC")
