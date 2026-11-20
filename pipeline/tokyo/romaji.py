"""Japanese place names -> readable romaji (no macrons).

Town names use their official readings from Japan Post's postcode data (pipeline/data/jp_town_kana.csv.gz,
built by pipeline/common/jp_kana.py) whenever the city is known: kanji readings are too irregular to guess
(上郷町 is Kamigocho, not Kamisatocho). Anything not in that table falls back to pykakasi + hand fixes.
"""
import csv, gzip, os, re, unicodedata
import pykakasi
_k = pykakasi.kakasi()
CITY = {"千代田区": "Chiyoda", "中央区": "Chuo", "港区": "Minato", "新宿区": "Shinjuku", "文京区": "Bunkyo", "台東区": "Taito", "墨田区": "Sumida",
        "江東区": "Koto", "品川区": "Shinagawa", "目黒区": "Meguro", "大田区": "Ota", "世田谷区": "Setagaya", "渋谷区": "Shibuya", "中野区": "Nakano",
        "杉並区": "Suginami", "豊島区": "Toshima", "北区": "Kita", "荒川区": "Arakawa", "板橋区": "Itabashi", "練馬区": "Nerima", "足立区": "Adachi",
        "葛飾区": "Katsushika", "江戸川区": "Edogawa", "八王子市": "Hachioji", "立川市": "Tachikawa", "武蔵野市": "Musashino", "三鷹市": "Mitaka",
        "青梅市": "Ome", "府中市": "Fuchu", "昭島市": "Akishima", "調布市": "Chofu", "町田市": "Machida", "小金井市": "Koganei", "小平市": "Kodaira",
        "日野市": "Hino", "東村山市": "Higashimurayama", "国分寺市": "Kokubunji", "国立市": "Kunitachi", "福生市": "Fussa", "狛江市": "Komae",
        "東大和市": "Higashiyamato", "清瀬市": "Kiyose", "東久留米市": "Higashikurume", "武蔵村山市": "Musashimurayama", "多摩市": "Tama",
        "稲城市": "Inagi", "羽村市": "Hamura", "あきる野市": "Akiruno", "西東京市": "Nishitokyo"}
