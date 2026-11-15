"""Write app/public/compare.html: which lines and data each city has, how definitions differ, and what new countries could support.

    python pipeline/common/coverage_page.py

Built from app/data/*.json, so it stays in step with the cities on the site.
"""
import glob, html, json, os, statistics
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
OUT = os.path.join(ROOT, "app", "public", "compare.html")

ORDER = [("Australia", ["sydney", "melbourne", "brisbane", "perth", "adelaide"]),
         ("Japan", ["tokyo", "osaka", "kyoto", "nagoya", "yokohama", "kobe", "fukuoka", "sapporo"]),
         ("England", ["london", "manchester", "birmingham", "liverpool", "brighton"])]
NAME = {"yokohama": "Yokohama–Kawasaki", "kobe": "Kobe–Hanshin"}
PAGE = lambda c: "index.html" if c == "sydney" else f"{c}.html"

# rows: (family, label, line ids that count as this measure in any city)
ROWS = [
    ("Work and class", "Hi-Vis (manual vs managerial jobs)", ["the-hi-vis-line"]),
    ("Work and class", "Degree", ["the-degree-line"]),
    ("Work and class", "Factory", ["the-factory-line"]),
    ("Work and class", "Laptop vs Hard Hat", ["the-laptop-vs-hard-hat-line", "the-laptop-vs-ute-line"]),
    ("Inner city", "Flats vs Houses", ["flats-vs-houses"]),
    ("Inner city", "Renters", ["the-renters-line"]),
    ("Inner city", "Living Alone", ["the-living-alone-line"]),
    ("Inner city", "Train vs Car", ["train-vs-car"]),
    ("Inner city", "Bicycle", ["the-bicycle-line"]),
    ("Inner city", "No Car", ["the-no-car-line"]),
    ("Inner city", "Tower blocks", ["the-tower-line"]),
    ("Age", "Grey (over-65s)", ["the-grey-line"]),
    ("Food and night out", "Latte (cafés vs fast food)", ["the-latte-line"]),
    ("Food and night out", "Coffee vs Alcohol", ["coffee-vs-alcohol"]),
    ("Food and night out", "Drink Out vs Drink In", ["drink-out-vs-drink-in"]),
    ("Food and night out", "Late Night", ["the-late-night-line"]),
    ("Gambling", "Pokies / Betting shops", ["the-pokies-line", "the-betting-shop-line"]),
]
TIER = {"line": ('<i class="d d-line"></i>', "Real line", "t-line"), "gentle": ('<i class="d d-gentle"></i>', "Gentle pattern", "t-gentle"),
        "chance": ('<i class="d d-chance"></i>', "Could be chance", "t-chance")}

D = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob(os.path.join(ROOT, "app", "data", "*.json"))}
cols = [(ctry, [c for c in cs if c in D]) for ctry, cs in ORDER]
extra = sorted(set(D) - {c for _, cs in ORDER for c in cs})
if extra: cols.append(("Other", extra))
allc = [c for _, cs in cols for c in cs]

COUNTRY = {c: ctry for ctry, cs in ORDER for c in cs}
def cell(c, ids):
    for l in D[c]["lines"]:
        if l["id"] in ids:
            sym, txt, cls = TIER[l["tier"]]
            return f'<td class="{cls}" title="{html.escape(l["name"])}: {txt} (p = {l["p"]})"><a href="{PAGE(c)}#lines">{sym}</a></td>'
    peers = [o for o in D if COUNTRY.get(o) == COUNTRY.get(c) and any(l["id"] in ids for l in D[o]["lines"])]
    if peers:   # another city in the same country builds it from the same census, so the data exist here too
        return '<td class="t-todo" title="The data exist for this city; this line is not built for it yet"><i class="d d-todo"></i></td>'
    return '<td class="t-none" title="Not available from this city\'s data">–</td>'

def extras(c):
    d = D[c]; tl = d.get("timeline", {}); her = d.get("heritage", [])
    yrs = f'{tl["years"][0]}–{tl["years"][-1]}' if tl.get("years") else "–"
    return (len(tl.get("lines", [])), yrs, len(her), sum(1 for l in d["lines"] if l["group"] == "Chains"))

head = "".join(f'<th colspan="{len(cs)}" class="ctry">{ctry}</th>' for ctry, cs in cols)
sub = "".join(f'<th class="city"><a href="{PAGE(c)}">{NAME.get(c, c.capitalize())}</a></th>' for c in allc)
body, last = "", None
for famname, label, ids in ROWS:
    if famname != last: body += f'<tr class="fam"><th colspan="{len(allc) + 1}">{famname}</th></tr>'; last = famname
    body += f"<tr><th class=\"row\">{label}</th>" + "".join(cell(c, ids) for c in allc) + "</tr>"
