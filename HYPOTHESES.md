# Hypotheses, tested phase by phase

Each phase ends with written predictions; the next phase's cities test them. These were committed before any Phase 1 data was opened, so the commit date shows they were not fitted to the results. Settings stay fixed between phases (null scales, number of draws, correction groups, family clustering); any change is reported as a deviation.

**Phases.** Phase 0: the 18 cities (Australia, Japan, England). Phase 1, held out: New York (by borough), Los Angeles, Chicago, San Francisco–Oakland, Washington, Austin, Seattle, Miami, Auckland, Christchurch, Singapore.

**Reading the table.** ✓ held, ✗ failed, ◐ partly held, – not testable with this phase's data. The p-value is the test behind the verdict where one exists; otherwise the observed figure is given. **Bold** numbers mark the core claims of the paper.

## Phase 1 in brief (scored 16 Nov 2026)

Eleven held-out cities: eight US cities, Auckland, Christchurch and Singapore. Of 50 scorable hypotheses, 29 held, 15 failed and 6 partly held; 10 could not be tested with this phase's data (mostly change over time). The scoring code is `experiments/phase1_scoring.py`; each verdict's exact rule is in `results/phase1/hypotheses.csv`.

- **The method claims hold.** The published Moran spectral randomisation calls lines on 26–66% of smooth maps with no line, and on 99% of Chicago's gradients; ours stays at 0–10%. But the quick single-fit version reaches 10% on Chicago's smooth maps, above the predicted 8%. The cause is general, not a big-city problem: one map cannot pin down landscape scales as large as the city, so the simulated cities come out slightly too rough (about +0.3–0.4 SD on the border count in both Chicago and Seattle). The calibrated test that every verdict uses absorbs this: 5 false alarms in 72 Chicago maps (6.9%, p = 0.29 against 5%).
- **Few lines are real** (11 of 167), and **they are slopes, not cliffs** (94% of lines have no sharp stretch).
- **Which lines exist does not transfer well.** The four lines that looked real in general after pooling Phase 0 (Factory, Laptop vs Hard Hat, Degree, Bicycle) do not replicate in the new cities. The Latte Line does (pooled p = 0.002 after correction), and so does the Hi-Vis Line in direction (it passes outright in New York), though not after correction.
- **US cities split by shopping more than other countries do:** Starbucks vs Dunkin' in New York, the Latte Line and Whole Foods vs Walmart in Los Angeles, and Cold Storage vs FairPrice in Singapore.

## A. Does the test hold up?

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| **1** | Our test keeps false alarms low on new city shapes | false alarms < 8% on smooth maps with no line | 4% (Kyoto, Melbourne) | ✗ seattle 6% (13/200); chicago 10% (10/100) (p = 0.028) |
| **2** | Moran spectral randomisation keeps failing | > 25% false alarms, all three forms | 32–56% | ✓ seattle 26%–28%; chicago 65%–66% (p < 0.001) |
| **3** | Gradients fool the standard method most | MSR > 70% on gradients; ours < 5% | 79–95% vs 0–1% | ◐ seattle: MSR 49%–60%, ours 2%; chicago: MSR 99%–99%, ours 0% |
| 4 | Uneven smoothness is our weak spot, but a mild one | ours 5–15% when smoothness varies | 5% / 11% | ✓ seattle 10%; chicago 8% (p = 0.128) |
| 5 | More areas, fewer false alarms | false-alarm rate falls with number of areas | – | ✗ 100 areas 6%, 164 areas 4%, 307 areas 4%, 401 areas 10% (p = 0.800) |
| 6 | Shuffling areas is useless everywhere | > 95% false alarms in every city | 98–100% | ✓ 98%–100% |

## B. Which statistic works?

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| 7 | Global Geary's C and Moran's I never detect a line | < 10% detection at a 3 SD step | 0–4% | ✓ Geary and Moran at a 3 SD step: 0%–2% |
| 8 | Counting the border is never the worst statistic | border count ≥ edge test on rough backgrounds | 26/46% vs 13/22% | ✓ rough background: border 9%, 21% vs edge 1%, 8% (2 and 3 SD) |
| 9 | The edge test wins in calm, spread-out cities | edge > border count on smooth backgrounds in large low-density cities | Melbourne 48% vs 28% | ✓ Los Angeles, smooth background, 3 SD step: edge 54% vs border 36% |
| 10 | Ranking hides jumps | ranking first cuts jump-test power by more than half | near-zero power when ranked | ✓ smooth: edge 12% standardised vs 1% ranked; rough: edge 8% standardised vs 2% ranked |

