"""Cloud entrypoint: same app, with local review-storage fallback disabled."""

import os
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["PRODUCTLENS_DEPLOYMENT"] = "cloud"
runpy.run_path(str(ROOT / "app.py"), run_name="__main__")
