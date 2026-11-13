"""Every city in one place: where its data comes from and how its study area is defined.

Used by download.py (fetch the raw data) and osm_places.py (cut venues out of an OSM file).
Study areas are suggestions in the spirit of Sydney (urban suburbs) and Tokyo (23 wards + Tama):
dense, continuous urban areas with a few hundred areas once merged to a similar population.
"""

GEOFABRIK = "https://download.geofabrik.de"
ENGLAND = f"{GEOFABRIK}/europe/united-kingdom/england-latest.osm.pbf"   # shared by the English cities outside London

CITIES = {
    # ---------------------------------------------------------------- Australia (ABS Census, SA2s)
    "sydney": dict(country="au", name="Sydney", state="NSW", gccsa="1GSYD", crs=7856,
                   bbox=(150.50, -34.35, 151.40, -33.55), osm=f"{GEOFABRIK}/australia-oceania/australia-latest.osm.pbf",
                   study="SA2s in Greater Sydney with >= 1,000 residents and >= 300 per km2 (300 areas)"),
    "melbourne": dict(country="au", name="Melbourne", state="VIC", gccsa="2GMEL", crs=7855,
                      bbox=(144.40, -38.35, 145.65, -37.40), osm=f"{GEOFABRIK}/australia-oceania/australia-latest.osm.pbf",
                      study="SA2s in Greater Melbourne with >= 1,000 residents and >= 300 per km2 (about 330 areas)",
                      licences="vic", pokies="vic"),
    "brisbane": dict(country="au", name="Brisbane", state="QLD", gccsa="3GBRI", crs=7856,
                     bbox=(152.65, -27.85, 153.35, -27.00), osm=f"{GEOFABRIK}/australia-oceania/australia-latest.osm.pbf",
                     study="SA2s in Greater Brisbane with >= 1,000 residents and >= 300 per km2 (about 230 areas)",
                     licences="qld", pokies="qld"),
    "perth": dict(country="au", name="Perth", state="WA", gccsa="5GPER", crs=7850,
                  bbox=(115.65, -32.55, 116.15, -31.60), osm=f"{GEOFABRIK}/australia-oceania/australia-latest.osm.pbf",
                  study="SA2s in Greater Perth with >= 1,000 residents and >= 300 per km2 (about 180 areas)",
                  licences="wa", pokies=None),   # WA: poker machines only at the casino, so no Pokies line
    "adelaide": dict(country="au", name="Adelaide", state="SA", gccsa="4GADE", crs=7854,
                     bbox=(138.40, -35.25, 138.85, -34.60), osm=f"{GEOFABRIK}/australia-oceania/australia-latest.osm.pbf",
                     study="SA2s in Greater Adelaide with >= 1,000 residents and >= 300 per km2 (about 170 areas)",
                     licences="sa", pokies="sa"),

    # ---------------------------------------------------------------- Japan (Census small areas, 町丁・字)
    "tokyo": dict(country="jp", name="Tokyo", pref="13", crs=6677, hotpepper="東京",
                  bbox=(138.94, 35.48, 139.93, 35.90), osm=f"{GEOFABRIK}/asia/japan/kanto-latest.osm.pbf",
                  municipalities=[(13101, 13299)], target_pop=30000,
                  study="23 special wards + Tama cities (no islands); 町 merged to ~30,000 people (454 areas)"),
    "osaka": dict(country="jp", name="Osaka", pref="27", crs=6674, hotpepper="大阪",
                  bbox=(135.33, 34.45, 135.70, 34.85), osm=f"{GEOFABRIK}/asia/japan/kansai-latest.osm.pbf",
                  municipalities=[(27100, 27199),                    # Osaka City wards (271xx) and Sakai wards (2714x)
                                  (27203, 27203), (27205, 27205), (27209, 27209), (27211, 27211),   # Toyonaka Suita Moriguchi Ibaraki
                                  (27212, 27212), (27223, 27224), (27227, 27227)],                  # Yao, Kadoma+Settsu, Higashiosaka
                  target_pop=20000,
                  study="Osaka City (24 wards), Sakai and the inner ring (Toyonaka, Suita, Moriguchi, Ibaraki, Yao, "
                        "Kadoma, Settsu, Higashiosaka); 町 merged to ~20,000 people (about 280 areas)"),
    "kyoto": dict(country="jp", name="Kyoto", pref="26", crs=6674, hotpepper="京都",
                  bbox=(135.55, 34.87, 135.90, 35.15), osm=f"{GEOFABRIK}/asia/japan/kansai-latest.osm.pbf",
                  municipalities=[(26100, 26199)], target_pop=8000, drop_low_density=True,
                  study="Kyoto City (11 wards), dropping the mountain areas of Sakyo, Kita and Ukyo; "
                        "町 merged to ~8,000 people (about 170 areas)"),
    "nagoya": dict(country="jp", name="Nagoya", pref="23", crs=6675, hotpepper="愛知",
                   bbox=(136.79, 35.04, 137.06, 35.27), osm=f"{GEOFABRIK}/asia/japan/chubu-latest.osm.pbf",
                   municipalities=[(23100, 23199)], target_pop=12000,
                   study="Nagoya City (16 wards); 町 merged to ~12,000 people (about 190 areas)"),
    "yokohama": dict(country="jp", name="Yokohama-Kawasaki", pref="14", crs=6677, hotpepper="神奈川",
                     bbox=(139.45, 35.30, 139.80, 35.65), osm=f"{GEOFABRIK}/asia/japan/kanto-latest.osm.pbf",
                     municipalities=[(14100, 14119), (14130, 14139)], target_pop=15000,
                     study="Yokohama (18 wards) and Kawasaki (7 wards); 町 merged to ~15,000 people (about 350 areas)"),
    "kobe": dict(country="jp", name="Kobe-Hanshin", pref="28", crs=6673, hotpepper="兵庫",
                 bbox=(134.95, 34.58, 135.45, 34.85), osm=f"{GEOFABRIK}/asia/japan/kansai-latest.osm.pbf",
                 municipalities=[(28100, 28199), (28202, 28202), (28204, 28204), (28206, 28206)], target_pop=10000,
                 drop_low_density=True,
                 study="Kobe (9 wards) plus Amagasaki, Nishinomiya and Ashiya along the bay; mountain 町 dropped; "
                       "merged to ~10,000 people (about 250 areas)"),
    "fukuoka": dict(country="jp", name="Fukuoka", pref="40", crs=6670, hotpepper="福岡",
                    bbox=(130.20, 33.47, 130.52, 33.72), osm=f"{GEOFABRIK}/asia/japan/kyushu-latest.osm.pbf",
                    municipalities=[(40130, 40139)], target_pop=8000, drop_low_density=True,
                    study="Fukuoka City (7 wards), mountain 町 dropped; merged to ~8,000 people (about 190 areas)"),
    "sapporo": dict(country="jp", name="Sapporo", pref="01", crs=6680, hotpepper="北海道",
                    bbox=(141.15, 42.90, 141.55, 43.20), osm=f"{GEOFABRIK}/asia/japan/hokkaido-latest.osm.pbf",
                    municipalities=[(1100, 1110)], target_pop=9000, drop_low_density=True,
                    study="Sapporo City (10 wards), mountain 町 dropped; merged to ~9,000 people (about 210 areas)"),

    # ---------------------------------------------------------------- UK (Census 2021, MSOAs)
    "london": dict(country="uk", name="London", crs=27700, level="msoa", lads="LONDON_BOROUGHS",
                   bbox=(-0.52, 51.28, 0.34, 51.70), osm=f"{GEOFABRIK}/europe/united-kingdom/england/greater-london-latest.osm.pbf",
                   study="Greater London MSOAs (about 1,000 areas of ~9,000 people; merge pairs for ~500 if needed)"),
    "manchester": dict(country="uk", name="Manchester", crs=27700, level="msoa", bbox=(-2.75, 53.33, -1.90, 53.69), osm=ENGLAND,
                       lads=["Manchester", "Salford", "Trafford", "Stockport", "Tameside", "Oldham", "Rochdale", "Bury", "Bolton", "Wigan"],
                       study="Greater Manchester's 10 boroughs, MSOAs (about 350 areas)"),
    "birmingham": dict(country="uk", name="Birmingham", crs=27700, level="msoa", bbox=(-2.25, 52.35, -1.65, 52.70), osm=ENGLAND,
                       lads=["Birmingham", "Solihull", "Sandwell", "Dudley", "Walsall", "Wolverhampton"],
                       study="Birmingham, Solihull and the Black Country (Sandwell, Dudley, Walsall, Wolverhampton), MSOAs (about 340 areas)"),
    "liverpool": dict(country="uk", name="Liverpool", crs=27700, level="msoa", bbox=(-3.20, 53.28, -2.55, 53.70), osm=ENGLAND,
                      lads=["Liverpool", "Knowsley", "Sefton", "Wirral", "St. Helens", "Halton"],
                      study="Liverpool City Region (Liverpool, Knowsley, Sefton, Wirral, St Helens, Halton), MSOAs (about 200 areas)"),
    "brighton": dict(country="uk", name="Brighton", crs=27700, level="lsoa", bbox=(-0.30, 50.78, -0.02, 50.90), osm=ENGLAND,
                     lads=["Brighton and Hove"],
                     study="Brighton and Hove, LSOAs (about 165 areas of ~1,700 people; the city has only ~37 MSOAs)"),
}

