#!/usr/bin/env python3
# Railway/Railpack may retain this historical entrypoint in deployment snapshots.
# Delegate to the frozen pairwise realization-defect runner.
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("run_pairwise8.py")), run_name="__main__")
