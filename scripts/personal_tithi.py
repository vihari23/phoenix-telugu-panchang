"""Generate annual personal Telugu-tithi occurrences for Phoenix, without a Gregorian RRULE.

Event configuration is intentionally empty until the repository owner explicitly
chooses whether to publish the (publicly readable) personal event names and dates.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from icalendar import Calendar, Event

MAASAMS = {
    "Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana",
    "Bhadrapada", "Ashvina", "Kartika", "Margashira", "Pushya",
    "Magha", "Phalguna",
}
TITHIS = {
    "Pratipat", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi",
    "Pournami", "Amavasya",
}
PAKSHAMS = {"Shukla", "Krishna"}
ADHIKA_POLICIES = {"regular", "adhika", "both"}


def validate_events(config: dict) -> list[dict]:
    if not isinstance(config, dict) or not isinstance(config.get("events"), list):
        raise ValueError("Configuration must contain an events array")
    events = config["events"]
    seen = set()
    for item in events:
        if not isinstance(item, dict):
            raise ValueError("Personal events must be objects")
        event_id = item.get("id")
        if not isinstance(event_id, str) or not re.fullmatch(r"[a-z0-9-]{3,60}", event_id):
            raise ValueError("Every event needs a lowercase slug ID (3–60 characters)")
        if event_id in seen:
            raise ValueError(f"Duplicate event ID: {event_id}")
        seen.add(event_id)
        label = item.get("title")
        if not isinstance(label, str) or not (1 <= len(label.strip()) <= 100):
            raise ValueError(f"Event {event_id}: title must be 1–100 characters")
        if item.get("maasam") not in MAASAMS:
            raise ValueError(f"Event {event_id}: unknown Telugu maasam")
        if item.get("paksham") not in PAKSHAMS:
            raise ValueError(f"Event {event_id}: invalid paksham")
        if item.get("tithi") not in TITHIS:
            raise ValueError(f"Event {event_id}: invalid tithi")
        if item["tithi"] == "Pournami" and item["paksham"] != "Shukla":
            raise ValueError(f"Event {event_id}: Pournami must be Shukla")
        if item["tithi"] == "Amavasya" and item["paksham"] != "Krishna":
            raise ValueError(f"Event {event_id}: Amavasya must be Krishna")
        if item.get("adhika_policy", "regular") not in ADHIKA_POLICIES:
            raise ValueError(f"Event {event_id}: invalid Adhika policy")
    return events


def moon_month_matches(actual: str, event: dict) -> bool:
    expected = event["maasam"]
    policy = event.get("adhika_policy", "regular")
    if policy == "regular":
        return actual in (expected, f"Nija {expected}")
    if policy == "adhika":
        return actual == f"Adhika {expected}"
    return actual in (expected, f"Nija {expected}", f"Adhika {expected}")


def matches(event: dict, day: dict) -> bool:
    if not moon_month_matches(day["maasam"], event):
        return False
    if day["paksham"] != event["paksham"]:
        return False
    actual = day["tithi"]
    target = event["tithi"]
    if target == "Ekadashi":
        return actual.endswith(" Ekadashi") or actual == "Ekadashi"
    if target in ("Pournami", "Amavasya"):
        return actual == target
    return actual == f"{event['paksham']} {target}"


def load_days(path: Path) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("city") != "Phoenix" or raw.get("system") != "drik":
        raise ValueError("Expected Phoenix Drik day data")
    records = []
    for key, item in sorted(raw["days"].items()):
        d = item["day"]
        records.append({
            "date": datetime.strptime(key, "%Y%m%d").date().isoformat(),
            "maasam": d["maasam"],
            "paksham": d["paksham"],
            "tithi": d["tithi"]["name"],
        })
    return records


def find_dates(event: dict, records: list[dict]) -> list[dict]:
    """Match the tithi prevailing at Phoenix sunrise; take first of twin sunrise days."""
    hits = []
    previous = None
    for day in records:
        if not matches(event, day):
            continue
        current = date.fromisoformat(day["date"])
        if previous is not None and (current - previous).days == 1:
            continue
        hits.append(day)
        previous = current
    return hits


def build_ics(events: list[dict], records: list[dict]) -> bytes:
    calendar = Calendar()
    calendar.add("prodid", "-//Phoenix Telugu Panchang Personal Dates//EN")
    calendar.add("version", "2.0")
    calendar.add("x-wr-calname", "Personal Telugu Tithi — Phoenix")
    calendar.add("x-wr-timezone", "America/Phoenix")
    calendar.add("x-wr-caldesc", "Annual Telugu tithi events, computed using Phoenix sunrise")
    calendar.add("refresh-interval;value=duration", "PT12H")
    calendar.add("x-published-ttl", "PT12H")

    for item in events:
        for day in find_dates(item, records):
            start = date.fromisoformat(day["date"])
            event = Event()
            event.add("uid", f"personal-{item['id']}-{start.isoformat()}@phoenix-telugu-panchang")
            event.add("summary", item["title"].strip())
            event.add("dtstart", start)
            event.add("dtend", start + timedelta(days=1))
            event.add("dtstamp", datetime.now(timezone.utc))
            event.add("description", (
                f"Personal annual Telugu tithi event\\n"
                f"{day['maasam']} Maasam · {day['paksham']} Paksham · {day['tithi']}\\n"
                "Calculated for Phoenix sunrise. Review important religious observances "
                "and skipped/extended tithi conventions with your family tradition."
            ))
            calendar.add_component(event)
    return calendar.to_ical()


def generate_personal_feeds(day_data: Path, event_config: Path, output: Path) -> None:
    records = load_days(day_data)
    events = validate_events(json.loads(event_config.read_text(encoding="utf-8")))
    (output / "phoenix-day-index.json").write_text(
        json.dumps({"city": "Phoenix", "timezone": "America/Phoenix", "days": records},
                   ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    data = build_ics(events, records)
    target = output / "phoenix-personal.ics"
    target.write_bytes(data)
    if not data.startswith(b"BEGIN:VCALENDAR") or not data.rstrip().endswith(b"END:VCALENDAR"):
        raise ValueError("Personal ICS was not valid")
    print(f"Personal recurring tithi feed: {len(events)} configured events, "
          f"{data.count(b'BEGIN:VEVENT')} generated occurrences")
