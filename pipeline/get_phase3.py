"""Phase 3 downloads: Netherlands, Sweden, Denmark (Eurostat grid), Brazil (Sao Paulo). Standard library only, any OS.

    python get_phase3.py

Downloads into <home>/Downloads/phase3/<country>/, skips files it already has (and re-fetches broken zips),
cuts the national files to the study cities, and writes one <home>/Downloads/upload_phase3_<country>.zip each.
No race, ethnicity, nationality or indigenous tables are downloaded.
"""
import csv, io, os, re, shutil, sqlite3, sys, tempfile, time, urllib.request, zipfile
from pathlib import Path

HOME = Path.home() / "Downloads"; ROOT = HOME / "phase3"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"}
csv.field_size_limit(2**31 - 1)
bad = []


def fetch(url, timeout=600):
    for k in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r: return r.read()
        except Exception as e:
            print(f"   retry {k + 1}: {e}"); time.sleep(5 * (k + 1))
    return None


def ok(p):
    if not p.exists() or p.stat().st_size < 1000: return False
    if p.suffix.lower() == ".zip":
        try: return zipfile.ZipFile(p).testzip() is None
        except Exception: return False
    return True


def get(folder, url, name=None):
    d = ROOT / folder; d.mkdir(parents=True, exist_ok=True); p = d / (name or url.split("/")[-1].split("?")[0])
    if ok(p): print("have", folder, p.name); return p
    print("->", folder, p.name, flush=True); tmp = p.with_suffix(p.suffix + ".part"); p.unlink(missing_ok=True)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=1200) as r, open(tmp, "wb") as f:
            shutil.copyfileobj(r, f, 1 << 20)
        tmp.replace(p)
    except Exception as e:
        print("   failed:", e); tmp.unlink(missing_ok=True)
    if not ok(p): bad.append(f"{folder}/{p.name}")
    return p


def find(start, pattern, depth=4):
    """First file under a web directory listing whose name matches pattern (case-insensitive)."""
    seen, todo = set(), [(start, 0)]
    while todo:
        u, k = todo.pop(0)
        if u in seen or k > depth: continue
        seen.add(u); html = fetch(u, 120)
        if not html: continue
        for h in re.findall(r'href="([^"?#]+)"', html.decode("latin-1")):
            if h.startswith(("/", "..", "http")) and not h.startswith(start): continue
            full = h if h.startswith("http") else u.rstrip("/") + "/" + h
            if h.endswith("/"): todo.append((full, k + 1))
            elif re.search(pattern, h, re.I): return full
    return None


# ---------------- Netherlands: CBS 100 m grid (Amsterdam, Rotterdam, The Hague, Utrecht; Dutch RD metres) ----------------
NL = {"amsterdam": (111000, 479000, 133000, 494000), "rotterdam": (86000, 430000, 101000, 442000),
      "thehague": (73000, 448000, 88000, 461000), "utrecht": (130000, 451000, 141000, 461000)}
for url in ["https://www.cbs.nl/-/media/cbs/dossiers/nederland-regionaal/vierkanten/100/2017-cbsvierkant100m.zip",   # 2000-2014
            "https://www.cbs.nl/-/media/cbs/dossiers/nederland-regionaal/vierkanten/100/2019-cbs-vk100-2015_v2.zip",
            "https://www.cbs.nl/-/media/cbs/dossiers/nederland-regionaal/vierkanten/100/2023-cbs_vk100_2020_vol.zip",
            "https://download.cbs.nl/vierkant/100/2026-cbs_vk100_2023_vol.zip"]:
    get("netherlands", url)


def nl_keep(code):
    m = re.search(r"E(\d+)N(\d+)", str(code))
    if not m: return False
    x, y = int(m.group(1)), int(m.group(2))
    if x < 10000: x, y = x * 100, y * 100           # hectometre codes, e.g. E0643N4567
    return any(a <= x < c and b <= y < d for a, b, c, d in NL.values())


