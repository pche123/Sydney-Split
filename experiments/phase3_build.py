"""Phase 3 areas: 1 km cells with every year's values, for the Netherlands, Sweden, Denmark and São Paulo.

    python experiments/phase3_build.py <phase3 folder from pipeline/get_phase3.py, unpacked>

Writes results/phase3/<city>_cells.csv.gz: one row per 1 km cell (x, y = lower-left corner in the city's metric CRS),
residents in the reference year, and per variable and year the counts needed for its share (num_<var>_<year>,
den_<var>_<year>). Variable definitions are in HYPOTHESES.md (Phase 3). Shares are built only from small areas where
both counts are published (CBS suppresses small 100 m counts; SCB perturbs them).
"""
import glob, os, re, sys, zipfile, io
import numpy as np, pandas as pd, geopandas as gpd, pyogrio
from shapely.geometry import box
from scipy import sparse
from scipy.sparse.csgraph import connected_components

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); IN = sys.argv[1]
OUT = os.path.join(ROOT, "results", "phase3"); os.makedirs(OUT, exist_ok=True)
NL = {"amsterdam": (111000, 479000, 133000, 494000), "rotterdam": (86000, 430000, 101000, 442000),
      "thehague": (73000, 448000, 88000, 461000), "utrecht": (130000, 451000, 141000, 461000)}
SE = {"stockholm": (661000, 6571000, 683000, 6589000), "gothenburg": (311000, 6392000, 328000, 6407000),
      "malmo": (369000, 6155000, 381000, 6167000)}
DK = {"copenhagen": (4471000, 3613000, 4492000, 3631000), "aarhus": (4325000, 3666000, 4338000, 3679000)}
CRS = {**{c: 28992 for c in NL}, **{c: 3006 for c in SE}, **{c: 3035 for c in DK}, "saopaulo": 31983}


def keep_largest(df):
    df = df[df.ref_pop >= 1000].reset_index(drop=True)
    key = {(a, b): i for i, (a, b) in enumerate(zip(df.x, df.y))}
    E = [(i, key[(a + dx, b + dy)]) for i, (a, b) in enumerate(zip(df.x, df.y)) for dx, dy in ((1000, 0), (0, 1000)) if (a + dx, b + dy) in key]
    E = np.array(E); _, lab = connected_components(sparse.coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), shape=(len(df),) * 2), directed=False)
    return df[lab == np.bincount(lab).argmax()].reset_index(drop=True)


def pair(num, den):
    """Counts from small areas where both are published (non-negative), so shares are not biased by suppression."""
    ok = (num >= 0) & (den > 0)
    return num.where(ok, 0), den.where(ok, 0)


# ---------------- Netherlands ----------------
def nl_xy(code):
    m = code.str.extract(r"E(\d+)N(\d+)").astype(float)
    x, y = m[0], m[1]; small = x < 10000
    x[small] *= 100; y[small] *= 100
    return (np.floor(x / 1000) * 1000).astype("Int64"), (np.floor(y / 1000) * 1000).astype("Int64")


def nl_frame(path, code, cols, rename):
    if path.endswith(".csv"):
        d = pd.read_csv(path, usecols=[code] + cols, low_memory=False)
    else:
        d = pyogrio.read_dataframe(path, columns=[code] + cols, read_geometry=False)
    d = d.rename(columns=rename); d[code] = d[code].astype(str)
    d["x"], d["y"] = nl_xy(d[code]); d = d.dropna(subset=["x"])
    for c in rename.values():
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(-1)
    return d


N = f"{IN}/netherlands/cut"
src = {2023: (glob.glob(f"{N}/*2023*.csv")[0], "crs28992res100m"), 2020: (glob.glob(f"{N}/*2020*.csv")[0], "crs28992res100m"),
       2015: (glob.glob(f"{N}/*2015*.dbf")[0], "C28992R100")}
new = dict(pop="aantal_inwoners", old="aantal_inwoners_65_jaar_en_ouder", hh="aantal_part_huishoudens", alone="aantal_eenpersoonshuishoudens",
           dw="aantal_woningen", rentpct="percentage_huurwoningen", hhsize="gemiddelde_huishoudensgrootte")
old15 = dict(pop="INWONER", old="INW_65PL", hh="AANTAL_HH", alone="TOTHH_EENP", dw="WONING", rentpct="P_HUURWON", hhsize="GEM_HH_GR")
NLD = {}
for y, (p, code) in src.items():
    m = new if y != 2015 else old15
    NLD[y] = nl_frame(p, code, list(m.values()), {v: k for k, v in m.items()})
