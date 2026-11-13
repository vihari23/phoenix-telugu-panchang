#!/usr/bin/env python3
"""Make every published Phoenix ICS VEVENT a timed 08:00–09:00 MST event.

Run after upstream calendar generation; applies to all *.ics in the output
directory, including full Panchang, festivals, observances, and the optional
personal feed. Source UID, summary, description, and any alarm components remain
intact. America/Phoenix observes UTC-07:00 year-round.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from icalendar import Calendar

PHOENIX_TZ = ZoneInfo("America/Phoenix")
EVENT_START = time(8, 0)
EVENT_END = time(9, 0)


def _phoenix_day(original: date | datetime) -> date:
    if isinstance(original, datetime):
        return (
            original.astimezone(PHOENIX_TZ).date()
            if original.tzinfo is not None
            else original.date()
        )
    if isinstance(original, date):
        return original
    raise ValueError(f"Unexpected ICS DTSTART value: {original!r}")


def _as_utc(day: date, clock: time) -> datetime:
    local = datetime.combine(day, clock, tzinfo=PHOENIX_TZ)
    return local.astimezone(timezone.utc)


def convert_ics_to_timed(path: Path) -> int:
    """Update all VEVENTs and verify calendar validity, UIDs and local times."""
    original_data = path.read_bytes()
    calendar = Calendar.from_ical(original_data)
    events = calendar.walk("VEVENT")
    source_uids = [str(event.get("UID", "")) for event in events]
    if any(not uid for uid in source_uids):
        raise ValueError(f"VEVENT with missing UID in {path.name}")
    source_summaries = [str(event.get("SUMMARY", "")) for event in events]
    source_descriptions = [str(event.get("DESCRIPTION", "")) for event in events]

    for event in events:
        original = event.decoded("DTSTART")
        day = _phoenix_day(original)
        # Drop any mutually exclusive duration so DTSTART+DTEND is canonical.
        for key in ("DTSTART", "DTEND", "DURATION"):
            event.pop(key, None)
        event.add("dtstart", _as_utc(day, EVENT_START))
        event.add("dtend", _as_utc(day, EVENT_END))

    encoded = calendar.to_ical()
    if not encoded.startswith(b"BEGIN:VCALENDAR") or b"END:VCALENDAR" not in encoded:
        raise ValueError(f"Invalid normalized ICS file: {path.name}")
    reparsed = Calendar.from_ical(encoded)
    after = reparsed.walk("VEVENT")
    if len(after) != len(events):
        raise ValueError(f"Event count changed in {path.name}")
    if [str(event.get("UID", "")) for event in after] != source_uids:
        raise ValueError(f"Event UIDs changed in {path.name}")
    if [str(event.get("SUMMARY", "")) for event in after] != source_summaries:
        raise ValueError(f"Event summaries changed in {path.name}")
    if [str(event.get("DESCRIPTION", "")) for event in after] != source_descriptions:
        raise ValueError(f"Event descriptions changed in {path.name}")

    for event in after:
        start = event.decoded("DTSTART")
        end = event.decoded("DTEND")
        if not isinstance(start, datetime) or not isinstance(end, datetime):
            raise ValueError(f"All-day event found in {path.name}")
        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError(f"Timezone missing for event in {path.name}")
        if start.astimezone(PHOENIX_TZ).time() != EVENT_START:
            raise ValueError(f"Event does not begin at 8:00 AM Phoenix in {path.name}")
        if end.astimezone(PHOENIX_TZ).time() != EVENT_END:
            raise ValueError(f"Event does not end at 9:00 AM Phoenix in {path.name}")
        if end - start != timedelta(hours=1):
            raise ValueError(f"Event duration is not one hour in {path.name}")

    path.write_bytes(encoded)
    return len(after)


def normalize_ics_directory(output_dir: Path) -> dict[str, int]:
    paths = sorted(output_dir.glob("*.ics"))
    if not paths:
        raise ValueError(f"No ICS feeds found in {output_dir}")
    counts = {}
    for path in paths:
        counts[path.name] = convert_ics_to_timed(path)
        print(f"Phoenix timed events 08:00–09:00: {path.name}: {counts[path.name]}")
    return counts
