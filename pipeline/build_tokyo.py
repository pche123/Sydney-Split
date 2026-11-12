"""Tokyo neighbourhoods (町, e.g. 高円寺南 = all its 丁目 merged) with Census + venue signals.

python build_tokyo.py raw2020 tokyo_places.csv out/
"""
import sys, os, re, ast, numpy as np, pandas as pd, geopandas as gpd

raw, places, out = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
CRS = 6677  # JGD2011 / Japan Plane Rectangular CS IX (Tokyo), metres

# ---------- shapes: merge 丁目 into 町, mainland Tokyo only (23 wards + Tama cities) ----------
g = gpd.read_file(f"{raw}/r2ka13.shp")
g = g[g.KEY_CODE.str.len() >= 9]
g["CITY"] = g.CITY.astype(int); g = g[(g.CITY >= 101) & (g.CITY < 300)]
g["U"] = g.KEY_CODE.str[:9]
g["NAME"] = g.S_NAME.fillna("").str.replace(r"[一二三四五六七八九十]+丁目$", "", regex=True)
U = g.to_crs(CRS).dissolve("U", aggfunc={"CITY_NAME": "first", "NAME": "first", "JINKO": "sum"}).reset_index()
U["km2"] = U.area / 1e6

# ---------- census tables, 町 level rows (HYOSYO 2 = no 丁目 split, 3 = sum of 丁目) ----------
def tab(code):
    t = pd.read_csv(f"{raw}/tbl{code}C13.txt", encoding="cp932", dtype=str)
    lab = t.iloc[0]; t = t.iloc[1:]; t = t[t.HYOSYO.isin(["2", "3"])].set_index("KEY_CODE")
    cols = [c for c in t.columns if c.startswith("T")]
    v = t[cols].apply(pd.to_numeric, errors="coerce"); v.columns = [lab[c] for c in cols]; return v
pop = tab("T001081"); age = tab("T001082"); hsz = tab("T001083"); fam = tab("T001084")
ten = tab("T001085"); bld = tab("T001086"); ind = tab("T001103"); occ = tab("T001104")
S = pd.DataFrame(index=U.U)
def put(name, num, den):
    S[name] = (num / den.replace(0, np.nan)).reindex(S.index)
P = pop["人口総数"]
S["population"] = P.reindex(S.index)
put("age_65_plus", age["総数６５歳以上"], age["総数、年齢「不詳」含む"])
put("age_20_39", age[["総数２０～２４歳", "総数２５～２９歳", "総数３０～３４歳", "総数３５～３９歳"]].sum(1), age["総数、年齢「不詳」含む"])
put("kids_under_15", age["総数１５歳未満"], age["総数、年齢「不詳」含む"])
put("living_alone", hsz["世帯人員１人"], hsz["一般世帯数（世帯人員６人以上含む）"])
put("families_with_kids", fam["１８歳未満世帯員のいる一般世帯総数"], fam["一般世帯総数"])
put("owners", ten["持ち家"], ten["住宅に住む一般世帯"])
put("renters", ten["民営借家"], ten["住宅に住む一般世帯"])
put("detached_houses", bld["一戸建"], bld["主世帯数"])
put("towers_11_floors_plus", bld["共同住宅１１階建以上"], bld["主世帯数"])
o = occ["総数"]
put("managers", occ.iloc[:, 1], o); put("professionals", occ.iloc[:, 2], o); put("office_workers", occ.iloc[:, 3], o)
put("sales_workers", occ.iloc[:, 4], o); put("service_workers", occ.iloc[:, 5], o)
put("factory_workers", occ.iloc[:, 8], o); put("drivers", occ.iloc[:, 9], o); put("builders", occ.iloc[:, 10], o)
put("cleaning_packing", occ.iloc[:, 11], o)
put("hivis_jobs", occ.iloc[:, [8, 9, 10, 11]].sum(1), o)
put("laptop_jobs", occ.iloc[:, [1, 2]].sum(1), o)
w = ind["総数"]
for nm, c in [("ind_it", "Ｇ情報通信業"), ("ind_manufacturing", "Ｅ製造業"), ("ind_finance", "Ｊ金融業、保険業"),
              ("ind_hospitality", "Ｍ宿泊業、飲食サービス業"), ("ind_health", "Ｐ医療、福祉"), ("ind_construction", "Ｄ建設業"),
              ("ind_transport", "Ｈ運輸業、郵便業"), ("ind_retail", "Ｉ卸売業、小売業")]:
    put(nm, ind[c], w)
put("self_employed", ind["自営業主（家庭内職者を含む）"], ind["総数（従業上の地位「不詳」を含む）"])
S["density"] = S.population.values / U.set_index("U").km2.reindex(S.index).values