FIX = {"月島": "Tsukishima", "勝どき": "Kachidoki", "晴海": "Harumi", "佃": "Tsukuda", "日本橋": "Nihonbashi", "神田": "Kanda", "御茶ノ水": "Ochanomizu",
       "麹町": "Kojimachi", "番町": "Bancho", "丸の内": "Marunouchi", "有楽町": "Yurakucho", "霞が関": "Kasumigaseki", "永田町": "Nagatacho",
       "高輪": "Takanawa", "白金台": "Shirokanedai", "白金": "Shirokane", "麻布": "Azabu", "赤坂": "Akasaka", "六本木": "Roppongi", "芝浦": "Shibaura",
       "港南": "Konan", "台場": "Daiba", "三田": "Mita", "早稲田": "Waseda", "神楽坂": "Kagurazaka", "歌舞伎町": "Kabukicho", "大久保": "Okubo",
       "高田馬場": "Takadanobaba", "四谷": "Yotsuya", "市谷": "Ichigaya", "本郷": "Hongo", "小石川": "Koishikawa", "千駄木": "Sendagi", "根津": "Nezu",
       "谷中": "Yanaka", "上野": "Ueno", "浅草": "Asakusa", "蔵前": "Kuramae", "押上": "Oshiage", "両国": "Ryogoku", "錦糸": "Kinshi", "亀戸": "Kameido",
       "豊洲": "Toyosu", "有明": "Ariake", "門前仲町": "Monzen-Nakacho", "木場": "Kiba", "大井": "Oi", "大崎": "Osaki", "五反田": "Gotanda",
       "戸越": "Togoshi", "自由が丘": "Jiyugaoka", "中目黒": "Naka-Meguro", "蒲田": "Kamata", "田園調布": "Den-en-Chofu", "羽田": "Haneda",
       "三軒茶屋": "Sangenjaya", "下北沢": "Shimokitazawa", "北沢": "Kitazawa", "代沢": "Daizawa", "代田": "Daita", "二子玉川": "Futako-Tamagawa",
       "玉川": "Tamagawa", "成城": "Seijo", "恵比寿": "Ebisu", "代々木": "Yoyogi", "原宿": "Harajuku", "神宮前": "Jingumae", "道玄坂": "Dogenzaka",
       "高円寺": "Koenji", "阿佐谷": "Asagaya", "荻窪": "Ogikubo", "西荻": "Nishiogi", "池袋": "Ikebukuro", "巣鴨": "Sugamo", "駒込": "Komagome",
       "赤羽": "Akabane", "王子": "Oji", "十条": "Jujo", "日暮里": "Nippori", "町屋": "Machiya", "高島平": "Takashimadaira", "練馬": "Nerima",
       "光が丘": "Hikarigaoka", "大泉": "Oizumi", "石神井": "Shakujii", "千住": "Senju", "北千住": "Kita-Senju", "綾瀬": "Ayase", "竹ノ塚": "Takenotsuka",
       "西新井": "Nishiarai", "柴又": "Shibamata", "金町": "Kanamachi", "亀有": "Kameari", "葛西": "Kasai", "小岩": "Koiwa", "瑞江": "Mizue",
       "吉祥寺": "Kichijoji", "葛西": "Kasai", "深大寺": "Jindaiji", "成増": "Narimasu", "赤塚": "Akatsuka", "大森": "Omori", "田無": "Tanashi", "高幡": "Takahata", "聖蹟桜ヶ丘": "Seiseki-Sakuragaoka", "府中": "Fuchu", "国立": "Kunitachi", "立川": "Tachikawa", "八王子": "Hachioji", "町田": "Machida", "調布": "Chofu", "三鷹": "Mitaka", "武蔵": "Musashi", "小平": "Kodaira", "日野": "Hino", "東村山": "Higashimurayama", "清瀬": "Kiyose", "狛江": "Komae", "多摩": "Tama", "稲城": "Inagi", "羽村": "Hamura", "福生": "Fussa", "青梅": "Ome", "昭島": "Akishima", "万願寺": "Manganji", "新宿": "Shinjuku", "渋谷": "Shibuya", "品川": "Shinagawa", "目黒": "Meguro", "世田谷": "Setagaya", "中野": "Nakano", "杉並": "Suginami", "板橋": "Itabashi", "足立": "Adachi", "葛飾": "Katsushika", "江戸川": "Edogawa", "東雲": "Shinonome", "南陽台": "Nanyodai", "新橋": "Shinbashi", "新川": "Shinkawa", "新富": "Shintomi", "築地": "Tsukiji", "銀座": "Ginza", "京橋": "Kyobashi", "八丁堀": "Hatchobori", "人形町": "Ningyocho", "南砂": "Minamisuna", "東陽": "Toyo", "東日本橋": "Higashi-Nihonbashi", "東麻布": "Higashi-Azabu", "南青山": "Minami-Aoyama", "北青山": "Kita-Aoyama", "西麻布": "Nishi-Azabu", "元麻布": "Moto-Azabu", "東中野": "Higashi-Nakano", "西荻北": "Nishiogi-Kita", "西荻南": "Nishiogi-Minami", "正光寺": "Shokoji", "曙町": "Akebonocho", "聖ケ丘": "Hijirigaoka", "百草": "Mogusa", "大字": "", "字": "", "六角橋": "Rokkakubashi"}
PRE = ("nishi", "higashi", "minami", "kita", "naka", "shin", "kami", "shimo", "moto", "oo")
SUF = ("honcho", "minami", "kita", "higashi", "nishi", "naka", "machi", "cho", "dai", "gaoka")

def _kana(s):
    r = "".join(x["hepburn"] for x in _k.convert(s))
    r = r.replace("ou", "o").replace("uu", "u").replace("oo", "o")
    return r

