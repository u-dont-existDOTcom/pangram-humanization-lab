#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from pangram_lab.cache import PangramCache
from pangram_lab.fixed_batch import load_spec, run_batch
from pangram_lab.git_sync import GitSync
from pangram_lab.pangram4 import PangramClient


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an exact fixed Pangram-4 batch")
    parser.add_argument("spec", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-variants", type=int, default=8)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    key = os.environ.get("PANGRAM_API_KEY", "").strip()
    if not key:
        raise SystemExit("PANGRAM_API_KEY is not set")

    spec = load_spec(args.spec, max_variants=args.max_variants)
    git = GitSync(root, require_remote=True)
    client = PangramClient(key, sync=git.sync)
    client.probe_auth()
    result = run_batch(
        spec,
        client=client,
        cache=PangramCache(root / "cache"),
        output_path=args.out,
    )
    git.sync(f"fixed batch {spec['experiment_id']} complete")
    print(json.dumps({
        "experiment_id": result["experiment_id"],
        "result_count": len(result["results"]),
        "output": str(args.out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
