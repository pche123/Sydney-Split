"""Turn every licence, gaming and food-business list a city has into one tidy points file.

    python pipeline/common/venues.py melbourne data/melbourne work/melbourne/venues.csv

Columns: source, name, lat, lon, kind, drink, egms
  kind   on = drink there (pub, bar, restaurant, club), off = bottle shop, producer = brewery/winery/distillery
         licence, gaming = gaming venue, food:<type> = UK hygiene-rating business type, osm:<tag> for OSM-only cities
  drink  beer / wine / spirits when the venue's own name or licence says so (e.g. "Young Henrys Brewing",
         "Wine bar" business type, "Archie Rose Distilling"), otherwise blank. Never guessed from anything else.
  egms   gaming machines at the venue where the source gives them (NSW, VIC), otherwise blank.
Sources it understands: NSW premises list, VIC liquor licences + VIC gaming expenditure by venue, UK FSA hygiene
ratings XML + Gambling Commission premises register, and OSM (places.csv from osm_places.py) for every city.
"""
import ast, glob, os, re, sys
import xml.etree.ElementTree as ET
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cities import CITIES

DRINK = [("beer", r"brew|taphouse|tap ?room|\bbeer|ale ?house|bierhaus|biergarten|craft beer"),
         ("wine", r"winer|vineyard|wine ?bar|cellar door|enoteca|\bvino\b|wine room|\bwines?\b"),
         ("spirits", r"distill|whisk(e)?y|\bgin\b|\brum\b|spirits|cocktail")]
COLS = ["source", "name", "lat", "lon", "kind", "drink", "egms"]


def drink_of(name):
    n = str(name).lower()
    hits = [d for d, p in DRINK if re.search(p, n)]
    return hits[0] if len(hits) == 1 else ""      # names that mention two drinks stay blank


def col(df, *words):
    """First column whose name contains all the words (case-insensitive); fails loudly with the column list."""
    for c in df.columns:
        if all(w.lower() in str(c).lower() for w in words): return c
    raise SystemExit(f"no column with {words}; columns are: {list(df.columns)}")


def nsw(path):
    x = pd.read_excel(path, header=3) if path.endswith("xlsx") else pd.read_csv(path)
    lt = x["Licence type"].fillna("")
    kind = lt.map(lambda t: "off" if "packaged" in t else "producer" if "producer" in t else "on")
    bt = x["Business type"].fillna("")
    d = x["Licence name"].map(drink_of).where(bt != "Wine bar", "wine")
    egm = pd.to_numeric(x["EGMs"] if "EGMs" in x.columns else pd.Series(index=x.index, dtype=float), errors="coerce")
    return pd.DataFrame(dict(source="nsw_licence", name=x["Licence name"], lat=x.Latitude, lon=x.Longitude,
                             kind=kind, drink=d, egms=egm))


def vic(raw):
    out = []
    for f in glob.glob(f"{raw}/venues/vic_liquor_licences*.xlsx"):
        x = pd.read_excel(f)
        if not any("lat" in str(c).lower() for c in x.columns):    # the sheet has a title block above the header
            x = pd.read_excel(f, header=next(i for i in range(15) if any("lat" in str(v).lower() for v in pd.read_excel(f, header=i).columns)))
        cat = x[col(x, "categ")].fillna("").str.lower()
        kind = cat.map(lambda t: "off" if "packaged" in t else "producer" if "producer" in t else "on")
        nm = x[col(x, "trading")] if any("trading" in str(c).lower() for c in x.columns) else x[col(x, "name")]
        out.append(pd.DataFrame(dict(source="vic_licence", name=nm, lat=x[col(x, "lat")], lon=x[col(x, "lon")],
                                     kind=kind, drink=nm.map(drink_of), egms=None)))
    for f in glob.glob(f"{raw}/venues/vic_gaming_by_venue.xlsx"):
        print("  VIC gaming venues have names and addresses but no coordinates: matched to licences by name in the build step")
        x = pd.read_excel(f, header=None); h = next(i for i in range(20) if x.iloc[i].astype(str).str.contains("Venue", case=False).any())
        x = pd.read_excel(f, header=h)
        out.append(pd.DataFrame(dict(source="vic_gaming", name=x[col(x, "venue")], lat=None, lon=None, kind="gaming",
                                     drink="", egms=pd.to_numeric(x[col(x, "egm")], errors="coerce"))))
    return out


