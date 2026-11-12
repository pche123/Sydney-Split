"""Export everything the web app needs into one JSON (map paths, lines, profiles, suburb passport)."""
import sys, json, re, numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import mapping

shp, out = sys.argv[1:3]
a = pd.read_csv("q_classic/areas.csv", dtype=str)
G = gpd.read_file(shp).to_crs(7856).set_index("SA2_CODE21").loc[a.SA2_CODE21].reset_index()
Gfull = G.copy()
G["geometry"] = G.geometry.simplify(70, preserve_topology=True)
sig = pd.read_csv("signals_all.csv", dtype={"SA2_CODE_2021": str}).set_index("SA2_CODE_2021").loc[a.SA2_CODE21].reset_index(drop=True)

# projection: metres (EPSG:7856) -> viewBox units
minx, miny, maxx, maxy = G.total_bounds
S = 1000 / (maxx - minx); H = (maxy - miny) * S
def P(x, y): return f"{(x - minx) * S:.1f},{(maxy - y) * S:.1f}"
def path(geom):
    out = []
    def ring(coords): return "M" + "L".join(P(x, y) for x, y in coords) + "Z"
    def line(coords): return "M" + "L".join(P(x, y) for x, y in coords)
    gt = geom.geom_type
    if gt == "Polygon": out += [ring(geom.exterior.coords)] + [ring(r.coords) for r in geom.interiors]
    elif gt == "MultiPolygon": [out.extend(path(p).split("|")) for p in geom.geoms]
    elif gt == "LineString": out.append(line(geom.coords))
    elif gt in ("MultiLineString", "GeometryCollection"):
        for g in geom.geoms:
            if g.geom_type in ("LineString", "MultiLineString"): out.append(path(g))
    return "|".join(out) if gt in ("MultiPolygon",) else "".join(out)

def short(n):
    n = n.split(" - ")[0]
    return re.sub(r" \((NSW|East|West|North|South)\)", lambda m: "" if m.group(1) == "NSW" else f" ({m.group(1)})", n)

areas = [dict(name=G.SA2_NAME21[i], short=short(G.SA2_NAME21[i]), d=path(G.geometry[i]).replace("|", ""),
              cx=round((G.geometry[i].representative_point().x - minx) * S, 1),
              cy=round((maxy - G.geometry[i].representative_point().y) * S, 1),
              pop=int(sig.population[i])) for i in range(len(G))]

# plain-English names for signals
NICE = {"kids_0_14": "kids", "young_adults_20_34": "people in their 20s and early 30s", "retirees_65plus": "over-65s",
 "year12_finished": "people who finished Year 12", "median_age_persons": "older median age", "median_mortgage_repay_monthly": "bigger mortgage repayments",
 "median_rent_weekly": "higher rents", "median_tot_hhd_inc_weekly": "higher household income", "average_num_psns_per_bedroom": "more people per bedroom",
 "average_household_size": "bigger households", "private_high_school": "kids at private high schools", "uni_students": "uni students",
 "tafe_students": "TAFE students", "volunteers": "volunteers", "no_car": "households with no car", "three_plus_cars": "households with 3+ cars",
 "living_alone": "people living alone", "share_houses": "share houses", "big_households_6plus": "households of 6+", "detached_houses": "detached houses",
 "townhouses": "townhouses", "apartments": "apartments", "high_rise_9plus": "high-rise apartments", "empty_dwellings": "empty dwellings",
 "owned_outright": "homes owned outright", "mortgaged": "homes with a mortgage", "renting_private": "private renters", "social_housing": "social housing",
 "four_plus_bedrooms": "4+ bedroom homes", "moved_in_last_year": "people who moved in the last year", "arrived_from_overseas_last_year": "recent arrivals from overseas",
 "university_degree": "university degrees", "trade_certificate": "trade certificates", "works_construction": "construction workers",
 "works_manufacturing": "manufacturing workers", "works_health_care": "health-care workers", "works_finance": "finance workers",
 "works_professional_services": "professional-services workers", "works_hospitality": "hospitality workers", "works_transport_logistics": "transport & logistics workers",
 "works_retail": "retail workers", "works_media_tech": "media & IT workers", "works_education": "teachers & education workers", "managers": "managers",
 "professionals": "professionals", "tradies": "tradies", "labourers": "labourers", "drivers_operators": "drivers & machine operators",
 "care_service_workers": "care & service workers", "train_commute": "train commuters", "bus_commute": "bus commuters", "drive_to_work": "people who drive to work",
 "walk_to_work": "people who walk to work", "cycle_to_work": "cyclists", "work_from_home": "people working from home", "ute_truck_commute": "ute & truck commuters",
 "food_venues_per_1k": "food venues per resident", "late_licences_per_1k": "after-midnight liquor licences", "very_late_3am_per_1k": "after-3am liquor licences",
 "pokies_per_1k": "poker machines per resident", "small_bars_per_1k": "small bars", "clubs_per_1k": "licensed clubs", "near_late_night_venue": "further from a late-night venue"}
