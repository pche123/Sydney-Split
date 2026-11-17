#!/bin/bash
# Calibrated double-check for every food line with quick p < 0.2 (results/phase2/food/tests.csv), checkpointed.
cd "$(dirname "$0")/.."; F=results/phase2/food
for spec in paris:croissant,latte lyon:croissant marseille:latte madrid:starbucks barcelona:latte,paella rome:latte \
            toronto:timmies ottawa:latte calgary:latte hamburg:bread; do
  c=${spec%%:*}; l=${spec#*:}
  python3 experiments/calibrate_checkpoint.py $c $F/$c $l 40 $F/${c}_calibrated.json
done
