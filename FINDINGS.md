# Findings

Short, plain conclusions from the tests. "Beats chance" means the line is cleaner than almost every random map with the same patchiness (or, for chain-vs-chain, than shuffling which shops belong to which chain). "Could be chance" means the map may still tell a story, but the data can't prove it yet. Neighbourhood descriptions are about areas, not the people in them.

## Sydney

| Line | Verdict | What it shows |
|---|---|---|
| Hi-Vis Line | Beats chance, strongly | Sydney's main split: managers and professionals in the east, north and inner west; warehouse, driving, factory and building jobs in the west and south-west. |
| Latte Line | Beats chance, strongly | Cafés lead the food mix in Bellevue Hill, Bondi and Balmain; fast food leads in Green Valley, Currans Hill and Narellan. It follows the Hi-Vis Line on 79% of suburbs, so the "latte" is really a jobs story. |
| Red Rooster Line | Beats chance | Closer to a Red Rooster in Penrith, St Clair and Currans Hill; closer to a Messina in Surry Hills, Bondi and Manly. Same route as the Hi-Vis Line on 81% of suburbs. |
| Late Night Line | Beats chance, strongly | After-midnight licences cluster where people walk to work, live alone and don't own a car (Potts Point, Darlinghurst, Haymarket). Families and big houses sit on the other side. |
| Small Bar Line | Beats chance, strongly | Small bars outweigh pubs in uni-educated, professional areas (and, oddly, Castle Hill West); pubs dominate in Rooty Hill and Plumpton. |
| Pokies Line | Beats chance | Poker machines per resident peak in the city and in lower-rent, social-housing areas, with late kebab shops nearby. |
| Aldi Line | Beats chance | Aldi's share of supermarkets is highest where people drive to work (Fairfield, Chester Hill); it is the one line that cuts across the Hi-Vis Line (57% overlap). |
| Bubble Tea Line | Could be chance | Bubble tea leans towards uni students and areas with Chinese and Korean food (Hornsby, Burwood), but not cleanly enough. |
| Pho vs Pad Thai | Could be chance | Vietnamese leads around Campsie and Canterbury, Thai in the outer south and north, but the border is too ragged. |
| Charcoal Chook (El Jannah vs Starbucks) | Could be chance | Patchy. |

**Over time (2001 to 2021):**
- 93% of suburbs stayed on the same side of the Hi-Vis Line (random maps: about 57%). Sydney's main split is old and stubborn.
- The suburbs that clearly moved were mostly an inner-south professional wave (Zetland, Waterloo, Rosebery, Wolli Creek, St Peters). Rosehill to Harris Park moved the other way.
- Factory workers fell from 11.6% to 5.3% of workers.
- "No religion" rose from 12% to 30%.
- People born in India are concentrating as the community grows; people born in Vietnam and the Philippines are spreading out.

**Street level:** the suburb-level lines agree with street-level ones for 94–96% of people. Parramatta South is the most split suburb (51% vs 26% professionals on its two sides).

**A trap we found:** a single chain's "territory" (e.g. "the KFC line") looks like a line on a map but is no cleaner than a fake chain put on random real food venues. Only chain-vs-chain comparisons are meaningful.

## Tokyo (first pass)

**In the app (454 neighbourhoods of about 30,000 people; verdicts corrected for trying several lines in each group):**