d11 = nl_frame(glob.glob(f"{N}/*20002014*.dbf")[0], "C28992R100", ["INW2011", "I2011_65PL"], {"INW2011": "pop", "I2011_65PL": "old"})
NLD[2011] = d11
for city, (x0, y0, x1, y1) in NL.items():
    agg = []
    for y, d in NLD.items():
        d = d[(d.x >= x0) & (d.x < x1) & (d.y >= y0) & (d.y < y1)].copy()
        g = pd.DataFrame({"x": d.x, "y": d.y})
        n, k = pair(d.old, d["pop"]); g[f"num_grey_{y}"], g[f"den_grey_{y}"] = n, k
        if "alone" in d:
            n, k = pair(d.alone, d.hh); g[f"num_alone_{y}"], g[f"den_alone_{y}"] = n, k
            ok = (d.rentpct >= 0) & (d.dw > 0); g[f"num_renters_{y}"] = (d.rentpct / 100 * d.dw).where(ok, 0); g[f"den_renters_{y}"] = d.dw.where(ok, 0)
            ok = (d.hhsize > 0) & (d.hh > 0); g[f"num_hhsize_{y}"] = (d.hhsize * d.hh).where(ok, 0); g[f"den_hhsize_{y}"] = d.hh.where(ok, 0)
        if y == 2023: g["ref_pop"] = d["pop"].clip(lower=0)
        agg.append(g.groupby(["x", "y"]).sum())
    df = pd.concat(agg, axis=1).fillna(0).reset_index(); df["x"] = df.x.astype(int); df["y"] = df.y.astype(int)
    df = keep_largest(df); df.to_csv(os.path.join(OUT, f"{city}_cells.csv.gz"), index=False)
    print(city, len(df), "cells", int(df.ref_pop.sum()), "residents (2023)", flush=True)

# ---------------- Sweden ----------------
SEY = {}
for f in sorted(glob.glob(f"{IN}/sweden/befolkning_1km_*.gpkg")):
    y = int(re.search(r"(\d{4})", os.path.basename(f)).group(1))
    g = gpd.read_file(f); b = g.geometry.bounds
    g["x"] = (np.round(b.minx / 1000) * 1000).astype(int); g["y"] = (np.round(b.miny / 1000) * 1000).astype(int)   # corners carry float noise
    oldc = [c for c in g.columns if re.fullmatch(r"ald(6[5-9]|[7-9]\d|100w?)_?\d*", c)]
    allc = [c for c in g.columns if c.startswith("ald")]
    g["old"] = g[oldc].sum(axis=1); g["agesum"] = g[allc].sum(axis=1); g["pop"] = g.beftotalt
    SEY[y] = g[["x", "y", "pop", "old", "agesum"]]
    print("sweden", y, "65+ columns:", oldc)
for city, (x0, y0, x1, y1) in SE.items():
    parts = []
    for y, g in SEY.items():
        g = g[(g.x >= x0) & (g.x < x1) & (g.y >= y0) & (g.y < y1)]
        h = pd.DataFrame({"x": g.x, "y": g.y, f"num_grey_{y}": g.old, f"den_grey_{y}": g.agesum})
        if y == max(SEY): h["ref_pop"] = g["pop"]
        parts.append(h.groupby(["x", "y"]).sum())
    df = keep_largest(pd.concat(parts, axis=1).fillna(0).reset_index())
    df.to_csv(os.path.join(OUT, f"{city}_cells.csv.gz"), index=False); print(city, len(df), "cells", int(df.ref_pop.sum()), "residents", flush=True)

# ---------------- Denmark (Eurostat 2021) ----------------
E = pd.read_csv(glob.glob(f"{IN}/eu_grid/cut/*ESTAT_Census_2021_V3.csv")[0])
E["y"] = E.GRD_ID.str.extract(r"N(\d+)E")[0].astype(int); E["x"] = E.GRD_ID.str.extract(r"E(\d+)$")[0].astype(int)
for city, (x0, y0, x1, y1) in DK.items():
    e = E[(E.CNTR_ID == "DK") & (E.x >= x0) & (E.x < x1) & (E.y >= y0) & (E.y < y1)]
    df = pd.DataFrame({"x": e.x, "y": e.y, "ref_pop": e["T"], "num_grey_2021": e.Y_GE65.clip(lower=0), "den_grey_2021": e["T"].clip(lower=0),
                       "num_working_2021": e.EMP.clip(lower=0), "den_working_2021": e["T"].clip(lower=0)})
    df = keep_largest(df); df.to_csv(os.path.join(OUT, f"{city}_cells.csv.gz"), index=False); print(city, len(df), "cells", int(df.ref_pop.sum()), "residents", flush=True)

