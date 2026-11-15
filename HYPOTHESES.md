# Hypotheses, tested phase by phase

Each phase ends with written predictions; the next phase's cities test them. These were committed before any Phase 1 data was opened, so the commit date shows they were not fitted to the results. Settings stay fixed between phases (null scales, number of draws, correction groups, family clustering); any change is reported as a deviation.

**Phases.** Phase 0: the 18 cities (Australia, Japan, England). Phase 1, held out: New York (by borough), Los Angeles, Chicago, San Francisco–Oakland, Washington, Austin, Seattle, Miami, Auckland, Christchurch, Singapore.

**Reading the table.** ✓ held, ✗ failed, ◐ partly held, – not testable with this phase's data. The p-value is the test behind the verdict where one exists; otherwise the observed figure is given. **Bold** numbers mark the core claims of the paper.

## A. Does the test hold up?

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| **1** | Our test keeps false alarms low on new city shapes | false alarms < 8% on smooth maps with no line | 4% (Kyoto, Melbourne) | |
| **2** | Moran spectral randomisation keeps failing | > 25% false alarms, all three forms | 32–56% | |
| **3** | Gradients fool the standard method most | MSR > 70% on gradients; ours < 5% | 79–95% vs 0–1% | |
| 4 | Uneven smoothness is our weak spot, but a mild one | ours 5–15% when smoothness varies | 5% / 11% | |
| 5 | More areas, fewer false alarms | false-alarm rate falls with number of areas | – | |
| 6 | Shuffling areas is useless everywhere | > 95% false alarms in every city | 98–100% | |

## B. Which statistic works?

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| 7 | Global Geary's C and Moran's I never detect a line | < 10% detection at a 3 SD step | 0–4% | |
| 8 | Counting the border is never the worst statistic | border count ≥ edge test on rough backgrounds | 26/46% vs 13/22% | |
| 9 | The edge test wins in calm, spread-out cities | edge > border count on smooth backgrounds in large low-density cities | Melbourne 48% vs 28% | |
| 10 | Ranking hides jumps | ranking first cuts jump-test power by more than half | near-zero power when ranked | |

## C. Which lines are real?

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| **11** | Few lines pass | < 10% of tested lines pass after correction | 14 of 358 (4%) | |
| 12 | Work lines recur | Factory or Hi-Vis passes in ≥ 2 new cities | 4 passes in 3 cities | |
| 13 | The Bicycle Line passes where cycling is concentrated | passes in ≥ 1 of Seattle, San Francisco, Christchurch | Adelaide, Brighton, Kyoto | |
| 14 | Age and household lines almost never pass | Grey, Living Alone, Renters pass in ≤ 1 new city | 0 passes | |
| 15 | Food and night lines rarely pass | venue lines pass in ≤ 2 new cities | 5 passes in 3 cities | |
| 16 | US cities produce more real lines than Japanese ones | passes per US city > passes per Japanese city | Japan: 5 in 8 cities | |
| 17 | New York boroughs act like separate cities | within-borough lines pass more often than city-wide lines | – | |
| 18 | Singapore has the fewest real lines | 0 passes in Singapore | – | |

## D. Sharp or gradual?

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| **19** | Slopes, not cliffs | ≥ 90% of lines have no sharp stretch | 253 of 259 (98%) | |
| 20 | Sharp stretches are short | each covers < 15% of its line | 5–10% | |
| 21 | Sharp stretches sit on physical barriers | most fall on a freeway, rail line, river or park edge | not yet checked | |
| 22 | US cities have more sharp stretches | share of lines with one: US > Australia and Japan | Australia 1 of 57 lines, Japan 2 of 119, England 3 of 83 | |

## E. Line families

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| 23 | The same four families appear | ≥ 60% of lines land in the matching family | 4 families over 16 cities | |
| 24 | Latte sits between families | Latte not assigned to one family | between work/class and night out | |
| **25** | Families are slopes, not walls | shared-border test passes ≤ 10% of families | 2 of 48 (4%) | |
| 26 | The age family is the most independent | lowest route match with other families | not yet checked | |
| 27 | Inner city is the tightest family | highest within-family route match | not yet checked | |

