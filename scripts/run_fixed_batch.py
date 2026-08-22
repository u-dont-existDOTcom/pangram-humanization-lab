#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from pangram_lab.cache import PangramCache
from pangram_lab.call_budget import PangramCallLedger
from pangram_lab.fixed_batch import load_spec, run_batch
from pangram_lab.git_sync import GitSync
from pangram_lab.pangram4 import PangramClient
from pangram_lab.result_paths import (
    load_compatible_existing_result,
    resolve_result_path,
    result_is_complete,
)
from pangram_lab.review_registration import register_result
from pangram_lab.text_sources import resolve_text_sources
from pangram_lab.tracked_pangram import TrackedPangramClient


def current_commit(root: Path) -> str:
    cp = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    )
    return cp.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an exact fixed Pangram-4 batch")
    parser.add_argument("spec", type=Path)
    parser.add_argument(
        "--out",
        type=Path,
        help="compatibility-only; when supplied it must equal state/experiments/<experiment_id>-results.json",
    )
    parser.add_argument("--max-variants", type=int, default=8)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    registered_spec = load_spec(args.spec, max_variants=args.max_variants)
    # Resolve only immutable, hash-bound sources. result_paths.spec_sha256 strips
    # the derived runtime text when text_source is present, so experiment
    # identity remains exactly the registered source metadata.
    spec = resolve_text_sources(registered_spec)
    output_path = resolve_result_path(root, spec, args.out)
    existing = load_compatible_existing_result(spec, output_path)
    if existing is not None and result_is_complete(spec, existing):
        print(
            json.dumps(
                {
                    "experiment_id": existing["experiment_id"],
                    "result_count": len(existing.get("results", [])),
                    "output": str(output_path.relative_to(root)),
                    "reused_result": True,
                    "spec_sha256": existing.get("spec_sha256"),
                },
                indent=2,
            )
        )
        return 0

    key = os.environ.get("PANGRAM_API_KEY", "").strip()
    if not key:
        raise SystemExit("PANGRAM_API_KEY is not set")

    git = GitSync(root, require_remote=True)
    call_ledger = PangramCallLedger(root, spec["audit_id"]) if spec.get("audit_id") else None
    if call_ledger is None:
        client = PangramClient(key, sync=git.sync)
    else:
        client = TrackedPangramClient(key, sync=git.sync, call_ledger=call_ledger)
    client.probe_auth()
    result = run_batch(
        spec,
        client=client,
        cache=PangramCache(root / "cache"),
        output_path=output_path,
        call_ledger=call_ledger,
    )

    # Commit and push the exact result bytes before registering review metadata.
    # The inbox therefore points to an immutable commit, not a moving branch name.
    git.sync(f"fixed batch {spec['experiment_id']} result")
    result_ref = current_commit(root)
    review_entry = register_result(root, output_path, result_ref, result)
    git.sync(f"lesson review {spec['experiment_id']}")

    report = {
        "experiment_id": result["experiment_id"],
        "result_count": len(result["results"]),
        "output": str(output_path.relative_to(root)),
        "result_ref": result_ref,
        "lesson_review_id": review_entry["id"],
        "reused_result": False,
        "spec_sha256": result.get("spec_sha256"),
    }
    if result.get("call_accounting") is not None:
        report["call_accounting"] = result["call_accounting"]
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
