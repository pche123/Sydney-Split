# Line tests

Tests for "is this line real?" that work for any city. All you need is a set of area polygons and either a map (one number per area) or the records behind it.

| File | What it gives you |
|---|---|
| `landscape.py` | `MultiScaleNull`: the random-landscape null (the default). `step_test`: the edge test. `calibrated_map_test` and `calibrated_edge_map`: the same tests with double-bootstrap calibration. |
| `records.py` | Tests that simulate the records (venues, licences, listings, stores) rather than the map: `Line`, `landscape_calibrated`, `calibrated_edge_data`. |
| `msr.py` | The original Moran spectral randomisation test. Kept for comparison only: it is not calibrated (see `FINDINGS.md`). |

## Three questions, three tests

1. **Is there any geography at all?** Shuffle the records between places (`p_perm`). Almost every map passes this.
2. **Is the line cleaner than a random landscape that is just as smooth?** Use `calibrated_map_test` for census maps and `landscape_calibrated` for record-based maps. This is the line test.
3. **Is there an edge on top of the landscape (a cliff rather than a slope)?** Use `calibrated_edge_map` or `calibrated_edge_data`.

## A new city

```python
from landscape import MultiScaleNull, calibrated_map_test, calibrated_edge_map
null = MultiScaleNull(polygons, I, J, W)   # areas, touching pairs, shared border length (m)
calibrated_map_test(null, f)               # f = rank-normal map; returns p_raw, p_cal, size, ...
calibrated_edge_map(null, f)
```

For record-based lines, write a `Line(name, records, estimate, simulate, recipe)`. The recipe should be the same formula the app uses to turn records into a map. `pipeline/experiments/audit/lines_*.py` has worked examples: two-type venue shares, per-resident licences, machines per venue, mean listing price, and chain-vs-chain distance.
