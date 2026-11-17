#!/bin/bash
# Firm up the close calls: every food line with calibrated p (R=40) below 0.1 gets R = 200 refits.
cd "$(dirname "$0")/.."; F=results/phase2/food
for spec in "$@"; do c=${spec%%:*}; l=${spec#*:}
  R_FINE=200 python3 experiments/calibrate_checkpoint.py $c $F/$c $l 200 $F/${c}_calibrated.json
done
