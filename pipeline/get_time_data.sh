#!/usr/bin/env bash
# Older census data (1991-2015) for the time test. Every link below was checked by hand.
# Run on the Mac:  cd ~/Downloads && bash get_time_data.sh
# Everything lands in ~/Downloads/time_data/<country>/ ; at the end it prints OK/BAD per file
# and builds one upload_<country>.zip per country in Downloads (Germany and the EU grid are cut to our cities first).

set -u
ROOT=~/Downloads/time_data
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/130 Safari/537.36"
get() { # get <folder> <url> [name]
  mkdir -p "$ROOT/$1"; local name="${3:-$(basename "${2%%\?*}")}"
  local p="$ROOT/$1/$name"
  if [ -s "$p" ]; then case "$name" in *.zip) unzip -tq "$p" >/dev/null 2>&1 && { echo "have $1/$name"; return; } ;; *) echo "have $1/$name"; return ;; esac; fi
  echo "-> $1/$name"; curl -L -A "$UA" --retry 20 --retry-delay 5 -s -S -o "$ROOT/$1/$name" "$2"
}

# ---------- Germany: Zensus 2011 on the 100 m grid (same grid as 2022) ----------
Z=http://www.destatis.de/static/DE/zensus/2011_gitterdaten
get germany $Z/Download-Tabelle_Bevoelkerung_im_100_Meter_Gitter.zip
get germany $Z/Tabelle_Haushalt_im_100_Meter-Gitter.zip
get germany $Z/Download-Tabelle_Familien_im_100_Meter-Gitter.zip
get germany $Z/Wohnungen_im_100_Meter-Gitter.zip
get germany $Z/Gebaeude_und_Wohnungen_im_100_Meter-Gitter.zip

# ---------- Italy: census sections 1991, 2001, 2011 (Milan = Lombardia R03, Rome = Lazio R12) ----------
I=https://www.istat.it/storage/cartografia
get italy $I/variabili-censuarie/dati-cpa_1991.zip
get italy $I/variabili-censuarie/dati-cpa_2001.zip
get italy $I/variabili-censuarie/dati-cpa_2011.zip
for y in 91 01 11; do
  yy=$([ $y = 91 ] && echo 1991 || ([ $y = 01 ] && echo 2001 || echo 2011))
  get italy $I/basi_territoriali/WGS_84_UTM/$yy/R03_${y}_WGS84.zip
  get italy $I/basi_territoriali/WGS_84_UTM/$yy/R12_${y}_WGS84.zip
done

# ---------- France: IRIS 2010 and 2015 + matching boundaries ----------
S=https://www.insee.fr/fr/statistiques/fichier
get france $S/2028604/infra-population-2010.zip
get france $S/2028271/base-ic-logement-2010.xls
get france $S/2028259/base-ic-diplomes-formation-2010.xls
get france $S/2028670/infra-activite-resident-10.zip
get france $S/2028571/base-ic-couples-familles-menages-2010.zip
get france $S/3627376/base-ic-evol-struct-pop-2015.zip
get france $S/3627374/base-ic-logement-2015.zip
get france $S/3627372/base-ic-diplomes-formation-2015.zip
get france $S/3627009/base-ic-activite-residents-2015.zip
get france $S/3627367/base-ic-couples-familles-menages-2015.zip
G=https://data.geopf.fr/telechargement/download/CONTOURS-IRIS
get france $G/CONTOURS-IRIS_1-0__SHP_FRA_2013-01-01/CONTOURS-IRIS_1-0__SHP_FRA_2013-01-01.7z
get france $G/CONTOURS-IRIS_2-1__SHP__FRA_2017-01-01/CONTOURS-IRIS_2-1__SHP__FRA_2017-01-01.7z

# ---------- UK: 2011 Census, output areas (England & Wales) ----------
N=https://www.nomisweb.co.uk/output/census/2011
for t in ks102ew ks105ew ks401ew ks402ew ks501ew ks601ew ks608ew; do get uk $N/${t}_2011_oa.zip; done

