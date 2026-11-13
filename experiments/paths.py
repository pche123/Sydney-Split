"""Where the experiment scripts find the pipeline's working folders. Override with environment variables."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYD = os.environ.get("SPLIT_SYDNEY_WORK", str(ROOT / "build" / "sydney"))   # Sydney pipeline working folder
TOK = os.environ.get("SPLIT_TOKYO_WORK", str(ROOT / "build" / "tokyo"))     # Tokyo pipeline working folder
RAW = os.environ.get("SPLIT_RAW", str(ROOT / "data"))                        # raw downloads (shapefiles, licence list)
