from __future__ import annotations

from datetime import date, datetime, timedelta, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def parse_time_str(time_str: str) -> str:
    return time_str.split(" ")[0].strip()


def combine_date_time(target_date: date, time_str: str, timezone: str) -> datetime:
    hour, minute = [int(x) for x in time_str.split(":")]
    try:
        tz = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("UTC")
    return datetime(target_date.year, target_date.month, target_date.day, hour, minute, tzinfo=tz)


def apply_offset(time_str: str, offset_min: int, timezone: str, target_date: date) -> str:
    dt = combine_date_time(target_date, time_str, timezone)
    dt = dt + timedelta(minutes=offset_min)
    return dt.strftime("%H:%M")


def parse_hhmm_time(value: str) -> time:
    hour, minute = [int(x) for x in value.split(":")]
    return time(hour=hour, minute=minute)


def is_time_in_range(target: time, start: time, end: time) -> bool:
    if start == end:
        return False
    if start < end:
        return start <= target < end
    return target >= start or target < end