## C. Which lines are real?

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| **11** | Few lines pass | < 10% of tested lines pass after correction | 14 of 358 (4%) | ✓ 11 of 167 (7%) (p = 0.084) |
| 12 | Work lines recur | Factory or Hi-Vis passes in ≥ 2 new cities | 4 passes in 3 cities | ✗ 1 cities: newyork |
| 13 | The Bicycle Line passes where cycling is concentrated | passes in ≥ 1 of Seattle, San Francisco, Christchurch | Adelaide, Brighton, Kyoto | ✗ passes in no city; candidates tested: seattle, sanfrancisco, christchurch |
| 14 | Age and household lines almost never pass | Grey, Living Alone, Renters pass in ≤ 1 new city | 0 passes | ✓ 1 cities: sanfrancisco |
| 15 | Food and night lines rarely pass | venue lines pass in ≤ 2 new cities | 5 passes in 3 cities | ✗ venue lines pass in 3 cities: losangeles, newyork, sanfrancisco |
| 16 | US cities produce more real lines than Japanese ones | passes per US city > passes per Japanese city | Japan: 5 in 8 cities | ✓ 1.25 passes per US city vs 0.63 per Japanese city |
| 17 | New York boroughs act like separate cities | within-borough lines pass more often than city-wide lines | – | ✓ inside one borough 5 of 44 (11%); whole city 1 of 11 (9%) (p = 0.656) |
| 18 | Singapore has the fewest real lines | 0 passes in Singapore | – | ✗ 1 passes: Cold Storage vs FairPrice |

## D. Sharp or gradual?

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| **19** | Slopes, not cliffs | ≥ 90% of lines have no sharp stretch | 253 of 259 (98%) | ✓ 132 of 140 lines have none (94%) |
| 20 | Sharp stretches are short | each covers < 15% of its line | 5–10% | ✓ 5%–12% of the line |
| 21 | Sharp stretches sit on physical barriers | most fall on a freeway, rail line, river or park edge | not yet checked | – barrier check against OpenStreetMap roads and rail not run yet |
| 22 | US cities have more sharp stretches | share of lines with one: US > Australia and Japan | Australia 1 of 57 lines, Japan 2 of 119, England 3 of 83 | ✓ US 8 of 112 (7.1%) vs Australia 1.8%, Japan 1.7% |

## E. Line families

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| 23 | The same four families appear | ≥ 60% of lines land in the matching family | 4 families over 16 cities | ✓ 11 of 13 lines (85%) land in their Phase 0 family |
| 24 | Latte sits between families | Latte not assigned to one family | between work/class and night out | ✓ mean /r/ with Work and class 0.30, Night out 0.24 |
| **25** | Families are slopes, not walls | shared-border test passes ≤ 10% of families | 2 of 48 (4%) | ✓ 1 of 30 family tests pass (3%) (p = 0.785) |
| 26 | The age family is the most independent | lowest route match with other families | not yet checked | ✗ Night out 0.17, Work and class 0.19, Age 0.19, Inner city 0.23 |
| 27 | Inner city is the tightest family | highest within-family route match | not yet checked | ✓ Inner city 0.50, Work and class 0.49, Night out 0.31 |

## F. Change over time (US 5-year surveys; New Zealand 2013, 2018, 2023)

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| 28 | Work lines barely move | ≥ 80% of areas keep their side over 10 years | 83–99% | – earlier US survey periods and NZ 2013/2018 were not downloaded for this phase |
| 29 | Age moves fastest everywhere | Grey Line least stable in every city | yes, in every city with a timeline | – earlier US survey periods and NZ 2013/2018 were not downloaded for this phase |
| 30 | Age reshuffles to chance only in Japan | Grey Line stays above chance outside Japan | Japan 52–64%; Australia 77–83% | – earlier US survey periods and NZ 2013/2018 were not downloaded for this phase |
| 31 | Fast-growing cities move most | Austin, Seattle shift more than Chicago, New York | – | – earlier US survey periods and NZ 2013/2018 were not downloaded for this phase |
| 32 | Inner-city lines move outward | flats/renters side grows at the line's edge | – | – earlier US survey periods and NZ 2013/2018 were not downloaded for this phase |

