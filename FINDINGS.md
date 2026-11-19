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
- **US 1990–2020 (8 cities, NHGIS tracts on 2010 units) shows the same pattern.** Renting and living alone keep their sides on 82–97% of tracts per decade and their centre-to-edge slopes barely change. The over-65s move outward everywhere: rho with distance rises from 1990 to 2020 in all eight cities (Chicago +0.21 → +0.53, Washington −0.13 → +0.24, Seattle +0.03 → +0.36, Austin −0.41 → −0.03). Over thirty years only 58–76% of tracts keep their 1990 age side, against 82–95% for renting.

## Firming up (17 Nov 2026, later)

**Madrid's north–south border holds after calibration.** Degree Line: 78% of cells on the matching side, single-fit p 0.004, calibrated p 0.005 (200 refits; none of the 200 no-border maps did as well); Holm over the four pre-registered variables 0.02. Jobless Line: calibrated p 0.040, Holm 0.12. The single fit was nearly honest for this border (6–8% false alarms at 5%), so B1 holds on degrees.

**Poutine Line survives clustering.** Resampling whole 1 km squares (20,000 times): Gatineau's poutine share is 6.4 points higher, 95% interval 3.1 to 10.6 points, p < 0.0001. Counting each restaurant name once: 15 of 119 names in Gatineau vs 12 of 629 in Ottawa, p = 0.000002.

**Food lines, calibrated (40 refits; a calibrated p of 0.024 means none of 40 refits did as well, 0.049 means one).** Calibration moved p in both directions. Paris Croissant 0.024 (Holm over three cities 0.07: suggestive, not confirmed); Paris Latte 0.049; Marseille Latte 0.049; Barcelona Latte 0.024; Barcelona Paella 0.049 (Holm 0.10, fails as predicted); Rome Latte 0.049; Ottawa Latte 0.024; Hamburg Bread 0.024 (Holm 0.05, on the edge); Toronto Timmies 0.049 (predicted to fail; borderline); Lyon Croissant 0.12; Calgary Latte 0.12; Madrid Starbucks 0.29. Latte Line pooled over 10 European cities with calibrated p where available: Stouffer p = 0.014 (P7 likely holds); Canada pooled p = 0.46 (C3 fails). The pre-registered rule gives close calls 200 refits; that final step is still to run for every line at 0.049 or below.

**Canada census lines (quick test, 25 tests).** None passes after Holm within its city (lowest: Toronto Jobless 0.02, Montreal Renters 0.02, Edmonton Degree 0.035), so P6 holds. Pooled: Degree Z = 2.52 (p = 0.006), Renters Z = 1.69 (P9 fails for Canada: renting leans towards a line), Grey Z = −0.71. Living alone falls outward in all five cities (rho −0.34 to −0.70), as everywhere else.

**Did the lines move? Block bootstrap of the change in centre-to-edge slope** (5 km squares resampled, Holm over 37 city–variable tests). The age slope rose — older residents spreading outward — in all 13 cities measured (sign test p = 0.0002); it survives Holm in Los Angeles (+0.19), Washington (+0.37), Milan (+0.82), Berlin (+0.18) and Hamburg (+0.11), with Chicago (+0.32) and Austin (+0.38) at Holm 0.08 and 0.32. Renting and living alone changed by less than 0.07 in 20 of 24 cases; the exceptions are living alone in Miami (−0.22), Austin (+0.17) and Chicago (+0.10), and renting in Austin (+0.15).

## Phase 3: Netherlands, Sweden, Denmark, São Paulo, sister cities (17 Nov 2026)

