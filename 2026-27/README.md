# Cymru Premier 2026/27 attendance dashboard

Standalone addition at `/2026-27/`. The original study, downloads, analytics configuration and homepage are locked and must remain unchanged. Navigation back to the original is provided on this new page only.

This is a dated snapshot through 19 September 2026, verified 20 September: 79 played fixtures, 78 published attendances. The New Saints v Llandudno on 19 September has no published attendance in the checked source. Missing values stay null. Matchday 9's Cardiff Met v Haverfordwest fixture is scheduled for 29 September and is not a played record.

## Sources and updates

- `data/study-snapshot.json`: independent copy of the existing study's 2025/26 and early 2026/27 records, from commit f43c26f. Do not edit the original downloads.
- `data/new-matches.csv`: subsequent match records checked against the linked Football Web Pages match pages. The FAW fixture release identifies matchday rounds. Preserve exact source links and review dates.
- `data/weather-cache.json`: Open-Meteo historical weather responses at the study's ground coordinates. Weather is estimated, not measured stadium observations.
- `tools/weather.py`: retrieves weather for additions, using their dates and grounds.
- `tools/build.py`: builds `data.json` and downloadable `matches.csv`. Uses only this directory's independent source files.

To refresh, verify new match records and append/correct this page's CSV, update reviewed dates and snapshot metadata in the builder, retrieve weather where needed, then rebuild. Update the page's dated methods/pending-fixture text and test snapshot assertions when the dataset changes. This page does not claim automatic updates.

```sh
python3 2026-27/tools/weather.py
python3 2026-27/tools/build.py
node --test 2026-27/tools/model.test.mjs
```

## Calculations and checks

Averages exclude null attendances; totals sum recorded crowds and are not unique people. Club filters apply to home fixtures. Calendar weeks begin Monday. Rolling averages are weighted by recorded matches. Period changes compare adjacent periods. Club last-change compares the last two selected home matches, retaining missing attendance as missing. 2025/26 comparisons use the same filters and either matching rounds or the full available prior season. Promoted clubs have no prior Cymru Premier baseline in this dataset.

Test desktop/mobile light and dark layouts, filters, empty selections, keyboard chart controls, match-source dialogs, shared URLs and CSV downloads. Consent is handled by the existing unmodified `../analytics.js` script. Never replace the original homepage or source files when deploying this addition.