| Line | Verdict | What it shows |
|---|---|---|
| Hi-Vis Line | Beats chance, strongly | A professional core from central Tokyo west to Kichijōji; hi-vis jobs in the east (Hanahata, Mutsugi, Nishi-Mizumoto) and the outer west. |
| Factory Line, Laptop vs Hard Hat Line | Beats chance, strongly | Both retrace the Hi-Vis Line (90%+ of neighbourhoods). |
| Boomer vs Builder Line | Beats chance | Older and fewer builders in Seijō and Tama; younger with more builders around Shinbori and Kasai. Only 57% the same route as the Hi-Vis Line. |
| Living Alone Line, Grey Line | Beats chance | One-person homes in Nishi-Shinjuku and Kōenji; over-65s in the Tama new towns. |
| Latte Line | Could be chance (close) | Cafés lead in Minami-Aoyama, Daita and Tsukiji, fast food in the north-east; same route as the Hi-Vis Line on 72%. Raw p = 0.03, 0.08 after correction: Tokyo's Latte Line is faint compared with Sydney's (p = 0.002). |
| Coffee vs Alcohol | Beats chance | Cafés lean towards Todoroki and other family areas; izakaya and bars elsewhere. |
| My Basket vs the Konbini | Beats chance | Mini-supermarkets in the dense inner wards; konbini everywhere else. |
| Izakaya vs Italian & French | Beats chance | Izakaya in Nishiarai, Saginomiya and Ōmori; Italian and French hold their own in Jindaiji and the south-west. |
| Konbini, Gyudon, Starbucks vs Doutor, Ramen Wars | Could be chance | Chains mostly compete shop by shop. |
| Shrines vs Temples | Could be chance | No shrine side and temple side. Japan's Census doesn't ask about religion, so this counts buildings only; the shrine-vs-temple balance barely relates to the share of over-65s (rank correlation 0.07). |
| Price, Late-Night, Bars vs Izakaya, Yakiniku | Could be chance at this scale | These pass on the finer 1,402-町 map below, but not after merging into larger neighbourhoods and correcting for several night-time lines. |

**Grey Flip in the app:** only 48% of neighbourhoods are on the same side of the Grey Line in 2020 as in 2000, no better than two unrelated maps (about 52%). The Hi-Vis (86%), Living Alone (88%) and Tower (90%) lines barely moved.

**Finer-grained checks (1,402 町):**

1,402 neighbourhoods (町, all their 丁目 merged), about 13.6 million people. Census 2020 plus OpenStreetMap venues (Nov 2026).

| Line | Verdict | What it shows |
|---|---|---|
| Hi-Vis Line | Beats chance, strongly | A professional core from central Tokyo west to Kichijōji. Hi-vis jobs dominate the east (Adachi, Katsushika, Edogawa) and the outer west. |
| Living Alone Line | Beats chance | One-person homes in Shibuya, Kabukichō and the rail hubs; families in Tama. |
| Coffee vs Alcohol | Beats chance | Café-leaning areas are where owners and families live. Izakaya-leaning areas are around Adachi and Akishima. |
| Ramen vs Soba | Beats chance, modestly | Ramen is ahead where renters and people living alone are. Soba holds on in older areas like Komagome and Jindaiji. |
| Indie Café Line | Beats chance | Independent cafés cluster in Asakusa/Senzoku, Daita and Wakabayashi; chains win around Meguro, Shinagawa and Tōyōchō. |
| My Basket vs the konbini | Beats chance, strongly | Aeon's My Basket mini-supermarkets live in the dense inner wards with IT and office workers; the outer west is pure konbini. |
| Konbini Wars (7-Eleven vs FamilyMart vs Lawson) | Could be chance | No front line at all: the three are mixed shop by shop, everywhere. The opposite of Sydney's Red Rooster pattern. |
| Gyudon Wars (Matsuya, Sukiya, Yoshinoya) | Could be chance | Matsuya vs Yoshinoya came close (Matsuya leans north-west suburbs) but not close enough. |
| Ramen Wars: Iekei vs Hakata tonkotsu | Could be chance (close) | Iekei in the suburbs (Nerima, Machida, Higashikurume); Hakata in Ikebukuro, Roppongi and Ryōgoku. Raw p = 0.04, but we tried several ramen match-ups, so it doesn't pass yet. |
| Tsukemen vs other ramen | Could be chance (close) | Tsukemen shops bunch together more than other ramen; raw p = 0.02. |
| Starbucks vs Doutor, Saizeriya vs Gusto, McDonald's vs Mos, CoCo Ichi vs Indian/Nepali curry | Could be chance | Mixed together. |