# ---------- Japan: census on the fixed 500 m grid (Tokyo 5339 5340 5439 5440, Osaka-Kobe-Kyoto 5135 5235) ----------
E="https://www.e-stat.go.jp/gis/statmap-search/data?downloadType=2"
for m in 5339 5340 5439 5440 5135 5235; do
  # 2015 and 2020: age, jobs, tenure (2020 also population and households)
  for s in T001177 T001203 T001204 T001101 T001173 T001182 T001183; do get japan "$E&statsId=$s&code=$m" "${s}_${m}.zip"; done
  # 1995-2010: population and households only (older grids have nothing else)
  for s in T000752 T000386 T000387 T000609; do get japan "$E&statsId=$s&code=$m" "${s}_${m}.zip"; done
done


# ---------- EU: Eurostat 1 km grid, same cells in every year (2006, 2011 population; 2021 age, jobs, moves) ----------
get eu_grid https://ec.europa.eu/eurostat/cache/GISCO/geodatafiles/GEOSTAT_Grid_POP_2006_1K.zip
get eu_grid https://ec.europa.eu/eurostat/cache/GISCO/geodatafiles/GEOSTAT-grid-POP-1K-2011-V2-0-1.zip
get eu_grid https://gisco-services.ec.europa.eu/census/2021/Eurostat_Census-GRID_2021_V3.zip

# ---------- Spain: 2011 census sections + their boundaries ----------
get spain https://www.ine.es/censos2011_datos/indicadores_seccion_censal_csv.zip
get spain https://www.ine.es/censos2011_datos/indicadores_seccen_rejilla.xls
get spain https://www.ine.es/censos2011_datos/cartografia_censo2011_nacional.zip

# ---------- Canada: 2021 census, dissemination areas (Ontario, Quebec, Prairies incl. Alberta) + boundaries ----------
SC=https://www12.statcan.gc.ca/census-recensement/2021
for r in Ontario Quebec Prairies; do
  get canada "$SC/dp-pd/prof/details/download-telecharger/comp/GetFile.cfm?Lang=E&FILETYPE=CSV&GEONO=006_$r" "census2021_DA_$r.zip"
done
get canada $SC/geo/sip-pis/boundary-limites/files-fichiers/lda_000b21a_e.zip


# ---------- UK: 2001 Census Key Statistics for 2001 LSOAs (nomis API, 25,000 rows per call) ----------
# KS002 age 1602, KS012a occupation 1616, KS013 qualifications 1619, KS016 dwellings 1624, KS018 tenure 1626, KS020 households 1628
mkdir -p "$ROOT/uk2001"
for id in 1602 1616 1619 1624 1626 1628; do
  out="$ROOT/uk2001/ks_${id}_lsoa2001.csv"; [ -s "$out" ] && head -1 "$out" | grep -q "_NAME" && [ "$(head -1 "$out" | tr , "\n" | wc -l)" -gt 3 ] && { echo "have uk2001/ks_${id}"; continue; }
  echo "-> uk2001/ks_${id}"; off=0; : > "$out.part"
  while :; do
    curl -s -S -A "$UA" --retry 10 "https://www.nomisweb.co.uk/api/v01/dataset/NM_${id}_1.data.csv?geography=TYPE304&measures=20100&recordoffset=$off" -o page.csv
    n=$(($(wc -l < page.csv) - 1)); [ $n -le 0 ] && break
    if [ $off -eq 0 ]; then cat page.csv >> "$out.part"; else tail -n +2 page.csv >> "$out.part"; fi
    off=$((off + 25000)); [ $n -lt 25000 ] && break
  done
  rm -f page.csv; mv "$out.part" "$out"
done

# ---------- check ----------
echo; echo "=== check ==="
bad=0
for f in $(find "$ROOT" -type f); do
  case "$f" in
    *.zip) unzip -tq "$f" >/dev/null 2>&1 && echo "OK   ${f#$ROOT/}" || { echo "BAD  ${f#$ROOT/}"; bad=1; } ;;
    *) [ $(wc -c < "$f") -gt 100000 ] && echo "OK   ${f#$ROOT/}" || { echo "BAD  ${f#$ROOT/}"; bad=1; } ;;
  esac
done

# ---------- cut Germany to the three cities (the full files are ~840 MB) ----------
python3 - "$ROOT/germany" <<'PY'
import sys, zipfile, glob, os, io, csv
d = sys.argv[1]; out = os.path.join(d, "cut"); os.makedirs(out, exist_ok=True)
box = {"berlin": (4530000, 3252000, 4577000, 3292000), "munich": (4425000, 2773000, 4449000, 2794000),
       "hamburg": (4307000, 3374000, 4340000, 3404000)}
