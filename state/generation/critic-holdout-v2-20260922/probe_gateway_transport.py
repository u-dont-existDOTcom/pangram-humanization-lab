#!/usr/bin/env python3
# Railway/Railpack retained this historical entrypoint in deployment snapshots.
# Delegate to the frozen holdout runner without changing benchmark bytes or rubric.
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("run_holdout_v2.py")), run_name="__main__")
