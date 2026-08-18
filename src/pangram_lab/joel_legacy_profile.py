from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .corpus_acquire import acquire_inventory, canonicalize


def _split_rule(rule: str) -> tuple[str, str | None]:
    if ":" not in rule:
        return rule, None
    kind, value = rule.split(":", 1)
    return kind, value


def _line_label_pattern(label: str) -> re.Pattern:
    return re.compile(rf"(?im)^\s*{re.escape(label)}\s*:\s*(.*)$")


def apply_cleanup_rule(text: str, rule: str) -> str:
    kind, value = _split_rule(rule)
    if kind in {"whole-after-existing-blockquote-drop", "whole-message-by-you-extraction"}:
        return text.strip()

    if kind == "after-first-label" and value:
        match = _line_label_pattern(value).search(text)
        if not match:
            raise ValueError(f"cleanup marker not found: {value}")
        remainder = match.group(1).strip()
        suffix = text[match.end():].lstrip("\n")
        pieces = [part for part in (remainder, suffix) if part]
        if not pieces:
            raise ValueError(f"cleanup marker found but no retained text after: {value}")
        return "\n".join(pieces).strip()

    if kind == "before-first-label" and value:
        match = _line_label_pattern(value).search(text)
        if not match:
            raise ValueError(f"cleanup marker not found: {value}")
        prefix = text[:match.start()].rstrip()
        if not prefix:
            raise ValueError(f"cleanup marker found but no retained text before: {value}")
        return prefix

    raise ValueError(f"unsupported cleanup rule: {rule}")


def build_legacy_profile(
    spec_path: Path,
    *,
    out_dir: Path,
    receipt_out: Path,
    timeout: int = 30,
) -> dict:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    include = spec.get("include", [])
    ids = {row["sample_id"] for row in include}
    inventory = Path(spec["source_inventory"])

    raw_out = out_dir.parent / "joel-legacy-source-text"
    source_manifest = out_dir.parent / "joel-legacy-source-manifest.json"
    runtime = acquire_inventory(
        inventory,
        out_dir=raw_out,
        manifest_out=source_manifest,
        sample_ids=ids,
        timeout=timeout,
    )
    if runtime.get("errors"):
        return {
            "schema_version": 1,
            "raw_or_canonical_prose_in_output": False,
            "errors": runtime["errors"],
            "samples": [],
        }

    by_id = {row["sample_id"]: row for row in runtime.get("results", [])}
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    errors: list[dict] = []
    for spec_row in include:
        sample_id = spec_row["sample_id"]
        source = by_id.get(sample_id)
        if not source:
            errors.append({"sample_id": sample_id, "error": "source-not-acquired"})
            continue
        try:
            source_text = Path(source["local_text_path"]).read_text(encoding="utf-8")
            cleaned = apply_cleanup_rule(source_text, spec_row["cleanup_rule"])
            canon = canonicalize(cleaned)
            if canon.word_count <= 0:
                raise ValueError("cleanup-produced-zero-words")
            local_path = out_dir / f"{sample_id}.txt"
            local_path.write_text(canon.text + "\n", encoding="utf-8")
            rows.append(
                {
                    "sample_id": sample_id,
                    "source_group": source.get("source_group"),
                    "site_group": source.get("site_group"),
                    "cleanup_rule": spec_row["cleanup_rule"],
                    "source_canonical_sha256": source.get("canonical_sha256"),
                    "profile_canonical_sha256": canon.sha256,
                    "source_word_count": int(source.get("word_count", 0)),
                    "profile_word_count": canon.word_count,
                    "words_removed_by_profile_cleanup": max(
                        0, int(source.get("word_count", 0)) - canon.word_count
                    ),
                    "quality_flags_after_cleanup": canon.quality_flags,
                    "local_text_path": str(local_path),
                }
            )
        except Exception as exc:
            errors.append({"sample_id": sample_id, "error": str(exc)})

    if errors:
        return {
            "schema_version": 1,
            "raw_or_canonical_prose_in_output": False,
            "errors": errors,
            "samples": rows,
        }

    total_words = sum(row["profile_word_count"] for row in rows)
    largest = max((row["profile_word_count"] for row in rows), default=0)
    receipt = {
        "schema_version": 1,
        "raw_or_canonical_prose_in_output": False,
        "profile_status": spec.get("profile_status"),
        "independent_source_count": len(rows),
        "total_words": total_words,
        "largest_source_words": largest,
        "largest_source_fraction": round(largest / total_words, 6) if total_words else None,
        "errors": [],
        "samples": sorted(rows, key=lambda row: row["sample_id"]),
        "excluded_for_first_profile": spec.get("exclude_for_first_profile", []),
    }
    receipt_out.parent.mkdir(parents=True, exist_ok=True)
    receipt_out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="python -m pangram_lab.joel_legacy_profile")
    parser.add_argument(
        "spec",
        nargs="?",
        default="state/IDIOLECT-JOEL-LEGACY-PROFILE-SPEC-2026-08-18.json",
    )
    parser.add_argument("--out-dir", default=".local/idiolect-corpus/joel-legacy-profile-text")
    parser.add_argument("--receipt-out", default=".local/idiolect-corpus/joel-legacy-profile-receipt.json")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args(argv)

    result = build_legacy_profile(
        Path(args.spec),
        out_dir=Path(args.out_dir),
        receipt_out=Path(args.receipt_out),
        timeout=args.timeout,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if result.get("errors"):
        print(json.dumps(result["errors"], ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
