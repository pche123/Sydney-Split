# linetests

Calibrated tests for "is this line real?" on any city's area map.

| Question | Finished map (census shares) | Map built from records (venues, licences, stores) |
|---|---|---|
| Is there any geography? | always yes for census maps | re-draw records from flat surfaces |
| Is it a line? | `calibrated_map_test(null, f)` | `landscape_calibrated(null, T, line)` |
| Is it a cliff, not a slope? | `calibrated_edge_map(null, f)` | `calibrated_edge_data(null, line)` |

`null = MultiScaleNull(polygons, I, J, W)` models the map as smooth random landscapes at seven scales (0.7–50 km), averaged over each real area and fitted by maximum likelihood. Every p-value is calibrated with a double bootstrap. `LineTest` in `msr.py` is the original Moran spectral randomisation test, kept only for comparison: it is miscalibrated on smooth maps (see `FINDINGS.md`).
