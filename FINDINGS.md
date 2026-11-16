# Findings in plain words

What we know after testing 29 cities. A **real line** splits a city more cleanly than random versions of that city that are just as smooth. A **gentle pattern** is real geography, but a slope rather than a line. **Could be chance** means the data can't tell. Descriptions are about areas, not the people in them. Older, longer notes are in the git history; where they disagree with this page, this page is right.

How sure each result is: see "Confirmatory or exploratory?" in [HYPOTHESES.md](HYPOTHESES.md).

## The test works, and the usual one doesn't

- The standard method (Moran spectral randomisation) calls lines on 26–66% of maps that have none, and on 99% of Chicago-shaped gradients. Ours, as every verdict uses it, called 5 lines in 72 empty Chicago maps (6.9%, close to the 5% it should).
- Our quick version runs a little hot (up to 10%) because one map can't reveal how broad the city's biggest gradients are. The double-check fixes this.
- The cost of being careful is power. A real step of 2 standard deviations across a border is found about one time in ten; one of 3 standard deviations, 17–54% of the time. "Gentle" means "no step big enough to see", not "no step".

## What's out there

- **Few lines are real.** 4% of lines in the first 18 cities, 7% in the 11 held-out ones.
- **They're slopes, not cliffs.** 94–98% of lines have no sharp stretch at all.
- **Lines rarely travel.** Four lines that looked general in Australia, Japan and England (Factory, Laptop vs Hard Hat, Degree, Bicycle) failed in the US, New Zealand and Singapore.
- **The Latte Line travels.** Cafés and fast food sort apart in all 29 cities, and the line is real pooled over the held-out cities (p = 0.02, with the pooling checked against maps that have no line). Across all 27 cities it survives taking out how well OpenStreetMap is filled in and how dense each area is (p = 0.005); in the held-out cities alone that leaves it borderline (p = 0.09), and in San Francisco it is mostly a mapping-and-density pattern. We found this by pooling every line, not as a written prediction, so the European cities are its real test.
- **US cities split by shopping:** Starbucks vs Dunkin' (New York), Whole Foods vs Walmart (Los Angeles).
- **Money is a slope.** Rent forms a line in none of 14 cities. It follows the class divide (Hi-Vis or Degree) in all 12 Australian and US cities, and renting and car ownership in New Zealand.
- **No hidden grammar.** Neighbouring areas' four-letter "words" (work, inner city, age, nightlife) go together beyond chance in only 1 of 26 cities once the broad gradients the lines share are kept in the comparison.
- **Countries have their own lines.** The Factory Line is real across Australia although no single city (Melbourne, Brisbane, Perth, Adelaide) shows it alone, and across England. Bicycle (Australia), Degree (England) and Latte (US) lean the same way but don't pass. Found, not yet confirmed.
- **Pooling needs checking too.** Even with no line anywhere, our p-values lean slightly low, and adding up 11 cities turns that lean into 14% false alarms. Every pooled result here is checked against pools of maps with no line.
- **Area size doesn't change the story.** Rebuilding four US cities from census tracts changed 3 of 56 verdicts.

## The Latte Line on trial (Sydney)

| Claim | Verdict |
|---|---|
| The 2021 lockdown's councils of concern were its fast-food side | **Holds** (p = 0.004; 0.02 after allowing for the six claims tested). Where the rules fell, not whether they were fair. |
| There are Latte Lines in other cities | **Holds** (see above) |
| Melbourne's divide is weaker | **Holds** (2 real lines in Sydney, none in Melbourne) |
| It runs north-east vs south-west through Parramatta | Likely (p = 0.03; 0.08 corrected) |
| School results depend on the side | Likely, for degrees (p = 0.01; 0.07 corrected) |
| It's a figure of speech, not coffee data | The data has one anyway, but it's a slope |
| The Red Rooster Line | Half true (p = 0.03 alone, 0.16 corrected) |
| Haves vs have-nots | Money falls the same way, as a slope that follows jobs more than coffee |
| $1m homes above the line | Mostly (70% and 79%, not "almost always") |
| It's breaking down | Consistent: El Jannah vs Starbucks could be chance |
| It's hardening | **No**, up to 2021: the jobs line was a real line in every census from 2001, equally sharp |
| Heat and tree cover; "ethnic west" | Not tested (no data; and we never test heritage against a line) |

## Sydney and Tokyo

- **Sydney:** two real lines, Hi-Vis (logistics, driving and labouring jobs vs professionals) and Factory. 93% of suburbs stayed on the same side of the Hi-Vis Line from 2001 to 2021.
- **Tokyo:** no line passes. Its divides ride one very broad gradient from the bay-side wards to the Tama hills, so short borders are what its scale predicts.

## What's next

