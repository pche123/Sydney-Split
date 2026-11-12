"""Make tokyo_split_app.html from the Sydney app template + app_data_tokyo.json.

python make_tokyo_page.py <Sydney app_template.html> app_data_tokyo.json tokyo_split_app.html
"""
import sys, json
tpl, data, out = sys.argv[1:4]
s = open(tpl, encoding="utf-8").read(); D = json.load(open(data, encoding="utf-8"))

def R(old, new, count=1):
    global s
    k = s.count(old)
    assert k >= 1 and (count == "all" or k == count), f"expected {count} of {old[:70]!r}, found {k}"
    s = s.replace(old, new)

HP = '<a href="https://webservice.recruit.co.jp/" target="_blank" rel="noopener">Powered by ホットペッパー Webサービス</a>'
# --- intro and header
R("Sydney has invisible lines.", "Tokyo has invisible lines too.")
R("<li><b>You've heard of the Latte Line.</b> We used the Census, café and chicken-shop maps, and liquor licences to find it, plus a dozen more.</li>",
  "<li><b>@@SYD@@ has its Latte Line.</b> We went looking for Tokyo's, using the 2020 Census, OpenStreetMap and HotPepper restaurant listings, and found lines for jobs, ramen, konbini, gyudon, izakaya and more.</li>")
R("""      <button id="introLatte">Show me the Latte Line</button>""", """      <button id="introLatte">Show me the Hi-Vis Line</button>""")
R("""    <button class="introclose" id="introClose" aria-label="Close">Just let me explore</button>""",
  f"""    <button class="introclose" id="introClose" aria-label="Close">Just let me explore</button>
    <p class="hpnote">Restaurant listings: {HP}. Shown for fun and learning; not affiliated with HotPepper.</p>""")
R("""      <button role="tab" data-mode="heritage">Heritage</button>
      <button role="tab" data-mode="overlay">Overlay</button>
""", "")
R('placeholder="e.g. Marrickville"', 'placeholder="e.g. Koenji"')
R("""    <div id="tip" role="status"></div>""", f"""    <div id="tip" role="status"></div>
    <div class="hpcredit">Restaurant listings {HP}</div>""")
R("</style>", """.hpcredit { position: absolute; right: 14px; bottom: 14px; background: var(--panel); border: 1px solid var(--rule); border-radius: 8px; padding: 4px 8px; font-size: 11.5px; color: var(--muted); }
.hpcredit a, .hpnote a { color: inherit; }
.hpnote { font-size: 12px; color: var(--muted); margin: 10px 0 0; text-align: center; }
</style>""")
# --- lists and groups
R('const GROUPS = [["Food", "Food & shops"], ["Night", "After dark"], ["Work", "Work (Census)"], ["Hidden", "Hidden lines (not just rich vs poor)"]];',
  'const GROUPS = [["Work", "Work (Census)"], ["Homes", "People & homes (Census)"], ["Food", "Food & cafés"], ["Chains", "Chain wars"], ["Night", "After dark (HotPepper)"], ["Worship", "Shrines & temples"]];')
R('const TL = DATA.timeline, TKINDS = [["lines", "Lines"], ["birth", "Birthplace"], ["religion", "Religion"]];',
  'const TL = DATA.timeline, TKINDS = [["lines", "Lines"], ["people", "People"], ["homes", "Homes & work"]];')
R('head(tKind === "birth" ? "Born in…" : "Religion");', 'head(tKind === "people" ? "People" : "Homes & work");')
R("""    const note = g.kind === "birth" ? NOTE.birth : NOTE.religion + (g.name === "No religion" ? " From 2016 this also includes secular and other spiritual beliefs." : "");""",
  """    const note = "Japan Census, 2000 to 2020. Each year's small areas are shared onto today's neighbourhoods by area.";""")
R('d.querySelector("h2").textContent = g.kind === "birth" ? `Born in ${g.name}` : g.name;', 'd.querySelector("h2").textContent = g.name;')
R("""const ASKS = `<p class="small">The Census doesn't ask about race or ethnicity. It asks where you were born, your ancestry and (optionally) your religion.</p>`;""",
  """const ASKS = `<p class="small">Japan's Census asks about age, homes and jobs. It doesn't ask about religion, ancestry or income.</p>`;""")
# --- timeline wording
R("<p class=\"small\" style=\"margin:0 0 4px\">Only changes bigger than normal measurement wobble are listed.</p>",
  "<p class=\"small\" style=\"margin:0 0 4px\">Neighbourhoods that changed side with the biggest moves (top 10% of change).</p>")
R("Clearly changed side", "Biggest moves", "all")
R("<footer>ABS Census 2001–2021 (Time Series Profiles), all years mapped onto today's suburbs. Each year the line splits Sydney's suburbs in half, so it shows who is relatively high or low that year.</footer>`;",
  "<footer>Japan Census 2000–2020 (e-Stat small areas), each year shared onto today's neighbourhoods by area. Each year the line splits Tokyo's neighbourhoods in half, so it shows who is relatively high or low that year. The Census changed its job categories in 2010; comparing within each year keeps the job lines fair.</footer>${l.id === \"grey\" ? GREYFLIP : \"\"}`;")