# What each city adds to the cross-country comparison (for the paper's discussion)
CONTRAST = {
    "sydney": "The reference city: harbour, sprawl, a strong Latte Line and pokies in pubs and clubs.",
    "melbourne": "Sydney's rival: flatter, tram grid, pokies capped by law at a different level; does the Latte Line move?",
    "brisbane": "Hilly river city with a younger boom; licence data are thin, so its lines lean on the census.",
    "perth": "No pub or club pokies at all: a natural experiment on the Pokies Line.",
    "adelaide": "Planned grid centre (Light's plan) ringed by parklands, an old wine state: grid and drinks contrasts.",
    "tokyo": "The reference Japanese city: rail-shaped, many centres, konbini and ramen wars.",
    "osaka": "Merchant city, Tokyo's rival; Kansai food culture and its own chains.",
    "kyoto": "Old imperial grid, temples and students: does an 8th-century plan still show in today's lines?",
    "nagoya": "Car city (Toyota): wide roads, low rail use; Train vs Car should flip relative to Tokyo.",
    "yokohama": "Tokyo's commuter belt: do Tokyo's lines carry across the city border, or reset?",
    "kobe": "Port city squeezed between mountains and sea: a thin strip, so lines can only run one way.",
    "fukuoka": "Home of Hakata tonkotsu ramen: the ramen wars on home turf; compact and young.",
    "sapporo": "Modern planned grid (1870s), snow and subways: a young grid against Kyoto's ancient one.",
    "london": "The UK reference: vast, many centres, deep heritage mix.",
    "manchester": "Post-industrial north, student city: Factory and Hi-Vis lines in their birthplace.",
    "birmingham": "Car-built city with the Black Country next door: industry vs services on one map.",
    "liverpool": "Port city across the Mersey (Wirral): a river split, like Sydney's harbour.",
    "brighton": "Small seaside city, students and London commuters: a coast line on the smallest scale.",
}

