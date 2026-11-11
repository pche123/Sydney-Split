# Current methods: auditable description

This page describes **what the current JavaScript implements**, not what future releases may do.

## 1. Geographic objects

Each of 301 selected SA2s is a node. A spatial edge joins two nodes only when the corresponding real polygons share >=170 m of boundary within the cropped map. The app retains 650 such edges. The exact study mask has four graph components (295, 4, 1, 1). To run one hierarchy, three nearest-centroid *virtual connections* join smaller components to the largest, without appearing as physical borders. This is a known connectivity limitation.

## 2. Feature transformations

An index or derived signal is transformed into a centered rank representation in approximately [-1,1]. Every input observation is weighted by its *rank*, not raw units; ties share a midrank. A signed user recipe with K=2–8 selected signals is combined as

`z_i = sum_j w_j * rank_j(i) / sum_j |w_j|`.

Two rounds of adjacency smoothing then update each area's value with its border-length-weighted neighbours (alpha=0.32). This favours spatially coherent areas at the cost of possibly smoothing away genuine local exceptions.

## 3. Discovery screening

A seeded pseudorandom generator samples signed combinations (weights approximately 0.5–1.5) from selected signals. The script attempts roughly 900–2650 trials and deduplicates repeated signed subsets. It is **not an exhaustive combinatorial search**.

The prefilter forms two sides by a median threshold on the smoothed composite, examines connected components and measures dominant coverage, main-border share, average border jump, balance and total border simplicity. Its illustrative score is

`100*(0.29*coverage + 0.20*mainShare + 0.22*clamp(jump/0.25,0,1) + 0.16*balance + 0.13*simplicity)`

with mild penalties for redundant signal bundles and bundle length. This is a design-chosen heuristic, not an optimized statistical likelihood or significance test. Screening requires a few real shared-border segments, a minimum border length and dominant component coverage >=0.69; it may exclude small but genuinely interesting local lines.

## 4. Geographic hierarchy

A shortlist containing up to 190 top-screening and 150 additional sampled candidates is subjected to **greedy, spatially constrained Ward-style agglomerative regionalization**. Feature vectors emphasize the smoothed composite (factor 1.8) and include smaller signed per-signal contributions (factor 0.65 normalized by absolute sum). The node weights depend on clipped square roots of resident population, not directly on raw population.

For two adjacent groups A, B with feature means mu_A, mu_B and weights m_A, m_B, the base Ward increase is

`D(A,B) = (m_A*m_B/(m_A+m_B)) * ||mu_A - mu_B||^2`.

The implementation applies small shared-border-length incentives and virtual-link penalties when choosing the next greedy merge. It remembers snapshots at 7,6,5,4,3,2 territories from the **same** merge tree. Thus increasing K refines a previously larger territory; it is not rerunning independent models at each K. Ward's greedy hierarchy does **not** globally optimize a perimeter-regularized multiway cut.

## 5. Ranking and diversification

For a chosen K, the app reports a candidate score approximately

`100*(0.34*explainedVariance + 0.25*borderContrast + 0.22*populationEntropy + 0.12*boundarySimplicity + 0.07*minimumShareGuard)`.

Constants are hand selected and context dependent. Partition similarity is tested via normalized mutual information of region membership and a heuristic maximum-similarity threshold. Very similar recipe results are filtered, and counts are balanced across recipe sizes. It is a ranked **gallery**, not a discovery claim with calibrated uncertainty.

## 6. What the names mean

The current app often proposes a name by joining two signal labels with the multiplication sign, e.g. "Degrees vs money x Disadvantage pockets territories." These are *recipe summaries*, not interpretations and definitely not heritage names like the "Red Rooster Line". Users can save a chosen name and recipe in browser localStorage. For K>2 the map has K territories and multiple boundaries, so an entire candidate should not casually be called a single named 'line'. The public interface should instead identify which branch/split is being named and provide an ordinary-language statement of what is higher on each side.

## 7. Venue points

The browser can query public Overpass endpoints or import raw Overpass JSON. POI categories are recognized from OSM tags and name matches, assigned to polygons using approximated point-in-polygon checks, normalized by resident population and supplemented with neighbour smoothing. No venue dataset is preloaded. Brands and amenity categories may be misclassified, incomplete or biased by urban density and mapping effort.

## 8. Verification scope

The project includes offline integrity checks that assert number of real SA2 polygons/edges, nonempty geographic paths, and absence of fabricated OSM signal keys. Existing browser interaction checks were performed on the prototype, but their locally fabricated **test fixture** was used only in testing the import control and is **not** a scientific dataset. The release does not claim externally validated line discoveries.