body += f'<tr class="fam"><th colspan="{len(allc) + 1}">Other views</th></tr>'
for k, lab in [(0, "Timeline lines"), (1, "Timeline years"), (2, "Heritage maps"), (3, "Chain wars")]:
    body += f"<tr><th class=\"row\">{lab}</th>" + "".join(f"<td>{extras(c)[k] or '–'}</td>" for c in allc) + "</tr>"
body += "<tr><th class=\"row\">Typical people per area</th>" + "".join(
    f"<td>{round(statistics.median([a['pop'] for a in D[c]['areas']]), -2):,.0f}</td>" for c in allc) + "</tr>"

DEFS = [
    ("Census date", "10 Aug 2021", "1 Oct 2020 (COVID)", "21 Mar 2021 (COVID rules: commuting figures unusual)"),
    ("Areas", "ABS SA2s with ≥1,000 people and ≥300 per km²", "町丁 (blocks) merged into neighbourhoods of similar size", "MSOAs (about 8,000 people); Brighton uses LSOAs (about 1,700)"),
    ("Degree", "Bachelor's or higher, share of all residents", "University or graduate school, share of those who answered (about 1 in 4 big-city residents leave it blank)", "Level 4+ (includes some diplomas), share of residents 16+"),
    ("Hi-Vis jobs", "Machinery operators & drivers + labourers", "Production, transport, construction & cleaning occupations", "Process & plant operatives + elementary occupations"),
    ("Commuting", "Method on census day", "Usual method (one or several)", "Usual method, but in lockdown"),
    ("Heritage", "Country of birth (top 18 countries)", "Foreign nationals, all countries together", "World region of birth"),
    ("Restaurants & bars", "NSW and VIC liquor licences; OpenStreetMap elsewhere", "HotPepper listings (not in downloads); OpenStreetMap", "Food Standards Agency hygiene records"),
    ("Gambling", "Poker machine venues (NSW, VIC); none in Perth by law", "None", "Gambling Commission betting shops"),
    ("Timeline", "2011, 2016, 2021 (ABS Time Series Profile)", "2000–2020, five censuses, shared onto today's areas", "Not yet (needs 2011 tables on old boundaries)"),
]
defs = "".join(f"<tr><th>{a}</th><td>{b}</td><td>{c}</td><td>{e}</td></tr>" for a, b, c, e in DEFS)

PLAN = [
    ("USA", "Census tracts (ACS 5-year)", "Excellent", "Work, degrees, commuting incl. cycling and working from home, birthplace, ancestry, rent. A survey estimate with margins of error, not a full count."),
    ("New Zealand", "SA2 (2023 Census)", "Excellent", "Very close to Australia: most lines can be compared directly."),
    ("Singapore", "Subzones (2020 Census)", "Good", "Housing type (public flats vs condos), education, transport mode; a city-state, so no suburbs beyond the border."),
    ("France", "IRIS (about 2,000 people)", "Very good", "Managers vs manual workers, diplomas, cycling, immigrants, renting."),
    ("Spain", "Census sections", "Good", "INE indicator files and boundaries for census sections, plus a 1 km grid."),
    ("Italy", "Census sections", "OK", "2021 section data exist for every municipality, but fewer topics than older censuses."),
    ("Germany", "100 m grid (Zensus 2022)", "Thinner", "Grid squares, not neighbourhoods; population, age, housing and rent, little on jobs or degrees."),
]
plan = "".join(f"<tr><th>{a}</th><td>{b}</td><td>{c}</td><td>{d}</td></tr>" for a, b, c, d in PLAN)

