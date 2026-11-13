# India OTT Releases — Apple Calendar subscription

**Live feed:** https://vihari23.github.io/phoenix-telugu-panchang/india-ott.ics

**Information page:** https://vihari23.github.io/phoenix-telugu-panchang/ott.html

The existing Phoenix Panchangam and private personal calendars remain separate. This new calendar publishes minimal factual release-date metadata only: title, announced streaming date, original/dub languages, OTT service and source link. It does not republish articles, posters, reviews or descriptions.

GitHub Pages publishes the feed with the same workflow as the Panchangam calendar; its daily schedule runs at 15:00 UTC (08:00 Phoenix time). The script reads the Cinebuds public release listing once per scheduled run, honors its robots rules, and selects only explicitly **confirmed**, **released**, or **out today** dated table rows; tentative/expected/undated titles are excluded. If fetch or parsing fails, a small manually reviewed November 13, 2026 seed prevents a blank or broken subscription, **but it cannot supply new releases**. Investigate GitHub Actions logs and source access when that happens. Do not claim the feed is fresh until the run logs confirm a live source.

All events show **08:00–09:00 America/Phoenix** on the India-announced date. This is a display slot, not a streaming premiere hour. UIDs are stable across date changes; Apple Calendar subscription refresh frequency is selected by the subscriber. Dates and streaming availability are subject to change; check the actual platform.

On Mac, use Calendar → File → New Calendar Subscription and paste the live URL (do not import the downloaded file if you want future changes). The feed is public; it contains no personal events.

Source: https://cinebuds.com/ott-release-dates/