LONDON_BOROUGHS = ["City of London", "Barking and Dagenham", "Barnet", "Bexley", "Brent", "Bromley", "Camden", "Croydon",
                   "Ealing", "Enfield", "Greenwich", "Hackney", "Hammersmith and Fulham", "Haringey", "Harrow", "Havering",
                   "Hillingdon", "Hounslow", "Islington", "Kensington and Chelsea", "Kingston upon Thames", "Lambeth",
                   "Lewisham", "Merton", "Newham", "Redbridge", "Richmond upon Thames", "Southwark", "Sutton",
                   "Tower Hamlets", "Waltham Forest", "Wandsworth", "Westminster"]


# City- and country-specific caveats. Each city's app shows these under "About the data" (on the map and in the intro).
# Add to these whenever a source turns out to be old, partial, odd or missing.
AU_CENSUS = "People: 2021 Census, counted on 10 August 2021."
JP_CENSUS = "People: 2020 Census (October 2020, during COVID)."
UK_CENSUS = ("People: Census 2021, counted on 21 March 2021 while England was still under COVID rules, so the "
             "census office warns that travel-to-work figures are unusual.")
JP_SHARED = ["Restaurants: only those listed on HotPepper, which leans towards places that use the site; many small old shops are missing.",
             "Foreign residents, degrees and how people commute come from separate census tables, not the small-area release."]