Predictions Q1–Q5 in HYPOTHESES.md, committed before the first statistic. Line tests are quick tests (199 draws).
- **Q1 holds: older residents move outward almost everywhere.** The over-65 (São Paulo 60+) centre-to-edge slope rose in 18 of 21 cities with two or more censuses (sign test p = 0.0015): all 13 Phase 2 cities, all four Dutch cities (The Hague +0.29, Holm 0.01; Utrecht +0.39; Rotterdam +0.20; Amsterdam +0.04) and São Paulo (+0.11, Holm 0.01). **Sweden is the exception:** Stockholm (−0.11, p = 0.02), Gothenburg (−0.20) and Malmö (−0.10) moved the other way between 2015 and 2025, the shortest series.
- **Q2 holds: housing lines stay put.** Renting, living alone and household size changed slope by less than 0.1 per decade in 11 of 13 city–variable pairs (85%).
- **Q3 holds:** living alone falls from centre to edge in every Dutch city and year.
- **Q4 holds:** 1 of 25 lines passes after Holm (Aarhus Grey Line, quick p = 0.005, Holm 0.01; calibrated check pending).
- **Q5 holds: cities have national sisters.** Comparing each city's slopes for age, living alone and renting, the most similar city is in the same country for 13 of 22 cities (59%; permutation p = 0.001). Cross-border pairs: Amsterdam–Washington, Hamburg–Seattle, Madrid–Calgary, Barcelona–Edmonton, Austin–Toronto, Ottawa–Miami. Figures: results/phase3/fig_sisters.png, fig_age_front.png, fig_age_maps.png.


## The Chippy Line (pre-registered 17 Nov 2026, commit 7651aa7)

Chippies (fish_and_chips cuisine or chip / fish bar names) vs cafés, Phase 1 England areas, quick test (199 draws). `experiments/chippy_line.py` → `results/chippy/chippy_line.csv`.

| City | Chippies | Cafés | Chippies per café | p | Holm | Spearman with Latte field |
|---|---|---|---|---|---|---|
| London | 638 | 6878 | 0.09 | 0.28 | 1 | −0.45 |
| Manchester | 332 | 1029 | 0.32 | 0.63 | 1 | −0.44 |
| Birmingham | 345 | 819 | 0.42 | 0.58 | 1 | −0.60 |
| Liverpool | 206 | 630 | 0.33 | 0.95 | 1 | −0.63 |
| Brighton | 58 | 408 | 0.14 | 0.23 | 1 | −0.35 |

Pooled Stouffer Z = −0.36 (p = 0.64). H1 (no line after Holm) holds. H2 holds in substance: the Latte field is log(cafés/fast food), so a negative correlation means chippies sit on the fast-food side; |ρ| > 0.3 in the predicted direction in all five cities. Deviation: the pre-registration wrote "> 0.3" without fixing the sign convention. H3 (Brighton and Liverpool most chippies per café) fails: Birmingham is first, Liverpool second, Brighton fourth.

## Paris boulangeries vs pâtisseries (exploratory, reader suggestion, not pre-registered)

shop=bakery (3,265) vs shop=pastry (441) on the 903 Paris food cells: quick p = 0.67; Spearman with distance from the centre −0.40 (pâtisseries relatively central). `experiments/paris_bakeries.py`. Viennoiserie has no OSM tag.

## Phase 3 meme lines (pre-registered 17 Nov 2026)

`experiments/phase3_food.py` → `results/phase3/food_lines.csv`. Quick test (199 draws, m=9) on the Phase 3 1 km cells; field log((A+.5)/(B+.5)); slope = Spearman with distance from the population-weighted centre. Holm over all 11 tests.

| City | Line | A | B | Cells | p | Slope | Holm |
|---|---|---|---|---|---|---|---|
| Amsterdam | Cafés vs fast food (Snackbar vs Koffiebar) | 740 | 743 | 129 | 0.89 | −0.30 | 1 |
| Rotterdam | Cafés vs fast food (Snackbar vs Koffiebar) | 256 | 450 | 122 | 0.37 | −0.11 | 1 |
| The Hague | Cafés vs fast food | 324 | 546 | 114 | 0.88 | 0.13 | 1 |
| Utrecht | Cafés vs fast food | 149 | 238 | 49 | 0.81 | 0.31 | 1 |
| Stockholm | Cafés vs fast food (Fika) | 656 | 730 | 221 | 0.31 | −0.04 | 1 |
| Gothenburg | Cafés vs fast food (Fika) | 288 | 238 | 127 | 0.50 | −0.10 | 1 |
| Malmö | Cafés vs fast food (Fika) | 159 | 193 | 60 | 0.52 | 0.20 | 1 |
| Copenhagen | Cafés vs fast food | 957 | 1547 | 198 | 0.32 | 0.13 | 1 |
| Aarhus | Cafés vs fast food | 183 | 344 | 72 | 0.63 | 0.18 | 1 |
| São Paulo | Cafés vs fast food | 417 | 1306 | 1012 | 0.32 | 0.28 | 1 |
| São Paulo | Coffee vs Churrasco | 417 | 107 | 1012 | 0.95 | −0.15 | 1 |

