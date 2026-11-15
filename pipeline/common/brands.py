"""Chain brands matched in OpenStreetMap, per country (shared by build_app.py and own_p.py)."""
BRANDS_BY_COUNTRY = {
    "au": {"Woolworths": (r"woolworths", ["supermarket"]), "Coles": (r"^coles$|\|coles\||^coles\|", ["supermarket"]), "Aldi": (r"aldi", ["supermarket"]),
           "McDonald's": (r"mcdonald", ["fast_food"]), "KFC": (r"\bkfc\b", ["fast_food"]), "Hungry Jack's": (r"hungry jack", ["fast_food"]),
           "Nando's": (r"nando", ["restaurant", "fast_food"]), "Grill'd": (r"grill'd", ["restaurant", "fast_food"])},
    "jp": {"7-Eleven": (r"7-eleven|セブン-イレブン|セブンイレブン|seven-eleven", ["convenience"]), "FamilyMart": (r"familymart|ファミリーマート", ["convenience"]),
           "Lawson": (r"lawson|ローソン", ["convenience"]), "Matsuya": (r"^松屋|\|松屋|matsuya", ["fast_food", "restaurant"]),
           "Yoshinoya": (r"吉野家|yoshinoya", ["fast_food", "restaurant"]), "Sukiya": (r"すき家|sukiya", ["fast_food", "restaurant"]),
           "Starbucks": (r"starbucks|スターバックス", ["cafe"]), "Doutor": (r"doutor|ドトール", ["cafe"]),
           "Saizeriya": (r"サイゼリヤ|saizeriya", ["restaurant", "fast_food"]), "Gusto": (r"ガスト|\bgusto\b", ["restaurant", "fast_food"]),
           "McDonald's": (r"mcdonald|マクドナルド", ["fast_food"]), "Gyoza no Ohsho": (r"餃子の王将|ohsho", ["restaurant", "fast_food"])},
    "uk": {"Greggs": (r"greggs", ["fast_food", "cafe", "bakery"]), "Pret": (r"pret a manger|\bpret\b", ["cafe", "fast_food"]),
           "Costa": (r"\bcosta\b", ["cafe"]), "Starbucks": (r"starbucks", ["cafe"]), "Tesco": (r"tesco", ["supermarket", "convenience"]),
           "Sainsbury's": (r"sainsbury", ["supermarket", "convenience"]), "Waitrose": (r"waitrose", ["supermarket", "convenience"]),
           "Lidl & Aldi": (r"\blidl\b|\baldi\b", ["supermarket"]), "Wetherspoon": (r"wetherspoon|\bjd wetherspoon", ["pub", "bar"]),
           "McDonald's": (r"mcdonald", ["fast_food"]), "KFC": (r"\bkfc\b", ["fast_food"])},
}
