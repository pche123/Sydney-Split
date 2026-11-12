#!/usr/bin/env bash
# Rebuild the Sydney / Split app data and page, in order. Expects the inputs described in README (ABS + OSM + liquor files).
set -e
SHP=data/shp/SA2_2021_AUST_GDA2020.shp
GCP2=data/gcp_sa2/2021\ Census\ GCP\ Statistical\ Area\ 2\ for\ NSW
python3 -I export_app.py "$SHP" app_data.json          # map shapes, lines, grey areas
python3 -I add_split.py                                 # street-level "split suburb" notes
python3 -I heritage2_export.py "$GCP2" app_data.json   # birthplace, ancestry, religion
python3 -I timeline_export.py                           # 2001-2021 lines and communities
python3 -I make_export.py                               # live features: signals, graph, basis, chains
python3 -I sydney_extras.py                            # zoom labels, shops inside the map, hi-vis note
python3 -c "t=open('app_template.html').read(); open('sydney_split_app.html','w').write(t.replace('__DATA__', open('app_data.json').read()))"
echo "built sydney_split_app.html"
