# Phoenix Telugu Panchangam — Apple Calendar

A free, automatically updated, Phoenix-localized Telugu Amanta Panchangam calendar. This repository builds daily ICS feeds using the open-source [Astro Chaganti Telugu Calendar Utilities](https://github.com/socraticsurge/telugu-calendar-utilities) calculation engine.

## Apple Calendar subscriptions

Once GitHub Pages deployment succeeds:

- **Full daily tithi + Telugu festivals**: https://vihari23.github.io/phoenix-telugu-panchang/phoenix-drik.ics
- **Festivals only**: https://vihari23.github.io/phoenix-telugu-panchang/phoenix-drik-festivals.ics
- **Tithi observances**: https://vihari23.github.io/phoenix-telugu-panchang/phoenix-drik-observances.ics

The first feed includes the other two types of events; usually subscribe to **just the full feed**.

On iPhone, open Calendar → Calendars → Add Calendar → Add Subscription Calendar, paste the URL, and save the subscription to iCloud if offered. This is a **subscription**, not a one-time ICS import.

## Personal annual Telugu tithi dates

Visit https://vihari23.github.io/phoenix-telugu-panchang/personal.html to save birthdays, anniversaries and family puja dates by Telugu masam, paksha and sunrise tithi. Choose a civil date within the live data window to automatically fill in its lunar components, or enter them manually.

**Privacy first:** the planner stores personal event details in your browser only. It displays upcoming occurrences using the published Phoenix date index and generates a **downloadable** `.ics` calendar. That download is a static import, **not** a live subscription. It does not automatically push event names or dates to Apple Calendar, GitHub, or the web.

An optional public `phoenix-personal.ics` is generated monthly from `data/personal-events.json`. The committed configuration intentionally starts as `{"events": []}`, so the public feed contains **no personal events**. Add events there only after the owner explicitly understands and approves publication of their labels and dates; anyone with the feed URL can read them, and Git history retains past commits. The source uses local-sunrise tithi, regular/Nija month by default, and needs separate review for skipped tithis or alternate observance traditions.

Example public opt-in configuration (not enabled by default):

```json
{
  "events": [
    {
      "id": "example-observance",
      "title": "Family observance",
      "maasam": "Kartika",
      "paksham": "Shukla",
      "tithi": "Panchami",
      "adhika_policy": "regular"
    }
  ]
}
```

## Details

- Coordinates: Phoenix, AZ (33.4484, -112.0740), elevation approximately 331 m
- Timezone: `America/Phoenix` — no DST
- Lunar calendar: Telugu Amanta, Drik Ganita engine
- Rolling date coverage: current month through month +17, regenerated monthly
- Each day has one all-day event with tithi, nakshatra, yoga in the title; masam, paksha, timing details and festivals in the description
- ICS generation uses stable event UIDs so future refreshed events can be recognized
- No private information or account tokens are needed to read the public feed

The source is pinned to a reviewed revision of the upstream calculation engine for reproducibility. Astronomical/religious conventions may differ from Drik Panchang; double-check important rituals.

## Maintenance

GitHub Actions `.github/workflows/publish.yml` runs when changes are pushed, manually via Actions → Run workflow, and on the first day of each month at 14:00 UTC (07:00 Phoenix time).

GitHub Pages must use **GitHub Actions** as its build source in Settings → Pages. The workflow installs dependencies, calculates Phoenix days, validates file structure and daily event count, and deploys files to Pages.

The project does not yet support personalized annual recurrence by Telugu tithi.

## License

Calendar computations © Vinay Chaganti / Astro Chaganti Telugu Calendar Utilities under AGPL-3.0-or-later. This repository's additions are AGPL-3.0-or-later. See [LICENSE-NOTICE.md](LICENSE-NOTICE.md) and the [upstream source and license](https://github.com/socraticsurge/telugu-calendar-utilities).
