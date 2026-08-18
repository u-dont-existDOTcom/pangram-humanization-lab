from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Callable

from .corpus_acquire import acquire_inventory
from .joel_register_corpus import build_register_corpus


class PacedInventoryAcquirer:
    """Serialize public-source fetches across inventory batches.

    ``build_register_corpus`` groups requests by inventory. Blogger throttling is
    global rather than inventory-local, so the pacing counter must remain shared
    across every inventory call in one corpus-freeze run.
    """

    def __init__(
        self,
        *,
        spacing_seconds: float,
        base_acquire_fn: Callable = acquire_inventory,
        sleep_fn: Callable[[float], None] = time.sleep,
    ):
        if spacing_seconds < 0:
            raise ValueError("spacing_seconds must be non-negative")
        self.spacing_seconds = float(spacing_seconds)
        self.base_acquire_fn = base_acquire_fn
        self.sleep_fn = sleep_fn
        self.request_count = 0
        self.sleep_count = 0

    def __call__(
        self,
        inventory_path: Path,
        *,
        out_dir: Path,
        manifest_out: Path,
        sample_ids: set[str],
        timeout: int = 30,
    ) -> dict:
        results: list[dict] = []
        errors: list[dict] = []
        per_sample_receipts: list[dict] = []

        for sample_id in sorted(str(value) for value in sample_ids):
            if self.request_count:
                self.sleep_fn(self.spacing_seconds)
                self.sleep_count += 1
            self.request_count += 1

            sample_out = out_dir / sample_id
            sample_manifest = (
                manifest_out.parent
                / f"{manifest_out.stem}-{sample_id}{manifest_out.suffix}"
            )
            runtime = self.base_acquire_fn(
                inventory_path,
                out_dir=sample_out,
                manifest_out=sample_manifest,
                sample_ids={sample_id},
                timeout=timeout,
            )
            results.extend(runtime.get("results", []))
            errors.extend(runtime.get("errors", []))
            per_sample_receipts.append(
                {
                    "sample_id": sample_id,
                    "result_count": len(runtime.get("results", [])),
                    "error_count": len(runtime.get("errors", [])),
                }
            )

        aggregate = {
            "inventory": str(inventory_path),
            "raw_text_committed": False,
            "network_strategy": "one-sample-at-a-time-global-spacing",
            "spacing_seconds": self.spacing_seconds,
            "results": results,
            "errors": errors,
            "per_sample_receipts": per_sample_receipts,
        }
        manifest_out.parent.mkdir(parents=True, exist_ok=True)
        manifest_out.write_text(
            json.dumps(aggregate, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        return aggregate

    def metadata(self) -> dict:
        return {
            "strategy": "one-sample-at-a-time-global-spacing",
            "spacing_seconds": self.spacing_seconds,
            "request_count": self.request_count,
            "sleep_count": self.sleep_count,
        }


def build_network_register_corpus(
    spec_path: Path,
    *,
    out_dir: Path,
    receipt_out: Path,
    timeout: int = 30,
    base_acquire_fn: Callable = acquire_inventory,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> dict:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    spacing_seconds = float(spec.get("network_request_spacing_seconds", 0))
    acquirer = PacedInventoryAcquirer(
        spacing_seconds=spacing_seconds,
        base_acquire_fn=base_acquire_fn,
        sleep_fn=sleep_fn,
    )
    result = build_register_corpus(
        spec_path,
        out_dir=out_dir,
        receipt_out=receipt_out,
        timeout=timeout,
        acquire_fn=acquirer,
    )
    result["source_acquisition"] = acquirer.metadata()
    receipt_out.parent.mkdir(parents=True, exist_ok=True)
    receipt_out.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m pangram_lab.joel_register_corpus_network"
    )
    parser.add_argument(
        "spec",
        nargs="?",
        default="state/IDIOLECT-JOEL-REGISTER-CORPUS-SPEC-2026-08-18.json",
    )
    parser.add_argument(
        "--out-dir",
        default=".local/idiolect-corpus/joel-register-corpus-text",
    )
    parser.add_argument(
        "--receipt-out",
        default=".local/idiolect-corpus/joel-register-corpus-receipt.json",
    )
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args(argv)

    try:
        result = build_network_register_corpus(
            Path(args.spec),
            out_dir=Path(args.out_dir),
            receipt_out=Path(args.receipt_out),
            timeout=args.timeout,
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not result.get("errors") else 1


if __name__ == "__main__":
    raise SystemExit(main())