out = ROOT / "netherlands" / "cut"; out.mkdir(parents=True, exist_ok=True)
for z in sorted((ROOT / "netherlands").glob("*.zip")):
    if not ok(z): continue
    with zipfile.ZipFile(z) as zf, tempfile.TemporaryDirectory() as td:
        for name in zf.namelist():
            low = name.lower()
            if low.endswith(".gpkg"):
                gp = zf.extract(name, td); con = sqlite3.connect(gp)
                for (tab,) in con.execute("select table_name from gpkg_contents where data_type='features'"):
                    cols = [r[1] for r in con.execute(f'pragma table_info("{tab}")') if r[2].upper() != "BLOB"]
                    code = next((c for c in cols if "28992" in c.lower() or "vierkant" in c.lower() or c.lower().startswith("c28992")), None)
                    if not code: continue
                    o = out / f"{z.stem}__{tab}.csv"
                    with open(o, "w", newline="", encoding="utf-8") as f:
                        w = csv.writer(f); w.writerow(cols); n = 0
                        for row in con.execute(f'select {",".join(chr(34) + c + chr(34) for c in cols)} from "{tab}"'):
                            if nl_keep(row[cols.index(code)]): w.writerow(row); n += 1
                    print(f"cut {z.name}/{tab}: {n} squares")
                con.close()
            elif low.endswith(".dbf"):                     # 2000-2014 bundle: keep the attribute tables whole (small)
                (out / f"{z.stem}__{Path(name).name}").write_bytes(zf.read(name)); print("kept", name)

# ---------------- Sweden: SCB 1 km grid, whole country (small), 2015, 2020, 2025 ----------------
for y in (2015, 2020, 2025):
    get("sweden", f"https://geodata.scb.se/geoserver/stat/wfs?service=WFS&REQUEST=GetFeature&version=1.1.0"
                  f"&TYPENAMES=stat:befolkning_1km_{y}&outputFormat=geopackage", f"befolkning_1km_{y}.gpkg")

# ---------------- Denmark (and the Swedish and Dutch cities again): Eurostat 1 km grid, 2011 and 2021 ----------------
EU = {"copenhagen": (4471000, 3613000, 4492000, 3631000), "aarhus": (4325000, 3666000, 4338000, 3679000),
      "stockholm": (4766000, 4041000, 4789000, 4061000), "gothenburg": (4431000, 3838000, 4447000, 3853000),
      "malmo": (4505000, 3606000, 4517000, 3619000), "amsterdam": (3963000, 3254000, 3985000, 3271000),
      "rotterdam": (3935000, 3208000, 3951000, 3221000), "thehague": (3923000, 3226000, 3938000, 3241000),
      "utrecht": (3980000, 3226000, 3992000, 3237000)}
for url in ["https://ec.europa.eu/eurostat/cache/GISCO/geodatafiles/GEOSTAT-grid-POP-1K-2011-V2-0-1.zip",
            "https://gisco-services.ec.europa.eu/census/2021/Eurostat_Census-GRID_2021_V3.zip"]:
    get("eu_grid", url)


def eu_keep(line):
    m = re.search(r"N(\d+)E(\d+)", line)
    if not m: return False
    n, e = int(m.group(1)), int(m.group(2))
    if n < 100000: n, e = n * 1000, e * 1000
    return any(a <= e < c and b <= n < d for a, b, c, d in EU.values())


def walk(zf, tag, out):
    for name in zf.namelist():
        low = name.lower()
        if low.endswith(".zip"): walk(zipfile.ZipFile(io.BytesIO(zf.read(name))), tag, out); continue
        if not low.endswith(".csv"): continue
        with zf.open(name) as fh:
            raw = io.TextIOWrapper(fh, encoding="latin-1", newline=""); head = raw.readline()
            o = out / f"{tag}__{Path(name).name}"; k = 0
            with open(o, "w", encoding="utf-8") as w:
                w.write(head)
                for line in raw:
                    if eu_keep(line): w.write(line); k += 1
            if k == 0: o.unlink()
            else: print(f"cut {tag}/{Path(name).name}: {k} cells")


