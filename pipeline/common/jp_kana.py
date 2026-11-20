"""Official readings of Japanese town names, from Japan Post's postcode data (KEN_ALL).

Usage: python pipeline/common/jp_kana.py <postaldata.db from the posuto package>
Writes pipeline/data/jp_town_kana.csv.gz (city, town, city_kana, town_kana) for the prefectures we map.
Japan Post does not claim copyright on the postcode data.
"""
import collections, gzip, csv, json, re, sqlite3, sys

PREFS = ("東京都", "大阪府", "京都府", "愛知県", "神奈川県", "兵庫県", "福岡県", "北海道")

def norm_town(s):
    s = re.sub(r"（.*?）|\(.*?\)", "", s or "")
    return s.replace("ヶ", "ケ").replace("ヵ", "カ").strip()

def main(db, out="pipeline/data/jp_town_kana.csv.gz"):
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    seen = collections.defaultdict(collections.Counter)
    for (raw,) in c.execute("select data from postal_data"):
        r = json.loads(raw)
        if r["prefecture"] not in PREFS or not r["neighborhood"] or r["neighborhood"].startswith("以下に掲載がない"):
            continue
        town, tk = norm_town(r["neighborhood"]), re.sub(r"[（(].*?[）)]", "", r["neighborhood_kana"] or "")
        if town and tk:
            seen[(r["city"], town)][(r["city_kana"], tk)] += 1
    with gzip.open(out, "wt", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["city", "town", "city_kana", "town_kana"])
        for (city, town), cnt in sorted(seen.items()):
            (ck, tk), _ = cnt.most_common(1)[0]
            w.writerow([city, town, ck, tk])
    print(out, len(seen))

if __name__ == "__main__":
    main(sys.argv[1])