UK_SHARED = ["Pubs, restaurants and takeaways: Food Standards Agency hygiene-rating records (every food business councils inspect).",
             "Betting shops, arcades and bingo: the Gambling Commission register, listed by postcode and placed at the postcode's centre.",
             "Scotland is not included anywhere: it held its own census in 2022 with different tables."]
DATA_NOTES = {
    "melbourne": [AU_CENSUS + " Melbourne was in lockdown, so work-from-home and travel-to-work figures are unusual.",
                  "Pokies: machines and player losses by venue from the Victorian regulator; venues have no coordinates and are placed by matching their names to the liquor licence list, so a few may be missing."],
    "brisbane": [AU_CENSUS,
                 "Pubs, bars and bottle shops: OpenStreetMap only. Queensland publishes no bulk licence list, so venue lines are thinner than in Sydney or Melbourne."],
    "perth": [AU_CENSUS,
              "No Pokies line: Western Australia allows poker machines only at the casino. That is a real difference, not missing data.",
              "Pubs, bars and bottle shops: OpenStreetMap only. WA sells its licence list rather than publishing it."],
    "adelaide": [AU_CENSUS,
                 "Licences and pokies: the newest open South Australian list is from August 2019, placed on the map from its addresses. Venues that opened or closed since are wrong; current OpenStreetMap pubs and bottle shops are used alongside."],
    "osaka": [JP_CENSUS, "Area: Osaka City, Sakai and the inner ring of cities around them."] + JP_SHARED,
    "kyoto": [JP_CENSUS, "Area: Kyoto City without its mountain districts (few residents)."] + JP_SHARED,
    "nagoya": [JP_CENSUS, "Area: Nagoya City's 16 wards."] + JP_SHARED,
    "yokohama": [JP_CENSUS, "Area: Yokohama and Kawasaki together, treated as one city because they are one built-up belt."] + JP_SHARED,
    "kobe": [JP_CENSUS, "Area: Kobe plus Amagasaki, Nishinomiya and Ashiya along the bay; Kobe's mountain and rural districts are left out."] + JP_SHARED,
    "fukuoka": [JP_CENSUS, "Area: Fukuoka City without its mountain districts."] + JP_SHARED,
    "sapporo": [JP_CENSUS, "Area: Sapporo City without its mountain districts (most of Minami ward)."] + JP_SHARED,
    "london": [UK_CENSUS, "Areas: the 33 boroughs, as MSOAs (about 8,000 people each)."] + UK_SHARED,
    "manchester": [UK_CENSUS, "Area: Greater Manchester's ten boroughs, as MSOAs."] + UK_SHARED,
    "birmingham": [UK_CENSUS, "Area: Birmingham, Solihull and the Black Country, as MSOAs; Coventry is left out."] + UK_SHARED,
    "liverpool": [UK_CENSUS, "Area: the Liverpool City Region, including the Wirral across the Mersey, as MSOAs."] + UK_SHARED,
    "brighton": [UK_CENSUS, "Areas: Brighton and Hove only, as the smaller LSOAs (about 1,700 people each) because the city has only about 37 MSOAs."] + UK_SHARED,
}

CITIES["london"]["lads"] = LONDON_BOROUGHS


def in_study(city, municipality_code):
    """Japanese cities: is this 5-digit municipality code inside the study area?"""
    return any(lo <= int(municipality_code) <= hi for lo, hi in CITIES[city]["municipalities"])
