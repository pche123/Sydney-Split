#!/bin/bash
# Checkpointed calibrations for the German lines with quick p < 0.2 (safe to re-run after a restart).
cd "$(dirname "$0")/.." && D=results/phase2/germany
python3 -W ignore experiments/calibrate_checkpoint.py berlin $D/berlin the-renters-line,the-living-alone-line,flats-vs-houses,money 40 $D/berlin_calibrated.json
python3 -W ignore experiments/calibrate_checkpoint.py munich $D/munich the-living-alone-line,the-renters-line,the-grey-line 40 $D/munich_calibrated.json
