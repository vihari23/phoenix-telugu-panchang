"""Deterministic tests for personal annual tithi recurrence logic."""
import json
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from icalendar import Calendar

from personal_tithi import (
    build_ics, find_dates, generate_personal_feeds,
    matches, validate_events,
)

SAMPLE = {
    "id": "family-anniversary",
    "title": "Family anniversary",
    "maasam": "Kartika",
    "paksham": "Shukla",
    "tithi": "Panchami",
    "adhika_policy": "regular",
}
DAYS = [
    {"date": "2026-11-10", "maasam": "Kartika", "paksham": "Shukla", "tithi": "Shukla Panchami"},
    {"date": "2026-11-11", "maasam": "Kartika", "paksham": "Shukla", "tithi": "Shukla Panchami"},
    {"date": "2027-10-30", "maasam": "Nija Kartika", "paksham": "Shukla", "tithi": "Shukla Panchami"},
    {"date": "2027-09-30", "maasam": "Adhika Kartika", "paksham": "Shukla", "tithi": "Shukla Panchami"},
]


class PersonalTithiTest(unittest.TestCase):
    def test_validates_and_deduplicates_extended_tithi(self):
        events = validate_events({"events": [SAMPLE]})
        self.assertEqual(len(events), 1)
        self.assertEqual(
            [record["date"] for record in find_dates(SAMPLE, sorted(DAYS, key=lambda d: d["date"]))],
            ["2026-11-10", "2027-10-30"],
        )

    def test_adhika_policies(self):
        adhika = dict(SAMPLE, adhika_policy="adhika")
        self.assertTrue(matches(adhika, DAYS[-1]))
        self.assertFalse(matches(SAMPLE, DAYS[-1]))
        both = dict(SAMPLE, adhika_policy="both")
        self.assertTrue(matches(both, DAYS[-1]))

    def test_ics_contains_stable_each_occurrence_uid(self):
        records = sorted(DAYS, key=lambda d: d["date"])
        first = Calendar.from_ical(build_ics([SAMPLE], records))
        second = Calendar.from_ical(build_ics([SAMPLE], records))
        events = list(first.walk("VEVENT"))
        self.assertEqual(len(events), 2)
        self.assertEqual(
            [str(e.get("uid")) for e in events],
            [str(e.get("uid")) for e in second.walk("VEVENT")],
        )
        self.assertEqual(events[0].decoded("dtstart"), date(2026, 11, 10))

    def test_empty_feed_has_calendar_header(self):
        output = Calendar.from_ical(build_ics([], DAYS))
        self.assertFalse(list(output.walk("VEVENT")))

    def test_invalid_observance_rejected(self):
        invalid = dict(SAMPLE, tithi="Pournami", paksham="Krishna")
        with self.assertRaises(ValueError):
            validate_events({"events": [invalid]})


if __name__ == "__main__":
    unittest.main()
