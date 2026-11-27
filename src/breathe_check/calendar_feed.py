"""Calendar feeds: tomorrow's best run window, as an event in your calendar.

    uv run python -m breathe_check.calendar_feed

For each city, writes data/public/calendar/<city>.ics, an iCalendar feed (RFC 5545)
that Google Calendar, Apple Calendar and Outlook can subscribe to. Each evening's
forecast adds one event for the next day's best 2-hour window. Past events are kept
for 14 days (in data/public/calendar/<city>.json), so your calendar shows a short
history instead of only tomorrow.

Times are written in UTC (the "Z" suffix), which every calendar app understands,
and shown to you in your own time zone.
"""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from breathe_check import settings
from breathe_check.standards import PM25_PER_CIGARETTE

APP_URL = "https://breathe-check-flax.vercel.app"
FORECASTS = settings.DATA_DIR / "public" / "forecast"
CALENDARS = settings.DATA_DIR / "public" / "calendar"
KEEP_DAYS = 14
IST = timedelta(hours=5, minutes=30)


def hour_label(h: int) -> str:
    h %= 24
    if h == 0:
        return "midnight"
    if h == 12:
        return "noon"
    return f"{h % 12} {'am' if h < 12 else 'pm'}"


def event_for(forecast: dict) -> dict | None:
    """One calendar event for a city's best window, or None if there isn't one."""
    best = forecast.get("best_window")
    if not best:
        return None
    day = forecast["for_date"]
    start_ist = datetime.fromisoformat(f"{day}T00:00:00") + timedelta(hours=best["start"])
    end_ist = datetime.fromisoformat(f"{day}T00:00:00") + timedelta(hours=best["end"])
    pm = best["pm25"]
    cigs = pm * (best["end"] - best["start"]) / 24 / PM25_PER_CIGARETTE
    title = (
        f"Best time to be outside: {hour_label(best['start'])} to {hour_label(best['end'])} "
        f"({best['category']}, about {round(pm)} µg/m³)"
    )
    lines = [
        f"{forecast['name']}, {day}: the cleanest 2 hours tomorrow, by Breathe Check's forecast.",
        f"PM2.5 about {round(pm)} µg/m³ ({best['category']}). {best['advice']}",
        f"Two hours outside at this level is like {cigs:.1f} of a cigarette "
        "(Berkeley Earth's rough rule of thumb, not a medical measure).",
    ]
    worst = next((h for h in forecast["hours"] if h["hour"] == forecast.get("worst_hour")), None)
    if worst and worst["mid"] > pm * 1.2:
        lines.append(
            f"Worst hour: around {hour_label(worst['hour'])}, about {round(worst['mid'])} µg/m³."
        )
    smoke = forecast.get("smoke")
    if smoke and smoke.get("level") == "Likely":
        lines.append(f"Crop-fire smoke likely: {smoke['why']}")
    lines.append(f"Hour by hour: {APP_URL}/?city={forecast['city']}")
    lines.append("Not medical advice.")
    return {
        "uid": f"{forecast['city']}-{day}@breathe-check",
        "date": day,
        "start_utc": (start_ist - IST).strftime("%Y%m%dT%H%M%SZ"),
        "end_utc": (end_ist - IST).strftime("%Y%m%dT%H%M%SZ"),
        "title": title,
        "description": "\n".join(lines),
        "url": f"{APP_URL}/?city={forecast['city']}",
    }


def escape(text: str) -> str:
    """Escape text the way iCalendar wants it (RFC 5545, section 3.3.11)."""
    backslash = "\\"
    for ch in (backslash, ";", ","):
        text = text.replace(ch, backslash + ch)
    return text.replace("\n", backslash + "n")


def fold(line: str) -> str:
    """Lines longer than 75 bytes are split, with each extra part starting with a space."""
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return line
    parts, current = [], b""
    for ch in line:
        b = ch.encode("utf-8")
        limit = 75 if not parts else 74
        if len(current) + len(b) > limit:
            parts.append(current.decode("utf-8"))
            current = b""
        current += b
    parts.append(current.decode("utf-8"))
    return "\r\n ".join(parts)


def render(city_name: str, city: str, events: list[dict], now: datetime) -> str:
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    about = f"Best 2 hours to be outside each day in {city_name}, by PM2.5 forecast."
    out = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Breathe Check//Run window//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{escape(f'Breathe Check: {city_name}')}",
        f"X-WR-CALDESC:{escape(about)}",
        "X-WR-TIMEZONE:Asia/Kolkata",
        "REFRESH-INTERVAL;VALUE=DURATION:PT6H",
        "X-PUBLISHED-TTL:PT6H",
    ]
    for e in sorted(events, key=lambda e: e["date"]):
        out += [
            "BEGIN:VEVENT",
            f"UID:{e['uid']}",
            f"DTSTAMP:{stamp}",
            f"DTSTART:{e['start_utc']}",
            f"DTEND:{e['end_utc']}",
            f"SUMMARY:{escape(e['title'])}",
            f"DESCRIPTION:{escape(e['description'])}",
            f"URL:{e['url']}",
            "TRANSP:TRANSPARENT",  # doesn't mark you as busy
            "END:VEVENT",
        ]
    out.append("END:VCALENDAR")
    return "\r\n".join(fold(line) for line in out) + "\r\n"


def update_city(forecast: dict, now: datetime, folder: Path = CALENDARS) -> Path:
    """Add tomorrow's event to a city's history, drop events older than 14 days, write the feed."""
    folder.mkdir(parents=True, exist_ok=True)
    history_path = folder / f"{forecast['city']}.json"
    history = json.loads(history_path.read_text()) if history_path.exists() else []
    by_date = {e["date"]: e for e in history}
    event = event_for(forecast)
    if event:
        by_date[event["date"]] = event  # a later forecast for the same day replaces the earlier one
    cutoff = (now + IST - timedelta(days=KEEP_DAYS)).date().isoformat()
    kept = [e for d, e in sorted(by_date.items()) if d >= cutoff]
    history_path.write_text(json.dumps(kept, indent=1))
    path = folder / f"{forecast['city']}.ics"
    path.write_text(render(forecast["name"], forecast["city"], kept, now), newline="")
    return path


def main() -> None:
    now = datetime.now(UTC)
    written = 0
    for file in sorted(FORECASTS.glob("*.json")):
        if file.name == "index.json":
            continue
        update_city(json.loads(file.read_text()), now)
        written += 1
    print(f"[{datetime.now():%H:%M:%S}] wrote {written} calendar feeds to {CALENDARS}")


if __name__ == "__main__":
    main()
