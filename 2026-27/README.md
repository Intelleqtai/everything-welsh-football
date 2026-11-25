# Cymru Premier 2026/27 attendance dashboard

Standalone addition at `/2026-27/`. The original historical match values and COVID exclusions are retained. As authorised on 13 October, both pages and all downloads now rebuild together using `study-tools/build_site.py`; current-season data and all derived study results are refreshed. Analytics configuration is unchanged. The shared header links the study and dashboard, includes a mobile menu, and stores a consistent theme preference.

Snapshot through **24 November 2026**, reviewed **25 November 2026**: all 136 played games in rounds 1–17, with 135 published attendances. The rearranged MD14 fixture Holywell v Penybont was played on 24 November (298), so rounds 1–15 now contain every club pairing. Barry v Haverfordwest (24 October) remains awaiting attendance; a blank is not zero.

Added 17 fixtures. Dates, results, local kickoffs, attendances and available venues were checked in the browser on Football Web Pages. Flint v Holywell (890) and Cardiff Met v Penybont (413) have since been published there. All 119 earlier records were rechecked against the source; the only difference is the documented Penybont v TNS correction to 1,025.

Current recorded total: 81,014 / 135 = 600.1037, +31.5176% against the published 2025/26 full-season average (87,608 / 192). Penybont: 8,945 / 9 = 993.8889; without the 2,666 Big Bont Bash: 6,279 / 8 = 784.8750, +97.6704% against 6,353 / 16 last season. The Bash remains in actual totals and growth and is excluded from conditions and models.

Weather is complete for all 136 matches, with no earlier classification revised. It remains reanalysis, not observed stadium readings. Regional clash calendars and Welsh school-term coverage reviewed through 24 November. Holywell's Bartons North Wales Stadium is the sponsored name of Halkyn Road, so travel and weather mapping are unchanged.

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