- Ten European cities (Paris, Lyon, Marseille, Berlin, Munich, Hamburg, Rome, Milan, Madrid, Barcelona) against 20 predictions already on record, including whether Berlin's lines still follow the Wall.
- The 2026 Australian Census, to test "hardening" properly.

## Phase 2b so far (Spain, Italy; 16 Nov 2026)

Census only (venues wait for the OpenStreetMap cut). Same 1 km grid as Germany. Pre-registered in HYPOTHESES.md (Phase 2b) before testing.

- **Madrid's north–south divide (B1) holds, as a slope.** University degrees put 78% of the city's cells on the side of the seven southern districts that matches (random Madrids of the same smoothness: 59%; p = 0.008, 0.03 after Holm). Unemployment points the same way (74%, p = 0.03, 0.08 after Holm). But the Degree Line itself is not a sharp line: calibrated p = 0.055 (R = 200). Degrees rise steadily to the north (rank correlation with northing 0.62); the border sits across a slope.
- **Barcelona's Diagonal (B2) fails, as predicted.** No line matches the avenue better than random Barcelonas (best: the Grey Line, 66% vs 58%, p = 0.15).
- **Quick tests:** Rome's Living Alone Line p = 0.04 and Grey Line 0.06; Barcelona's Living Alone 0.07; calibrations running.
- **Exploratory, not pre-registered: who lives in the middle.** Living alone falls from the centre outwards in all seven European cities (rank correlation with distance from the centre −0.59 to −0.86). Old age goes the other way north and south of the Alps: in Berlin, Munich and Hamburg the share aged 65+ rises towards the edge (+0.31 to +0.42), in Madrid, Barcelona and Rome it falls (−0.39 to −0.60; Milan about 0).
- **Caveat on border tests.** The Berlin, Madrid and Barcelona border tests use the single-fit null, which Phase 1 found makes simulated cities slightly too rough (P2). A too-rough null can make a smooth slope look like it follows a big border more often than chance. A calibrated border test is the next step before B1 is final.

## Phase 2b: food lines and change over time (17 Nov 2026)

All venue p-values below are from the quick test (199 draws); cities with quick p < 0.2 still need the calibrated double-check, which usually raises p. Canada uses built-up cells as areas (no population data yet), a recorded deviation.

**Food lines**
- **Poutine Line (C1) holds.** 7.7% of Gatineau's fast-food places are poutine or casse-croûte spots (15 of 194) vs 1.3% across the river in Ottawa (15 of 1,130); one-sided Fisher p = 0.000004. Predicted.
- **Latte Line in Europe (P7):** pooled over 10 cities, Stouffer p = 0.019 (quick). Strongest in Marseille (0.02), Barcelona (0.03), Rome (0.07). Plain Stouffer is a little generous (no-line p-values lean low), so this is "likely holds", pending calibrated pooling.
- **Latte Line in Canada (C3) fails:** pooled p = 0.46. Only Ottawa shows one (0.015). Predicted to pass.
- **Croissant Line (F1):** Paris quick p = 0.005 (Holm over 3 cities 0.015); Lyon 0.155, Marseille 0.96. Predicted to fail; Paris goes against the prediction unless the calibrated check overturns it.
- **Bread Line (F2):** Hamburg 0.025, Berlin 0.225; Munich has too few chain bake-shops in OpenStreetMap (7). Holm over two cities: Hamburg 0.05, on the edge.
- **Paella Line (F3):** Barcelona 0.045, Madrid 0.48; Holm over two cities 0.09, so fails as predicted.
- **Starbucks Line (F4) cannot be tested properly:** only Paris (77) and Madrid (34) have ≥ 30 mapped Starbucks; pooled p = 0.15 over those two. Starbucks sits in the centre (rho −0.47 to −0.51 with distance), a slope not a line.
- **Timmies Line (C2) fails** in Toronto (0.125) and Calgary (0.915), as predicted.

**Change over time** (exploratory; T1–T3 in HYPOTHESES.md)
- **Most lines stay put.** Living alone and renting keep the same sides on 86–96% of cells across each decade (Rome, Milan 1991–2021; Berlin, Munich, Hamburg 2011–2022).
- **Living alone falls outward in every census** (T3 holds): Rome rho −0.69 to −0.71, Milan −0.79 to −0.85 from 1991 to 2021; German cities −0.58 to −0.78 in both 2011 and 2022.
- **The age line is the one that moves.** In Milan, over-65s were concentrated in the centre in 1991 (rho −0.76) and are now spread evenly (+0.06 in 2021); only 45% of cells keep their 1991 side. In Berlin and Hamburg the old are drifting outward (Berlin +0.21 → +0.39, 2011–2022). Rome's age pattern is stable (−0.65 → −0.60). Ageing suburbs, younger centres.
