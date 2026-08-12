#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from authorial_flow.release import build_release, verify_release, write_root_release_metadata


def main() -> int:
    p = argparse.ArgumentParser(description="Build and verify deterministic Authorial Flow release ZIP")
    p.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--out", type=Path)
    p.add_argument("--write-root-metadata", action="store_true")
    p.add_argument("--clean-zip-compile", action="store_true")
    args = p.parse_args()
    if args.out is None and not args.write_root_metadata:
        p.error("one of --out or --write-root-metadata is required")
    if args.out is None and args.clean_zip_compile:
        p.error("--clean-zip-compile requires --out")
    if args.write_root_metadata:
        root_manifest = write_root_release_metadata(args.repo)
        print("root_metadata=PASS")
        print(f"source_commit={root_manifest.source_commit_sha}")
        print(f"graph_version={root_manifest.graph_version}")
        print(f"policy_version={root_manifest.policy_version}")
    if args.out is None:
        return 0
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
