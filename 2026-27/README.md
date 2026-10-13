# Cymru Premier 2026/27 attendance dashboard

Standalone addition at `/2026-27/`. The original study content, downloads and analytics configuration are locked. Shared navigation on both pages is authorized; keep all study content and data unchanged. The shared header links the study and dashboard, includes a mobile menu, and stores a consistent theme preference.

This is a dated snapshot through 10 October 2026, verified 13 October: 104 played fixtures and 104 published attendances across 13 complete rounds. Added 25 matches and filled TNS v Llandudno (19 September) with 496. Cardiff Met v Haverfordwest (MD9) was played on 29 September, crowd 437.

The Big Bont Bash, Penybont v Airbus on 26 September (2,666), remains in actual club and league totals, averages, growth, trends and downloads. `excludeFromConditions` removes it from day, kick-off, weather, temperature and travel comparisons, including their sample-size denominators.

Weather refresh is incomplete: Open-Meteo timed out/returned 502 on 13 October. Preserve valid saved observations; 75/104 fixtures have weather, 29 are Unknown. Four early Connah’s Quay observations are withheld because the old coordinates were Deeside, whereas all its checked current-season match pages list Essity Stadium. September observations use the saved Flint-location cache. All new 25 matches have unknown weather. Do not claim full weather verification.

All current-season match pages were inspected for kick-off and venue. July–September FWP browser pages displayed times one hour earlier than UK local time; existing UK times were retained, corroborated by Penybont’s official Big Bont Bash announcement (14:30) and TNS–Llandudno published 17:30 listing. October pages showed UK local times. Cambrian match pages omit venue: existing ground postcode coordinates remain an estimate. Travel reuses the original ground-to-ground routing matrix, mapping Connah’s Quay to Flint/Essity at both ends, with explicit estimate labels. No live traffic or fan travel claims.

Full-season unfiltered comparisons now use independently verified Transfermarkt totals: 87,608 / 192 = 456.2917 league baseline; Penybont 6,353 / 16 = 397.0625. Current league 64,789 / 104 = 622.9712 (+36.5%); Penybont 7,056 / 7 = 1,008 (+153.9%). Filtered/matched-round comparisons still use frozen historical match rows, which have gaps/source differences, disclosed on the page. The locked historical study is unchanged.

## Sources and updates

- `data/study-snapshot.json`: independent copy of the existing study's 2025/26 and early 2026/27 records, from commit f43c26f. Do not edit the original downloads.
- `data/new-matches.csv`: subsequent match records checked against the linked Football Web Pages match pages. The FAW fixture release identifies matchday rounds. Preserve exact source links and review dates.
- `data/published-baselines.json`: verified full-season top-flight totals from Transfermarkt, separate from frozen match records.
- `data/weather-cache.json`: Open-Meteo historical weather responses at the study's ground coordinates. Weather is estimated, not measured stadium observations.
- `tools/weather.py`: retrieves weather for the whole current season, using verified ground mapping. It preserves the saved cache if any request fails.
- `tools/build.py`: builds `data.json` and downloadable `matches.csv`. Uses only this directory's independent source files.

To refresh, verify new match records and append/correct this page's CSV, update reviewed dates and snapshot metadata in the builder, retrieve weather where needed, then rebuild. Update the page's dated methods/pending-fixture text and test snapshot assertions when the dataset changes. This page does not claim automatic updates.

```sh
python3 2026-27/tools/weather.py
python3 2026-27/tools/build.py
node --test 2026-27/tools/model.test.mjs
```

## Calculations and checks

Averages exclude null attendances; totals sum recorded crowds and are not unique people. Club filters apply to home fixtures. Calendar weeks begin Monday. Rolling averages are weighted by recorded matches. Period changes compare adjacent periods. Club last-change compares the last two selected home matches, retaining missing attendance as missing. 2025/26 comparisons use the same filters and either matching rounds or the full available prior season. Promoted clubs have separate sourced, rounded 2025/26 Cymru North/South aggregates in `data/promoted-baselines.json`. The default full-season comparison uses these averages without inventing fixture rows. Historical filters cannot apply to aggregate baselines; matched-round mode requires switching to full season for these six clubs.

Test desktop/mobile light and dark layouts, filters, empty selections, keyboard chart controls, match-source dialogs, shared URLs and CSV downloads. Consent is handled by the existing unmodified `../analytics.js` script. Never replace the original homepage or source files when deploying this addition.