out = ROOT / "eu_grid" / "cut"; out.mkdir(parents=True, exist_ok=True)
for z in (ROOT / "eu_grid").glob("*.zip"):
    if ok(z): walk(zipfile.ZipFile(z), z.stem, out)

# ---------------- Brazil: Sao Paulo city (municipality 3550308), census sectors 2010 and 2022 ----------------
B22 = "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/Agregados_por_Setor_csv/"
for f in ["Agregados_por_setores_basico_BR_20260520.zip", "Agregados_por_setores_demografia_BR.zip",
          "Agregados_por_setores_caracteristicas_domicilio1_BR_20261021.zip",
          "Agregados_por_setores_caracteristicas_domicilio2_BR_20250417.zip", "Agregados_por_setores_parentesco_BR.zip",
          "Agregados_por_setores_alfabetizacao_BR.zip"]:
    get("brazil", B22 + f)
get("brazil", "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/"
              + "dicionario_de_dados_agregados_por_setores_censitarios.xlsx")
G = "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_de_setores_censitarios__divisoes_intramunicipais/"
for start, pat, name in [(G + "censo_2022/", r"(^|/)SP_?.*setor.*\.zip$|(^|/)SP_.*\.zip$", "malha_SP_2022.zip"),
                         (G + "censo_2010/", r"sp_setores_censitarios\.zip$", "malha_SP_2010.zip"),
                         ("https://ftp.ibge.gov.br/Censos/Censo_Demografico_2010/Resultados_do_Universo/Agregados_por_Setores_Censitarios/",
                          r"SP_Capital.*\.zip$", "agregados_SP_Capital_2010.zip")]:
    u = find(start, pat)
    print("found", u)
    if u: get("brazil", u, name)
    else: bad.append(f"brazil/{name} (not found)")

out = ROOT / "brazil" / "cut"; out.mkdir(parents=True, exist_ok=True)
for z in (ROOT / "brazil").glob("Agregados_por_setores_*.zip"):
    if not ok(z): continue
    with zipfile.ZipFile(z) as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".csv"): continue
            with zf.open(name) as fh:
                raw = io.TextIOWrapper(fh, encoding="latin-1", newline=""); head = raw.readline(); k = 0
                with open(out / Path(name).name, "w", encoding="utf-8") as w:
                    w.write(head)
                    for line in raw:
                        if line.lstrip('"').startswith("3550308"): w.write(line); k += 1
                print(f"cut {Path(name).name}: {k} Sao Paulo sectors")

# ---------------- one upload zip per country ----------------
pack = {"netherlands": ["cut"], "sweden": ["."], "eu_grid": ["cut"],
        "brazil": ["cut", "malha_SP_2022.zip", "malha_SP_2010.zip", "agregados_SP_Capital_2010.zip",
                   "dicionario_de_dados_agregados_por_setores_censitarios.xlsx"]}
for c, parts in pack.items():
    zp = HOME / f"upload_phase3_{c}.zip"; zp.unlink(missing_ok=True)
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as zf:
        for part in parts:
            p = ROOT / c / part
            files = [p] if p.is_file() else sorted(q for q in p.rglob("*") if q.is_file()) if p.exists() else []
            for q in files:
                if q.name.endswith(".part") or (c == "sweden" and q.suffix.lower() != ".gpkg"): continue
                zf.write(q, q.relative_to(ROOT))
    print(f"{zp}  {zp.stat().st_size / 1e6:.0f} MB")
print("\nDONE. Upload the four upload_phase3_*.zip files in Downloads." if not bad else
      "\nThese did not download (run the same command again; good files are kept): " + ", ".join(bad))