## G. Chain wars

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| **33** | Same-type chains are more mixed than chance | burger and supermarket pairs mixed (p ≤ 0.05) in ≥ half the US cities | Maccas vs Hungry Jack's 4/4 AU; McDonald's vs KFC 3/4 UK | ✗ mixed in 2 of 5 US cities with a burger pair (chicago, losangeles) |
| 34 | Premium vs budget chains show a real line | e.g. Whole Foods vs Walmart passes in ≥ 2 US cities | Waitrose vs Lidl & Aldi, Greggs vs Pret pass in London | ◐ Whole Foods vs Walmart passes in 1 of 1 cities tested |
| 35 | Neutral pairs stay neutral | CVS vs Walgreens, Starbucks vs Dunkin' neither split nor mixed | konbini mostly neutral | ◐ 7 of 10 tests neutral |
| 36 | Mixing comes from each chain spacing out its own shops | own-shop spacing wider than random where a pair is mixed | not yet checked | ✓ own shops spaced out (p ≤ 0.05) in 3 of 5 mixed pairs: chicago McDonald's vs Burger King p=0.001; chicago McDonald's vs Wendy's p=0.001; chicago CVS vs Walgreens p=1.000; losangeles McDonald's vs Burger King p=0.001; losangeles Starbucks vs Dunkin' p=0.078 |
| 37 | Premium chains follow the work and class family | a passing premium line matches Degree or Laptop on ≥ 70% of areas | – | ✓ losangeles: matches degree on 74% |

## H. City rules

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| 38 | Rules beat correlation more often than chance | > 8% pass in each new city | 12% overall (4–18%) | ◐ 7%–21% by city, 14% overall |
| 39 | Bigger cities produce more passing rules | pass rate rises with number of areas | 4% Adelaide to 18% Manchester | ✓ Spearman ρ = 0.72 over 24 cities (p < 0.001) |
| **40** | Rules travel badly | AU or UK consistent rules pass in < 35% of US tests | 13–32% between countries | ✓ Australian rules 34%, English rules 19% of US tests |
| 41 | US rules transfer best to Australia | US→AU rate > US→JP rate | – | ✗ 6 US rules: 0% into Australia, 14% into Japan |
| 42 | New Zealand behaves like Australia | AU rules pass in > 50% of NZ tests | – | ✗ Australian rules pass in 22 of 45 New Zealand tests (49%) |
| 43 | Japan stays the odd one out | foreign rules pass in Japan least often | 13–32% into Japan | ✗ into AU 15%, into JP 20%, into US 27%, into UK 27% |
| 44 | The walking rule recurs | "few over-65s + few houses ⇒ more walking" holds in ≥ half the US cities | 3 of 3 testable AU cities | ✗ holds in 2 of 8 US cities where at least 12 areas match |

## I. Sister cities

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| 45 | Pairs come from size, not country | fingerprint distance correlates with size difference | – | ✗ Spearman ρ = -0.05 over 325 pairs (p = 0.408) |
| 46 | Sapporo–Brighton gets company | a new city within 0.25 of either | 0.19 apart | ✓ closest: chicago–brighton at 0.23 |
| 47 | Auckland's nearest sister is Australian | nearest is Brisbane or Perth | – | ✓ nearest: adelaide (0.18), then perth (0.19) |
| 48 | US cities cluster together | US cities' nearest sister is usually another US city | – | ✓ 8 of 8 US cities: newyork→chicago, losangeles→austin, chicago→washington, sanfrancisco→chicago, washington→chicago, austin→miami, seattle→washington, miami→austin |

## J. Scale and areas

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| 49 | Results don't hinge on area size | merging tracts changes < 20% of verdicts | Brighton fingerprint unchanged | ✓ 3 of 56 verdicts change at tract level (5%; seattle, austin, washington, sanfrancisco) |
| 50 | Real lines survive merging | passing lines stay real or gentle, never chance | – | ✓ sanfrancisco the-latte-line: line at tract level; sanfrancisco drink-out-vs-drink-in: line at tract level; sanfrancisco the-grey-line: gentle at tract level; sanfrancisco coffee-vs-alcohol: line at tract level |
| 51 | More areas mean more power, not more false passes | pass rate rises with areas; false alarms don't | – | – needs both levels in many cities; four cities are too few |

