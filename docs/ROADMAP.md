# Research and product roadmap

## The key pivot: from "best demographic map" to "surprising cultural fault lines"

The current prototype can generate visually coherent partitions. The missing ingredient is **independent, diverse, properly measured city signals**, followed by a discovery algorithm that rewards surprising, stable separations rather than ordinary east-west socioeconomic gradients.

### Priority 0: repair explanations and UI

Replace "Zone 1–7" with descriptive local names generated from feature contrasts and anchored to actual suburbs. Explain explicitly that zone number is a local partition identifier, not a ranking. Replace "Degrees vs money" (IEO-minus-IER index points) with "Education/occupation relative to economic resources". Use one simple landing screen: featured discoveries, a well-labelled map, and an obvious "Find another line" button. Put weights, rank signals, matching controls and advanced diagnostics behind an expandable Research view. Make a discovery card answer: Where? What divides? Why? How reliable? Can I name/share it?

### Priority 1: data that can support actual Latte and Red Rooster lines

Ingest and cache real venue coordinates with source, retrieval date, tag, chain confidence, deduplication and coverage uncertainty. For cafes, do **not** equate counts with "busy" without actual visit/transaction data. Normalize café density by commercial land use, businesses in the area, walkable catchment area, or estimated daytime population in addition to residential population. Compare Red Rooster/KFC/Oporto/El Jannah to matched control categories and to all restaurants, not to an arbitrary zero baseline.

### Priority 2: several different boundary engines

- **A / Signed-margin graph cut**: find a partition that separates two venue/signal distributions while penalizing shared-border complexity and tiny groups; use population balance and actual graph cut. A geographic SVM can produce a continuous latent separating score; **snapping to SA2/SA1 borders should be a separate, explicit optimization problem**, not simply tracing the contour.
- **B / Graph fused lasso or Potts model**: joint segmentation minimizing loss plus penalty for cutting graph edges; robust to local spikes, with a controllable simplicity parameter.
- **C / SKATER / AZP / max-p regionalization**: established, public baselines under population/connectivity constraints; compare solutions rather than claiming novelty for Ward clustering.
- **D / Persistent boundary tree**: recursive split discovery where each candidate edge gets a persistence score under spatial scales, resamples, POI tagging uncertainty and held-out features. **This is the leading research direction.**
- **E / Contrastive topic discovery**: learn sparse combinations of heterogeneous data with contrastive objectives and residualize urban density, CBD distance and mapping completeness; map only the stable, independent residual structure.
- **F / Multiplex boundary consensus**: construct independent trees for food, transit, housing, demographics and recreation; find shared/crossing borders. The misalignments may be the best stories.

### Priority 3: discovery worth a story

Search for out-of-sample, geographically robust, **distinct** split patterns, not simply the highest in-sample variance. Score an ensemble of interestingness dimensions separately: (i) separation/margin, (ii) geographic coherence, (iii) meaningful population balance, (iv) stability, (v) null-relative surprise, (vi) cross-data-family agreement or unexpectedly strong disagreement, (vii) descriptive simplicity, (viii) source confidence. Diversity should be explicit; otherwise the top 20 will be twenty ways to rediscover CBD distance.

### Priority 4: trustworthy evidence

Use split-sample feature discovery versus confirmation, spatially constrained permutations/surrogate maps, spatial block cross-validation, missingness/coverage stress tests, and multiple-comparison corrections. Report confidence in *boundary location*, not just a numeric quality score. A line should have a repeatability profile across SA1/SA2 masks, smoothing strengths, time snapshots and OSM coverage assumptions.

### Priority 5: user interaction

Let visitors click a **single** split in a hierarchical tree, view two clearly labelled sides (never unlabeled "Zone 1/2"), compare distributions, and suggest a catchy name. Offer an optional dynamic "Top 20", "weirdest exceptions", and "unexpected agreements" gallery. Keep naming distinct from statistical evidence; a fun story needs a caveat and provenance card.

### Priority 6: Tokyo translation

Start with the 23 wards and a core-region definition; treat the Greater Tokyo mega-region as a later, separately scoped experiment. Japan's e-Stat/jSTAT MAP offers small-area Census tables and spatial boundaries, and Tokyo's statistical bureau publishes 2020 chome-level reports. Japanese POI names, tag coverage and commercial land-use denominators require localization; there is no direct Japanese SEIFA equivalent. Recommended initial signals: train accessibility, household composition, housing tenure, small-area age structures, density, chain café/fast-food presence. Compare location boundaries before inferring human demographics.

Official sources: https://www.e-stat.go.jp/ and https://www.toukei.metro.tokyo.lg.jp/kokusei/2020/kd-20index.htm

## Publication positioning

A well-executed interactive atlas + transparent case studies fits a creative personal project, public-interest data journalism, urban analytics, or evidence-based policy engagement. A modest academic or applied conference paper is plausible **if there is a substantive methodological insight or unusually well-validated empirical finding**. Merely ranking attractive maps with tuned heuristics is not research novelty. Do not assume social or political policy implications from consumer-location associations.