def inside(cid):  # e.g. 100mN32540E45481 -> north 3254000, east 4548100
    try: n = int(cid.split("N")[1].split("E")[0]) * 100; e = int(cid.split("E")[1]) * 100
    except Exception: return None
    for c, (x0, y0, x1, y1) in box.items():
        if x0 <= e < x1 and y0 <= n < y1: return c
for z in glob.glob(os.path.join(d, "*.zip")):
    try: zf = zipfile.ZipFile(z)
    except zipfile.BadZipFile: print("skip (broken)", z); continue
    for name in zf.namelist():
        if not name.lower().endswith(".csv"): continue
        with zf.open(name) as fh:
            raw = io.TextIOWrapper(fh, encoding="latin-1", newline="")
            first = raw.readline(); sep = ";" if first.count(";") > first.count(",") else ","
            outf = os.path.join(out, os.path.basename(name)); w = open(outf, "w", encoding="utf-8"); w.write(first); kept = 0
            for line in raw:
                if inside(line.split(sep, 1)[0].strip('"')): w.write(line); kept += 1
            w.close(); print(f"cut {name}: {kept} rows")
PY

# ---------- cut the EU grid to the ten Phase 2 cities (the 2021 file is EU-wide) ----------
python3 - "$ROOT/eu_grid" <<'PY'
import sys, zipfile, glob, os, io, re
d = sys.argv[1]; out = os.path.join(d, "cut"); os.makedirs(out, exist_ok=True)
box = {"paris": (3725649, 2854877, 3795649, 2924877), "lyon": (3884383, 2495287, 3954383, 2565287),
       "marseille": (3909555, 2220158, 3979555, 2290158), "rome": (4494175, 2056977, 4564175, 2126977),
       "milan": (4222553, 2448417, 4292553, 2518417), "madrid": (3124766, 1995142, 3194766, 2065142),
       "barcelona": (3629765, 2031119, 3699765, 2101119), "berlin": (4516697, 3238252, 4586697, 3308252),
       "munich": (4403636, 2746974, 4473636, 2816974), "hamburg": (4285337, 3347479, 4355337, 3417479)}
pat = re.compile(r"N(\d+)E(\d+)")
def keep(line):
    m = pat.search(line)
    if not m: return False
    n, e = int(m.group(1)), int(m.group(2))
    if n < 100000: n, e = n * 1000, e * 1000          # ids in km (1kmN2689E4337) vs metres
    return any(x0 <= e < x1 and y0 <= n < y1 for x0, y0, x1, y1 in box.values())
def walk(zf, tag):
    for name in zf.namelist():
        low = name.lower()
        if low.endswith(".zip"): walk(zipfile.ZipFile(io.BytesIO(zf.read(name))), tag); continue
        if not low.endswith(".csv"): continue
        with zf.open(name) as fh:
            raw = io.TextIOWrapper(fh, encoding="latin-1", newline=""); head = raw.readline()
            o = os.path.join(out, tag + "__" + os.path.basename(name)); w = open(o, "w", encoding="utf-8"); w.write(head); k = 0
            for line in raw:
                if keep(line): w.write(line); k += 1
            w.close(); print(f"cut {tag}/{name}: {k} rows")
for z in glob.glob(os.path.join(d, "*.zip")):
    try: walk(zipfile.ZipFile(z), os.path.basename(z)[:-4])
    except zipfile.BadZipFile: print("skip (broken)", z)
PY

# ---------- one upload zip per country ----------
cd "$ROOT"
for c in */; do
  c=${c%/}; rm -f ~/Downloads/upload_$c.zip
  case $c in
    germany|eu_grid) zip -rq ~/Downloads/upload_$c.zip $c/cut ;;
    *) zip -rq ~/Downloads/upload_$c.zip $c ;;
  esac
done
ls -lh ~/Downloads/upload_*.zip
[ $bad = 0 ] && echo "All files OK. Upload every upload_*.zip in Downloads." || echo "Some files are BAD (listed above): run the script again, it skips the good ones."
