# One verified update, one complete website build

Run `python study-tools/build_site.py` after installing `study-tools/requirements.txt`.
This rebuilds the season dashboard, the full attendance study, both copies of the
study page, every statistics download, and the reproduction package. Independent
raw-data and matrix-algebra checks must pass before a deployable `_site` exists.
GitHub Actions runs this same build on every main-branch push; deployment depends
on its success. No page percentages, counts, or snapshot dates need hand editing.

## Weekly source update

1. Verify completed fixtures, attendance, date, UK local kick-off and venue against
   their source pages. Add/correct `2026-27/data/new-matches.csv`; do not invent
   missing crowds. Preserve match source URLs.
2. Update `2026-27/data/update-audit.json` only to the genuinely reviewed cutoff.
   The build rejects later unaudited fixtures.
3. Extend `study-tools/source/current-context.json` with verified regional home-fixture calendars and school-term coverage for newly added dates. Keep prior verified intervals/fixtures; unknown context is never assumed to mean no clash.
4. Run `python 2026-27/tools/weather.py` to refresh all required hourly weather
   fields at the mapped grounds. A failed request preserves the previous cache.
5. Run the complete build and review material changes. Commit source changes.
   GitHub then recalculates, verifies and publishes the complete site together.

This is automatic recalculation/publication **when verified inputs are updated**;
it is not an unattended scraper that assumes all third-party figures are correct.

`source/original-matches.csv` preserves the original historical data, including
COVID exclusions and known missing historical crowds. Current-season rows are
replaced from the dashboard feed, never appended blindly. Published previous
season aggregates remain separate from historical match records: source totals
and coverage differences are identified, not silently imputed into match rows.

Big Bont Bash counts toward actual totals, season averages, rankings and growth.
It is omitted from conditions and regression comparisons. Condition-normalised
indices also use non-event club averages, avoiding indirect event influence.
Weather is reanalysis at approximate ground locations; travel is an estimated
routing matrix, not measured spectator journeys. Pre-match form/position are
calculated from completed season results. Unverified clash/holiday context stays
unknown and is omitted from analyses requiring those fields, with model coverage
reported explicitly.
