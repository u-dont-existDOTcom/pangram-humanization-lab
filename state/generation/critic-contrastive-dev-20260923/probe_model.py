#!/usr/bin/env python3
# Railway/Railpack retained this historical entrypoint in the deployment snapshot.
# Delegate to the frozen contrastive quick-eight runner.
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("run_quick8.py")), run_name="__main__")