DIR = {"東": "Higashi", "西": "Nishi", "南": "Minami", "北": "Kita"}
def place(name, city_name=None):
    """町 name (丁目 removed) -> 'Koenji-Minami' style; official reading when the city is given and known."""
    if city_name:
        o = official(name, city_name)
        if o:
            return o
    s = re.sub(r"^大字|^字", "", str(name or "").strip())
    s = re.sub(r"[ケヶが]丘", "がおか", s)
    if len(s) >= 3 and s[0] in DIR and not any(s.startswith(k) for k in FIX):
        stem = s[1:]
        if any(stem.startswith(k) for k in FIX) or len(stem) >= 2:
            return DIR[s[0]] + "-" + place(stem)
    parts, rest = [], s
    for jp in sorted(FIX, key=len, reverse=True):          # longest known stem first
        if jp and rest.startswith(jp):
            parts.append(FIX[jp]); rest = rest[len(jp):]; break
    if rest:
        r = _kana(rest)
        if parts and r in ("honcho", "minami", "kita", "higashi", "nishi", "naka", "cho", "machi"):
            parts.append(r.capitalize())
        elif parts: parts.append(r.capitalize())
        else:
            for p in PRE:
                if r.startswith(p) and len(r) > len(p) + 3:
                    r = p.capitalize() + "-" + r[len(p):].capitalize(); break
            else:
                r = r.capitalize()
            for sfx in ("honcho", "minami", "kita", "higashi", "nishi"):
                if r.lower().endswith(sfx) and len(r) > len(sfx) + 3:
                    r = r[: -len(sfx)] + "-" + sfx.capitalize(); break
            parts.append(r)
    out = "-".join(p for p in parts if p)
    out = re.sub(r"-+", "-", out).strip("-")
    return out or s

def city(name): return CITY.get(name, _kana(name).capitalize())


# ---------------------------------------------------------------- official readings (Japan Post)
_TAB = None
def _table():
    global _TAB
    if _TAB is None:
        f = os.path.join(os.path.dirname(__file__), "..", "data", "jp_town_kana.csv.gz")
        towns, cities = {}, {}
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                towns[(r["city"], r["town"])] = r["town_kana"]; cities[r["city"]] = r["city_kana"]
        _TAB = (towns, cities)
    return _TAB

def kana_romaji(k, kanji=""):
    """Katakana reading -> 'kamigocho' (Hepburn, long vowels written short). None if the reading has anything else."""
    if not k or re.search(r"[^\u30a0-\u30ffー]", k):
        return None
    r = "".join(x["hepburn"] for x in _k.convert(k)).lower()
    keep = "内" in kanji and "uchi" in r                     # 丸の内 Marunouchi: the u of uchi is not a long vowel
    if keep:
        r = r.replace("uchi", "#")
    r = r.replace("ou", "o").replace("uu", "u").replace("'", "")
    if keep:
        r = r.replace("#", "uchi")
    r = re.sub(r"^oo", "o", r).replace("doori", "dori").replace("ooo", "oo")   # 上大岡 Kamiooka       # 大 Okubo, 通 dori (but Toyooka keeps both o's)
    return r if re.fullmatch(r"[a-z]+", r) else None

def _jo(k, kanji="", sib=()):
    """Sapporo grid names: 南十九条西 / ミナミ19ジョウニシ -> 'Minami 19-jo Nishi', as on the street signs."""
    m = re.fullmatch(r"(\D*?)(\d+)ジョウ(\D*)", unicodedata.normalize("NFKC", k or ""))
    if not m:
        return None
    mk = re.fullmatch(r"(.*?)[一二三四五六七八九十〇]+条(.*)", kanji or "")
    parts = []
    for i, x in ((1, m.group(1)), (2, m.group(3))):
        if x:
            r = kana_romaji(x)
            if r is None:
                return None
            parts.append(_style(mk.group(i), r, sib) if mk and mk.group(i) else r.capitalize())
        if i == 1:
            parts.append(m.group(2) + "-jo")
    return " ".join(parts)

