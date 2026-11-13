"""Ramen style from a shop's name (and, for HotPepper, its blurb). Chains first, then style words.

Each style: (chains, style words). A shop gets the first style that matches, in the order below.
"""
import re

STYLES = {
    "iekei": (  # Yokohama-style pork-bone soy, thick noodles, spinach and nori
        ["吉村家", "杉田家", "本牧家", "六角家", "壱角家", "町田商店", "魂心家", "武蔵家", "王道家", "末廣家", "せい家", "横浜家", "横濱家",
         "大和家", "一刀家", "介一家", "環2家", "輝道家", "渡来武", "侍", "天下一家", "濃厚家", "寿々喜家", "道玄坂マンモス", "ラーメン 大桜",
         "ラーメン大桜", "百麺", "まこと家", "とらきち家", "家系総本山", "上越家", "厚木家", "近藤家", "田中家", "はじめ家"],
        ["家系", "iekei", r"ラーメン\s?\S*家$", r"^\S{1,4}家$"]),
    "jiro": (  # mountain of bean sprouts, garlic, thick pork
        ["ラーメン二郎", "豚山", "千里眼", "夢を語れ", "野郎ラーメン", "立川マシマシ", "ラーメン荘", "蓮爾", "麺屋 歩夢", "ラーメン 歩夢",
         "用心棒", "ジャンクガレッジ", "ラーメン大 ", "ラーメン大池袋", "ぽっぽっ屋", "ラーメン富士丸", "ハナイロモ", "ばり馬"],
        ["二郎", "ジロー", "マシマシ", "jiro"]),
    "tonkotsu": (  # Hakata / Kyushu creamy pork bone
        ["一蘭", "一風堂", "博多風龍", "一幸舎", "長浜ナンバーワン", "長浜ラーメン", "一双", "ShinShin", "田中商店", "なんでんかんでん",
         "九州じゃんがら", "ばりき", "博多天神", "博多一双", "暖暮", "ずんどう屋", "らーめん山頭火", "山頭火", "麺屋 ふぅふぅ亭"],
        ["豚骨", "とんこつ", "トンコツ", "博多", "長浜", "久留米", "熊本", "鹿児島", "tonkotsu", "hakata"]),
    "miso": (  # Sapporo / miso
        ["田所商店", "味噌乃家", "すみれ", "花道", "くるまやラーメン", "どさん子", "味噌一", "麺場", "蔵出し味噌", "らーめん 信玄"],
        ["味噌", "みそ", "ミソ", "札幌", "miso"]),
    "spicy": (  # Nakamoto, tantanmen, spicy miso
        ["蒙古タンメン中本", "中本", "ニュータンタンメン", "辛麺屋", "希望軒"],
        ["担々", "担担", "坦々", "タンタン", "辛麺", "激辛"]),
    "tsukemen": (  # dipping noodles
        ["六厘舎", "大勝軒", "やすべえ", "三田製麺所", "舎鈴", "つじ田", "頑者", "風雲児", "TETSU", "つけ麺 TETSU"],
        ["つけ麺", "つけめん", "ツケメン", "tsukemen"]),
    "kotteri": (  # Kyoto thick chicken
        ["天下一品", "天一", "魁力屋", "来来亭", "ますたに"], ["こってり"]),
    "shoyu_classic": (  # Tokyo-style clear soy / chūka soba
        ["春木屋", "丸長", "喜多方ラーメン坂内", "坂内", "幸楽苑", "日高屋", "福しん", "珍来", "桂花", "支那そばや", "青葉", "AFURI", "らあめん花月"],
        ["中華そば", "支那そば", "醤油", "しょうゆ", "喜多方", "煮干", "にぼし", "淡麗", "shoyu"]),
    "shio": ([], ["塩らーめん", "塩ラーメン", "しお", "shio"]),
    "abura_soba": (["東京油組総本店", "油そば専門店 春日亭", "武蔵野アブラ学会", "ぶぶか"], ["油そば", "まぜそば", "汁なし"]),
}
NAMES = {"iekei": "Iekei (Yokohama pork-soy)", "jiro": "Jiro-style (mountain of sprouts)", "tonkotsu": "Hakata tonkotsu",
         "miso": "Miso", "spicy": "Spicy / tantanmen", "tsukemen": "Tsukemen (dipping)", "kotteri": "Kotteri (thick chicken)",
         "shoyu_classic": "Classic shoyu / chūka soba", "shio": "Shio (salt)", "abura_soba": "Abura soba (soupless)"}
_RX = {k: (re.compile("|".join(re.escape(c) for c in ch)) if ch else None, re.compile("|".join(w), re.I)) for k, (ch, w) in STYLES.items()}

def style(name, extra=""):
    """name: shop name; extra: cuisine tag / HotPepper blurb. Returns a style key or None."""
    name = str(name or ""); txt = name + " " + str(extra or "")
    for k, (chains, words) in _RX.items():      # chains first, on the name
        if chains is not None and chains.search(name): return k
    for k, (chains, words) in _RX.items():      # then style words anywhere
        if words.search(txt): return k
    return None