## F. Change over time (US 5-year surveys; New Zealand 2013, 2018, 2023)

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| 28 | Work lines barely move | ≥ 80% of areas keep their side over 10 years | 83–99% | |
| 29 | Age moves fastest everywhere | Grey Line least stable in every city | yes, in every city with a timeline | |
| 30 | Age reshuffles to chance only in Japan | Grey Line stays above chance outside Japan | Japan 52–64%; Australia 77–83% | |
| 31 | Fast-growing cities move most | Austin, Seattle shift more than Chicago, New York | – | |
| 32 | Inner-city lines move outward | flats/renters side grows at the line's edge | – | |

## G. Chain wars

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| **33** | Same-type chains are more mixed than chance | burger and supermarket pairs mixed (p ≤ 0.05) in ≥ half the US cities | Maccas vs Hungry Jack's 4/4 AU; McDonald's vs KFC 3/4 UK | |
| 34 | Premium vs budget chains show a real line | e.g. Whole Foods vs Walmart passes in ≥ 2 US cities | Waitrose vs Lidl & Aldi, Greggs vs Pret pass in London | |
| 35 | Neutral pairs stay neutral | CVS vs Walgreens, Starbucks vs Dunkin' neither split nor mixed | konbini mostly neutral | |
| 36 | Mixing comes from each chain spacing out its own shops | own-shop spacing wider than random where a pair is mixed | not yet checked | |
| 37 | Premium chains follow the work and class family | a passing premium line matches Degree or Laptop on ≥ 70% of areas | – | |

## H. City rules

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| 38 | Rules beat correlation more often than chance | > 8% pass in each new city | 12% overall (4–18%) | |
| 39 | Bigger cities produce more passing rules | pass rate rises with number of areas | 4% Adelaide to 18% Manchester | |
| **40** | Rules travel badly | AU or UK consistent rules pass in < 35% of US tests | 13–32% between countries | |
| 41 | US rules transfer best to Australia | US→AU rate > US→JP rate | – | |
| 42 | New Zealand behaves like Australia | AU rules pass in > 50% of NZ tests | – | |
| 43 | Japan stays the odd one out | foreign rules pass in Japan least often | 13–32% into Japan | |
| 44 | The walking rule recurs | "few over-65s + few houses ⇒ more walking" holds in ≥ half the US cities | 3 of 3 testable AU cities | |

## I. Sister cities

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| 45 | Pairs come from size, not country | fingerprint distance correlates with size difference | – | |
| 46 | Sapporo–Brighton gets company | a new city within 0.25 of either | 0.19 apart | |
| 47 | Auckland's nearest sister is Australian | nearest is Brisbane or Perth | – | |
| 48 | US cities cluster together | US cities' nearest sister is usually another US city | – | |

## J. Scale and areas

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| 49 | Results don't hinge on area size | merging tracts changes < 20% of verdicts | Brighton fingerprint unchanged | |
| 50 | Real lines survive merging | passing lines stay real or gentle, never chance | – | |
| 51 | More areas mean more power, not more false passes | pass rate rises with areas; false alarms don't | – | |

## K. Questions only the new cities can answer

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| 52 | The Income Line joins the work family | clusters with work and class | no income data | |
| 53 | The Car Line is the strongest US line | no-car line passes in New York, San Francisco, Washington | – | |
| 54 | Commute time adds its own divide | long-commute line not in the car family | – | |
| 55 | Remote work joins the inner-city family | work-from-home follows Degree, not Train | – | |
| 56 | Singapore's planned estates are invisible | no line follows estate boundaries beyond chance | – | |

## L. Process

| # | Hypothesis | Holds if | Phase 0 | Phase 1 |
|---|---|---|---|---|
| 57 | Nothing is retuned | no setting changed for Phase 1 | – | |
| 58 | Most hypotheses won't survive untouched | at least a third fail or partly hold | – | |