# ---------- venues ----------
d = pd.read_csv(places); d["t"] = [ast.literal_eval(s) for s in d.tags]
d = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d.lon, d.lat), crs=4326).to_crs(CRS)
txt = d.t.map(lambda q: "|".join(str(q.get(k, "")) for k in ("brand", "name", "brand:en", "name:en", "brand:ja", "operator")).lower())
am = d.t.map(lambda q: q.get("amenity")); sh = d.t.map(lambda q: q.get("shop")); cu = d.t.map(lambda q: str(q.get("cuisine", "")).lower())
food = am.isin(["restaurant", "fast_food", "cafe", "pub", "bar", "food_court"])
eat = am.isin(["restaurant", "fast_food", "food_court"])
def has(p): return txt.str.contains(p, regex=True)
ramen = eat & (cu.str.contains("ramen") | d.t.map(lambda q: bool(re.search("ラーメン|らーめん|拉麺|中華そば|つけ麺|らあめん|二郎|家系", str(q.get("name", "")))))) & ~has("洋麺屋|五右衛門")
rname = d.t.map(lambda q: str(q.get("name", "")))
V = {
 "food": food, "cafe": am.eq("cafe"), "izakaya_bar": am.isin(["pub", "bar"]), "fast_food": am.eq("fast_food"),
 "ramen": ramen, "soba_udon": eat & cu.str.contains("soba|udon") & ~ramen,
 "sushi": eat & cu.str.contains("sushi"), "curry": eat & (cu.str.contains("curry") | has("カレー|curry")) & ~cu.str.contains("indian|nepal"),
 "indian_nepali": eat & cu.str.contains("indian|nepal"), "yakiniku": eat & cu.str.contains("barbecue|yakiniku|焼肉"),
 "iekei": ramen & (rname.str.contains("家系|壱角家|町田商店|魂心家|武蔵家|吉村家|杉田家|せい家|横浜家|横濱家|王道家|末廣家|大和家|一刀家") | cu.str.contains("iekei")),
 "jiro": ramen & (cu.str.contains("jiro") | rname.str.contains("二郎|豚山|ジロー|マシマシ|夢を語れ|野郎ラーメン")),
 "tonkotsu_hakata": ramen & rname.str.contains("豚骨|とんこつ|博多|一蘭|一風堂|長浜|久留米|風龍|一幸舎|ばりき"),
 "chuka_soba": ramen & rname.str.contains("中華そば|支那そば|醤油|喜多方|大勝軒|春木屋|永福町"),
 "seven_eleven": sh.eq("convenience") & has("7-eleven|セブン-イレブン|セブンイレブン|seven-eleven|seven eleven"),
 "familymart": sh.eq("convenience") & has("familymart|family mart|ファミリーマート"),
 "lawson": sh.eq("convenience") & has("lawson|ローソン"),
 "ministop": sh.eq("convenience") & has("ministop|ミニストップ"),
 "konbini": sh.eq("convenience"),
 "my_basket": has("まいばすけっと|my basket|mybasket"),
 "starbucks": has("starbucks|スターバックス"), "doutor": has("doutor|ドトール"), "tullys": has("tully|タリーズ"),
 "komeda": has("komeda|コメダ"), "veloce": has("veloce|ベローチェ"),
 "indie_cafe": am.eq("cafe") & ~has("starbucks|スターバックス|doutor|ドトール|tully|タリーズ|komeda|コメダ|veloce|ベローチェ|サンマルク|st.marc|excelsior|エクセルシオール|プロント|pronto|上島|ueshima|blue bottle|ブルーボトル|ルノアール|renoir|caffe|kohikan|珈琲館|星乃|サンマルク"),
 "matsuya": eat & has("^松屋\\||\\|松屋\\||matsuya") & ~has("銀座|浅草|デパート|department"),
 "sukiya": eat & has("すき家|sukiya"), "yoshinoya": eat & has("吉野家|yoshinoya"),
 "coco_ichi": eat & has("coco壱|ココイチ|coco ichi|ｃｏｃｏ壱"), "go_go_curry": eat & has("ゴーゴーカレー|go go curry|gogo curry"),
 "saizeriya": has("サイゼリヤ|saizeriya"), "gusto": has("ガスト|gusto") & ~has("ガストロ|gastro"),
 "mcdonalds": has("mcdonald|マクドナルド"), "mos_burger": has("mos burger|モスバーガー"),
 "hidakaya": has("日高屋|hidakaya"), "station": d.t.map(lambda q: q.get("railway") == "station" or q.get("public_transport") == "station"),
}
for k, m in V.items(): print(f"{k:16s} {int(m.sum())}")
pickle_keep = d[["osm_id", "lat", "lon"]].copy()
for k, m in V.items(): pickle_keep[k] = m.values
pickle_keep["x"] = d.geometry.x; pickle_keep["y"] = d.geometry.y
pickle_keep.to_pickle(f"{out}/venues.pkl")

j = gpd.sjoin(d[["geometry"]], U[["U", "geometry"]], predicate="within")
for k, m in V.items():
    S["n_" + k] = j[m.loc[j.index].values].groupby("U").size().reindex(S.index).fillna(0)
nf = S.n_food.replace(0, np.nan)
for k in ["cafe", "izakaya_bar", "fast_food", "ramen", "soba_udon", "sushi", "curry", "indian_nepali", "yakiniku", "indie_cafe"]:
    S["share_" + k] = S["n_" + k] / nf
S["konbini_per_1k"] = S.n_konbini / S.population * 1000
S["food_per_1k"] = S.n_food / S.population * 1000
U = U.merge(S.reset_index().rename(columns={"index": "U"}), on="U")
U.to_file(f"{out}/tokyo_units.gpkg", driver="GPKG")
print(U.shape)
