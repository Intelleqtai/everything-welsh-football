# Cymru Premier 2026/27 attendance dashboard

Standalone addition at `/2026-27/`. The original historical match values and COVID exclusions are retained. As authorised on 13 October, both pages and all downloads now rebuild together using `study-tools/build_site.py`; current-season data and all derived study results are refreshed. Analytics configuration is unchanged. The shared header links the study and dashboard, includes a mobile menu, and stores a consistent theme preference.

This is a dated snapshot through 10 October 2026, verified 13 October: 104 played fixtures and 104 published attendances across 13 complete rounds. Added 25 matches and filled TNS v Llandudno (19 September) with 496. Cardiff Met v Haverfordwest (MD9) was played on 29 September, crowd 437.

The Big Bont Bash, Penybont v Airbus on 26 September (2,666), remains in actual club and league totals, averages, growth, trends and downloads. `excludeFromConditions` removes it from day, kick-off, weather, temperature and travel comparisons, including their sample-size denominators.

Weather refreshed successfully on 13 October after the service recovered: all 104/104 fixtures now have temperature, wind and 3-hour rainfall. All 16 ground requests succeeded and use Europe/London timestamps, Celsius, mm and km/h. The previous 29 unknown records are filled, including four early Connah’s Quay games at Essity Stadium. No previously known wet/dry classifications changed. Excluding the Bash, conditions are 93 Dry, 9 Wet, 1 Heavy rain (103 matches). Temperature/wind use the floored kick-off hour; precipitation is the three hourly observations ending at that hour. These remain model estimates, not stadium measurements.

All current-season match pages were inspected for kick-off and venue. July–September FWP browser pages displayed times one hour earlier than UK local time; existing UK times were retained, corroborated by Penybont’s official Big Bont Bash announcement (14:30) and TNS–Llandudno published 17:30 listing. October pages showed UK local times. Cambrian match pages omit venue: existing ground postcode coordinates remain an estimate. Travel reuses the original ground-to-ground routing matrix, mapping Connah’s Quay to Flint/Essity at both ends, with explicit estimate labels. No live traffic or fan travel claims.

Full-season unfiltered comparisons now use independently verified Transfermarkt totals: 87,608 / 192 = 456.2917 league baseline; Penybont 6,353 / 16 = 397.0625. Current league 64,789 / 104 = 622.9712 (+36.5%); Penybont 7,056 / 7 = 1,008 (+153.9%). Filtered/matched-round comparisons still use frozen historical match rows, which have gaps/source differences, disclosed on the page. The historical input rows are unchanged; the whole study is recalculated with the current season.

## Sources and updates

- `data/study-snapshot.json`: independent copy of the existing study's 2025/26 and early 2026/27 records, from commit f43c26f. Do not edit the original downloads.
- `data/new-matches.csv`: subsequent match records checked against the linked Football Web Pages match pages. The FAW fixture release identifies matchday rounds. Preserve exact source links and review dates.
- `data/published-baselines.json`: verified full-season top-flight totals from Transfermarkt, separate from frozen match records.
- `data/weather-cache.json`: Open-Meteo historical weather responses at the study's ground coordinates. Weather is estimated, not measured stadium observations.
- `tools/weather.py`: retrieves weather for the whole current season, using verified ground mapping. It preserves the saved cache if any request fails.
- `tools/build.py`: builds `data.json` and downloadable `matches.csv`. Uses only this directory's independent source files.

To refresh, verify new match records and append/correct `data/new-matches.csv`, then record the actual verification date and last verified fixture date in `data/update-audit.json`. The builder rejects fixtures beyond that audited cutoff. Retrieve weather and rebuild. Counts, coverage, cutoff dates, chart ranges, averages, totals and percentages are calculated from the resulting data; no chart text or fixed test counts need editing. The dashboard revalidates its dataset on load. This does not claim unattended verification of third-party fixtures.

```sh
python3 2026-27/tools/weather.py
python3 2026-27/tools/build.py
node --test 2026-27/tools/model.test.mjs
```

## Calculations and checks

Averages exclude null attendances; totals sum recorded crowds and are not unique people. Club filters apply to home fixtures. Calendar weeks begin Monday. Rolling averages are weighted by recorded matches. Period changes compare adjacent periods. Club last-change compares the last two selected home matches, retaining missing attendance as missing. 2025/26 comparisons use the same filters and either matching rounds or the full available prior season. Promoted clubs have separate sourced, rounded 2025/26 Cymru North/South aggregates in `data/promoted-baselines.json`. The default full-season comparison uses these averages without inventing fixture rows. Historical filters cannot apply to aggregate baselines; matched-round mode requires switching to full season for these six clubs.

Test desktop/mobile light and dark layouts, filters, empty selections, keyboard chart controls, match-source dialogs, shared URLs and CSV downloads. Consent is handled by the existing unmodified `../analytics.js` script. Publish via the unified verified build; do not hand-edit calculated figures.
