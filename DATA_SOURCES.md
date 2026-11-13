# Data sources

Every file the new cities need, where it comes from, and whether a script fetches it.
The study areas and codes for each city live in `pipeline/cities.py`.

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

## Australia: Melbourne, Brisbane, Perth (and Sydney)

| Data | Link | Gives | Licence | How |
|---|---|---|---|---|
| Census 2021 General Community Profile, SA2 and SA1 | [ABS DataPacks](https://www.abs.gov.au/census/find-census-data/datapacks) `2021_GCP_SA2_for_{VIC,QLD,WA}_short-header.zip` | every topic: age, jobs, industry, travel, tenure, dwelling, languages, religion, income | CC BY 4.0 | auto |
| Census Time Series, SA2 | same page, `2021_TSP_SA2_for_{STATE}`, `2016_TSP_SA2_for_{STATE}`, `2011_TSP_SA2_for_AUST` | 2011/2016/2021 (and 2001/2006) for the timeline | CC BY 4.0 | auto |
| Boundaries 2021 | [ASGS Edition 3](https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-3-july-2021-june-2026/access-and-downloads/digital-boundary-files) SA2, SA1, GCCSA, suburbs (SAL), LGA | maps; GCCSA codes 2GMEL, 3GBRI, 5GPER | CC BY 4.0 | auto |
| Boundaries 2016, 2011 | `2016_SA2_shape.zip`, `2011_SA2_shape.zip` on the DataPacks page | timeline on old maps | CC BY 4.0 | auto |
| OSM | [Geofabrik Australia](https://download.geofabrik.de/australia-oceania/australia.html) | chains, cafes, pubs, bars, bottle shops, breweries | ODbL | auto |
| VIC liquor licences | [data.vic: Victorian liquor licences by location](https://discover.data.vic.gov.au/dataset/victorian-liquor-licences-by-location) | every licence with category and coordinates, monthly | CC BY 4.0 | auto |
| VIC gaming by venue | [data.vic: Current](https://discover.data.vic.gov.au/dataset/current-gaming-expenditure-by-venue) and [Historical gaming expenditure by venue](https://discover.data.vic.gov.au/dataset/historical-gaming-expenditure-by-venue) | machines and player losses per venue (names, no coordinates: matched to licences) | CC BY 4.0 | auto |
| QLD licences and gaming | [OLGR licence search](https://secure.olgr.qld.gov.au/forms/lls) | one-at-a-time search only; no bulk file | — | manual (or skip) |
| WA licences | [Search of licensed premises](https://www.wa.gov.au/organisation/racing-gaming-and-liquor/search-of-licensed-premises) | the department sells the list (about $70) | paid | manual (or skip) |
| NSW premises list (Sydney) | [data.nsw: Liquor licence premises list](https://data.nsw.gov.au/data/dataset/nsw-liquor-licence-premises-list) | licences, coordinates, machines | CC BY | auto |

Brisbane and Perth fall back to OSM pubs, bars and bottle shops. WA has no poker machines outside the casino,
so Perth has no Pokies line: that is a real difference between the cities, not missing data.

## Japan: Osaka, Kyoto, Nagoya (and Tokyo)

| Data | Link | Gives | Licence | How |
|---|---|---|---|---|
| Census small areas 2020 (町丁・字) | [e-Stat 地図で見る統計](https://www.e-stat.go.jp/gis/statmap-search?type=1) `statsId=T001081..T001106&code={27,26,23}` | population, age, household size, family, tenure, building, industry, occupation | e-Stat terms (credit) | auto |
| Census small areas 2000–2015 | same, older `statsId`s (in `download.py`) | timeline | e-Stat terms | auto |
| Boundaries | same, `dlserveyId=A00200521{year}&code={pref}` | 町丁 maps per census year | e-Stat terms | auto |
| Foreign residents, degrees, commute mode | [e-Stat database, 2020 Census](https://www.e-stat.go.jp/stat-search/database?toukei=00200521) (町丁・字等 tables), or the [e-Stat API](https://www.e-stat.go.jp/api/) with a free appId | the Degree, Train vs Car and Bicycle lines | e-Stat terms | manual |
| OSM | Geofabrik [Kansai](https://download.geofabrik.de/asia/japan/kansai.html) (Osaka, Kyoto), [Chubu](https://download.geofabrik.de/asia/japan/chubu.html) (Nagoya) | konbini, chains, shrines, temples, stations | ODbL | auto |
| HotPepper Gourmet | [Recruit Web Service](https://webservice.recruit.co.jp/register) (free key) | every listed restaurant: genre, budget, hours, text; drinks filters | credit "Powered by ホットペッパー Webサービス" | key, then script |

## UK: London (maybe)

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