def nice(c):
    if c in NICE: return NICE[c]
    if c.startswith("share_cuisine_"):
        w = c[14:].replace("_", " ")
        if w in ("thai", "vietnamese", "chinese", "japanese", "korean", "indian", "italian", "greek", "lebanese", "mexican", "portuguese", "turkish", "nepalese"): w = w.title()
        return w + " places in the food mix"
    if c.startswith("share_super_"): return c[12:].title() + " share of supermarkets"
    if c.startswith("share_"): return {"cafe": "cafes", "fast_food": "fast food", "pub": "pubs", "bar": "bars", "bakery": "bakeries", "butcher": "butchers",
                                       "liquor_shop": "bottle shops", "convenience": "convenience stores", "gym": "gyms"}.get(c[6:], c[6:]) + " in the venue mix"
    if c.startswith("near_"):
        b = c[5:]
        nm = b.replace("_", " ").title().replace("Mcdonalds", "McDonald's").replace("Dan Murphys", "Dan Murphy's").replace("Gloria Jeans", "Gloria Jean's").replace("Nandos", "Nando's").replace("Kfc", "KFC").replace("Train Station", "train station").replace("Bubble Tea", "bubble tea shop").replace("Gelato Or Ice Cream", "gelato or ice-cream shop")
        return ("further from an " if nm[0] in "AEIOUF" else "further from a ") + nm
        _ = b.replace("_", " ").title().replace("Mcdonalds", "McDonald's").replace("Dan Murphys", "Dan Murphy's").replace("Gloria Jeans", "Gloria Jean's").replace("Nandos", "Nando's").replace("Kfc", "KFC").replace("F45", "F45")
    return c
exec(open("./labels.py").read())
def nicelist(s): return [more(x.strip()) for x in str(s).split(",") if x.strip() and x.strip() != "nan"]

fun = pd.read_csv("fun_lines_tested.csv"); fs = np.load("fun_sides.npy")
qc, qq = pd.read_csv("q_classic/leaderboard.csv"), pd.read_csv("q_quirky/leaderboard.csv")
sc, sq = np.load("q_classic/sides.npy"), np.load("q_quirky/sides.npy")
GROUP = {"The Latte Line": "Food", "The Red Rooster Line": "Food", "The Charcoal Chook Line": "Food", "The Aldi Line": "Food",
         "The Bubble Tea Line": "Food", "Pho vs Pad Thai": "Food", "The Pokies Line": "Night", "The Late Night Line": "Night", "The Small Bar Line": "Night"}
lines = []
for k, r in fun.iterrows():
    lines.append(dict(id=re.sub(r"[^a-z0-9]+", "-", r.line.lower()).strip("-"), name=r.line, group=GROUP[r.line], a=r.side_A, b=r.side_B, p=float(r.p),
                      more=nicelist(r.A_side_also_more), less=nicelist(r.A_side_also_less), ex_a=[short(x) for x in r.A_examples.split(", ")],
                      ex_b=[short(x) for x in r.B_examples.split(", ")], side=fs[:, k].astype(int).tolist()))
census = [  # (board, sides, rank, name, group, A words, B words, adjusted?)
 (qc, sc, 0, "The Hi-Vis Line", "Work", "more warehouse, driving & labouring jobs", "more professionals and degrees", False),
 (qc, sc, 1, "The Factory Line", "Work", "more manufacturing workers", "fewer manufacturing workers", False),
 (qq, sq, 2, "The Laptop vs Ute Line", "Hidden", "more media & IT workers, relative to tradies", "more tradies, relative to media & IT workers", True),
 (qq, sq, 0, "The Tradie Belt", "Hidden", "bigger households, relative to construction workers", "more construction workers, relative to household size", True),
 (qq, sq, 1, "The Full House Line", "Hidden", "bigger households, relative to logistics workers", "more logistics workers, relative to household size", True),
 (qq, sq, 3, "The Boomer vs Builder Line", "Hidden", "older, relative to construction workers", "younger and more construction workers", True)]
for board, sides, k, nm, grp, aw, bw, adj in census:
    r = board.iloc[k]
    lines.append(dict(id=re.sub(r"[^a-z0-9]+", "-", nm.lower()).strip("-"), name=nm, group=grp, a=aw, b=bw, p=float(r.p_chance), adjusted=adj,
                      more=nicelist(r.higher_side_also_more), less=nicelist(r.higher_side_also_less),
                      ex_a=[short(x) for x in r.most_extreme_high.split(", ")], ex_b=[short(x) for x in r.most_extreme_low.split(", ")],
                      side=sides[:, k].astype(int).tolist()))

for L in lines:  # drop circular chips (the line's own brands)
    own = [w for w in ["Red Rooster", "Messina", "El Jannah", "Starbucks"] if w in L["a"]]
    L["more"] = [c for c in L["more"] if not any(w in c for w in own)]
    L["less"] = [c for c in L["less"] if not any(w in c for w in own)]
