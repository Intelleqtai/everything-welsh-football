# Cymru Premier 2026/27 attendance dashboard

Standalone addition at `/2026-27/`. The original historical match values and COVID exclusions are retained. As authorised on 13 October, both pages and all downloads now rebuild together using `study-tools/build_site.py`; current-season data and all derived study results are refreshed. Analytics configuration is unchanged. The shared header links the study and dashboard, includes a mobile menu, and stores a consistent theme preference.

Snapshot through **31 October 2026**, reviewed **3 November 2026**: all 119 played games in rounds 1–15, with 116 published attendances. Penybont v Holywell (MD14) was postponed and is not a played row. Barry v Haverfordwest (24 October), Flint v Holywell (30 October) and Cardiff Met v Penybont (31 October) remain awaiting attendance; blanks are not zero. A club-pair coverage test confirms every first-half pairing except that postponement.

Added 15 fixtures. Dates, results, local kickoffs and available venues were checked in the browser on each Football Web Pages match page. Six missing FWP crowds are supplemented from Y Clwb Pêl-droed's 1 November attendance report, with separate fixture and attendance provenance. No figure was inferred from a rounded average. Penybont v TNS remains corrected to 1,025.

Current recorded total: 70,532 / 116 = 608.0345, +33.2557% against the published 2025/26 full-season average (87,608 / 192). Penybont: 7,206 / 7 = 1,029.4286; without the 2,666 Big Bont Bash: 4,540 / 6 = 756.6667, +90.5661% against 6,353 / 16 last season. Both figures are labelled on both pages. The Bash remains in actual totals and growth and is excluded from conditions and models.

Weather refreshed successfully for all 119 matches. The archive revised five previously Wet classifications to Dry: Barry and Penybont on 28 August; Airbus, Connah's Quay and Haverfordwest on 18 September. All weather remains reanalysis, not observed stadium readings. Current conditions excluding Bash: 109 recorded Dry crowds from 111 fixtures, 5/5 Wet, 1/2 Heavy rain. One missing attendance lies in Heavy rain. Travel retains the estimated ground routing matrix; known Connah's Quay venue is Essity Stadium. Regional clash calendars reviewed through 31 October. School holiday classification uses the published Welsh half-term dates with the following weekend included, an explicitly approximate regional convention.

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
