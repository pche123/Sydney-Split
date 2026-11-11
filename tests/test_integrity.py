"""Basic offline smoke and provenance tests; no invented restaurant observations."""
from pathlib import Path
import json,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
d=json.loads((ROOT/'src/atlas-data.json').read_text());regions=d['regions'];edges=d['edges'];n=len(regions)
assert n==301,(n,'Unexpected study mask')
assert len(edges)==650,len(edges)
assert len({r['id'] for r in regions})==n
assert all(0<=e['a']<n and 0<=e['b']<n and e['a']!=e['b'] and e['len']>0 for e in edges)
assert all(len(r['signals'])>=11 and r['polys'] and r['path'] for r in regions)
assert all(not k.startswith('osm_') for r in regions for k in r['signals']), 'OSM never bundled unless verified'
assert len(d['signals'])==11
assert 'const ATLAS=' in (ROOT/'index.html').read_text()
print('PASS:',n,'SA2 areas,',len(edges),'real borders,',len(d['signals']),'ABS/derived features; no bundled OSM')