Latte pooled over the nine European cities: Stouffer Z = −0.76, p = 0.78. All three meme-line predictions hold (no line in any of them). Coffee vs Churrasco was predicted a slope; the slope is weak (ρ = −0.15, cafés relatively central). The Latte Line's spread is now mixed: pooled real across the Phase 2 European cities (p = 0.014, driven by Barcelona, Paris, Marseille, Rome), absent in the Netherlands, Sweden and Denmark. 82–95% of cafés inside each city box fall in a populated cell; OpenStreetMap coverage of São Paulo cafés is thin (509 in the box).

## COVID-19 cases and Sydney's lines (pre-registered 17 Nov 2026, commit a619166)

`experiments/covid_lines.py` → `results/covid/{summary.json, suburbs.csv}`; figure `experiments/covid_figure.py` → `results/covid/fig_covid_sides.png`. NSW Health confirmed cases by postcode of usual residence (one row per case, 25 Jan 2020 – 7 Feb 2022; 973,412 cases, 1.4% without a postcode), shared to the 300 Sydney suburbs with the ABS POA→SA2 2021 correspondence; 2021 Census population. Delta wave 16 Jun – 15 Dec 2021: 67,293 cases in the study suburbs (of 84,964 NSW cases with a postcode).

| # | Result | Verdict |
|---|---|---|
| V1 | Spearman ρ (Delta rate, Latte field) = −0.63; 999 random Sydneys just as smooth: mean 0.00, 95% range −0.51 to 0.54; one-sided p = 0.003, Holm 0.003 | holds |
| V2 | ρ (Delta rate, Hi-Vis field) = +0.74, p = 0.001 (Holm 0.002); |0.74| ≥ |0.63| | holds |
| V3 | councils of concern 22.4 vs rest 5.8 cases per 1,000: ratio 3.84 (suburb bootstrap 95% CI 3.44–4.98) | holds (descriptive) |
| V4 | fast-food side / café side: first wave 2020 0.74 (0.61–0.87), Delta 3.06 (2.47–3.75), Omicron to 7 Feb 2022 1.17 (1.03–1.30) | holds (descriptive) |
| V5 | within the café side: ρ with household size −0.24, with Hi-Vis +0.40; fast-food side: +0.19 and +0.67 | fails for household size (negative on the café side); Hi-Vis positive on both |

Delta rates: fast-food side 22.2 per 1,000 (about 1 resident in 45), café side 7.3 (1 in 137). By council of concern (per 1,000): Cumberland 38.9, Canterbury-Bankstown 34.9, Liverpool 27.8, Fairfield 27.3, Blacktown 19.8, Campbelltown 16.9, Penrith 15.9, Parramatta 12.1, Strathfield 12.1, Bayside 12.0, Georges River 9.8, Burwood 8.5.

Deviation: the pre-registration said Omicron runs "to the end of the series"; the case-level PCR table ends on 7 Feb 2022, and the aggregated table that runs to 2023 adds rapid antigen tests from January 2022, so Omicron uses the case-level table only. The 2020 first wave had 3,105 study-area cases (≥ 1,000), so it is reported. Reading: these are confirmed cases by home postcode; they mix infection with testing, and the orders followed the cases, so none of this separates cause and effect.
Share of the study area's Delta cases: 75% on the fast-food side of the Latte Line (which holds 50% of residents), 82% in the councils of concern.

## Aarhus Grey Line, calibrated (R = 200)

`experiments/aarhus_calibrated.py` → `results/phase3/aarhus_grey_calibrated.json`: quick p 0.005, calibrated p 0.005, size of the quick test on refit maps 2.5%. Holm within Aarhus (two lines) 0.01. The one Phase 3 line that passed stands.

## Food lines with 200 refits (17 Nov 2026)

`experiments/run_food_cal200.sh`; every food line with calibrated p (R = 40) below 0.1 rerun with R = 200 (smallest p 0.005).