R("<footer>ABS Census 2001–2021 (Time Series Profiles), mapped onto today's suburbs. A place's colour describes the area, not anyone in it.</footer>`;",
  "<footer>Japan Census 2000–2020 (e-Stat small areas), mapped onto today's neighbourhoods. A place's colour describes the area, not anyone in it.</footer>`;")
R("function renderTimeline() {", """const GREYFLIP = `<div class="box"><h3>The Grey Flip</h3><p style="margin:0">Where older people live has almost completely reshuffled.</p>
  <p class="small">In 2000 the inner wards were older than Tama. By 2020 it had reversed: new towns built for young families in the 1970s and 80s (Tama, Machida, Hachioji) aged in place, some going from 10% to over 40% aged 65+, while old downtown areas like Kuramae, Torigoe and Toranomon got younger.</p></div>`;
function renderTimeline() {""")
# --- line page
R('const splitNote = l.id === "the-hi-vis-line" ?', 'const splitNote = false ?')
R('${l.id === "the-latte-line" ? "" : `<div class="box"><h3>Same route as the Latte Line?</h3>', '${l.id === lines[0].id ? "" : `<div class="box"><h3>Same route as the Hi-Vis Line?</h3>')
R("""    <footer>${DATA.meta.sources}. Covers 300 Sydney suburbs. Shop and café locations come from OpenStreetMap, which volunteers map, so a few may be missing. A suburb's side describes the area, not the people in it.</footer>`;""",
  """    ${l.id === "shrines-vs-temples" ? WORSHIP : ""}
    <footer>${DATA.meta.sources}. Covers ${DATA.meta.areas} Tokyo neighbourhoods of about 30,000 people each, built by merging neighbouring 町 within each ward or city. Shops and cafés come from OpenStreetMap, which volunteers map, so some are missing. Restaurant prices and hours come from HotPepper, which lists mostly sit-down places. "Nearby" means within 1 km of a neighbourhood's centre. Neighbourhood names are romanised automatically and may have small mistakes. A neighbourhood's side describes the area, not the people in it.</footer>`;""")
R("function render() {", """const WORSHIP = `<div class="box"><h3>Buildings, not beliefs</h3><p style="margin:0">This counts shrines and temples on the map, not what people believe.</p>
  <p class="small">Japan's Census doesn't ask about religion, so there is no data on who is Buddhist, Shinto or Christian in each neighbourhood. Many people visit both a shrine and a temple. Across neighbourhoods, the shrine-vs-temple balance barely relates to how many over-65s live there (rank correlation ${DATA.meta.worship_age}).</p></div>`;
function render() {""")
# --- make your own
R('if (k === "chain") { MK.A = "Red Rooster"; MK.B = "Messina"; }', 'if (k === "chain") { MK.A = "Iekei ramen"; MK.B = "Hakata tonkotsu ramen"; }')
R("return dA.map((a, i) => Math.log(dB[i] + 200) - Math.log(a + 200));", "return dA.map((a, i) => Math.log(dB[i] + 50) - Math.log(a + 50));")
R("function chainTest(bA, bB, draws = 199) {", "function chainTest(bA, bB, draws = 99) {")
R("<footer>Calculated live in your browser from the 2021 Census, OpenStreetMap venues (Nov 2026) and NSW liquor licences.",
  "<footer>Calculated live in your browser from the 2020 Census, OpenStreetMap venues and HotPepper listings (Nov 2026). Restaurant listings Powered by ホットペッパー Webサービス.")
R("<h3>Same route as the Latte Line?</h3><p style=\"margin:0\" id=\"mklatte\"></p>", "<h3>Same route as the Hi-Vis Line?</h3><p style=\"margin:0\" id=\"mklatte\"></p>")
# --- routing and intro
R('if (h === "heritage" || h === "overlay" || h === "timeline" || h === "make") { setMode(h); return; }', 'if (h === "timeline" || h === "make") { setMode(h); return; }')
R('location.hash = "the-latte-line"; route(); };\n$("#introSuburb")', 'location.hash = "the-hi-vis-line"; route(); };\n$("#introSuburb")')
R('if (mode !== "lines") { location.hash = "the-latte-line"; route(); }', 'if (mode !== "lines") { location.hash = "the-hi-vis-line"; route(); }')
R("ss_intro_seen", "ts_intro_seen", 2)
R("Census by Census: 2001 to 2021.", "Census by Census: 2000 to 2020.")
# --- city-wide words
for a, b in [("Sydneys", "Tokyos"), ("Sydney's", "Tokyo's"), ("Sydney", "Tokyo"), ("Suburbs", "Neighbourhoods"), ("suburbs", "neighbourhoods"),
             ("Suburb", "Neighbourhood"), ("suburb", "neighbourhood"), ("2001–2021", "2000–2020"), (">2001<", ">2000<"), (">2006<", ">2005<"),
             (">2011<", ">2010<"), (">2016<", ">2015<"), (">2021<", ">2020<"), ("as in 2001", "as in 2000"), ("(2001: ", "(2000: "),
             ("From 2001 to 2021", "From 2000 to 2020")]:
    s = s.replace(a, b)
assert "Sydney" not in s, [l for l in s.splitlines() if "Sydney" in l][:5]
s = s.replace("@@SYD@@", "Sydney")
s = s.replace("__DATA__", json.dumps(D, ensure_ascii=False, separators=(",", ":")))
open(out, "w", encoding="utf-8").write(s)
print("built", out, round(len(s.encode()) / 1e6, 2), "MB")
