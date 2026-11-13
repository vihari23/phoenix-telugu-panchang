#!/usr/bin/env python3
"""Build rolling Phoenix-local Telugu Panchang ICS feeds from Astro Chaganti."""
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from telugu_panchangam.cities import CITIES
from telugu_panchangam.generate import default_feed_window, generate_feeds
from telugu_panchangam.models.panchangam_day import Location

from personal_tithi import generate_personal_feeds

CITY = "Phoenix"
TIMEZONE = "America/Phoenix"
OUTPUT = Path(__file__).resolve().parents[1] / "_site"


def main() -> None:
    if not any(city.name == CITY for city in CITIES):
        CITIES.append(
            Location(
                CITY,
                lat=33.4484,
                lon=-112.0740,
                timezone=TIMEZONE,
                alt=331,
            )
        )

    today = datetime.now(ZoneInfo(TIMEZONE)).date()
    start, end = default_feed_window(today)
    expected = (end - start).days + 1
    OUTPUT.mkdir(exist_ok=True, parents=True)
    generate_feeds(
        output_dir=str(OUTPUT),
        start=start,
        end=end,
        systems=["drik"],
        city_names=[CITY],
    )

    generate_personal_feeds(
        day_data=OUTPUT / 'phoenix-drik.days-v1.json',
        event_config=Path(__file__).resolve().parents[1] / 'data' / 'personal-events.json',
        output=OUTPUT,
    )

    feed_names = (
        "phoenix-drik.ics",
        "phoenix-drik-festivals.ics",
        "phoenix-drik-observances.ics",
    )
    for name in feed_names:
        data = (OUTPUT / name).read_bytes()
        if not data.startswith(b"BEGIN:VCALENDAR") or b"END:VCALENDAR" not in data:
            raise RuntimeError(f"Invalid ICS: {name}")
        print(f"{name}: {len(data):,} bytes")

    daily = (OUTPUT / feed_names[0]).read_bytes()
    count = daily.count(b"BEGIN:VEVENT")
    if count != expected:
        raise RuntimeError(f"Expected {expected} daily events, found {count}")
    if b"Phoenix" not in daily:
        raise RuntimeError("Phoenix not present in calendar name")
    for json_file in OUTPUT.glob("*.json"):
        if json_file.name != "phoenix-day-index.json":
            json_file.unlink()
    print(f"Validated {count} Phoenix-local days, {start} through {end}")


if __name__ == "__main__":
    main()
