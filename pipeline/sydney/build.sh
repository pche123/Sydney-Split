#!/usr/bin/env bash
# Build the Sydney app data (app/data/sydney.json) from a working folder that holds the
# outputs of the analysis steps in the README (signals, line search, timeline, venues).
# Usage: pipeline/sydney/build.sh <working folder>      (raw downloads in $SPLIT_RAW, default ./data)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$HERE/../.." && pwd)"; WORK="${1:?usage: build.sh <working folder>}"
RAW="${SPLIT_RAW:-$ROOT/data}"
SHP="$RAW/shp/SA2_2021_AUST_GDA2020.shp"
GCP2="$RAW/gcp_sa2/2021 Census GCP Statistical Area 2 for NSW"
export SPLIT_RAW="$RAW"
run() { PYTHONPATH="$HERE:$ROOT/pipeline/common" python3 -P "$@"; }
cd "$WORK"
run "$HERE/export_app.py" "$SHP" app_data.json            # map shapes and lines
run "$HERE/add_split.py"                                   # street-level "split suburb" notes
run "$HERE/heritage2_export.py" "$GCP2" app_data.json     # birthplace, ancestry, religion
run "$HERE/timeline_export.py"                             # 2001-2021 lines and communities
run "$HERE/make_export.py"                                 # "Make your own": signals, graph, eigenvectors, chains
run "$ROOT/pipeline/common/apply_verdicts.py" app_data.json "$ROOT/results/verdicts.csv" Sydney   # audited verdicts
run "$HERE/sydney_extras.py"                               # zoom labels, shops inside the map
cp app_data.json "$ROOT/app/data/sydney.json"
echo "wrote app/data/sydney.json"
