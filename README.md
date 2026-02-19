# Alabama Realignment Project

This project tracks Alabama county-level political results across statewide and U.S. Senate contests, with a focus on long-run partisan realignment.

Primary output:
- `results_by_year_grouped.statewide_plus_ussenate_1968_2026.json`

CSV exports:
- `data/csv_exports/contest_county_results.csv`
- `data/csv_exports/candidate_results.csv`
- `data/csv_exports/contest_year_statewide_summary.csv`

## Historical Throughline

### 1) The Wallace Era and the "Politics of Rage"
Alabama's modern political identity was shaped by the Wallace period, when grievance politics became a statewide mobilization strategy. George Wallace translated resistance to federal civil-rights intervention, anti-elite rhetoric, and cultural backlash into a durable electoral style. This was not just issue positioning; it was emotional framing designed to turn resentment into turnout.

By the time Wallace was shot on May 15, 1972, that style was already institutionalized. The immediate personalities changed over time, but the political language of threat, betrayal, and restoration remained highly effective in Alabama campaigns.

### 2) From Democratic Dominance to Partisan Sorting
For much of the 20th century, Alabama was formally Democratic at the state level, but ideology was already diverging from the national Democratic Party. As national parties polarized around civil rights, race, religion, and social issues, Alabama's conservative white electorate moved steadily into Republican alignment.

County patterns hardened:
- Most majority-white counties trended strongly Republican.
- Black Belt counties remained the core Democratic base.
- Urban counties became the main arenas for marginal Democratic competitiveness.

### 3) The Siegelman Moment
Don Siegelman represented one of the last statewide Democratic coalitions capable of winning executive office in a changing Alabama. His success reflected an older coalition model:
- Strong Black turnout
- Enough crossover or moderate support in selected white counties
- Candidate-centered appeal in down-ballot statewide races

That model became progressively harder to sustain as straight-ticket nationalization intensified and partisan identity overtook candidate identity.

### 4) Why Alabama Became So Republican
Alabama's current Republican depth is the product of layered forces over decades:
- Racial and cultural sorting after the civil-rights era
- Religious conservatism aligning with national GOP messaging
- Rural and exurban partisan hardening
- Nationalized media and federalized political identity
- Decline in durable ticket-splitting

The result is a state where Democratic viability is concentrated geographically (especially Black Belt and some urban pockets), while statewide Republican performance is structurally advantaged across most cycles.

## Data Scope

This repository's merged JSON focuses on:
- Statewide offices
- U.S. Senate
- County-level aggregation for the included contests and years

Current merged coverage includes historical cycles through modern cycles, including 2016-2024 data restored from county workbook sources.

## How to Rebuild JSON

```powershell
py scripts/build_statewide_ussenate_filtered_json.py
```

## How to Export CSVs

```powershell
py scripts/export_statewide_plus_ussenate_csv.py
```

## CSV Output Definitions

### `contest_county_results.csv`
One row per county per contest-year with:
- Democratic/Republican/other vote totals
- winners and margins
- competitiveness labels

### `candidate_results.csv`
One row per county-candidate per contest-year with:
- candidate name
- party
- votes
- incumbent flag

### `contest_year_statewide_summary.csv`
One row per contest-year with statewide totals:
- dem/rep/other totals
- margin and margin percent
- inferred statewide winner

## Notes

- Candidate-name normalization is applied in the build pipeline (including comma-name reordering such as `Last, First -> First Last` when appropriate).
- Empty placeholder contests are pruned from output.
- Legacy `.xls` parsing requires `xlrd`.
