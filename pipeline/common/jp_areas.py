"""Japanese city: build 町 (丁目 merged), pick the study area, merge into suburb-sized areas, cut the Census tables.

    pip install geopandas scikit-learn scipy
    python pipeline/common/jp_areas.py osaka data/osaka/census/2020 work/osaka

Writes:
  units.gpkg         every 町 in the study municipalities: U (9-digit key), city, name, population, km2, study flag
  areas.gpkg         study 町 merged, inside each ward/city, into areas of about target_pop people (cities.py)
  unit_area.csv      which area each study 町 belongs to
  census/T00xxxx.csv every small-area table at 町 level (HYOSYO 2 or 3 rows), columns labelled in Japanese
Same method as Tokyo (which gets 467 areas this way; the published 454 used a slightly stricter 町 filter): Ward clustering of 町 centres, constrained to 町 that share a border, one municipality at a time.
A 町 is in the study area when it has >= 100 residents and (for cities flagged drop_low_density) >= 1,000 per km2.
"""
import glob, os, sys, zipfile
import numpy as np, pandas as pd, geopandas as gpd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.cluster import AgglomerativeClustering

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cities import CITIES, in_study


def unzip_all(root):
    for z in glob.glob(f"{root}/**/*.zip", recursive=True):
        if not os.path.isdir(z[:-4]): zipfile.ZipFile(z).extractall(z[:-4])


def table(path):
    t = pd.read_csv(path, encoding="cp932", dtype=str)
    lab = t.iloc[0]; t = t.iloc[1:]; t = t[t.HYOSYO.isin(["2", "3"])].set_index("KEY_CODE")
    cols = [c for c in t.columns if c.startswith("T")]
    v = t[cols].apply(pd.to_numeric, errors="coerce"); v.columns = [lab[c] for c in cols]; return v


def main(city, raw, out):
    c = CITIES[city]; p = c["pref"]; os.makedirs(f"{out}/census", exist_ok=True)
    unzip_all(raw)
    shp = glob.glob(f"{raw}/**/r2ka{p}.shp", recursive=True) or glob.glob(f"{raw}/**/*.shp", recursive=True)
    g = gpd.read_file(shp[0])
    g = g[g.KEY_CODE.str.len() >= 9].copy()
    g["muni"] = g.PREF.astype(str).str.zfill(2) + g.CITY.astype(str).str.zfill(3)
    g = g[g.muni.map(lambda m: in_study(city, m))]
    g["U"] = g.KEY_CODE.str[:9]
    g["NAME"] = g.S_NAME.fillna("").str.replace(r"[一二三四五六七八九十]+丁目$", "", regex=True)
    U = g.to_crs(c["crs"]).dissolve("U", aggfunc={"muni": "first", "CITY_NAME": "first", "NAME": "first", "JINKO": "sum"}).reset_index()
    U = U.rename(columns={"JINKO": "population"}); U["km2"] = U.area / 1e6
    dens = U.population / U.km2
    U["study"] = (U.population >= 100) & ((dens >= 1000) | (not c.get("drop_low_density")))
    U.to_file(f"{out}/units.gpkg", driver="GPKG")
    print("municipalities:", ", ".join(sorted(set(U.CITY_NAME))))   # check this list against the study area in cities.py
    S = U[U.study].reset_index(drop=True)

    # 町 that share a border (a few metres of slack for slivers)
    buf = gpd.GeoDataFrame(geometry=S.buffer(5), crs=S.crs)
    pairs = gpd.sjoin(buf, buf, predicate="intersects"); pairs = pairs[pairs.index < pairs.index_right]
    I0, J0 = pairs.index.values, pairs.index_right.values
    xy = np.column_stack([S.representative_point().x, S.representative_point().y])
    lab = np.full(len(S), -1); nxt = 0
    for _, idx in S.groupby("muni").indices.items():
        idx = np.array(sorted(idx)); pos = {u: k for k, u in enumerate(idx)}
        m = np.isin(I0, idx) & np.isin(J0, idx)
        A = coo_matrix((np.ones(m.sum()), ([pos[i] for i in I0[m]], [pos[j] for j in J0[m]])), shape=(len(idx), len(idx)))
        A = ((A + A.T) > 0).astype(float)
        ncomp, comp = connected_components(A, directed=False)
        for k_ in range(ncomp):
            sub = np.where(comp == k_)[0]; k = int(max(1, round(S.population.values[idx[sub]].sum() / c["target_pop"])))
            if k >= len(sub): l = np.arange(len(sub))
            elif k == 1: l = np.zeros(len(sub), int)
            else: l = AgglomerativeClustering(n_clusters=k, connectivity=A.tocsr()[sub][:, sub], linkage="ward").fit_predict(xy[idx[sub]])
            for u in np.unique(l): lab[idx[sub[l == u]]] = nxt; nxt += 1
    S["area"] = lab
    S[["U", "area", "muni", "CITY_NAME", "NAME", "population"]].to_csv(f"{out}/unit_area.csv", index=False)
    A_ = S.dissolve("area", aggfunc={"population": "sum", "CITY_NAME": "first", "NAME": "first"}).reset_index()
    A_["km2"] = A_.area / 1e6; A_.to_file(f"{out}/areas.gpkg", driver="GPKG")
    print(f"{c['name']}: {len(U)} 町, {len(S)} in study, {len(A_)} areas, median {int(A_.population.median()):,} people")

    for f in sorted(glob.glob(f"{raw}/**/tbl*C{p}.txt", recursive=True)):
        t = table(f); t[t.index.isin(set(S.U))].to_csv(f"{out}/census/{os.path.basename(f)[3:10]}.csv")
    print("  tables ->", f"{out}/census")


if __name__ == "__main__":
    main(*sys.argv[1:4])