| Line | City | Calibrated p (R = 200) | Holm (family) |
|---|---|---|---|
| Latte | Barcelona | 0.010 | |
| Latte | Ottawa | 0.010 | |
| Latte | Marseille | 0.010 | |
| Latte | Rome | 0.020 | |
| Latte | Paris | 0.045 | |
| Croissant | Paris | 0.005 | 0.015 (Paris, Lyon, Marseille) |
| Bread | Hamburg | 0.005 | 0.010 (Berlin, Hamburg) |
| Paella | Barcelona | 0.045 | 0.090 (Madrid, Barcelona) |
| Timmies | Toronto | 0.040 | 0.080 (Toronto, Calgary) |

Latte pooled over the ten European cities (calibrated where available): Stouffer Z = 2.67, p = 0.004 (was 2.20, 0.014 with R = 40). Canada: Z = 0.25, p = 0.40. Croissant and Bread now pass after Holm; Paella and Timmies do not.

## Korea: Seoul and Busan (pre-registered 18 Nov 2026, commit d075499)

`experiments/korea_build.py`, `experiments/korea_analysis.py` → `results/phase3/{seoul,busan}_cells.csv.gz, korea.json, sisters_two_slopes.csv`. SGIS 2024 1 km grid (data.go.kr, 국가데이터처). Seoul box: 716 cells, 11.95 million residents (Seoul plus the inner Gyeonggi suburbs in the box); Busan: 238 cells, 2.89 million. Quick test, 199 draws, Holm within city (3 lines).

| City | Line | p | Holm | Slope with distance |
|---|---|---|---|---|
| Seoul | Grey (65+) | 0.63 | 0.88 | +0.01 |
| Seoul | Living Alone | 0.44 | 0.88 | −0.30 |
| Seoul | Apartment | 0.21 | 0.63 | +0.23 |
| Busan | Grey | 0.16 | 0.48 | +0.06 |
| Busan | Living Alone | 0.51 | 1.0 | −0.06 |
| Busan | Apartment | 0.71 | 1.0 | +0.16 |

K1 (no line) holds. K2 (living alone falls outward) holds, strongly in Seoul, weakly in Busan. K3 (over-65s rise outward) holds on sign only: both slopes are close to zero, so age is spread almost evenly. K4 (Seoul's sister is Japanese) fails: on the two slopes every city has (Grey, Living Alone), Seoul's nearest city is Ottawa (distance 0.04), then Montreal and Kobe; Busan's is Yokohama, then Kobe. On these two slopes alone, the nearest sister shares a country for 20% of 40 cities (permutation p = 0.10), weaker than the 59% on three slopes. Phase 1 cities enter with their app Living Alone field (living alone minus families), not the plain share.

## COVID-19: is the Latte Line just the jobs line? (exploratory, 19 Nov 2026)

`experiments/covid_partial.py` → `results/covid/partial.json`. Partial Spearman of the Delta case rate on one line with the other held fixed (rank residuals). The two lines correlate at ρ = −0.79 across the 300 suburbs.

| Partial | r | 999-map null, 95% range | one-sided p |
|---|---|---|---|
| Latte, holding Hi-Vis fixed | −0.11 | −0.35 to 0.35 | 0.30 |
| Hi-Vis, holding Latte fixed | +0.52 | −0.40 to 0.42 | 0.003 |

Once the jobs divide is known, the café divide adds nothing about where Delta cases fell; the jobs divide still adds a lot once the café divide is known. In this sense the Latte Line's COVID result is the jobs line seen through coffee. Not pre-registered.

## Suburb twins (app feature, 19 Nov 2026)

`experiments/suburb_twins.py` → `app/public/twins/`. Every area in 28 cities (Singapore lacks the census lines) gets its three nearest areas in other cities, one per city, on eight within-city normal scores (Hi-Vis, Degree, Grey, Living Alone, Flats vs Houses, Renters, Train vs Car, Latte), needing ≥ 6 shared lines. Twins sit on the same side of their city's middle on 91% of shared lines on average (median 100%, 5th percentile 75%; Sydney, London, Tokyo). Examples: Surry Hills ↔ Tenjin (Fukuoka), Barons Court (London); Mount Druitt ↔ Farnworth North (Manchester); Bondi Beach ↔ Daita (Tokyo).
