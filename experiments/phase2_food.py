"""Phase 2b venue lines: Latte (P7, C3), Croissant (F1), Bread (F2), Paella (F3), Starbucks (F4), Timmies (C2), Poutine (C1).

    python experiments/phase2_food.py <folder with phase2/<city>/raw/osm/places.csv> <Eurostat 2021 grid csv>

Definitions are in HYPOTHESES.md ("Venue definitions and areas"). Writes results/phase2/food/tests.csv and poutine.json.
"""
import ast, json, os, re, sys
import numpy as np, pandas as pd, geopandas as gpd
from pyproj import Transformer
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from scipy.stats import norm, rankdata, fisher_exact
from shapely.geometry import box

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path[:0] = [ROOT]
from linetests.landscape import MultiScaleNull

OSM, GRID = sys.argv[1], sys.argv[2]
OUT = os.path.join(ROOT, "results", "phase2", "food"); os.makedirs(OUT, exist_ok=True)
P2 = os.path.join(ROOT, "results", "phase2")
BOX = {"paris": (2.10, 48.72, 2.60, 49.00), "lyon": (4.75, 45.69, 4.98, 45.83), "marseille": (5.28, 43.20, 5.55, 43.42)}
CELLS = {**{c: f"{P2}/germany/{c}" for c in ("berlin", "munich", "hamburg")},
         **{c: f"{P2}/es_it/{c}" for c in ("madrid", "barcelona", "rome", "milan")}}
COUNTRY = {"paris": "fr", "lyon": "fr", "marseille": "fr", "berlin": "de", "munich": "de", "hamburg": "de", "madrid": "es",
           "barcelona": "es", "rome": "it", "milan": "it", "toronto": "ca", "ottawa": "ca", "montreal": "ca", "calgary": "ca", "edmonton": "ca"}
BAKE_CHAINS = r"back-factory|backfactory|backwerk|kamps|ditsch|le crobag|wiener feinb|lila b[aä]cker|junge|steinecke|backhaus mahl|mr\.? baker"
CAFE_CHAINS = r"starbucks|tim horton|second cup|costa|mccaf|columbus caf|coffee fellows|balzac|einstein|espresso house|caff[eè] nero|caf[eé] nero|segafredo|tchibo|lavazza|\bpaul\b|brioche dor"
POUTINE = r"poutin|casse-cro|casse cro|patate|belle province|ashton|lafleur|valentine|frite alors|smoke's"


def rz(v): return norm.ppf((rankdata(v) - 0.5) / len(v))


def venues(city):
    P = pd.read_csv(f"{OSM}/phase2/{city}/raw/osm/places.csv"); t = P.tags.map(ast.literal_eval)
    g = lambda k: t.map(lambda q: str(q.get(k, "")).lower())
    am, sh, cu = g("amenity"), g("shop"), g("cuisine")
    nm = t.map(lambda q: " | ".join(str(q.get(k, "")) for k in ("name", "brand", "operator")).lower())
    branded = t.map(lambda q: "brand" in q or "brand:wikidata" in q)
    cafe, ff, bake = am.eq("cafe"), am.eq("fast_food"), sh.isin(["bakery", "pastry"])
    chain_bake = sh.eq("bakery") & nm.str.contains(BAKE_CHAINS, regex=True)
    K = {"cafe": cafe, "fast_food": ff, "croissant": bake,
         "indep_bakery": sh.eq("bakery") & ~branded & ~chain_bake, "chain_bakery": chain_bake,
         "paella": am.eq("restaurant") & cu.str.contains(r"spanish|tapas|paella|regional", regex=True),
         "indep_cafe": cafe & ~branded & ~nm.str.contains(CAFE_CHAINS, regex=True),
         "starbucks": nm.str.contains("starbucks"), "timmies": nm.str.contains("tim horton"),
         "poutine": ff & (cu.str.contains("poutine") | nm.str.contains(POUTINE, regex=True))}
    return P[["lat", "lon"]].assign(**{k: v.values for k, v in K.items()})


def neighbours(x, y):
    key = {(a, b): i for i, (a, b) in enumerate(zip(x, y))}; I, J = [], []
    for i, (a, b) in enumerate(zip(x, y)):
        for dx, dy in ((1000, 0), (0, 1000)):
            j = key.get((a + dx, b + dy))
            if j is not None: I.append(i); J.append(j)
    return np.array(I), np.array(J)


def largest(xy):
    I, J = neighbours(xy.x.values, xy.y.values)
    _, lab = connected_components(sparse.coo_matrix((np.ones(len(I)), (I, J)), shape=(len(xy),) * 2), directed=False)
    return xy[lab == np.bincount(lab).argmax()].reset_index(drop=True)


GR = None
def cells(city, V):
    """Return (x, y, epsg) for the city's 1 km cells."""
    global GR
    if city in CELLS:
        g = gpd.read_file(f"{CELLS[city]}/areas.gpkg").bounds   # lower-left corners (German x, y columns are centres)
        return pd.DataFrame({"x": g.minx.round().astype(int), "y": g.miny.round().astype(int)}), 3035
    if COUNTRY[city] == "fr":
        if GR is None:
            GR = pd.read_csv(GRID, encoding="utf-8-sig", usecols=["GRD_ID", "T", "CNTR_ID"]); GR = GR[GR.CNTR_ID == "FR"]
            GR["y"] = GR.GRD_ID.str.extract(r"N(\d+)")[0].astype(int); GR["x"] = GR.GRD_ID.str.extract(r"E(\d+)")[0].astype(int)
        b = gpd.GeoSeries([box(*BOX[city])], crs=4326).to_crs(3035).iloc[0]
        c = GR[(GR["T"] >= 1000)]; c = c[[b.intersects(box(x, y, x + 1000, y + 1000)) for x, y in zip(c.x, c.y)]]
        return largest(c[["x", "y"]].reset_index(drop=True)), 3035
    tr = Transformer.from_crs(4326, 3347, always_xy=True); X, Y = tr.transform(V.lon.values, V.lat.values)
    c = pd.DataFrame({"x": (np.floor(X / 1000) * 1000).astype(int), "y": (np.floor(Y / 1000) * 1000).astype(int)})
    c = c.value_counts().reset_index(name="n"); c = c[c.n >= 10][["x", "y"]]
    return largest(c.reset_index(drop=True)), 3347


