"""Calibrated tests for informal lines on area maps.

Three questions, three tests (see README.md):
  1. any geography?   records re-drawn from a flat world (records.Line + flat surfaces)
  2. is it a line?    calibrated_map_test (a finished map) / landscape_calibrated (records)
  3. is it a cliff?   calibrated_edge_map (a finished map) / calibrated_edge_data (records)
"""
from .landscape import MultiScaleNull, calibrated_map_test, calibrated_edge_map, step_test
from .records import Line, two_type_line, logit_surface, lograte_surface, landscape_calibrated, calibrated_edge_data, dmsr_test
from .msr import LineTest

__all__ = ["MultiScaleNull", "calibrated_map_test", "calibrated_edge_map", "step_test", "Line", "two_type_line",
           "logit_surface", "lograte_surface", "landscape_calibrated", "calibrated_edge_data", "dmsr_test", "LineTest"]
