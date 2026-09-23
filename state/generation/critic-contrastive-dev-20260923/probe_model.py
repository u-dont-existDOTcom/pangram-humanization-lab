#!/usr/bin/env python3
# Railway/Railpack retains this historical entrypoint in deployment snapshots.
# Delegate to the frozen contrastive v2 development runner.
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("run_dev12_v2.py")), run_name="__main__")
