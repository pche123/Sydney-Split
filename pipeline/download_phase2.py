"""Phase 2 census downloads: France, Italy, Spain (and Germany, which is optional; see below).

Run from your split_kit folder:   python ~/Downloads/download_phase2.py
Then zip the census part (small) for upload:
    cd data && zip -rq ../upload/phase2_census.zip phase2 -x "phase2/_osm/*" -x "phase2/*/raw/*"

Italy   ISTAT 2021 census sections (Rome: Lazio, Milan: Lombardia) and the 2021 census variables.
Spain   INE 2021 census indicators by census section (Madrid, Barcelona) and the section boundaries.
Germany optional (--germany): Zensus 2022 grid cells. Not needed: I can fetch the same tables from a GitHub mirror.
France  INSEE census 2021 by IRIS (areas of about 2,000 people): population, activity (jobs, socio-professional
        groups, commuting), diplomas, housing, households. Boundaries: IGN CONTOURS-IRIS 2023 (the geography the 2021
        tables use), found on IGN's download listing. Licence: Licence Ouverte / Etalab.
Safe to re-run: anything already downloaded is skipped.
"""
import os, re, sys, time
import requests

ROOT = os.path.join("data", "phase2", "_census")
UA = {"User-Agent": "split-research/1.0 (academic; contact via github.com/pche123)"}


def get(url, **kw):
    for k in range(4):
        try:
            r = requests.get(url, headers=UA, timeout=600, **kw)
            if 200 <= r.status_code < 300: return r
            print("  HTTP", r.status_code, url[:120])
        except Exception as e:
            print("  error", type(e).__name__, str(e)[:120])
        time.sleep(5 * (k + 1))
    return None


def fetch(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 10000: print("  have", os.path.basename(path)); return True
    os.makedirs(os.path.dirname(path), exist_ok=True)
    r = get(url, stream=True)
    if r is None: print("  FAILED", url); return False
    with open(path + ".part", "wb") as f:
        for ch in r.iter_content(1 << 20): f.write(ch)
    os.replace(path + ".part", path); print(f"  saved {os.path.basename(path)} ({os.path.getsize(path) >> 20} MB)"); return True


FR = {   # INSEE base infracommunale 2021 (IRIS), CSV
    "population": "https://www.insee.fr/fr/statistiques/fichier/8268806/base-ic-evol-struct-pop-2021_csv.zip",
    "activite": "https://www.insee.fr/fr/statistiques/fichier/8268843/base-ic-activite-residents-2021_csv.zip",
    "diplomes": "https://www.insee.fr/fr/statistiques/fichier/8268840/base-ic-diplomes-formation-2021_csv.zip",
    "logement": "https://www.insee.fr/fr/statistiques/fichier/8268838/base-ic-logement-2021_csv.zip",
    "menages": "https://www.insee.fr/fr/statistiques/fichier/8268828/base-ic-couples-familles-menages-2021_csv.zip",
}


def france():
    d = os.path.join(ROOT, "france"); print("=== France (INSEE IRIS 2021)")
    for k, u in FR.items(): fetch(u, os.path.join(d, os.path.basename(u)))
    lst = get("https://geoservices.ign.fr/telechargement-api/CONTOURS-IRIS")
    links = re.findall(r'https://data\.geopf\.fr/telechargement/download/CONTOURS-IRIS/[^"\s<]+\.7z', lst.text) if lst else []
    pick = [l for l in links if "LAMB93_FXX_2023" in l and "GPKG" in l] or [l for l in links if "LAMB93_FXX_2023" in l]
    if not pick: print("  IRIS boundaries: link not found on IGN's listing; please download CONTOURS-IRIS 2023 (Lambert 93, France métropolitaine) by hand into", d); return
    fetch(pick[0], os.path.join(d, os.path.basename(pick[0])))
    print("  (the boundaries come as .7z; I unpack them on my side, no need to unpack)")


IT = {   # ISTAT: 2021 census sections (Basi Territoriali 2021, shapefile, WGS84 UTM 32N) per region, and the 2021 census variables
    "R03_21.zip": "https://www.istat.it/storage/cartografia/basi_territoriali/2021/R03_21.zip",          # Lombardia (Milan)
    "R12_21.zip": "https://www.istat.it/storage/cartografia/basi_territoriali/2021/R12_21.zip",          # Lazio (Rome)
    "Dati_regionali_2021.zip": "https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2021.zip",
}
ES = {   # INE Censo 2021: indicators by census section (CSV) and section boundaries at 1 Jan 2021
    "C2021_Indicadores.csv": "https://www.ine.es/censos2021/C2021_Indicadores.csv",
    "indicadores_seccen_c2021.xlsx": "https://www.ine.es/censos2021/indicadores_seccen_c2021.xlsx",
    "Cartografia_secc.zip": "https://www.ine.es/censos2021/Cartografia_secc.zip",
}
DE_BASE = "https://www.destatis.de/static/DE/zensus/gitterdaten/"   # Zensus 2022 grid cells (each zip holds 10 km, 1 km and 100 m)
DE = ["Zensus2022_Bevoelkerungszahl.zip", "Anteil_ab_65-jaehrige_in_Gitterzellen.zip", "Zensus2022_Groesse_des_privaten_Haushalts_in_Gitterzellen.zip",
      "Eigentuemerquote_in_Gitterzellen.zip", "Zensus2022_Durchschn_Nettokaltmiete.zip", "Wohnungen_nach_Gebaeudetyp_Groesse.zip",
      "Leerstandsquote_in_Gitterzellen.zip", "Durchschnittliche_Wohnflaeche_je_Bewohner_in_Gitterzellen.zip", "Typ_der_Kernfamilie_nach_Kindern.zip"]


def bundle(name, files):
    d = os.path.join(ROOT, name); print(f"=== {name}")
    for fn, u in files.items(): fetch(u, os.path.join(d, fn))


if __name__ == "__main__":
    france()
    bundle("italy", IT)
    bundle("spain", ES)
    if "--germany" in sys.argv:   # optional: the same Zensus 2022 tables are mirrored on GitHub (jslth/z22data), which I can fetch myself
        bundle("germany", {f: DE_BASE + f for f in DE})
    print("\nDone. Now:  cd data && zip -rq ../upload/phase2_census.zip phase2/_census")