## K. Questions only the new cities can answer

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| 52 | The Income Line joins the work family | clusters with work and class | no income data | – income table (B19013) was not downloaded |
| 53 | The Car Line is the strongest US line | no-car line passes in New York, San Francisco, Washington | – | ✗ newyork: gentle, sanfrancisco: gentle, washington: gentle |
| 54 | Commute time adds its own divide | long-commute line not in the car family | – | – commute-time table was not downloaded |
| 55 | Remote work joins the inner-city family | work-from-home follows Degree, not Train | – | ✓ work-from-home side matches Degree on 80%, Train on 56% of areas (mean over 8 cities) |
| 56 | Singapore's planned estates are invisible | no line follows estate boundaries beyond chance | – | – estate boundaries not available as a map layer |

## L. Process

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| 57 | Nothing is retuned | no setting changed for Phase 1 | – | ◐ one recorded deviation: US train commuting widened to include light rail (see HYPOTHESES.md) |
| 58 | Most hypotheses won't survive untouched | at least a third fail or partly hold | – | ✓ 21 of 49 scored hypotheses failed or partly held |

## Added during Phase 1 (not pre-registered)

Written on 16 Nov 2026 after some Phase 1 verdicts had been seen (counts of passing lines in Washington, Seattle and San Francisco), but before any Phase 1 line's own p-value was computed, which is what pooling uses. Treat as a weaker test than the table above.

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| 59 | Work and cycling lines are real in general | Factory, Laptop vs Hard Hat, Degree and Bicycle each pooled across Phase 1 cities (Stouffer) at p ≤ 0.05 after Holm across lines | all four, Z = 3.2–5.4 over 15–16 cities | ✗ The Factory Line Z = 1.2 over 10 cities; The Laptop vs Hard Hat Line Z = 1.3 over 10 cities; The Degree Line Z = 2.0 over 10 cities; The Bicycle Line Z = 1.7 over 10 cities (p = 0.827) |
| 60 | Housing lines are not lines anywhere | Flats vs Houses, Renters, Grey pooled Z ≤ 0 | Z = −2.3, −1.8, −1.8 | ◐ Flats vs Houses Z = -0.3; The Renters Line Z = -0.2; The Grey Line Z = 0.9 |

## Notes after scoring

- **Hypothesis 1** was about the benchmark's single-fit test, and stays failed as written (Chicago 10 of 100). The calibrated test that every verdict uses was benchmarked afterwards on 72 fresh Chicago maps with no line, run exactly as the verdicts are (close calls refit 200 times): 5 false alarms (6.9%, 95% interval 2.3–15.5%, p = 0.29 against 5%). The single-fit test called 3 of the same 72 maps (`experiments/calibrated_benchmark.py`).

