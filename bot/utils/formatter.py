from __future__ import annotations

from datetime import date

from bot.utils.i18n import I18n
from bot.utils.time import apply_offset, parse_time_str


def format_prayer_times(
    i18n: I18n,
    lang: str,
    timings: dict[str, str],
    timezone: str,
    method_name: str,
    target_date: date,
    offset_min: int,
) -> str:
    rows = []
    items = [
        ("Fajr", "prayer_fajr"),
        ("Sunrise", "prayer_sunrise"),
        ("Dhuhr", "prayer_dhuhr"),
        ("Asr", "prayer_asr"),
        ("Maghrib", "prayer_maghrib"),
        ("Isha", "prayer_isha"),
    ]
    dhuhr_time = None
    for key, label_key in items:
        base_time = parse_time_str(timings[key])
        time_value = apply_offset(base_time, offset_min, timezone, target_date)
        rows.append((i18n.t(label_key, lang), time_value))
        if key == "Dhuhr":
            dhuhr_time = time_value

    name_width = max(len(name) for name, _ in rows)
    lines = [
        i18n.t("prayer_times_header", lang, date=target_date.strftime("%d-%m-%Y")),
        "",
    ]
    for name, time_value in rows:
        lines.append(f"{name:<{name_width}}  {time_value}")
    if target_date.weekday() == 4 and dhuhr_time:
        lines.append("")
        lines.append(i18n.t("prayer_times_jumuah", lang, time=dhuhr_time))
    lines.append("")
    lines.append(i18n.t("prayer_times_tz", lang, timezone=timezone))
    lines.append(i18n.t("prayer_times_method", lang, method=method_name))
    if offset_min:
        lines.append(i18n.t("prayer_times_offset", lang, offset=offset_min))
    return "\n".join(lines)


def format_weekly_prayer_times(
    i18n: I18n,
    lang: str,
    week_data: list[tuple[date, dict[str, str]]],
    timezone: str,
    offset_min: int,
) -> str:
    lines = [i18n.t("prayer_times_week_header", lang), ""]
    for target_date, timings in week_data:
        label = target_date.strftime("%d-%m-%Y")
        fajr = apply_offset(parse_time_str(timings["Fajr"]), offset_min, timezone, target_date)
        maghrib = apply_offset(parse_time_str(timings["Maghrib"]), offset_min, timezone, target_date)
        isha = apply_offset(parse_time_str(timings["Isha"]), offset_min, timezone, target_date)
        lines.append(f"{label}: Fajr {fajr} | Maghrib {maghrib} | Isha {isha}")
    lines.append("")
    lines.append(i18n.t("prayer_times_tz", lang, timezone=timezone))
    if offset_min:
        lines.append(i18n.t("prayer_times_offset", lang, offset=offset_min))
    return "\n".join(lines)


def format_reminder_text(i18n: I18n, prayer_key: str, lang: str) -> str:
    prayer_map = {
        "Fajr": i18n.t("prayer_fajr", lang),
        "Dhuhr": i18n.t("prayer_dhuhr", lang),
        "Asr": i18n.t("prayer_asr", lang),
        "Maghrib": i18n.t("prayer_maghrib", lang),
        "Isha": i18n.t("prayer_isha", lang),
    }
    prayer_name = prayer_map.get(prayer_key, prayer_key)
    return i18n.t("reminder_text", lang, prayer=prayer_name)