**Over time (2000 to 2020):**
- 83% of neighbourhoods stayed on the same side of the Hi-Vis Line (random maps: about 56%). Like Sydney, the split is persistent.
- Biggest moves towards laptop jobs: Kōnan (Shinagawa towers, 6,000 → 22,000 people), Shinbashi, Minato (Chūō), Ōgibashi, and Rokuchō in Adachi (Tsukuba Express station opened 2005).
- Laptop jobs (managers and professionals) rose from 20.5% to 26.6% of workers; living alone from 41% to 51% of households; homes in 11+ floor blocks from 7.6% to 13.7%.
- **The Grey Flip:** in 2000 the inner wards were older than Tama (16.8% vs 14.1% aged 65+). By 2020 it had reversed (21.1% vs 25.3%). New towns built for young families in the 1970s–80s (Tama, Machida, Hachiōji) aged in place, some going from 10% to 45% aged 65+, while old downtown (Kuramae, Torigoe, Toranomon, Minato) got younger. Where old people live in 2020 is almost unrelated to where they lived in 2000 (rank correlation 0.06), even though the tower and living-alone maps barely changed (0.83, 0.85).
- Caveat: the Census changed its job categories in 2010, so the hi-vis share drops at 2010 partly for that reason. Comparisons use each neighbourhood's rank within its year, which is unaffected.

**HotPepper lines** (32,798 listings, restaurant data Powered by ホットペッパー Webサービス; "nearby" = within 1 km, about a 12–15 minute walk):

| Line | Verdict | What it shows |
|---|---|---|
| Price Line | Beats chance, strongly | The typical dinner nearby costs most around Azabu, Shirokane and Minami-Aoyama and least around Jūjō and Ōji in Kita. It follows the Hi-Vis Line on 70% of neighbourhoods: expensive dinners sit on the laptop side. Across neighbourhoods, the typical dinner band runs from about ¥2,500 to ¥4,500. |
| Late-Night Line | Beats chance | Places open past midnight lean towards renters and people living alone (Mishuku, Nakano, Mizue); early closers cluster around Higashi-Shinagawa, Yayoi and Nezu. It barely overlaps the Hi-Vis Line (52%): night life is its own map. |
| Izakaya vs Italian & French | Beats chance | Izakaya dominate in the north and east (Nishiarai, Kamiya, Saginomiya); Italian and French hold their own in Shirokane, Minami-Azabu and Ōmiya in Suginami. Izakaya-leaning areas are younger, with more renters and people living alone. |
| Bars vs Izakaya | Beats chance | Bars and bals outweigh izakaya in Shirokane, Azabu and Roppongi, and where more people are self-employed; izakaya hold the night out in Edogawa, Adachi and Akishima. |
| Yakiniku Line | Beats chance | Yakiniku is a bigger share of the food in builder and driver areas (Akishima, Hachiōji, Higashiyamato), and a small one around Komaba and Hakusan. Same route as the Hi-Vis Line on 70% of neighbourhoods. |

**Ramen Wars (OpenStreetMap + HotPepper merged):** 3,158 ramen shops, 1,208 with a known style (classic shoyu 418, Hakata 178, iekei 141, tsukemen 124, miso 97, Jiro-style 89, kotteri 64).

| Match-up | Verdict | What it shows |
|---|---|---|
| Iekei vs Hakata tonkotsu | Could be chance (closest) | Iekei holds the outer suburbs and older areas (Machida, Hamura, Nerima's Doshida); Hakata holds Ryōgoku, Roppongi and Kamiya. Raw p = 0.026, but after correcting for five match-ups it is 0.13. |
| Iekei vs classic shoyu | Could be chance | Mixed. |
| Tsukemen vs other ramen | Could be chance | Tsukemen leans to Kanamechō and Senkawa in Toshima, Chōfu and Akasaka; other ramen to Hachiōji. Weaker than in the OSM-only run. |
| Jiro-style vs classic shoyu; Miso vs Hakata | Could be chance | No real split: Tokyo's ramen styles mostly live side by side. |
