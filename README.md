# Split: the invisible lines that cut cities in two

The Latte Line, the Hi-Vis Line, Ramen Wars: informal city divides, found in Census, venue and licence data, and tested properly. Every line is checked against random versions of its city that are just as smooth, and gets one of three verdicts: **Real line**, **Real pattern, gentle** or **Could be chance**.

**Live:** [Sydney](https://pche123.github.io/Sydney-Split/) · [Tokyo](https://pche123.github.io/Sydney-Split/tokyo.html) · What we found, in plain words: [FINDINGS.md](FINDINGS.md) · Data for new cities: [DATA_SOURCES.md](DATA_SOURCES.md)

## Repository

| Folder | What's in it |
|---|---|
| `app/` | The web app (TypeScript + Vite). One codebase; each city is a config (`app/src/config.ts`) plus a data file (`app/data/<city>.json`). Builds to one self-contained HTML file per city. |
| `linetests/` | The statistical tests, as a small Python package: random-landscape null, record-level simulation, edge test. |
| `pipeline/` | Turns raw data into each city's data file: `sydney/`, `tokyo/`, and `common/`. |
| `experiments/` | The audit and simulation studies behind the paper and FINDINGS.md. |
| `results/` | Result tables, including `verdicts.csv` (every line's audited verdict). |
| `tests/` | Python tests (`pytest`); the app has its own (`app/tests`). |

## Run the app

```bash
cd app
npm install
npm run dev            # Sydney at http://localhost:5173 (npm run dev:tokyo for Tokyo)
npm run build          # site/index.html (Sydney) and site/tokyo.html (Tokyo)
npm test && npm run typecheck
```

Pushing to `main` deploys the site to GitHub Pages (`.github/workflows/pages.yml`).

## Test a line yourself

```python
from linetests import MultiScaleNull, calibrated_map_test, calibrated_edge_map

null = MultiScaleNull(polygons, I, J, W)   # areas, pairs that share a border, border length (m)
calibrated_map_test(null, f)               # is it a line?  f = one number per area
calibrated_edge_map(null, f)               # is it a cliff rather than a slope?
```

For maps built from counts (cafés vs fast food, licences per resident, nearest store), simulate the records with `linetests.Line`; `experiments/audit/lines_*.py` has worked examples. `pip install -e ".[dev]" && pytest` runs the library tests.

## Rebuild the data

Raw downloads go in `data/` (or set `SPLIT_RAW`). All sources are free; see the credits below.

| City | Step | Command |
|---|---|---|
| Sydney | Census signals | `python pipeline/sydney/build_signals.py <GCP SA2 folder> SA2 signals_sa2.csv` |
| | Venue and licence signals | `python pipeline/sydney/parse_places.py sydney_places.csv places.pkl`, then `python pipeline/sydney/build_poi.py <SA2 shp> places.pkl <premises.xlsx> signals_sa2.csv signals_all.csv` |
| | Line search | `python pipeline/sydney/quirky.py <SA2 shp> signals_sa2.csv q_classic classic` (and `quirky`) |
| | Food and night lines | `python pipeline/sydney/fun_test.py <SA2 shp>` |
| | 2001–2021 | `python pipeline/sydney/harmonise.py`, then `python pipeline/sydney/timeline20.py` |
| | App data | `pipeline/sydney/build.sh <working folder>` → `app/data/sydney.json` |
| Tokyo | Census downloads | `python pipeline/tokyo/tokyo_download.py tokyo_timeline` |
| | Venues | `python pipeline/tokyo/tokyo_places.py kanto-latest.osm.pbf tokyo_places.csv` |
| | Neighbourhoods | `python pipeline/tokyo/build_tokyo.py <2020 folder> tokyo_places.csv out` |
| | 2000–2020 | `python pipeline/tokyo/tokyo_timeline.py tokyo_timeline <2020 folder> out` |
| | Restaurants | `python pipeline/tokyo/hotpepper_tokyo.py YOUR_KEY hotpepper_tokyo.csv` |
| | App data | `pipeline/tokyo/build.sh <working folder> hotpepper_tokyo.csv` → `app/data/tokyo.json` |

| Result | Command (in `experiments/audit/`, with `SPLIT_SYDNEY_WORK` and `SPLIT_TOKYO_WORK` set) |
|---|---|
| Verdict table (`results/verdicts.csv`) | `final_census.py`, `final_data_lines.py`, `final_chains.py`, `final_edge.py`, `search_null.py`, `q1_geography.py`, then `assemble.py` |
| MSR calibration failure (paper Section 4) | `audit_census.py 200 199` |
| False alarms and power (paper Section 8) | `gp_check.py`, `power_check.py 60`, `power_step.py 60` |
| Persistence over time | `timeline_audit.py` |

## Credits and licences

ABS Census and ASGS data © Commonwealth of Australia (CC BY 4.0). Venue data © OpenStreetMap contributors (ODbL). Liquor licence data © NSW Liquor & Gaming (CC BY 4.0). Tokyo Census data © Statistics Bureau of Japan via e-Stat. Restaurant listings Powered by ホットペッパー Webサービス (HotPepper Gourmet); check Recruit's current terms before any paid use. A place's colour describes the area, not the people in it.