SIDES = {
 "The Latte Line": ("More cafés, less fast food", "More fast food, fewer cafés"),
 "The Red Rooster Line": ("A Red Rooster is closer than a Messina", "A Messina is closer than a Red Rooster"),
 "The Charcoal Chook Line": ("An El Jannah is closer than a Starbucks", "A Starbucks is closer than an El Jannah"),
 "The Aldi Line": ("More Aldis, fewer Woolies", "More Woolies, fewer Aldis"),
 "The Pokies Line": ("More poker machines per person", "Fewer poker machines per person"),
 "The Late Night Line": ("More venues licensed past midnight", "Fewer venues licensed past midnight"),
 "The Bubble Tea Line": ("More bubble tea shops", "Fewer bubble tea shops"),
 "Pho vs Pad Thai": ("More Vietnamese than Thai restaurants", "More Thai than Vietnamese restaurants"),
 "The Small Bar Line": ("More small bars, fewer pubs", "More pubs, fewer small bars"),
 "The Hi-Vis Line": ("More warehouse, delivery & labouring jobs", "More office & professional jobs"),
 "The Factory Line": ("More factory workers", "Fewer factory workers"),
 "The Laptop vs Ute Line": ("More tech & media workers, fewer tradies", "More tradies, fewer tech & media workers"),
 "The Tradie Belt": ("Bigger households, fewer builders", "More builders, smaller households"),
 "The Full House Line": ("Bigger households, fewer warehouse & delivery workers", "More warehouse & delivery workers, smaller households"),
 "The Boomer vs Builder Line": ("Older residents, fewer builders", "Younger residents, more builders"),
}
for L in lines:
    if L["name"] in SIDES: L["a"], L["b"] = SIDES[L["name"]]
# boundaries + agreement with Latte Line
latte = np.array(lines[0]["side"], bool)
for L in lines:
    s = np.array(L["side"], bool)
    A_, B_ = Gfull[s].geometry.union_all(), Gfull[~s].geometry.union_all()
    from shapely.ops import linemerge
    seg = A_.boundary.intersection(B_.boundary)
    lines_only = [g for g in getattr(seg, "geoms", [seg]) if g.geom_type in ("LineString", "MultiLineString")]
    from shapely.geometry import MultiLineString
    flat = []
    for g in lines_only: flat += list(getattr(g, "geoms", [g]))
    merged = linemerge(MultiLineString(flat)) if flat else seg
    L["cut"] = path(merged.simplify(40))
    ag = (s == latte).mean(); L["latte_agree"] = round(float(max(ag, 1 - ag)), 2)
    L["n_a"], L["n_b"] = int(s.sum()), int((~s).sum())

# areas with few or no residents (cemeteries, industry, airports, big parks) that sit inside the study area: draw them grey
allG = gpd.read_file(shp).to_crs(7856)
allG = allG[(allG.GCC_CODE21 == "1GSYD") & ~allG.SA2_CODE21.isin(a.SA2_CODE21)]
hull = G.geometry.union_all().convex_hull
inside = allG[allG.geometry.representative_point().within(hull)].copy()
inside["geometry"] = inside.geometry.simplify(70, preserve_topology=True)
empty = [dict(name=short(r.SA2_NAME21), d=path(r.geometry).replace("|", "")) for r in inside.itertuples()]
print("grey areas:", len(empty), ", ".join(e["name"] for e in empty))
labels = ["Sydney (North) - Millers Point", "Bondi Beach - North Bondi", "Manly - Fairlight", "Chatswood - East", "Hornsby - East",
          "Castle Hill - East", "Rouse Hill - Beaumont Hills", "Blacktown (East) - Kings Park", "Penrith", "Parramatta - South",
          "Auburn - Central", "Strathfield - East", "Newtown (NSW)", "Hurstville - Central", "Bankstown - North", "Lakemba",
          "Cabramatta - Lansvale", "Liverpool - East", "Campbelltown - Woodbine", "Camden - Ellis Lane", "Cronulla - Kurnell - Bundeena",
          "Dee Why - North", "Ryde - East", "Mount Druitt - Whalan", "Marrickville - North", "Randwick - North", "St Ives", "Sutherland - Kirrawee"]
names = G.SA2_NAME21.tolist()
lab = [dict(i=names.index(l), t=short(l).replace("Sydney (North)", "CBD")) for l in labels if l in names]
json.dump(dict(w=1000, h=round(H, 1), areas=areas, empty=empty, lines=lines, labels=lab,
               meta=dict(sources="ABS 2021 Census (GCP DataPack, SA2) · ABS ASGS 2021 boundaries · © OpenStreetMap contributors (venues, Nov 2026) · NSW Liquor & Gaming premises list (Nov 2026)",
                         areas=len(G))), open(out, "w"), separators=(",", ":"))
print("areas", len(G), "lines", len(lines), "bytes", len(open(out).read()))
