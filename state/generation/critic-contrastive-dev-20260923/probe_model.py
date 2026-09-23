#!/usr/bin/env python3
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).parents[1]/"specialized-audit-dev-20260923"/"run_antecedent_human_control.py"), run_name="__main__")
