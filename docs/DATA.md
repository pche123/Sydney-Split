# Data provenance and limitations

## Official inputs, not simulated points

The current offline app was constructed using user-supplied ABS source downloads:

1. `SA2_2021_AUST_SHP_GDA2020.zip` - official ASGS 2021 SA2 polygon shapefile.
2. `SA1_2021_AUST_SHP_GDA2020.zip` - official ASGS 2021 SA1 polygon shapefile.
3. `Statistical Area Level 2, Indexes, SEIFA 2021.xlsx` - SA2 SEIFA scores and population.
4. `Statistical Area Level 1, Indexes, SEIFA 2021.xlsx` - SA1 SEIFA scores and population.

Pre-extracted derived tables are included in `data/sa1_seifa_2021_extracted.csv` and `data/sa2_seifa_2021_selected.csv`, avoiding a fragile XLSX parser as a runtime dependency. The first is a broad SA1 score export, not a representative sample of Sydney alone; do not mistake row coverage for study-area coverage. The 301-region study mask is produced by joining Greater Sydney GCCSA polygons with available SEIFA scores and intersecting a projected bounding rectangle (roughly lon 150.69–151.36 / lat -34.18–-33.51). This is **an exploratory crop**, not an authoritative definition of Sydney or a fully connected metropolitan area.

## Current observed derived payload

- 301 selected SA2 regions.
- 650 polygons pairs with shared border above 170 metres, as encoded in the app; very short contacts are suppressed.
- 11 preloaded signals: four official ABS indexes plus seven derived/geographic signals.
- Four disconnected components (sizes 295, 4, 1, 1) in the extracted adjacency graph. For the current nested hierarchy, three *nearest-centroid virtual links* connect the algorithmic graph. These are not drawn as physical boundaries. **The apparent contiguous hierarchy is only a hierarchy on the augmented graph.** This must be fixed before any rigorous claim of geographic continuity.
- Drawing polygon simplification differs from exact analytical adjacency. SVG paths and point-in-polygon geometry are simplified for browser performance.

A public link to the ABS SEIFA 2021 source and methodology:
- https://www.abs.gov.au/statistics/people/people-and-communities/socio-economic-indexes-areas-seifa-australia/2021
- https://www.abs.gov.au/methodologies/socio-economic-indexes-areas-seifa-australia-methodology/2021
- https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026

## Signals and what they mean

- **IRSD**: relative disadvantage (larger means less disadvantage); **IRSAD**: balance of relative advantage/disadvantage; **IER**: economic resources; **IEO**: education and occupation. None is median salary and none measures people individually.
- **SA1 dispersion**: within each SA2, weighted standard deviation of SA1 index scores. Describes heterogeneity across SA1s, not variation among people.
- **Low-advantage population share**: weighted share of SA1 population in the study region below the first quartile of SA1 IRSAD scores. This is a **study-area-dependent** threshold, not national bottom-quartile prevalence.
- **IEO–IER gap**: subtraction of two standardized index scores, **not dollars minus educational degrees**. Its magnitude and interpretation are scale-dependent. Replace the UI's "Degrees vs money" shorthand.
- **Population density**: population/SA2 area, not daytime population; **CBD distance**: approximate straight-line geography and a potential confounder, not a social outcome.

## Cultural venues are absent until loaded

The browser performs OpenStreetMap/Overpass queries for named chains and broad amenity categories (cafes, fast food, restaurants, bars, pubs, bakeries, supermarkets, gyms and more). It counts nodes/ways/relations with usable coordinates and allocates them to SA2 polygons, with neighbour smoothing and per-capita normalization. OSM is incomplete, unevenly tagged and not a direct sample of venue footfall or business market share. OSM points assigned to polygons may be centroid-based for mapped ways. Unknown does not mean absent. The browser does not cache a canonical externally verified venue dataset.

Do not claim to show *the 100 busiest cafes* from OSM alone: OSM generally has place locations and tags, not audited visits/sales/footfall. A "top 50% busiest" selection requires a different measurement source and transparent definition; otherwise it means a derived density percentile, not busy venues.

## Additional issues for replication

- ABS Census observation year is **2021**, OSM query is **contemporary**; apparent alignment does not establish historical co-occurrence.
- SA2 polygons are variable in geographic area; the modifiable areal unit problem (MAUP) is substantial.
- Many signals are correlated/derived from the same four indexes; searching eight is not eight independent evidence streams.
- Privacy and small-cell disclosure must be respected in any future feature expansion.
- ABS area scores rank relative conditions and must not be interpreted as moral or personal judgements.