def fsa(raw):
    rows = []
    for f in glob.glob(f"{raw}/venues/fsa/*.xml"):
        for e in ET.parse(f).getroot().iter("EstablishmentDetail"):
            g = lambda k: (e.findtext(k) or "").strip()
            lat, lon = g("Geocode/Latitude"), g("Geocode/Longitude")
            if lat and lon:
                rows.append(("fsa", g("BusinessName"), float(lat), float(lon), "food:" + g("BusinessType"), drink_of(g("BusinessName")), None))
    return [pd.DataFrame(rows, columns=COLS)] if rows else []


def gambling(raw):
    out = []
    for f in glob.glob(f"{raw}/venues/gambling_premises.*"):
        x = pd.read_excel(f, sheet_name=None); x = max(x.values(), key=len)   # the premises tab is the biggest
        pc = x[col(x, "postcode")].astype(str).str.upper().str.replace(" ", "")
        print("  gambling premises are listed by postcode: geocoding with postcodes.io (free, no key)")
        import requests
        ll = {}
        u = sorted(set(pc))
        for i in range(0, len(u), 100):
            r = requests.post("https://api.postcodes.io/postcodes", json={"postcodes": u[i:i + 100]}, timeout=60).json()
            for q in r["result"]:
                if q["result"]: ll[q["query"]] = (q["result"]["latitude"], q["result"]["longitude"])
        act = x[col(x, "activity")].astype(str).str.lower()
        out.append(pd.DataFrame(dict(source="gambling", name=x[col(x, "name")], lat=pc.map(lambda p: ll.get(p, (None, None))[0]),
                                     lon=pc.map(lambda p: ll.get(p, (None, None))[1]), kind="gaming:" + act, drink="", egms=None)))
    return out


def osm(raw):
    f = glob.glob(f"{raw}/osm/places.csv")
    if not f: return []
    d = pd.read_csv(f[0]); t = d.tags.map(ast.literal_eval)
    tag = t.map(lambda q: q.get("amenity") if q.get("amenity") in ("pub", "bar", "biergarten", "nightclub") else
                "shop=" + q["shop"] if q.get("shop") in ("alcohol", "wine", "beverages") else
                "craft=" + q["craft"] if q.get("craft") in ("brewery", "winery", "distillery") else None)
    nm = t.map(lambda q: q.get("name", ""))
    dr = t.map(lambda q: "beer" if q.get("craft") == "brewery" or q.get("microbrewery") == "yes" or q.get("amenity") == "biergarten"
               else "wine" if q.get("craft") == "winery" or q.get("shop") == "wine" else "spirits" if q.get("craft") == "distillery" else "")
    dr = dr.where(dr != "", nm.map(drink_of))
    m = tag.notna()
    return [pd.DataFrame(dict(source="osm", name=nm[m], lat=d.lat[m], lon=d.lon[m], kind="osm:" + tag[m], drink=dr[m], egms=None))]


def main(city, raw, out):
    c = CITIES[city]; parts = []
    if city == "sydney":
        for f in glob.glob(f"{raw}/venues/nsw_premises_list.*"): parts.append(nsw(f))
    if c.get("licences") == "vic": parts += vic(raw)
    if c["country"] == "uk": parts += fsa(raw) + gambling(raw)
    parts += osm(raw)
    if not parts: raise SystemExit("no venue files found; run download.py (and osm_places.py) first")
    v = pd.concat(parts, ignore_index=True)[COLS]
    W, S, E, N = c["bbox"]
    v = v[v.lat.isna() | (v.lon.between(W, E) & v.lat.between(S, N))]
    v.to_csv(out, index=False)
    print(v.groupby(["source", "kind"]).size().to_string(), "\n", v.drink.value_counts().to_string(), "\n->", out)


if __name__ == "__main__":
    main(*sys.argv[1:4])