# ---------------- São Paulo ----------------
B = f"{IN}/brazil"; num = lambda s: pd.to_numeric(s.astype(str).str.replace(",", "."), errors="coerce")
s22 = gpd.read_file(glob.glob(f"{B}/map2022/*.shp")[0]); s22 = s22[s22.CD_MUN.astype(str) == "3550308"].to_crs(31983)
b = pd.read_csv(f"{B}/cut/Agregados_por_setores_basico_BR.csv", sep=";", dtype=str)
dm = pd.read_csv(f"{B}/cut/Agregados_por_setores_demografia_BR.csv", sep=";", dtype=str)
v22 = pd.DataFrame({"setor": b.CD_SETOR, "pop": num(b.v0001), "hh": num(b.v0007), "hhsize": num(b.v0005)}).merge(
      pd.DataFrame({"setor": dm.CD_setor, "agepop": num(dm.V01006), "old": num(dm.V01040) + num(dm.V01041)}), on="setor", how="left")
s22 = s22.merge(v22, left_on="CD_SETOR", right_on="setor", how="inner")
z = zipfile.ZipFile(f"{B}/malha_SP_2010.zip"); td = os.path.join(OUT, "_tmp_sp2010"); z.extractall(td)
s10 = gpd.read_file(glob.glob(f"{td}/**/*.shp", recursive=True)[0]); s10 = s10[s10.CD_GEOCODM.astype(str) == "3550308"].to_crs(31983)
bb = pd.read_csv(f"{B}/sp2010/Basico_SP1.csv", sep=";", encoding="latin1", dtype=str)
p13 = pd.read_csv(f"{B}/sp2010/Pessoa13_SP1.csv", sep=";", encoding="latin1", dtype=str)
v10 = pd.DataFrame({"setor": bb.Cod_setor, "hh": num(bb.V001), "res": num(bb.V002), "hhsize": num(bb.V003)}).merge(
      pd.DataFrame({"setor": p13.Cod_setor, "agepop": num(p13.V001), "old": sum(num(p13[f"V{i:03d}"]) for i in range(94, 135))}), on="setor", how="left")
s10 = s10.merge(v10, left_on="CD_GEOCODI", right_on="setor", how="inner")
print("sao paulo sectors: 2022", len(s22), int(s22["pop"].sum()), "residents; 2010", len(s10), int(s10.agepop.sum()), "residents", flush=True)


def to_cells(sec, cols):
    sec = sec.copy(); sec["sa"] = sec.area; x0, y0, x1, y1 = (np.floor(np.array(sec.total_bounds) / 1000) * 1000).astype(int)
    xs = [(x, y) for x in range(x0, x1 + 1000, 1000) for y in range(y0, y1 + 1000, 1000)]
    grid = gpd.GeoDataFrame({"x": [a for a, _ in xs], "y": [c for _, c in xs]}, geometry=[box(a, c, a + 1000, c + 1000) for a, c in xs], crs=sec.crs)
    ov = gpd.overlay(sec[cols + ["sa", "geometry"]], grid, how="intersection", keep_geom_type=True); w = ov.area / ov.sa
    return ov[cols].mul(w, axis=0).assign(x=ov.x, y=ov.y).groupby(["x", "y"]).sum()


for s in (s22, s10):
    for c in ("old", "agepop", "hh", "hhsize"): s[c] = s[c].fillna(-1)
s22["n_old"], s22["d_old"] = pair(s22.old, s22.agepop); s22["n_hs"] = (s22.hhsize * s22.hh).where((s22.hhsize > 0) & (s22.hh > 0), 0); s22["d_hs"] = s22.hh.where(s22.hhsize > 0, 0).clip(lower=0)
s10["n_old"], s10["d_old"] = pair(s10.old, s10.agepop); s10["n_hs"] = (s10.hhsize * s10.hh).where((s10.hhsize > 0) & (s10.hh > 0), 0); s10["d_hs"] = s10.hh.where(s10.hhsize > 0, 0).clip(lower=0)
c22 = to_cells(s22, ["pop", "n_old", "d_old", "n_hs", "d_hs"]).rename(columns={"pop": "ref_pop", "n_old": "num_grey_2022", "d_old": "den_grey_2022", "n_hs": "num_hhsize_2022", "d_hs": "den_hhsize_2022"})
c10 = to_cells(s10, ["n_old", "d_old", "n_hs", "d_hs"]).rename(columns={"n_old": "num_grey_2010", "d_old": "den_grey_2010", "n_hs": "num_hhsize_2010", "d_hs": "den_hhsize_2010"})
df = keep_largest(c22.join(c10, how="left").fillna(0).reset_index())
df.to_csv(os.path.join(OUT, "saopaulo_cells.csv.gz"), index=False); print("saopaulo", len(df), "cells", int(df.ref_pop.sum()), "residents (2022)", flush=True)
