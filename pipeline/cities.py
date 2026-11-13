"""Every city in one place: where its data comes from and how its study area is defined.

Used by download.py (fetch the raw data) and osm_places.py (cut venues out of an OSM file).
Study areas are suggestions in the spirit of Sydney (urban suburbs) and Tokyo (23 wards + Tama):
dense, continuous urban areas with a few hundred areas once merged to a similar population.
"""

GEOFABRIK = "https://download.geofabrik.de"

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

    # ---------------------------------------------------------------- UK (Census 2021, MSOAs)
    "london": dict(country="uk", name="London", crs=27700,
                   bbox=(-0.52, 51.28, 0.34, 51.70), osm=f"{GEOFABRIK}/europe/united-kingdom/england/greater-london-latest.osm.pbf",
                   study="Greater London MSOAs (about 1,000 areas of ~9,000 people; merge pairs for ~500 if needed)"),
}

LONDON_BOROUGHS = ["City of London", "Barking and Dagenham", "Barnet", "Bexley", "Brent", "Bromley", "Camden", "Croydon",
                   "Ealing", "Enfield", "Greenwich", "Hackney", "Hammersmith and Fulham", "Haringey", "Harrow", "Havering",
                   "Hillingdon", "Hounslow", "Islington", "Kensington and Chelsea", "Kingston upon Thames", "Lambeth",
                   "Lewisham", "Merton", "Newham", "Redbridge", "Richmond upon Thames", "Southwark", "Sutton",
                   "Tower Hamlets", "Waltham Forest", "Wandsworth", "Westminster"]


def in_study(city, municipality_code):
    """Japanese cities: is this 5-digit municipality code inside the study area?"""
    return any(lo <= int(municipality_code) <= hi for lo, hi in CITIES[city]["municipalities"])
