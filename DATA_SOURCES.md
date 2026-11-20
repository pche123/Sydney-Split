# Data sources

Every file the cities need, where it comes from, and whether a script fetches it.
The study areas and codes for each city live in `pipeline/cities.py`.

## The cities and why each is in

| City | Study area | What it adds to the comparison |
|---|---|---|
| Sydney | SA2s in Greater Sydney with >= 1,000 residents and >= 300 per km2 (300 areas) | The reference city: harbour, sprawl, a strong Latte Line and pokies in pubs and clubs. |
| Melbourne | SA2s in Greater Melbourne with >= 1,000 residents and >= 300 per km2 (about 330 areas) | Sydney's rival: flatter, tram grid, pokies capped by law at a different level; does the Latte Line move? |
| Brisbane | SA2s in Greater Brisbane with >= 1,000 residents and >= 300 per km2 (about 230 areas) | Hilly river city with a younger boom; licence data are thin, so its lines lean on the census. |
| Perth | SA2s in Greater Perth with >= 1,000 residents and >= 300 per km2 (about 180 areas) | No pub or club pokies at all: a natural experiment on the Pokies Line. |
| Adelaide | SA2s in Greater Adelaide with >= 1,000 residents and >= 300 per km2 (about 170 areas) | Planned grid centre (Light's plan) ringed by parklands, an old wine state: grid and drinks contrasts. |
| Tokyo | 23 special wards + Tama cities (no islands); 町 merged to ~30,000 people (454 areas) | The reference Japanese city: rail-shaped, many centres, konbini and ramen wars. |
| Osaka | Osaka City (24 wards), Sakai and the inner ring (Toyonaka, Suita, Moriguchi, Ibaraki, Yao, Kadoma, Settsu, Higashiosaka); 町 merged to ~20,000 people (about 280 areas) | Merchant city, Tokyo's rival; Kansai food culture and its own chains. |
| Kyoto | Kyoto City (11 wards), dropping the mountain areas of Sakyo, Kita and Ukyo; 町 merged to ~8,000 people (about 170 areas) | Old imperial grid, temples and students: does an 8th-century plan still show in today's lines? |
| Nagoya | Nagoya City (16 wards); 町 merged to ~12,000 people (about 190 areas) | Car city (Toyota): wide roads, low rail use; Train vs Car should flip relative to Tokyo. |
| Yokohama-Kawasaki | Yokohama (18 wards) and Kawasaki (7 wards); 町 merged to ~15,000 people (about 350 areas) | Tokyo's commuter belt: do Tokyo's lines carry across the city border, or reset? |
| Kobe-Hanshin | Kobe (9 wards) plus Amagasaki, Nishinomiya and Ashiya along the bay; mountain 町 dropped; merged to ~10,000 people (about 250 areas) | Port city squeezed between mountains and sea: a thin strip, so lines can only run one way. |
| Fukuoka | Fukuoka City (7 wards), mountain 町 dropped; merged to ~8,000 people (about 190 areas) | Home of Hakata tonkotsu ramen: the ramen wars on home turf; compact and young. |
| Sapporo | Sapporo City (10 wards), mountain 町 dropped; merged to ~9,000 people (about 210 areas) | Modern planned grid (1870s), snow and subways: a young grid against Kyoto's ancient one. |
| London | Greater London MSOAs (about 1,000 areas of ~9,000 people; merge pairs for ~500 if needed) | The UK reference: vast, many centres, deep heritage mix. |
| Manchester | Greater Manchester's 10 boroughs, MSOAs (about 350 areas) | Post-industrial north, student city: Factory and Hi-Vis lines in their birthplace. |
| Birmingham | Birmingham, Solihull and the Black Country (Sandwell, Dudley, Walsall, Wolverhampton), MSOAs (about 340 areas) | Car-built city with the Black Country next door: industry vs services on one map. |
| Liverpool | Liverpool City Region (Liverpool, Knowsley, Sefton, Wirral, St Helens, Halton), MSOAs (about 200 areas) | Port city across the Mersey (Wirral): a river split, like Sydney's harbour. |
| Brighton | Brighton and Hove, LSOAs (about 165 areas of ~1,700 people; the city has only ~37 MSOAs) | Small seaside city, students and London commuters: a coast line on the smallest scale. |

Each city's caveats (old lists, missing sources, census taken in lockdown, areas left out) are kept in
`DATA_NOTES` in `pipeline/cities.py` and shown in that city's app under "About the data", on the map and in the intro.

## Get the data (three commands per city)

```bash
pip install requests geopandas scikit-learn scipy osmium openpyxl
export SPLIT_RAW=~/split_raw                                        # one folder for all cities

python pipeline/download.py melbourne                               # census, boundaries, OSM, venues
python pipeline/common/osm_places.py melbourne $SPLIT_RAW/_osm/australia-latest.osm.pbf $SPLIT_RAW/melbourne/osm/places.csv
python pipeline/common/au_areas.py melbourne $SPLIT_RAW/melbourne work/melbourne   # jp_areas.py / uk_areas.py for the others
python pipeline/common/venues.py   melbourne $SPLIT_RAW/melbourne work/melbourne/venues.csv
```

`download.py` skips files it already has and prints a list of manual steps at the end.
Japanese cities also need `pipeline/common/hotpepper.py <city> <key> ...` (free key, see below).

| Step | Script | Output |
|---|---|---|
| Fetch | `pipeline/download.py <city>` | `$SPLIT_RAW/<city>/{census,boundaries,venues}`, `$SPLIT_RAW/_osm/*.pbf` |
| Venues from OSM | `pipeline/common/osm_places.py <city> <pbf> <csv>` | shops, cafes, restaurants, bars, breweries, stations |
| Areas + tables (AU) | `pipeline/common/au_areas.py` | study SA2s, every GCP and TSP table cut to them |
| Areas + tables (JP) | `pipeline/common/jp_areas.py` | 町, merged areas, every small-area table at 町 level |
| Areas + tables (UK) | `pipeline/common/uk_areas.py` | London MSOAs, every Census 2021 bulk table cut to them |
| Venues, tidy | `pipeline/common/venues.py` | one points file: on / off / producer / gaming, drink type, machines |
| Restaurants (JP) | `pipeline/common/hotpepper.py` | every HotPepper shop + raw JSON + drinks filters |

Checked against the existing cities: `au_areas.py` on Sydney gives 304 SA2s (all 300 published ones, plus four
far-northern-beaches SA2s dropped by hand before); `jp_areas.py` on Tokyo gives 467 areas (published: 454, with a
slightly stricter 町 filter); `venues.py` on the NSW list finds 877 venues with machines (45,918 machines).
The download URLs were checked by hand, but this sandbox cannot reach the sites, so the first real run is the test.

## Direct links, city by city

Japanese census files come per prefecture, not per city, so each city's links below are the prefecture's files.

### Osaka (files cover all of Osaka Prefecture, code 27; `jp_areas.py` cuts out the city)

- Census 2020 tables (population, age, household size, family, tenure, building, industry, occupation, extra): [T001081](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001081&code=27&downloadType=2) · [T001082](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001082&code=27&downloadType=2) · [T001083](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001083&code=27&downloadType=2) · [T001084](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001084&code=27&downloadType=2) · [T001085](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001085&code=27&downloadType=2) · [T001086](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001086&code=27&downloadType=2) · [T001103](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001103&code=27&downloadType=2) · [T001104](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001104&code=27&downloadType=2) · [T001106](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001106&code=27&downloadType=2)
- Map of 町丁 (2020): [boundaries](https://www.e-stat.go.jp/gis/statmap-search/data?dlserveyId=A002005212020&code=27&coordSys=1&format=shape&downloadType=5)
- Older years: the same links with the 2015/2010/2005/2000 table codes in `download.py`, and `A00200521{year}` for the maps
- OpenStreetMap: [kansai-latest.osm.pbf](https://download.geofabrik.de/asia/japan/kansai-latest.osm.pbf)
- Restaurants: HotPepper (free key from [Recruit](https://webservice.recruit.co.jp/register)), then `python pipeline/common/hotpepper.py osaka KEY out.csv`

### Kyoto (files cover all of Kyoto Prefecture, code 26; `jp_areas.py` cuts out the city)

- Census 2020 tables (population, age, household size, family, tenure, building, industry, occupation, extra): [T001081](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001081&code=26&downloadType=2) · [T001082](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001082&code=26&downloadType=2) · [T001083](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001083&code=26&downloadType=2) · [T001084](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001084&code=26&downloadType=2) · [T001085](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001085&code=26&downloadType=2) · [T001086](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001086&code=26&downloadType=2) · [T001103](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001103&code=26&downloadType=2) · [T001104](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001104&code=26&downloadType=2) · [T001106](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001106&code=26&downloadType=2)
- Map of 町丁 (2020): [boundaries](https://www.e-stat.go.jp/gis/statmap-search/data?dlserveyId=A002005212020&code=26&coordSys=1&format=shape&downloadType=5)
- Older years: the same links with the 2015/2010/2005/2000 table codes in `download.py`, and `A00200521{year}` for the maps
- OpenStreetMap: [kansai-latest.osm.pbf](https://download.geofabrik.de/asia/japan/kansai-latest.osm.pbf)
- Restaurants: HotPepper (free key from [Recruit](https://webservice.recruit.co.jp/register)), then `python pipeline/common/hotpepper.py kyoto KEY out.csv`

### Nagoya (files cover all of Aichi Prefecture, code 23; `jp_areas.py` cuts out the city)

- Census 2020 tables (population, age, household size, family, tenure, building, industry, occupation, extra): [T001081](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001081&code=23&downloadType=2) · [T001082](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001082&code=23&downloadType=2) · [T001083](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001083&code=23&downloadType=2) · [T001084](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001084&code=23&downloadType=2) · [T001085](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001085&code=23&downloadType=2) · [T001086](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001086&code=23&downloadType=2) · [T001103](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001103&code=23&downloadType=2) · [T001104](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001104&code=23&downloadType=2) · [T001106](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001106&code=23&downloadType=2)
- Map of 町丁 (2020): [boundaries](https://www.e-stat.go.jp/gis/statmap-search/data?dlserveyId=A002005212020&code=23&coordSys=1&format=shape&downloadType=5)
- Older years: the same links with the 2015/2010/2005/2000 table codes in `download.py`, and `A00200521{year}` for the maps
- OpenStreetMap: [chubu-latest.osm.pbf](https://download.geofabrik.de/asia/japan/chubu-latest.osm.pbf)
- Restaurants: HotPepper (free key from [Recruit](https://webservice.recruit.co.jp/register)), then `python pipeline/common/hotpepper.py nagoya KEY out.csv`

### London

- Census 2021 tables (each zip has every area level; `uk_areas.py` uses the MSOA file): [TS001](https://www.nomisweb.co.uk/output/census/2021/census2021-ts001.zip) · [TS003](https://www.nomisweb.co.uk/output/census/2021/census2021-ts003.zip) · [TS004](https://www.nomisweb.co.uk/output/census/2021/census2021-ts004.zip) · [TS007A](https://www.nomisweb.co.uk/output/census/2021/census2021-ts007a.zip) · [TS017](https://www.nomisweb.co.uk/output/census/2021/census2021-ts017.zip) · [TS021](https://www.nomisweb.co.uk/output/census/2021/census2021-ts021.zip) · [TS030](https://www.nomisweb.co.uk/output/census/2021/census2021-ts030.zip) · [TS044](https://www.nomisweb.co.uk/output/census/2021/census2021-ts044.zip) · [TS045](https://www.nomisweb.co.uk/output/census/2021/census2021-ts045.zip) · [TS054](https://www.nomisweb.co.uk/output/census/2021/census2021-ts054.zip) · [TS058](https://www.nomisweb.co.uk/output/census/2021/census2021-ts058.zip) · [TS059](https://www.nomisweb.co.uk/output/census/2021/census2021-ts059.zip) · [TS060](https://www.nomisweb.co.uk/output/census/2021/census2021-ts060.zip) · [TS061](https://www.nomisweb.co.uk/output/census/2021/census2021-ts061.zip) · [TS062](https://www.nomisweb.co.uk/output/census/2021/census2021-ts062.zip) · [TS063](https://www.nomisweb.co.uk/output/census/2021/census2021-ts063.zip) · [TS066](https://www.nomisweb.co.uk/output/census/2021/census2021-ts066.zip) · [TS067](https://www.nomisweb.co.uk/output/census/2021/census2021-ts067.zip) · [TS037](https://www.nomisweb.co.uk/output/census/2021/census2021-ts037.zip)
- Map of MSOAs: [ONS Open Geography Portal, MSOA Dec 2021 BGC](https://geoportal.statistics.gov.uk/) (`download.py` pulls just London from the ONS map service)
- Food businesses (pubs, restaurants, takeaways): [FSA open data](https://ratings.food.gov.uk/open-data), one XML file per borough
- Gambling premises: [Gambling Commission register](https://www.gamblingcommission.gov.uk/public-register/premises/download)
- OpenStreetMap: [greater-london-latest.osm.pbf](https://download.geofabrik.de/europe/united-kingdom/england/greater-london-latest.osm.pbf)

### Yokohama-Kawasaki (files cover all of Kanagawa Prefecture, code 14)

- Census 2020 tables: [T001081](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001081&code=14&downloadType=2) · [T001082](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001082&code=14&downloadType=2) · [T001083](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001083&code=14&downloadType=2) · [T001084](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001084&code=14&downloadType=2) · [T001085](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001085&code=14&downloadType=2) · [T001086](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001086&code=14&downloadType=2) · [T001103](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001103&code=14&downloadType=2) · [T001104](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001104&code=14&downloadType=2) · [T001106](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001106&code=14&downloadType=2)
- Map of 町丁 (2020): [boundaries](https://www.e-stat.go.jp/gis/statmap-search/data?dlserveyId=A002005212020&code=14&coordSys=1&format=shape&downloadType=5)
- OpenStreetMap: [kanto-latest.osm.pbf](https://download.geofabrik.de/asia/japan/kanto-latest.osm.pbf)
- Restaurants: HotPepper, `python pipeline/common/hotpepper.py yokohama KEY out.csv`

### Kobe-Hanshin (files cover all of Hyogo Prefecture, code 28)

- Census 2020 tables: [T001081](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001081&code=28&downloadType=2) · [T001082](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001082&code=28&downloadType=2) · [T001083](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001083&code=28&downloadType=2) · [T001084](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001084&code=28&downloadType=2) · [T001085](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001085&code=28&downloadType=2) · [T001086](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001086&code=28&downloadType=2) · [T001103](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001103&code=28&downloadType=2) · [T001104](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001104&code=28&downloadType=2) · [T001106](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001106&code=28&downloadType=2)
- Map of 町丁 (2020): [boundaries](https://www.e-stat.go.jp/gis/statmap-search/data?dlserveyId=A002005212020&code=28&coordSys=1&format=shape&downloadType=5)
- OpenStreetMap: [kansai-latest.osm.pbf](https://download.geofabrik.de/asia/japan/kansai-latest.osm.pbf)
- Restaurants: HotPepper, `python pipeline/common/hotpepper.py kobe KEY out.csv`

### Fukuoka (files cover all of Fukuoka Prefecture, code 40)

- Census 2020 tables: [T001081](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001081&code=40&downloadType=2) · [T001082](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001082&code=40&downloadType=2) · [T001083](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001083&code=40&downloadType=2) · [T001084](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001084&code=40&downloadType=2) · [T001085](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001085&code=40&downloadType=2) · [T001086](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001086&code=40&downloadType=2) · [T001103](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001103&code=40&downloadType=2) · [T001104](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001104&code=40&downloadType=2) · [T001106](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001106&code=40&downloadType=2)
- Map of 町丁 (2020): [boundaries](https://www.e-stat.go.jp/gis/statmap-search/data?dlserveyId=A002005212020&code=40&coordSys=1&format=shape&downloadType=5)
- OpenStreetMap: [kyushu-latest.osm.pbf](https://download.geofabrik.de/asia/japan/kyushu-latest.osm.pbf)
- Restaurants: HotPepper, `python pipeline/common/hotpepper.py fukuoka KEY out.csv`

### Sapporo (files cover all of Hokkaido, code 01)

- Census 2020 tables: [T001081](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001081&code=01&downloadType=2) · [T001082](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001082&code=01&downloadType=2) · [T001083](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001083&code=01&downloadType=2) · [T001084](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001084&code=01&downloadType=2) · [T001085](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001085&code=01&downloadType=2) · [T001086](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001086&code=01&downloadType=2) · [T001103](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001103&code=01&downloadType=2) · [T001104](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001104&code=01&downloadType=2) · [T001106](https://www.e-stat.go.jp/gis/statmap-search/data?statsId=T001106&code=01&downloadType=2)
- Map of 町丁 (2020): [boundaries](https://www.e-stat.go.jp/gis/statmap-search/data?dlserveyId=A002005212020&code=01&coordSys=1&format=shape&downloadType=5)
- OpenStreetMap: [hokkaido-latest.osm.pbf](https://download.geofabrik.de/asia/japan/hokkaido-latest.osm.pbf)
- Restaurants: HotPepper, `python pipeline/common/hotpepper.py sapporo KEY out.csv`

### Manchester, Birmingham, Liverpool, Brighton

The census tables, food-business files and gambling list above are national, so these cities reuse London's
downloads (saved once in `_uk_census/`). Each city only adds its own map of areas (from the ONS map service,
cut to its councils in `cities.py`) and the England-wide OpenStreetMap file,
[england-latest.osm.pbf](https://download.geofabrik.de/europe/united-kingdom/england-latest.osm.pbf) (about 1.5 GB).
Brighton uses the smaller LSOA areas because it has only about 37 MSOAs.

## Australia: Melbourne, Brisbane, Perth, Adelaide (and Sydney)

| Data | Link | Gives | Licence | How |
|---|---|---|---|---|
| Census 2021 General Community Profile, SA2 and SA1 | [ABS DataPacks](https://www.abs.gov.au/census/find-census-data/datapacks) `2021_GCP_SA2_for_{VIC,QLD,WA}_short-header.zip` | every topic: age, jobs, industry, travel, tenure, dwelling, languages, religion, income | CC BY 4.0 | auto |
| Census Time Series, SA2 | same page, `2021_TSP_SA2_for_{STATE}`, `2016_TSP_SA2_for_{STATE}`, `2011_TSP_SA2_for_AUST` | 2011/2016/2021 (and 2001/2006) for the timeline | CC BY 4.0 | auto |
| Boundaries 2021 | [ASGS Edition 3](https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-3-july-2021-june-2026/access-and-downloads/digital-boundary-files) SA2, SA1, GCCSA, suburbs (SAL), LGA | maps; GCCSA codes 2GMEL, 3GBRI, 5GPER | CC BY 4.0 | auto |
| Boundaries 2016, 2011 | `2016_SA2_shape.zip`, `2011_SA2_shape.zip` on the DataPacks page | timeline on old maps | CC BY 4.0 | auto |
| OSM | [Geofabrik Australia](https://download.geofabrik.de/australia-oceania/australia.html) | chains, cafes, pubs, bars, bottle shops, breweries | ODbL | auto |
| VIC liquor licences | [data.vic: Victorian liquor licences by location](https://discover.data.vic.gov.au/dataset/victorian-liquor-licences-by-location) | every licence with category and coordinates, monthly | CC BY 4.0 | auto |
| VIC gaming by venue | [data.vic: Current](https://discover.data.vic.gov.au/dataset/current-gaming-expenditure-by-venue) and [Historical gaming expenditure by venue](https://discover.data.vic.gov.au/dataset/historical-gaming-expenditure-by-venue) | machines and player losses per venue (names, no coordinates: matched to licences) | CC BY 4.0 | auto |
| SA licences and gaming (Adelaide) | [data.sa.gov.au: Liquor & Gaming Licences](https://data.sa.gov.au/data/dataset/liquor-gaming-licences) | newest open list is August 2019: addresses and machine counts, no coordinates | CC BY | auto (geocoding later) |
| QLD licences and gaming | [OLGR licence search](https://secure.olgr.qld.gov.au/forms/lls) | one-at-a-time search only; no bulk file | — | manual (or skip) |
| WA licences | [Search of licensed premises](https://www.wa.gov.au/organisation/racing-gaming-and-liquor/search-of-licensed-premises) | the department sells the list (about $70) | paid | manual (or skip) |
| NSW premises list (Sydney) | [data.nsw: Liquor licence premises list](https://data.nsw.gov.au/data/dataset/nsw-liquor-licence-premises-list) | licences, coordinates, machines | CC BY | auto |

Brisbane and Perth fall back to OSM pubs, bars and bottle shops. WA has no poker machines outside the casino,
so Perth has no Pokies line: that is a real difference between the cities, not missing data.

## Japan: Osaka, Kyoto, Nagoya, Yokohama-Kawasaki, Kobe-Hanshin, Fukuoka, Sapporo (and Tokyo)

| Data | Link | Gives | Licence | How |
|---|---|---|---|---|
| Census small areas 2020 (町丁・字) | [e-Stat 地図で見る統計](https://www.e-stat.go.jp/gis/statmap-search?type=1) `statsId=T001081..T001106&code={27,26,23}` | population, age, household size, family, tenure, building, industry, occupation | e-Stat terms (credit) | auto |
| Census small areas 2000–2015 | same, older `statsId`s (in `download.py`) | timeline | e-Stat terms | auto |
| Boundaries | same, `dlserveyId=A00200521{year}&code={pref}` | 町丁 maps per census year | e-Stat terms | auto |
| Foreign residents, degrees, commute mode | [e-Stat database, 2020 Census](https://www.e-stat.go.jp/stat-search/database?toukei=00200521) (町丁・字等 tables), or the [e-Stat API](https://www.e-stat.go.jp/api/) with a free appId | the Degree, Train vs Car and Bicycle lines | e-Stat terms | manual |
| OSM | Geofabrik [Kansai](https://download.geofabrik.de/asia/japan/kansai.html) (Osaka, Kyoto, Kobe), [Chubu](https://download.geofabrik.de/asia/japan/chubu.html) (Nagoya), [Kanto](https://download.geofabrik.de/asia/japan/kanto.html) (Yokohama), [Kyushu](https://download.geofabrik.de/asia/japan/kyushu.html) (Fukuoka), [Hokkaido](https://download.geofabrik.de/asia/japan/hokkaido.html) (Sapporo) | konbini, chains, shrines, temples, stations | ODbL | auto |
| HotPepper Gourmet | [Recruit Web Service](https://webservice.recruit.co.jp/register) (free key) | every listed restaurant: genre, budget, hours, text; drinks filters | credit "Powered by ホットペッパー Webサービス" | key, then script |

## UK: London, Manchester, Birmingham, Liverpool, Brighton

| Data | Link | Gives | Licence | How |
|---|---|---|---|---|
| Census 2021 bulk tables | [Nomis bulk download](https://www.nomisweb.co.uk/sources/census_2021_bulk) `census2021-ts001.zip` … | every TS table at OA, LSOA, MSOA; 19 tables fetched (list in `download.py`) | OGL | auto |
| MSOA / LSOA 2021 boundaries | [ONS Open Geography Portal](https://geoportal.statistics.gov.uk/) (BGC, 20 m) | maps, queried for London only | OGL | auto |
| Food hygiene ratings | [FSA open data](https://ratings.food.gov.uk/open-data) | every food business with type (pub/bar/nightclub, restaurant/cafe, takeaway, retailer…) and coordinates | OGL | auto |
| Gambling premises | [Gambling Commission register](https://www.gamblingcommission.gov.uk/public-register/premises/download) | betting shops, adult arcades, bingo, casinos (postcodes, geocoded with postcodes.io) | OGL | auto |
| OSM | [Geofabrik Greater London](https://download.geofabrik.de/europe/united-kingdom/england/greater-london.html) | chains, pubs, cafes | ODbL | auto |
| Census 2011 (timeline) | [Nomis 2011](https://www.nomisweb.co.uk/sources/census_2011) + MSOA 2011→2021 lookup | optional | OGL | manual |

London borough licensing registers exist but every borough publishes differently, so they are not in the kit;
FSA ratings cover the same pubs, bars and restaurants consistently.

## What the venue data can tell apart (drinks)

Counted on the data we already have, inside the study areas:

| | Beer | Wine | Spirits / whisky |
|---|---|---|---|
| Sydney, NSW licences by name | 82 breweries (producer licences) | 16 wine bars; most "wine" licences are importers' offices | 45 distilleries |
| Sydney, OSM tags | 26 microbreweries | 1 wine shop | 4 distilleries |
| Tokyo, HotPepper text | 940 mention beer (282 craft beer) | 1,637 mention wine | about 150 mention whisky |
| Tokyo, HotPepper text | | 1,423 mention sake, 520 shochu | |

Wine vs sake in Tokyo has enough venues on both sides for a line; a whisky line does not anywhere.
`venues.py` only tags a drink when a venue's own name or licence type says it, never from anything else.

## Phase 2 (Europe)

| Country | Census | Areas | Licence |
|---|---|---|---|
| Germany | Zensus 2022 grid tables (Destatis), read from the [jslth/z22data](https://github.com/jslth/z22data) mirror on GitHub | 1 km grid cells with at least 1,000 residents | Datenlizenz Deutschland – Namensnennung 2.0 (© Statistisches Bundesamt, Zensus 2022) |
| France | INSEE recensement 2021, base infracommunale (IRIS) | IRIS, IGN CONTOURS-IRIS 2023 | Licence Ouverte / Etalab |
| Italy | ISTAT Censimento permanente 2021, dati per sezione | Basi Territoriali 2021 (sezioni di censimento) | CC BY 4.0 (Istat) |
| Spain | INE Censo 2021, indicadores por sección censal | INE secciones censales, 1 Jan 2021 | INE terms: cite "INE, www.ine.es" as the source |

Berlin's borough outlines come from [funkeinteraktiv/Berlin-Geodaten](https://github.com/funkeinteraktiv/Berlin-Geodaten); the 1961–89 border inside Mitte and Friedrichshain-Kreuzberg is approximated by a polyline through Bornholmer Straße, Bernauer Straße, the Reichstag, Brandenburger Tor, Potsdamer Platz, Checkpoint Charlie and the Spree to Treptower Park (experiments/phase2_germany.py), which is exact enough for 1 km cells.

## Korea over time: Seoul and Busan, 2008–2025 (fetched 21 Nov 2026)

**Where the numbers come from.** The Ministry of the Interior and Safety (행정안전부) publishes the resident registration count for every administrative neighbourhood (행정동) every month at [jumin.mois.go.kr](https://jumin.mois.go.kr/ageStatMonth.do) (연령별 인구현황), free and without a login. `pipeline/get_korea_mois.py` asks that page's own CSV download (`downloadCsvAge.do`, "전체읍면동현황", five-year age bands, both sexes, all registration types) for December of each year, 2008 to 2025: the same file anyone gets by pressing the CSV button on that page. It ran on GitHub Actions (workflow "Fetch Korea over time"); the 18 raw files, exactly as downloaded, are kept on this repository's `korea-data` branch (commit `eaf28fcb2700`), so every number can be checked against the source.

**Boundaries.** Neighbourhood boundaries for each year come from the open [vuski/admdongkor](https://github.com/vuski/admdongkor) project (yearly 행정동 boundaries since 1975, matched on the same 10-digit 행정기관코드 that MOIS uses). The last file of each year is used; for 2016, 2017, 2018, 2020, 2021 and 2022 that file is dated earlier than December (Feb 2016, Oct 2017, Nov 2018, Oct 2020, Jul 2021, Oct 2022). Each year's counts are shared by area onto the 427 Seoul and 206 Busan neighbourhoods of December 2025, so every year sits on one map.

**How complete it is** (`results/korea_time/coverage.csv`). Every neighbourhood row matched a boundary of its year except one in Seoul in 2022 (17,318 people) and two in Busan in 2014 (16,633 people). In every year the people placed on the 2025 map are 99.1–100% of the city total that MOIS itself reports (Seoul 10,200,827 in Dec 2008 and 9,299,548 in Dec 2025; Busan 3,564,577 and 3,241,600). The share aged 65+ comes out at 8.7% → 20.4% for Seoul and 10.2% → 25.3% for Busan.

**What it is and isn't.** These are *registrations*, not a census: they count Korean nationals registered at an address, including people whose whereabouts are unknown (거주불명자, from 2010) and registered Koreans living abroad (재외국민, from 2015), and they leave out foreign residents. Someone who has moved without re-registering is counted at the old address. For the age pattern of whole neighbourhoods this matters little, but these figures will not match census counts exactly. Seoul and Busan here are the two cities themselves (서울특별시, 부산광역시), not their wider metro areas, unlike the 2024 SGIS grid used in Section 12.

| December of | SHA-256 of the raw file (first 16 hex) |
|---|---|
| 2008 | `ddece8aac214c2f1` |
| 2009 | `a84cc6f887a4f7eb` |
| 2010 | `a8b146c8e976a606` |
| 2011 | `3d645710c753b4f0` |
| 2012 | `8a949a3a7e073d9b` |
| 2013 | `3e8e81904ce2c777` |
| 2014 | `bba05ae7ac916eeb` |
| 2015 | `1b8997dd34719f1e` |
| 2016 | `81aeb350680d2a95` |
| 2017 | `1eeffc6b573c0076` |
| 2018 | `eb4b2a817b137672` |
| 2019 | `27f8e4480c8d531b` |
| 2020 | `4b2250e4bc079f51` |
| 2021 | `3fe65d9c0f396089` |
| 2022 | `c18750ab9d518be6` |
| 2023 | `3356e13caacb9852` |
| 2024 | `3a1bd2d8d1dd0e0e` |
| 2025 | `0d6684b51581edd8` |

## Safety and sights layer (fetched 20 Nov 2026)

All fetched by `pipeline/get_safety.py` on GitHub Actions (workflow "Fetch safety data"); logs of each run are in `results/safety/log_*.txt`.

| What | Source | Coverage | Licence |
|---|---|---|---|
| River flood zones | JRC / Copernicus Emergency Management Service, global river flood hazard maps v2.1, 1-in-100-year return period, categorised depth ([jeodpp.jrc.ec.europa.eu](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard/)) | All 29 cities, ~90 m; a model that ignores flood defences | CC BY 4.0 |
| Landslide warning zones (土砂災害警戒区域) | MLIT National Land Numerical Information A33, 2025 edition ([nlftp.mlit.go.jp](https://nlftp.mlit.go.jp/ksj/)) | 8 Japanese cities | MLIT terms (credit the source) |
| Tsunami inundation zones (津波浸水想定) | MLIT National Land Numerical Information A40 (prefecture editions 2016–2023) | Not Tokyo Bay or Kobe's Inland Sea coast: those prefecture files don't cover them, so Tokyo and Kobe show no tsunami map | MLIT terms |
| Designated emergency evacuation sites (指定緊急避難場所) | GSI national list, [hinanmap.gsi.go.jp](https://hinanmap.gsi.go.jp/hinanjocp/hinanbasho/koukaidate.html) (mergeFromCity_2.csv), 115,948 sites nationally | 8 Japanese cities (19,230 sites inside them) | GSI content terms |
| Hospitals, fire stations, assembly points, sights | OpenStreetMap via Geofabrik extracts (download.geofabrik.de); duplicates within 40–200 m merged | All cities but Nagoya (download refused); coverage depends on volunteer mapping | ODbL, © OpenStreetMap contributors |
