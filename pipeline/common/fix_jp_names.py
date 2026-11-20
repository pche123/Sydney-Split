"""Re-read Japanese neighbourhood and ward names in the built app data with their official readings.

Usage: python pipeline/common/fix_jp_names.py   (after pipeline/common/jp_kana.py)
Only names whose current form came from the guessed kanji reading are changed; station-based names (Kyoto) are kept.
"""
import json, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tokyo"))
from romaji import place, ward_official, official, _table, CITY

JP = ["tokyo", "osaka", "kyoto", "nagoya", "yokohama", "kobe", "fukuoka", "sapporo"]
_, CITIES = _table()
BYROMAJI = {v: k for k, v in CITY.items()}

def split_city(jp):
    for n in range(len(jp) - 1, 1, -1):
        if jp[:n] in CITIES:
            return jp[:n], jp[n:]
    return None, jp

def main(app="app"):
    log = []
    for c in JP:
        f = f"{app}/data/{c}.json"; d = json.load(open(f, encoding="utf-8"))
        rename = {}
        SHORT_OLD = [a["short"] for a in d["areas"]]
        for i, a in enumerate(d["areas"]):
            m = re.fullmatch(r"(.+), (.+?) · (.+) area", a["name"])
            if not m:
                continue
            short_old, ward_old, jp = m.groups()
            if c == "tokyo":
                city, town = BYROMAJI.get(ward_old), jp
            else:
                city, town = split_city(jp)
            if not city:
                continue
            ward_new = (ward_official(city) if c != "tokyo" else None) or ward_old
            suf = re.search(r"( \(.+\))?( \d+)?$", short_old).group(0)
            base = short_old[: len(short_old) - len(suf)] if suf else short_old
            new_base = official(town, city)
            if c == "kyoto" or not new_base or base != place(town):   # keep names that didn't come from the guess
                new_base = base
            suf_new = suf.replace(f"({ward_old})", f"({ward_new})")
            short_new = new_base + suf_new
            a["short"] = short_new
            a["name"] = f"{short_new}, {ward_new} · {jp} area"
            if short_new != short_old:
                rename[short_old] = short_new
            if ward_new != ward_old:
                log.append((c, city, "ward " + ward_old, ward_new))
        shorts = [a["short"] for a in d["areas"]]
        wardof = lambda i: re.fullmatch(r".+, (.+?) · .+", d["areas"][i]["name"]).group(1)
        for s in sorted({s for s in shorts if shorts.count(s) > 1}):   # same reading twice: add the ward, as the build does
            idx = [i for i, x in enumerate(shorts) if x == s]
            by_ward = len({wardof(i) for i in idx}) == len(idx)
            for j, i in enumerate(idx):
                new = f"{s} ({wardof(i)})" if by_ward else f"{s} {j + 1}"
                a = d["areas"][i]
                a["name"] = new + a["name"][len(s):]; a["short"] = new; shorts[i] = new
                rename[SHORT_OLD[i]] = new
        dup = {s for s in shorts if shorts.count(s) > 1}
        for i, a in enumerate(d["areas"]):
            if shorts[i] != SHORT_OLD[i]:
                log.append((c, a["name"].split(" · ")[-1][:-5], SHORT_OLD[i], shorts[i]))
        for lab in d.get("labels", []):
            if lab.get("t") in rename and 0 <= lab.get("i", -1) < len(shorts):
                lab["t"] = shorts[lab["i"]]
        for ln in d.get("lines", []):
            for k in ("ex_a", "ex_b"):
                if isinstance(ln.get(k), list):
                    ln[k] = [rename.get(x, x) for x in ln[k]]
        for h in d.get("heritage", []):
            if isinstance(h.get("peaks"), list):
                for p in h["peaks"]:
                    if p and p[0] in rename:
                        p[0] = rename[p[0]]
        json.dump(d, open(f, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        tn = f"{app}/public/twins/names/{c}.json"
        if os.path.exists(tn):
            json.dump(shorts, open(tn, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        print(c, "renamed", len(rename), "duplicates" if dup else "", sorted(dup)[:5])
    with open("results/jp_name_fixes.tsv", "w", encoding="utf-8") as fh:
        fh.write("city\tjapanese\tbefore\tafter\n")
        for r in log:
            fh.write("\t".join(r) + "\n")
    print(len(log), "changes -> results/jp_name_fixes.tsv")

if __name__ == "__main__":
    main()
