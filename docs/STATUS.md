# Release status and reproducibility checklist

**Snapshot:** 2026-11-11, Sydney / Split nested Discovery prototype.

- Data: 301 selected SA2, 650 actual >=170m boundary edges, 11 preloaded official/derived signals.
- Method: rank-transformed signed 2–8-signal recipes; two-way heuristic screening; contiguity-constrained Ward-style agglomerative grouping; cached nested cuts K=2–7; leaderboard with NMI filtering.
- Included HTML is an exact rebuild from `src/` at time of packaging.
- Browser click-tests previously covered topology nesting, 2–7 territories and name/POI import interaction in local Chromium. No production browser security or accessibility audit completed.
- **Unmet:** preloaded, independently audited OSM POI points; café "busyness" measurement; multiple algorithms; spatial null testing; public-readable labels; official service deployment; complete connected geographic study mask; temporal matching.
- **Historical two-region leaderboard CSV in `examples/` is older and NOT current K=4 ranking**. It is retained for traceability only, and is non-inferential.
- Source ABS ZIP and XLSX files are not duplicated in this GitHub repository. Required data lineage and regenerated derived artifacts are included.