page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Split: which cities can be compared?</title>
<style>
:root {{ --paper:#f3f4f1; --panel:#fff; --ink:#1c2126; --muted:#5d6870; --rule:#dfe2dc; --a:#f0a33a; --line:#2f8f5b; --gentle:#3a78a8; --chance:#a8862c; }}
@media (prefers-color-scheme: dark) {{ :root {{ --paper:#14181b; --panel:#1c2125; --ink:#e8ebe7; --muted:#9aa4ab; --rule:#2e353a; --line:#4fbf87; --gentle:#7fb6dc; --chance:#d2b25a; }} }}
body {{ margin:0; background:var(--paper); color:var(--ink); font:15px/1.55 "IBM Plex Sans","Segoe UI",system-ui,sans-serif; }}
main {{ max-width:1180px; margin:0 auto; padding:28px 20px 60px; }}
h1 {{ font:800 30px/1.15 "Bricolage Grotesque","Avenir Next",system-ui,sans-serif; margin:0 0 6px; }}
h2 {{ font:700 20px/1.2 "Bricolage Grotesque","Avenir Next",system-ui,sans-serif; margin:34px 0 8px; }}
p.lead {{ font-size:17px; max-width:820px; }} a {{ color:inherit; }}
.wrap {{ overflow-x:auto; background:var(--panel); border:1px solid var(--rule); border-radius:12px; padding:6px; }}
table {{ border-collapse:collapse; width:100%; font-size:13.5px; }}
th, td {{ padding:6px 8px; border-bottom:1px solid var(--rule); text-align:left; vertical-align:top; }}
table.m td {{ text-align:center; font-size:16px; min-width:40px; }} table.m td a {{ text-decoration:none; }}
th.ctry {{ text-align:center; border-left:2px solid var(--rule); font-size:12px; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); }}
th.city {{ writing-mode:vertical-rl; transform:rotate(180deg); white-space:nowrap; font-weight:600; height:118px; }}
tr.fam th {{ background:var(--paper); font-size:12px; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); }}
th.row {{ white-space:nowrap; font-weight:500; }}
.t-line {{ color:var(--line); }} .t-gentle {{ color:var(--gentle); }} .t-chance {{ color:var(--chance); }} .t-none {{ color:var(--muted); opacity:.6; }}
i.d {{ display:inline-block; width:12px; height:12px; border-radius:50%; vertical-align:-1px; }}
.d-line {{ background:var(--line); }} .d-gentle {{ background:var(--gentle); opacity:.75; width:10px!important; height:10px!important; }}
.d-chance {{ border:2px solid var(--chance); width:8px!important; height:8px!important; }} .d-todo {{ border:1.5px dashed var(--muted); width:8px!important; height:8px!important; opacity:.7; }}
.key span {{ margin-right:16px; white-space:nowrap; }} ol li {{ margin:6px 0; }} .small {{ font-size:13px; color:var(--muted); }}
</style></head><body><main>
<p class="small"><a href="index.html">← Back to the maps</a></p>
<h1>Which cities can be compared?</h1>
<p class="lead">Planners often want to model one city on another. That only works if the same thing was measured the same way in both. This page shows which lines each city has, where the definitions differ, and what other countries' data could support.</p>
<h2>Lines in each city</h2>
<p class="key small"><span><i class="d d-line"></i> Real line</span><span><i class="d d-gentle"></i> Gentle pattern</span><span><i class="d d-chance"></i> Could be chance</span><span><i class="d d-todo"></i> Data exist, line not built yet</span><span class="t-none">– Not in this city's data</span> Hover a mark for its p-value; click to open the map.</p>
<div class="wrap"><table class="m"><thead><tr><th></th>{head}</tr><tr><th></th>{sub}</tr></thead><tbody>{body}</tbody></table></div>
<p class="small">The verdict is about each city on its own: whether its border is sharper than random maps of that same city. Compare verdicts, not raw percentages.</p>
<h2>Same name, different measure</h2>
<p>A "Degree Line" exists in all three countries, but each census asks a different question. Within a country, cities compare like with like; across countries, compare the shape and the verdict, not the numbers.</p>
<div class="wrap"><table><thead><tr><th></th><th>Australia</th><th>Japan</th><th>England</th></tr></thead><tbody>{defs}</tbody></table></div>
<h2>Five rules for comparing cities</h2>
<ol>
<li><b>Same line, same definition.</b> Compare two cities on a line only if both have it (a mark above) and the definition table says it was measured the same way.</li>
<li><b>Compare verdicts and shapes, not percentages.</b> "Real line in both" or "inner-city core in both" travels; "34% vs 41% degree holders" does not, across countries.</li>
<li><b>Area size matters.</b> Smaller areas show sharper edges and give the tests more to work with. Adelaide (86 areas) can only confirm very sharp lines; London (1,002) can confirm subtle ones.</li>
<li><b>Census dates matter.</b> Japan counted in 2020, Australia and England in 2021, partly under COVID rules. Commuting and working from home are the most affected.</li>
<li><b>Restaurant and shop data come from different sources</b> (licences, hygiene records, HotPepper, OpenStreetMap). Treat venue lines as comparable in shape only.</li>
</ol>
<h2>Countries we could add, and what they would support</h2>
<div class="wrap"><table><thead><tr><th>Country</th><th>Small areas</th><th>Fit</th><th>What could be compared</th></tr></thead><tbody>{plan}</tbody></table></div>
<p class="small">Fit = how many of the lines above the country's small-area census can support with a similar definition.</p>
<p class="small" style="margin-top:30px">Please cite: Cheema, P. (2026). Is that line real? Calibrated tests for informal urban divides. https://pche123.github.io/Sydney-Split/</p>
</main></body></html>"""
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write(page)
print("written", OUT, len(allc), "cities")
