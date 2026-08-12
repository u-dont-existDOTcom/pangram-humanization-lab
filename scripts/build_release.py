#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from authorial_flow.release import build_release, verify_release


def main() -> int:
    p = argparse.ArgumentParser(description="Build and verify deterministic Authorial Flow release ZIP")
    p.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--clean-zip-compile", action="store_true")
    args = p.parse_args()
    manifest = build_release(args.repo, args.out)
    report = verify_release(args.out, run_install=args.clean_zip_compile)
    print(f"release={args.out}")
    print(f"source_commit={manifest.source_commit_sha}")
    print(f"graph_version={manifest.graph_version}")
    print(f"policy_version={manifest.policy_version}")
    print(f"project_instructions_chars={report.project_instructions_chars}")
    if not report.pass_:
        for error in report.errors:
            print("ERROR:", error, file=sys.stderr)
        return 2
    print("verification=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
