# Split: the invisible lines that cut cities in two

The Latte Line, the Hi-Vis Line, the Konbini Wars: informal city divides, found in census, venue and licence data, and tested properly. Every line is checked against random versions of its city that are just as smooth, and gets one of three verdicts: **Real line**, **Real pattern, gentle** or **Could be chance**.

**Live:** [18 cities](https://pche123.github.io/Sydney-Split/) in Australia, Japan and England, a [city comparison page](https://pche123.github.io/Sydney-Split/compare.html) and data downloads for every city.
**In plain words:** [FINDINGS.md](FINDINGS.md) · **Data sources:** [DATA_SOURCES.md](DATA_SOURCES.md)

| Country | Cities |
|---|---|
| Australia | Sydney, Melbourne, Brisbane, Perth, Adelaide |
| Japan | Tokyo, Osaka, Kyoto, Nagoya, Yokohama-Kawasaki, Kobe-Hanshin, Fukuoka, Sapporo |
| England | London, Manchester, Birmingham, Liverpool, Brighton |

Coming next: New York (by borough), Los Angeles, Chicago, San Francisco–Oakland, Washington, Austin, Seattle, Miami, Auckland, Christchurch and Singapore. They are held back as a test set: hypotheses formed on the 18 cities above are checked on them without retuning anything.

## What the tests do

- **Is it a line?** The length of the border between the two halves (the classical join count) is compared with random maps that are as smooth as the real one at every scale. Shuffling areas, or the standard Moran spectral randomisation, calls lines on a third or more of maps that have none; this test stays near 5%.
- **Where is it sharp?** Each border along the line is checked for a bigger jump than the smooth background makes there.
- **Which lines belong together?** Lines are grouped into families (work and class, inner city, age, night out), and each family is tested for sharing one hard border.
- **Do city rules travel?** Three-variable rules ("few over-65s and many people living alone ⇒ many degrees") are judged against their correlations and against smooth chance, then tested in other countries.

## Repository

| Folder | What's in it |
|---|---|
| `linetests/` | The tests as a small Python package: random-landscape null (`landscape.py`), join count, Geary and the local and family tests (`geary.py`), Moran spectral randomisation (`msr.py`), record-level simulation (`records.py`). |
| `pipeline/` | Raw data → each city's app data. `download.py` and `prepare_upload.py` fetch and shrink the data; `common/` builds and tests every city; `sydney/` and `tokyo/` are the two original cities. |
| `experiments/` | The studies behind the paper: benchmark against other nulls, statistic power, rules, and the original audit (`audit/`). |
| `results/` | Result tables. |
| `app/` | The web app (TypeScript + Vite): one codebase, one config and one data file per city. |
| `examples/explore_city.py` | A starter script for exploring any city's download. |

## Test a line yourself

```python
from linetests import MultiScaleNull, calibrated_map_test

null = MultiScaleNull(polygons, I, J, W)   # areas, pairs that share a border, border length (m)
calibrated_map_test(null, f)               # is it a line?  f = one number per area
```

`pip install -e ".[dev]" && pytest` runs the library tests.

## Rebuild a city

```bash
python pipeline/download.py melbourne                                   # free, open data
python pipeline/prepare_upload.py melbourne                             # shrink to work/melbourne
python pipeline/common/build_app.py melbourne work/melbourne app/data/melbourne.json
python pipeline/common/calibrate.py melbourne work/melbourne app/data/melbourne.json        # the double-check
python pipeline/common/sharp_and_families.py work melbourne             # sharp stretches, families
python pipeline/common/own_p.py work melbourne                          # each line's own p next to the corrected one
python pipeline/common/enrich_downloads.py work                         # download files
python pipeline/common/coverage_page.py                                 # comparison page
```

Sydney and Tokyo have their own pipelines in `pipeline/sydney/` and `pipeline/tokyo/` (see the `build.sh` in each).

## Reproduce the results

| Result | Command |
|---|---|
| Benchmark against other nulls | `python experiments/null_benchmark.py kyoto work 400` (and `melbourne`) |
| Which statistic notices a step | `python experiments/stat_power.py kyoto work 100` (and `melbourne`) |
| Urban rules and transfer | `python experiments/rules.py work` |
| Sydney and Tokyo audit | `experiments/audit/` (see its README) |

## Run the app

```bash
cd app
npm install
npm run dev            # http://localhost:5173
npm run build          # every city into site/
npm test && npm run typecheck
```

Pushing to `main` deploys the site to GitHub Pages.

## Credits and licences

ABS Census and ASGS data © Commonwealth of Australia (CC BY 4.0). Japanese census data © Statistics Bureau of Japan via e-Stat. England and Wales census data © Office for National Statistics (Open Government Licence). Venue data © OpenStreetMap contributors (ODbL). Liquor licence data © NSW Liquor & Gaming and the Victorian Government (CC BY 4.0). Food hygiene data © Food Standards Agency (OGL). Restaurant listings Powered by ホットペッパー Webサービス (HotPepper Gourmet); check Recruit's current terms before any paid use. A place's colour describes the area, not the people in it.