LINES = {"latte": ("cafe", "fast_food"), "croissant": ("croissant", "fast_food"), "bread": ("indep_bakery", "chain_bakery"),
         "paella": ("paella", "fast_food"), "starbucks": ("indep_cafe", "starbucks"), "timmies": ("timmies", "indep_cafe")}
WHICH = {"fr": ["latte", "croissant", "starbucks"], "de": ["latte", "bread", "starbucks"], "es": ["latte", "paella", "starbucks"],
         "it": ["latte", "starbucks"], "ca": ["latte"]}
PATH = os.path.join(OUT, "tests.csv"); rows = pd.read_csv(PATH).to_dict("records") if os.path.exists(PATH) else []
done = {(r["city"], r["line"]) for r in rows}
for city, cc in COUNTRY.items():
    V = venues(city); xy, epsg = cells(city, V)
    tr = Transformer.from_crs(4326, epsg, always_xy=True); X, Y = tr.transform(V.lon.values, V.lat.values)
    key = {(a, b): i for i, (a, b) in enumerate(zip(xy.x, xy.y))}
    idx = np.array([key.get((int(np.floor(a / 1000) * 1000), int(np.floor(b / 1000) * 1000)), -1) for a, b in zip(X, Y)])
    I, J = neighbours(xy.x.values, xy.y.values); W = np.full(len(I), 1000.0)
    geom = gpd.GeoSeries([box(x, y, x + 1000, y + 1000) for x, y in zip(xy.x, xy.y)], crs=epsg)
    todo = WHICH[cc] + (["timmies"] if city in ("toronto", "calgary") else [])
    wd = os.path.join(OUT, city); os.makedirs(wd, exist_ok=True)     # fields for the calibrated double-check
    FF = {}
    for line in todo:
        a, b = LINES[line]; k = idx >= 0
        A = np.bincount(idx[k & V[a].values], minlength=len(xy)); B = np.bincount(idx[k & V[b].values], minlength=len(xy))
        FF[line] = np.log((A + 0.5) / (B + 0.5)) + 1e-9 * np.random.default_rng(0).normal(size=len(xy))
    gpd.GeoDataFrame(xy, geometry=geom).to_file(os.path.join(wd, "areas.gpkg"), driver="GPKG")
    np.savez_compressed(os.path.join(wd, "fields.npz"), I=I, J=J, W=W, ids=np.array(list(FF)), F=np.column_stack(list(FF.values())))
    todo = [l for l in todo if (city, l) not in done]
    if not todo: continue
    GN = MultiScaleNull(geom, I, J, W, m=9); print(f"{city}: {len(xy)} cells", flush=True)
    for line in todo:
        a, b = LINES[line]; k = idx >= 0
        A = np.bincount(idx[k & V[a].values], minlength=len(xy)); B = np.bincount(idx[k & V[b].values], minlength=len(xy))
        r = dict(country=cc, city=city, line=line, cells=len(xy), n_a=int(A.sum()), n_b=int(B.sum()))
        if min(A.sum(), B.sum()) < 30:
            r.update(p=np.nan, note="too few venues")
        else:
            f = np.log((A + 0.5) / (B + 0.5)) + 1e-9 * np.random.default_rng(0).normal(size=len(xy))
            p, obs, nm, par = GN.test(rz(f), 199, seed=11)
            d = np.hypot(xy.x - np.average(xy.x), xy.y - np.average(xy.y))
            rho = pd.Series(f).corr(pd.Series(d.values), method="spearman")
            r.update(p=p, cleanness=obs, null_mean=nm, ell_km=par["ell"], rho_dist=rho, note="quick")
        rows.append(r); pd.DataFrame(rows).to_csv(PATH, index=False)
        print(f"  {line:10s} {r['n_a']:6d} vs {r['n_b']:6d}  p = {r['p']}", flush=True)

# C1 Poutine: Gatineau (Quebec side) vs Ottawa (Ontario side), share of fast food that is poutine/casse-croute
pc = {}
for c in ("gatineau", "ottawa"):
    V = venues(c); pc[c] = (int(V.poutine.sum()), int(V.fast_food.sum()))
(g1, n1), (o1, n2) = pc["gatineau"], pc["ottawa"]
odds, p = fisher_exact([[g1, n1 - g1], [o1, n2 - o1]], alternative="greater")
json.dump(dict(gatineau_poutine=g1, gatineau_fast_food=n1, ottawa_poutine=o1, ottawa_fast_food=n2,
               share_gatineau=g1 / n1, share_ottawa=o1 / n2, odds_ratio=odds, p_one_sided=p),
          open(os.path.join(OUT, "poutine.json"), "w"), indent=1)
print("poutine", pc, "p =", p)
