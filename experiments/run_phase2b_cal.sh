#!/bin/bash
# Checkpointed calibrations for Spain and Italy lines with quick p < 0.2 (safe to re-run after a restart).
cd "$(dirname "$0")/.." && D=results/phase2/es_it
python3 -W ignore experiments/calibrate_checkpoint.py madrid $D/madrid the-degree-line 40 $D/madrid_calibrated.json
python3 -W ignore experiments/calibrate_checkpoint.py rome $D/rome the-living-alone-line,the-grey-line 40 $D/rome_calibrated.json
python3 -W ignore experiments/calibrate_checkpoint.py barcelona $D/barcelona the-living-alone-line,the-jobless-line,the-degree-line 40 $D/barcelona_calibrated.json
python3 -W ignore experiments/calibrate_checkpoint.py milan $D/milan the-jobless-line 40 $D/milan_calibrated.json