LEAD = {"東": "higashi", "西": "nishi", "南": "minami", "北": "kita", "上": "kami", "下": "shimo", "中": "naka", "新": "shin", "元": "moto"}
TAIL = {"東": "higashi", "西": "nishi", "南": "minami", "北": "kita", "本町": "honcho", "中央": "chuo"}
def _style(kanji, r, sib=()):
    """Hyphens around direction/position words only when the rest is a place in its own right, i.e. the same
    city also has it with another direction or bare: 北寺尾 Kita-Terao (there is a 東寺尾), 山田西 Yamada-Nishi
    (山田東), 上末吉 Kami-Sueyoshi (下末吉); but 上郷町 Kamigocho, 中野島 Nakanoshima, 西宮浜 Nishinomiyahama."""
    sib = set(sib)
    def known(rest, swap):
        return bool(rest) and (rest in sib or rest + "町" in sib or any(x + rest in sib for x in swap) or any(rest + x in sib for x in swap))
    k, head, tail = kanji, "", ""
    base = re.sub(r"町$", "", k)
    for kt, rt in TAIL.items():
        if base.endswith(kt) and r.endswith(rt) and len(r) > len(rt) + 2 and not k.endswith("町"):
            rest = k[: -len(kt)]
            if known(rest, [x for x in TAIL if x != kt]):
                tail, k, r = "-" + rt.capitalize(), rest, r[: -len(rt)]; break
    p = LEAD.get(k[:1])
    if p and r.startswith(p) and len(r) > len(p) + 2 and known(k[1:], [x for x in LEAD if x != k[:1]]):
        head, r = p.capitalize() + "-", re.sub(r"^oo", "o", r[len(p):])
    return head + r.capitalize() + tail

_SIB = {}
def _siblings(city):
    if city not in _SIB:
        _SIB[city] = {t for (c, t) in _table()[0] if c == city}
    return _SIB[city]

def _stems(city):
    """Kanji names a town might start with: the city and the ward (横浜市鶴見区 -> 横浜, 鶴見; 西宮市 -> 西宮)."""
    return [x for x in re.split(r"[市区町村郡]", city or "") if len(x) >= 2]

def _town_key(name):
    s = re.sub(r"^大字|^字", "", str(name or "").strip())
    return s.replace("ヶ", "ケ").replace("ヵ", "カ")

def official(name, city):
    """Official romaji of a town in a city ('上郷町', '横浜市栄区' -> 'Kamigocho'), or None if not in Japan Post's list."""
    towns, _ = _table(); t = _town_key(name)
    if FIX.get(t):
        return FIX[t]
    k = towns.get((city, t))
    if k is None and t.endswith("町"):
        k = towns.get((city, t[:-1]))
    if k and _jo(k, t, _siblings(city)):
        return _jo(k, t, _siblings(city))
    r = kana_romaji(k, t) if k else None
    if not r:
        return None
    return _style(t, r, _siblings(city))

def ward_official(city_name):
    """'横浜市鶴見区' -> 'Tsurumi', '吹田市' -> 'Suita', '中京区' style wards read officially (Nakagyo, not Chukyo)."""
    _, cities = _table(); k = cities.get(city_name)
    if not k:
        return None
    m = re.match(r"(.+?市)(.+区)$", city_name)
    if m:
        sib = [cities[c] for c in cities if c.startswith(m.group(1)) and c.endswith("区")]
        pre = os.path.commonprefix(sib) if len(sib) > 1 else ""
        stem, kanji = k[len(pre):], m.group(2)
        stem = stem[:-1] if stem.endswith("ク") else stem
        kanji = kanji[:-1]
    else:
        kanji = re.sub(r"^.+?郡", "", city_name); stem = re.sub(r"^.+?グン", "", k)
        for a, b in (("シ", "市"), ("チョウ", "町"), ("マチ", "町"), ("ムラ", "村"), ("ソン", "村")):
            if stem.endswith(a) and kanji.endswith(b):
                stem, kanji = stem[: -len(a)], kanji[:-1]; break
    r = kana_romaji(stem)
    return _style(kanji, r) if r else None
