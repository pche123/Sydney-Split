"""Download the NSW COVID-19 case tables and the ABS postcode-to-suburb correspondence, and zip them for upload.

    python get_covid.py

Any OS, standard library only. Writes upload_covid.zip next to this script.
"""
import io, json, os, sys, urllib.request, zipfile

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "covid_data"); os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (research download)"}


def get(url, timeout=600):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def resources(apis):
    for api in apis:
        try:
            return json.loads(get(api, 60))["result"]["resources"]
        except Exception as e:
            print("  could not list", api, "-", e)
    return []


def fetch(name, urls):
    dest = os.path.join(OUT, name)
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        print("have", name); return True
    for u in urls:
        try:
            print("downloading", name, "from", u, flush=True); b = get(u)
            if len(b) > 1000: open(dest, "wb").write(b); print("  ok,", len(b) // 1024, "KB"); return True
        except Exception as e:
            print("  failed:", e)
    return False


NSW = "https://data.nsw.gov.au/data"; GOV = "https://data.gov.au/data"
# 1. Cases by notification date and postcode (and by likely source)
for pkg, want in [("aefcde60-3b0c-4bc0-9af1-6fe652944ec2", ["confirmed_cases_table1_location.csv", "confirmed_cases_table1_location_agg.csv"]),
                  ("97ea2424-abaf-4f3e-a9f2-b5c883f42b6a", ["confirmed_cases_table4_location_likely_source.csv"])]:
    res = resources([f"{NSW}/api/3/action/package_show?id={pkg}", f"{GOV}/api/3/action/package_show?id={pkg}"])
    for w in want:
        urls = [r["url"] for r in res if r.get("url", "").endswith(w)]
        urls += [f"{NSW}/dataset/{pkg}/resource/{r['id']}/download/{w}" for r in res if r.get("url", "").endswith(w)]
        if w == "confirmed_cases_table1_location.csv":
            urls.append(f"{NSW}/dataset/{pkg}/resource/21304414-1ff1-4243-a5d2-f52778048b29/download/{w}")
        if w == "confirmed_cases_table1_location_agg.csv":
            urls.append(f"{NSW}/dataset/{pkg}/resource/5d63b527-e2b8-4c42-ad6f-677f14433520/download/{w}")
        if w.startswith("confirmed_cases_table4"):
            urls.append(f"{NSW}/dataset/{pkg}/resource/2776dbb8-f807-4fb2-b1ed-184a6fc2c8aa/download/{w}")
        fetch(w, list(dict.fromkeys(urls)))

# 2. ABS ASGS 2021 correspondences: keep only the postcode -> SA2 file
corr = [f for f in os.listdir(OUT) if "POA_2021_SA2_2021" in f]
if not corr:
    res = resources([f"{GOV}/api/3/action/package_show?id=asgs-edition-3-2021-correspondences",
                     f"{GOV}/api/3/action/package_show?id=2c79581f-600e-4560-80a8-98adb1922dfc"])
    urls = [r["url"] for r in res if r.get("id") == "33d822ba-138e-47ae-a15f-460279c3acc3"] + [r["url"] for r in res if str(r.get("url", "")).lower().endswith(".zip")]
    for u in dict.fromkeys(urls):
        try:
            print("downloading ABS correspondences from", u, flush=True); z = zipfile.ZipFile(io.BytesIO(get(u)))
            def walk(zf):
                for m in zf.namelist():
                    if "POA_2021_SA2_2021" in m.replace("\\", "/").split("/")[-1]:
                        open(os.path.join(OUT, m.split("/")[-1]), "wb").write(zf.read(m)); print("  kept", m)
                    elif m.lower().endswith(".zip"):
                        walk(zipfile.ZipFile(io.BytesIO(zf.read(m))))
            walk(z)
            if [f for f in os.listdir(OUT) if "POA_2021_SA2_2021" in f]: break
        except Exception as e:
            print("  failed:", e)

have = sorted(os.listdir(OUT)); print("\nfiles:", have)
zp = os.path.join(HERE, "upload_covid.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for f in have: z.write(os.path.join(OUT, f), f"covid/{f}")
print(f"\nwrote {zp} ({os.path.getsize(zp) // 1024} KB) - upload this file")
if not any("table1" in f for f in have) or not any("POA_2021_SA2_2021" in f for f in have):
    print("SOMETHING IS MISSING - upload the zip anyway and say so")