**Pooled p-values (16 Nov 2026).** The pooled Phase 1 figures above (hypotheses 59 and 60, and the Latte Line's p = 0.002) use Stouffer's method as written. On maps with no line our p-values lean slightly low, so pooled results are now also compared with pools of no-line p-values (experiments/pooled_calibration.py): the Latte Line's pooled p becomes 0.02 after correction, and no verdict in the table changes.

## Deviations

- **Phase 2, Germany (recorded 16 Nov 2026, before any German result was scored).** Germany publishes the 2022 census on a grid, not on small districts, so German areas are 1 km grid cells with at least 1,000 residents (the US density rule), taken from the jslth/z22data mirror of Destatis's grid tables. The grid has no jobs, education or venues, so only the Grey, Living Alone, Flats vs Houses and Renters Lines and the Money Line (net rent per m²) can be built. To save compute, lines with quick-test p ≥ 0.2 are not given the calibrated double-check: in 388 calibrated tests so far, none with quick p ≥ 0.2 came out at p ≤ 0.05.
- **US train commuting includes light rail** (recorded 16 Nov 2026, before any Phase 1 hypothesis was scored). The first US build counted subway and commuter rail only. Before any calibrated test was run, light rail and streetcar were added, to match the English definition ("underground, metro, light rail, tram"). Washington's first-pass p-values had been seen; Washington has almost no light rail. Most affected: Seattle and Los Angeles, whose main rail lines are light rail.

## Confirmatory or exploratory?

Every headline result, sorted by how much it can bear. **Confirmatory**: written down before the data were opened and scored by a fixed rule. **Weaker**: written during Phase 1, before the numbers it uses were computed. **Exploratory**: found by looking; it needs new data before it counts. Corrections: Holm within each line group for verdicts; Holm across lines for pooled results, with each pooled Z compared with pools of p-values from maps with no line (Stouffer alone gives 14% false alarms over 11 cities, because no-line p-values lean slightly low); Holm across the six Latte claims with a p-value.

| Result | Status | Evidence | Confirmed by |
|---|---|---|---|
| Moran spectral randomisation fails on new city shapes | Confirmatory (H2) | 26–66% false alarms | Phase 1 ✓ |
| Few lines pass (< 10%) | Confirmatory (H11) | 11 of 167 (7%) | Phase 1 ✓; Phase 2 P6 |
| Slopes, not cliffs | Confirmatory (H19) | 94% no sharp stretch | Phase 1 ✓; Phase 2 P11 |
| Quick test < 8% false alarms | Confirmatory (H1) | failed: Chicago 10% | Phase 1 ✗ |
| Calibrated test holds its size | Exploratory check, method fixed in advance | Chicago 5 of 72 (6.9%) | Phase 2 P1 |
| Work lines recur in new cities | Confirmatory (H12) | failed: 1 city | Phase 1 ✗ |
| Factory, Laptop, Degree, Bicycle are general | Weaker (H59) | failed: Z = 1.2–2.0 | Phase 1 ✗; Phase 2 P8 |
| The Latte Line holds in new cities | Exploratory (pooling every line) | p = 0.02 (pooling checked against no-line maps; Holm across lines) | Phase 2 P7 |
| US cities split by shopping | Exploratory | 3 of 8 US cities | Phase 2 P10 |
| Money is a slope that follows class | Exploratory | 0 of 14 after Holm; 12 of 12 AU/US routes | Phase 2 P13, P14 |
| No grammar beyond shared gradients | Exploratory | 1 of 26 cities | Phase 2 P15, P16 |
| Country lines: Factory in Australia (0.008) and England (0.006); Bicycle (AU), Degree (UK), Latte (US) lean | Exploratory | calibrated pooling, Holm within country | new cities in those countries |
| Latte claims: lockdown councils on the fast-food side | Exploratory (one test fixed per claim before running it) | p = 0.004; 0.02 after Holm across six claims | exact council boundaries |
| Latte claims: north-east vs south-west route; degrees | Exploratory | p = 0.03 and 0.01; 0.08 and 0.07 after Holm | none yet |
| Latte claims: no hardening 2001–2021 | Exploratory | Hi-Vis line real in every census | 2026 Census |
| Verdicts barely change with smaller areas | Confirmatory (H49) | 3 of 56 change | Phase 1 ✓ (four cities) |
| Ranking hides jumps | Confirmatory (H10) | 12% → 1% (Seattle) | Phase 1 ✓; Phase 2 P4 |

## Phase 2 predictions (Europe), written 16 Nov 2026

Committed before any Phase 2 census or OpenStreetMap data was opened. Cities: Paris, Lyon, Marseille, Berlin, Munich, Hamburg, Rome, Milan, Madrid, Barcelona. They are built from Phase 0 and Phase 1 together (29 cities), and each states the evidence it rests on.

**Rules for scoring.** Settings stay as in Phases 0–1. Each European census variable is matched to a line before the first test is run; the mapping is committed as a deviation. A prediction whose variable a country lacks is scored – for that country, not dropped. Pooling uses Stouffer's method on each line's own one-sided p, with Holm across lines.

| # | Prediction | Holds if | Evidence from Phases 0–1 | Phase 2 |
|---|---|---|---|---|
| **P1** | The calibrated test keeps false alarms near 5% | ≤ 10% false alarms on ≥ 50 smooth no-line maps in Paris and Berlin, run as the verdicts are | Chicago 5 of 72 (6.9%) | |
| P2 | The single fit makes simulated cities too rough | fitted broad-scale share below the true one, and null border bias between +0.1 and +0.6 SD, in Paris and Berlin | Chicago 23% true vs 13% fitted, Seattle 24% vs 1%; bias about +0.3–0.4 SD in both | |
| P3 | Moran spectral randomisation keeps failing | > 25% false alarms on smooth no-line maps | 26–66% in Phase 1 | |
| P4 | Ranking hides jumps | ranking cuts edge-test power at a 3 SD step by more than half | LA 54% → 8%; Seattle 12% → 1% | |
| P5 | Only big steps are detectable | border-count power < 20% at a 2 SD step and < 60% at 3 SD, in every city tested | LA 10–12% and 36–46%; Seattle 8–9% and 17–21% | |
| **P6** | Few lines pass | < 10% of tested lines pass after correction | 4% (Phase 0), 7% (Phase 1) | |
| **P7** | The Latte Line is real in general | the Latte Line (cafés vs fast food) pooled across Phase 2 cities at p ≤ 0.05 | pooled p = 0.002 in Phase 1 after correction | |
| P8 | Phase 0's "general" lines stay local | Factory, Laptop vs Hard Hat, Degree, Bicycle: at most one pooled at p ≤ 0.05 after Holm | none of the four replicated in Phase 1 (Z = 1.2–2.0) | |
| P9 | Housing lines are not lines | Flats vs Houses, Renters, Grey: pooled Z ≤ 1 each | Phase 0 Z = −2.3 to −1.8; Phase 1 Z = −0.3 to 0.9 | |
| P10 | European cities split by shopping less than US cities | venue lines pass in ≤ 2 of the 10 cities | US: venue lines pass in 3 of 8 cities (New York, LA, San Francisco) | |
| **P11** | Slopes, not cliffs | ≥ 90% of lines have no sharp stretch | 98% (Phase 0), 94% (Phase 1) | |
| P12 | Sharp stretches are short | each covers < 15% of its line | 5–12% | |
| **P13** | Money is a slope, not a line | where a money variable exists (income or rent), no city's Money Line passes after Holm across cities | 0 of 14 after Holm (lowest Christchurch 0.025, Holm 0.35) | |
| P14 | Money follows class, as in Australia and the US | Money Line's route has the Degree or a manual-work line among its two closest routes, matching ≥ 65% of areas, in every city with a money variable | 12 of 12 AU/US cities (69–83%); New Zealand follows renting and cars instead | |
| **P15** | There is no grammar beyond shared gradients | factor baseline p ≤ 0.05 in at most 2 of the 10 cities | 1 of 26 cities (Auckland; 1.3 expected by chance) | |
| P16 | The apparent grammar is shared gradients | against the weaker mixed baseline, p ≤ 0.05 in ≥ 5 of the 10 cities | 19 of 26 under mixed vs 1 of 26 under factor | |
| P17 | Grammar is a little more alike within a country | within-country word-pair correlation > across-country, under both baselines | factor 0.23 vs 0.13; mixed 0.35 vs 0.25 | |
| P18 | Rules rarely beat chance | 4–20% of testable rules beat the copula-plus-spatial baseline | 12% overall (4–18% by city) | |
| P19 | Nothing is retuned | no setting changed for Phase 2 | one deviation in Phase 1 (US light rail) | |
| P20 | Many predictions fail | at least a third fail or partly hold | 21 of 49 in Phase 1 | |

**Correction, 16 Nov 2026, before any Phase 2 data was opened:** P7's rule first named the Coffee vs Alcohol line by mistake; the prediction, and its Phase 1 evidence, are about the Latte Line (cafés vs fast food).

**Exploratory, not scored as predictions:** whether any passing Berlin line follows the 1961–89 sector border, and whether Paris's passing lines follow the Boulevard Périphérique. These are reported either way.

## Phase 2b: named borders and country lines, written 16 Nov 2026

Committed before any test was run on Spanish, Italian or Canadian data (the Spanish and Italian census files were opened only to read their column names). Each named border is tested like the Berlin Wall: for each census line, the share of areas whose side of the line matches their side of the border, compared with 999 simulated cities from the same fitted landscape. Census lines tested on every border: university degrees, unemployment, renting, aged 65+ (Holm across the four). A border "holds" if at least one line matches it at p ≤ 0.05 after Holm. Heritage and language are never scored.

| # | Border or line | Defined as | Prediction | Reason |
|---|---|---|---|---|
| B1 | Madrid's north–south divide | the seven southern districts (Latina, Carabanchel, Usera, Puente de Vallecas, Villaverde, Villa de Vallecas, Vicálvaro) vs the rest of the city | holds (degrees or unemployment) | the most quoted divide in Spanish urban writing |
| B2 | Barcelona's Diagonal | areas uphill (north-west) of Avinguda Diagonal vs downhill, inside the city | fails | Barcelona's contrast is an uphill gradient plus a few poor districts at both ends, not one avenue |
| B3 | Rome's Grande Raccordo Anulare | inside vs outside the ring road | fails as a border (a slope instead) | poor eastern districts lie inside the ring too |
| B4 | Milan's outer ring (Circonvallazione esterna, the 90/91 bus route) | inside vs outside | holds (degrees) | strong centre–periphery contrast in Milan |
| B5 | Paris's Boulevard Périphérique | inside vs outside | holds (degrees) | already listed as exploratory above; promoted here with this rule |
| C1 | The Poutine Line | share of poutine/casse-croûte venues among fast food, Gatineau vs Ottawa (same box, either side of the Ottawa River) | higher in Gatineau, p ≤ 0.05 | poutine is a Quebec dish |
| C2 | The Timmies Line | Tim Hortons vs independent cafés, Toronto and Calgary, ordinary line test | fails in both | venue lines rarely pass (P10) |
| C3 | Canada's Latte Line | cafés vs fast food, Toronto, Ottawa, Montreal, Calgary, Edmonton, pooled with calibrated pooling | passes | P7 evidence from 27 cities |

Borders needing OpenStreetMap geometry (B3–B5) wait for the OSM cut; B1 and B2 use census districts and the avenue's end points.

**Variable mapping for Spain and Italy, committed 16 Nov 2026 before the first test.** Areas: census sections allocated to the same 1 km grid cells as Germany (area-weighted), cells with ≥ 1,000 residents, largest connected piece. Spain (INE 2021 section indicators): Degree Line = t9 (higher education, of 16+); Grey Line = t4_3 (65+); Renters Line = t20_2 / (t20_1 + t20_2 + t20_3); Living Alone Line = t22_1 / t21_1; Jobless Line (new) = t10 (unemployed, of the active). Italy (ISTAT 2021 sections) has no education, tenure or unemployment at section level: Grey Line = P27 + P28 + P29 (65+); Living Alone Line = PF3 / PF1; Jobless Line = 1 − (IT10 + ST31) / (IT2 + ST23), the share of 15–64s not in work (includes the inactive, so it is not the Spanish unemployment rate); Empty Homes Line (exploratory) = A3 / A8. Nationality columns are not used. On the borders B1–B5, "degrees, unemployment, renting, 65+" become, in Italy, "not in work, living alone, 65+" (Holm across three).

## Phase 2b food lines, written 16 Nov 2026

Committed before any European OpenStreetMap data was opened (the cut is still running). Same line test, same settings as every venue line; each city's own p, then calibrated pooling across the cities named. Venues are OSM points inside each city's box; a venue's brand comes from its `brand` or `name` tag.

| # | Line | Side A vs side B (OSM tags) | Cities | Prediction |
|---|---|---|---|---|
| F1 | The Croissant Line | bakeries and pâtisseries (`shop=bakery`, `shop=pastry`) vs fast food (`amenity=fast_food`) | Paris, Lyon, Marseille | fails in each city (bakeries are everywhere in France) |
| F2 | The Bread Line (Bäcker vs Backshop) | independent bakeries (`shop=bakery`, no chain brand) vs chain bake-shops (Back-Factory, BackWerk, Kamps, Ditsch, Le Crobag, Wiener Feinbäcker, Lila Bäcker, Junge, Steinecke, Backhaus Mahl, Bäckerei Junge, Mr. Baker) | Berlin, Munich, Hamburg | fails in each city; chains sit at stations, so it is a slope towards the centre |
| F3 | The Paella Line | Spanish and tapas restaurants (`cuisine` contains spanish, tapas, paella, regional) vs fast food | Madrid, Barcelona | fails in each city |
| F4 | The Starbucks Line | independent cafés (`amenity=cafe`, no chain brand) vs Starbucks | all eight French, German and Spanish cities, pooled | passes pooled (a centre-to-edge slope shared by every city) |

Italy (Rome, Milan) is run on F4 as exploratory only. Food names are a joke; what is scored is where cheap, chain or traditional food sits, never who lives there.

**Venue definitions and areas, committed 17 Nov 2026 before any venue line was computed.** (OpenStreetMap files had been checked only for file integrity and total counts per tag.)
- *Areas.* Germany, Spain, Italy: the same 1 km cells as their census tests. France: 1 km cells of the Eurostat 2021 census grid with ≥ 1,000 residents inside each city box, largest connected piece (French census areas on the grid are not built yet). Canada: no population data is in hand, so 1 km cells (Statistics Canada Lambert, EPSG 3347) holding ≥ 10 OpenStreetMap places of any kind stand in for built-up areas, largest connected piece; this is a deviation and Canada's results are marked as such.
- *Field and test.* As in Phases 0–1: per cell, log((A + 0.5) / (B + 0.5)), ranked to normal scores, quick landscape test (199 draws); a line needs ≥ 30 venues on each side in the city, else it is reported as "too few venues". Pooling: Stouffer on each city's quick p. The calibrated double-check follows for any city with quick p < 0.2; until then a result is marked quick.
- *Chains.* A café or bakery is a chain if it carries a `brand` tag or its name matches a chain list (Starbucks, Tim Hortons, Second Cup, Costa, McCafé, Columbus Café, Coffee Fellows, Balzac, Einstein, Espresso House, Café Nero, Segafredo, Tchibo, Lavazza, Paul, Brioche Dorée, and the F2 bake-shop list); independent = neither. Starbucks = name or brand contains "starbucks"; Tim Hortons = name or brand contains "tim horton".
- *Poutine venue (C1).* `cuisine` contains poutine, or name contains poutin, casse-cro, patate, belle province, ashton, lafleur, valentine, frite alors or smoke's. C1 is scored by a one-sided Fisher exact test of poutine venues among fast food (`amenity=fast_food`), Gatineau vs Ottawa; Gatineau and Ottawa are the Quebec and Ontario sides of the same box.
- *Paella venue (F3).* `amenity=restaurant` whose `cuisine` contains spanish, tapas, paella or regional.

**Time questions, committed 17 Nov 2026 before any spatial statistic on an older census was computed** (files had been checked only for completeness and national totals). Exploratory throughout. T1 *Lines stay put*: for a variable measured in two censuses on the same areas, the median-split sides agree on ≥ 80% of areas across ten years. T2 *Gradients do not sharpen*: the centre-to-edge Spearman correlation changes by less than 0.1 per decade. T3 *Living alone keeps falling outward*: negative centre-to-edge correlation in every census year where it can be measured. Areas: Italy 1991, 2001, 2011 census sections on the Rome and Milan 1 km cells; Germany 2011 (100 m grid) vs 2022 on the Berlin, Munich and Hamburg cells; Japan 500 m mesh 1995–2020 for Tokyo and Osaka; US 2010 tracts 1990–2020 once tract shapes are in hand.

**Canada census lines, mapping committed 17 Nov 2026 before the first test** (the file had been checked only for completeness). Statistics Canada 2021 Census Profile, dissemination areas allocated by area to 1 km cells (EPSG 3347), cells with ≥ 1,000 residents, largest connected piece; Toronto, Ottawa, Montreal, Calgary, Edmonton boxes as in the OpenStreetMap cut. Grey Line = 65+ (id 24) / all ages (8); Living Alone Line = one-person households (51) / households (50); Renters Line = renters (1416) / tenure total (1414); Degree Line = bachelor's or higher (2008) / 15+ (1998); Jobless Line = unemployment rate (2230), population-weighted. Heritage, language and immigration columns are not used. Scored by the existing predictions: P6 (few lines pass), P9 (housing lines are not lines, pooled Z ≤ 1 for Renters and Grey).
