# Hypotheses, tested phase by phase

Each phase ends with written predictions; the next phase's cities test them. These were committed before any Phase 1 data was opened, so the commit date shows they were not fitted to the results. Settings stay fixed between phases (null scales, number of draws, correction groups, family clustering); any change is reported as a deviation.

**Phases.** Phase 0: the 18 cities (Australia, Japan, England). Phase 1, held out: New York (by borough), Los Angeles, Chicago, San Francisco–Oakland, Washington, Austin, Seattle, Miami, Auckland, Christchurch, Singapore.

**Reading the table.** ✓ held, ✗ failed, ◐ partly held, – not testable with this phase's data. The p-value is the test behind the verdict where one exists; otherwise the observed figure is given. **Bold** numbers mark the core claims of the paper.

## Phase 1 in brief (scored 16 Nov 2026)

Eleven held-out cities: eight US cities, Auckland, Christchurch and Singapore. Of 46 scorable hypotheses, 25 held, 15 failed and 6 partly held; 14 could not be tested with this phase's data (mostly change over time). The scoring code is `experiments/phase1_scoring.py`; each verdict's exact rule is in `results/phase1/hypotheses.csv`.

- **The method claims hold.** The published Moran spectral randomisation calls lines on 26–66% of smooth maps with no line, and on 99% of Chicago's gradients; ours stays at 0–10%. But ours reaches 10% on Chicago's smooth maps, above the predicted 8%: a real, mild weakness in very large cities.
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
| 9 | The edge test wins in calm, spread-out cities | edge > border count on smooth backgrounds in large low-density cities | Melbourne 48% vs 28% | – needs a large low-density city; the power study was run on Seattle (100 areas) |
| 10 | Ranking hides jumps | ranking first cuts jump-test power by more than half | near-zero power when ranked | – the ranked versions of the jump tests were not rerun |

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
| 49 | Results don't hinge on area size | merging tracts changes < 20% of verdicts | Brighton fingerprint unchanged | – tract-level rebuild not run yet |
| 50 | Real lines survive merging | passing lines stay real or gentle, never chance | – | – tract-level rebuild not run yet |
| 51 | More areas mean more power, not more false passes | pass rate rises with areas; false alarms don't | – | – tract-level rebuild not run yet |

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
| 58 | Most hypotheses won't survive untouched | at least a third fail or partly hold | – | ✓ 21 of 45 scored hypotheses failed or partly held |

## Added during Phase 1 (not pre-registered)

Written on 16 Nov 2026 after some Phase 1 verdicts had been seen (counts of passing lines in Washington, Seattle and San Francisco), but before any Phase 1 line's own p-value was computed, which is what pooling uses. Treat as a weaker test than the table above.

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| 59 | Work and cycling lines are real in general | Factory, Laptop vs Hard Hat, Degree and Bicycle each pooled across Phase 1 cities (Stouffer) at p ≤ 0.05 after Holm across lines | all four, Z = 3.2–5.4 over 15–16 cities | ✗ The Factory Line Z = 1.2 over 10 cities; The Laptop vs Hard Hat Line Z = 1.3 over 10 cities; The Degree Line Z = 2.0 over 10 cities; The Bicycle Line Z = 1.7 over 10 cities (p = 0.827) |
| 60 | Housing lines are not lines anywhere | Flats vs Houses, Renters, Grey pooled Z ≤ 0 | Z = −2.3, −1.8, −1.8 | ◐ Flats vs Houses Z = -0.3; The Renters Line Z = -0.2; The Grey Line Z = 0.9 |

## Notes after scoring

- **Hypothesis 1** was about the benchmark's single-fit test, and stays failed as written (Chicago 10 of 100). The calibrated test that every verdict uses was benchmarked afterwards on 72 fresh Chicago maps with no line, run exactly as the verdicts are (close calls refit 200 times): 5 false alarms (6.9%, 95% interval 2.3–15.5%, p = 0.29 against 5%). The single-fit test called 3 of the same 72 maps (`experiments/calibrated_benchmark.py`).

## Deviations

- **US train commuting includes light rail** (recorded 16 Nov 2026, before any Phase 1 hypothesis was scored). The first US build counted subway and commuter rail only. Before any calibrated test was run, light rail and streetcar were added, to match the English definition ("underground, metro, light rail, tram"). Washington's first-pass p-values had been seen; Washington has almost no light rail. Most affected: Seattle and Los Angeles, whose main rail lines are light rail.
