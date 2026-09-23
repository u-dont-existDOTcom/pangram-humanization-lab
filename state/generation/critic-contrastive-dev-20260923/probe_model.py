#!/usr/bin/env python3
# Railway/Railpack may retain this historical entrypoint.
# Delegate to the frozen specialized-audit runner.
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).parents[1]/"specialized-audit-dev-20260923"/"run_specialized_audit.py"), run_name="__main__")
