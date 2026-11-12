# Sydney / Split

The invisible lines that cut Sydney in two: the Latte Line, the Red Rooster Line and a dozen more, found in the Census, café and shop maps, and liquor licences. Every line is checked against random versions of Sydney, so you can tell real patterns from coincidences.

**Open the app:** `index.html` (one self-contained file, works offline). With GitHub Pages enabled it lives at `https://pche123.github.io/Sydney-Split/`.

## What you can do

- **Lines**: 15 named lines (Latte, Red Rooster, Aldi, Pokies, Late Night, Hi-Vis, Laptop vs Ute …), each with a "Beats chance / Just for fun" verdict, what else changes across it, and a suburb lookup.
- **Heritage**: where Sydney's communities live, by birthplace (49 countries), ancestry (30) and religion (18).
- **Overlay**: a community map under any line, shown side by side (never scored against each other).
- **Timeline**: 2001 → 2021, five Censuses on today's suburbs.
- **Make your own**: pick any two things or any two chains; the map, verdict and a smoothness slider run live in the browser.

What we found so far, in plain words: [FINDINGS.md](FINDINGS.md).

## Rebuild from the raw data

1. Download into `data/` (all free):
   - ABS 2021 boundaries: SA1 and SA2 shapefiles (GDA2020); 2011 and 2016 SA2 shapefiles from the ABS DataPacks page.
   - ABS 2021 General Community Profile DataPacks, SA1 and SA2, NSW.
   - ABS Time Series Profile DataPacks (2011, 2016, 2021 releases), SA2, NSW.
   - OpenStreetMap places for Greater Sydney (cafés, restaurants, shops, pubs, stations, gyms), e.g. via Geofabrik + `osmium`, saved as `sydney_places.csv`.
   - NSW Liquor & Gaming premises list (XLSX).
2. In `pipeline/`:

| Step | Command | Makes |
|---|---|---|
| Census signals | `python build_signals.py <GCP SA2 folder> SA2 signals_sa2.csv` | 56 Census signals per suburb |
| Venue signals | `python parse_places.py sydney_places.csv places.pkl` then `python build_poi.py <SA2 shp> places.pkl <premises.xlsx> signals_sa2.csv signals_all.csv` | food, shop, pub and licence signals |
| Line search | `python quirky.py <SA2 shp> signals_sa2.csv q_classic classic` (and `quirky`) | ranked lines with chance tests |
| Fun lines | `python fun_test.py <SA2 shp>` | the curated food and night-time lines |
| Street level | `python sa1_graph.py` then `python sa1_line.py works_transport_logistics professionals hivis_l15 15` | split suburbs |
| 2001–2021 | `python harmonise.py` then `python timeline20.py` | timeline data and tests |
| Venue history | `python venue_history.py data/sydney_sa2_300.geojson venue_history.csv` (needs internet) | café, fast-food and chain counts per suburb, 2012–2026 |
| App | `bash build_app.sh` | `sydney_split_app.html` (copy to `index.html`) |

## Tokyo (work in progress)

| Step | Command | Makes |
|---|---|---|
| Census downloads (2000–2015) | `python tokyo_download.py tokyo_timeline` | one zip per table, per year |
| Venues | `python tokyo_places.py kanto-latest.osm.pbf tokyo_places.csv` | cafés, shops, bars, stations |
| Neighbourhoods | `python build_tokyo.py <2020 folder> tokyo_places.csv out` | ~1,600 neighbourhoods (町) with Census and venue signals |
| Lines and chain wars | `python tokyo_wars.py out` | tested lines, `tokyo_gallery.png` |
| 2000–2020 | `python tokyo_timeline.py tokyo_timeline <2020 folder> out` | Hi-Vis Line over time, ageing, towers |
| HotPepper restaurants | `python hotpepper_tokyo.py YOUR_KEY hotpepper_tokyo.csv` | every listed Tokyo restaurant, incl. ramen style blurbs |

## How the checks work (short version)

- **Is a line real?** We compare its border with 199+ random versions of Sydney that keep the same smoothness (Moran spectral randomisation, Wagner & Dray 2015), rerunning the whole search when many lines were tried.
- **Do two chains live in different Sydneys?** We shuffle which stores belong to which chain and see how often a split this clean appears.
- **Did a suburb really change side?** Years that appear in two Census packs give a free estimate of measurement noise; only changes bigger than that are shown.

## Credits and licences

ABS Census and ASGS data © Commonwealth of Australia (CC BY 4.0). Venue data © OpenStreetMap contributors (ODbL). Liquor licence data © NSW Liquor & Gaming (CC BY 4.0). Tokyo: Census data © Statistics Bureau of Japan via e-Stat. Restaurant listings Powered by ホットペッパー Webサービス (HotPepper Gourmet); check Recruit's current terms before any paid use. A suburb's colour describes the area, not the people in it. The Census asks about birthplace, ancestry and religion, not race or ethnicity.

An earlier prototype is kept at the git tag `v0-chatgpt-prototype`.
