#!/usr/bin/env bash
# Build the Tokyo app data (app/data/tokyo.json) from a working folder holding out/ (from
# build_tokyo.py and tokyo_timeline.py), the HotPepper listings and tplaces.pkl.
# Usage: pipeline/tokyo/build.sh <working folder> <hotpepper_tokyo.csv>
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$HERE/../.." && pwd)"
WORK="${1:?usage: build.sh <working folder> <hotpepper csv>}"; HP="${2:?hotpepper csv}"
run() { PYTHONPATH="$HERE:$ROOT/pipeline/common" python3 -P "$@"; }
cd "$WORK"
run "$HERE/tokyo_app_export.py" out "$HP" tplaces.pkl app_data_tokyo.json
run "$ROOT/pipeline/common/apply_verdicts.py" app_data_tokyo.json "$ROOT/results/verdicts.csv" Tokyo
cp app_data_tokyo.json "$ROOT/app/data/tokyo.json"
echo "wrote app/data/tokyo.json"
