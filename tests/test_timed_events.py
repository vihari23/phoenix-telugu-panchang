"""Verify all published feeds retain event identity and become timed in Phoenix."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zoneinfo import ZoneInfo

from icalendar import Calendar, Event

from normalize_timed_events import convert_ics_to_timed, normalize_ics_directory

PHOENIX = ZoneInfo("America/Phoenix")


def write_fixture(path: Path, start: date | datetime, name: str = "Telugu festival") -> None:
    calendar = Calendar()
    calendar.add("version", "2.0")
    calendar.add("prodid", "-//Phoenix Timed ICS Test//EN")
    item = Event()
    item.add("uid", f"stable-{name.replace(' ', '-')}@phoenix.example")
    item.add("summary", name)
    item.add("description", "A tithi and nakshatra description with timing details")
    item.add("dtstamp", datetime(2026, 11, 12, tzinfo=timezone.utc))
    item.add("dtstart", start)
    if isinstance(start, datetime):
        item.add("dtend", start + timedelta(hours=2))
    else:
        item.add("dtend", start + timedelta(days=1))
    calendar.add_component(item)
    path.write_bytes(calendar.to_ical())


class TimedPhoenixTest(unittest.TestCase):
    def test_all_day_festival_becomes_one_hour(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "phoenix-drik-festivals.ics"
            write_fixture(path, date(2027, 7, 19))
            self.assertEqual(convert_ics_to_timed(path), 1)
            event = Calendar.from_ical(path.read_bytes()).walk("VEVENT")[0]
            self.assertEqual(event.decoded("DTSTART"), datetime(2027, 7, 19, 15, tzinfo=timezone.utc))
            self.assertEqual(event.decoded("DTEND"), datetime(2027, 7, 19, 16, tzinfo=timezone.utc))
            self.assertEqual(str(event.get("SUMMARY")), "Telugu festival")
            self.assertEqual(str(event.get("UID")), "stable-Telugu-festival@phoenix.example")
            self.assertIn("nakshatra", str(event.get("DESCRIPTION")))

    def test_existing_timed_event_resets_to_phoenix_8am(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "phoenix-drik.ics"
            write_fixture(path, datetime(2027, 2, 2, 23, 30, tzinfo=timezone.utc))
            convert_ics_to_timed(path)
            event = Calendar.from_ical(path.read_bytes()).walk("VEVENT")[0]
            self.assertEqual(event.decoded("DTSTART"), datetime(2027, 2, 2, 15, tzinfo=timezone.utc))
            self.assertEqual(event.decoded("DTEND"), datetime(2027, 2, 2, 16, tzinfo=timezone.utc))

    def test_all_four_feeds_are_converted_and_empty_remains_valid(self):
        with TemporaryDirectory() as temp:
            base = Path(temp)
            feeds = (
                "phoenix-drik.ics",
                "phoenix-drik-festivals.ics",
                "phoenix-drik-observances.ics",
            )
            for name in feeds:
                write_fixture(base / name, date(2026, 11, 12), name)
            empty = Calendar()
            empty.add("version", "2.0")
            empty.add("prodid", "-//Phoenix Empty Personal ICS//EN")
            (base / "phoenix-personal.ics").write_bytes(empty.to_ical())
            counts = normalize_ics_directory(base)
            self.assertEqual(counts, {**dict.fromkeys(feeds, 1), "phoenix-personal.ics": 0})
            for name in feeds:
                event = Calendar.from_ical((base / name).read_bytes()).walk("VEVENT")[0]
                self.assertEqual(event.decoded("DTSTART").astimezone(PHOENIX).hour, 8)
                self.assertEqual(event.decoded("DTEND").astimezone(PHOENIX).hour, 9)
            self.assertEqual(
                len(Calendar.from_ical((base / "phoenix-personal.ics").read_bytes()).walk("VEVENT")),
                0,
            )

    def test_different_seasons_both_8am_local(self):
        with TemporaryDirectory() as temp:
            for d in (date(2027, 1, 15), date(2027, 6, 15)):
                path = Path(temp) / f"{d}.ics"
                write_fixture(path, d)
                convert_ics_to_timed(path)
                start = Calendar.from_ical(path.read_bytes()).walk("VEVENT")[0].decoded("DTSTART")
                self.assertEqual(start.astimezone(PHOENIX).strftime("%H:%M"), "08:00")
                self.assertEqual(start.hour, 15)


if __name__ == "__main__":
    unittest.main()
