from __future__ import annotations

import collections
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Callable

from .corpus_acquire import acquire_inventory, canonicalize
from .joel_legacy_profile import apply_cleanup_rule

_NAME_TOKEN = r"[A-Z][A-Za-zÀ-ÖØ-öø-ÿ.'’\-]*"
_EMPTY_PERSON_LABEL_RE = re.compile(
    rf"^\s*(?:"
    rf"{_NAME_TOKEN}(?:\s+{_NAME_TOKEN}){{1,4}}"
    rf"|{_NAME_TOKEN}\s+asked"
    rf"|Question|Answer"
    rf")\s*:\s*$"
)


def _sha256_json(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _drop_empty_person_label_lines(text: str) -> tuple[str, int]:
    kept: list[str] = []
    removed = 0
    for line in text.splitlines():
        if _EMPTY_PERSON_LABEL_RE.match(line):
            removed += 1
            continue
        kept.append(line)
    return "\n".join(kept).strip(), removed


def apply_cleanup_pipeline(text: str, rules: list[str]) -> tuple[str, dict[str, int]]:
    value = text
    effects = {"empty_person_label_lines_removed": 0}
    for rule in rules:
        if rule == "whole":
            value = value.strip()
            continue
        if rule == "drop-empty-person-label-lines":
            value, count = _drop_empty_person_label_lines(value)
            effects["empty_person_label_lines_removed"] += count
            continue
        value = apply_cleanup_rule(value, rule)
    return value.strip(), effects


def _partition_summary(rows: list[dict]) -> dict:
    total_words = sum(int(row["word_count"]) for row in rows)
    largest_words = max((int(row["word_count"]) for row in rows), default=0)
    site_words: collections.Counter[str] = collections.Counter()
    for row in rows:
        site_words[str(row.get("site_group") or "")] += int(row["word_count"])
    largest_site_words = max(site_words.values(), default=0)
    return {
        "independent_source_count": len({str(row["source_group"]) for row in rows}),
        "document_count": len(rows),
        "total_words": total_words,
        "largest_source_words": largest_words,
        "largest_source_fraction": (
            round(largest_words / total_words, 6) if total_words else None
        ),
        "site_group_count": len([key for key in site_words if key]),
        "largest_site_words": largest_site_words,
        "largest_site_fraction": (
            round(largest_site_words / total_words, 6) if total_words else None
        ),
        "thin_under_250_count": sum(
            1 for row in rows if int(row["word_count"]) < 250
        ),
        "quality_flag_counts": dict(
            sorted(
                collections.Counter(
                    flag
                    for row in rows
                    for flag in row.get("quality_flags", [])
                ).items()
            )
        ),
    }


def _public_row(row: dict) -> dict:
    return {
        "inventory": row["inventory"],
        "register_id": row["register_id"],
        "partition": row["partition"],
        "sample_id": row["sample_id"],
        "source_group": row["source_group"],
        "site_group": row.get("site_group"),
        "provenance": row.get("provenance"),
        "modality": row.get("modality"),
        "cleanup_rules": row["cleanup_rules"],
        "cleanup_effects": row["cleanup_effects"],
        "source_html_sha256": row.get("source_html_sha256"),
        "source_canonical_sha256": row.get("source_canonical_sha256"),
        "expected_source_canonical_sha256": row.get(
            "expected_source_canonical_sha256"
        ),
        "expected_source_word_count": row.get("expected_source_word_count"),
        "expected_source_quality_flags": row.get(
            "expected_source_quality_flags"
        ),
        "canonical_sha256": row["canonical_sha256"],
        "expected_canonical_sha256": row.get("expected_canonical_sha256"),
        "expected_word_count": row.get("expected_word_count"),
        "source_word_count": row["source_word_count"],
        "word_count": row["word_count"],
        "words_removed_by_cleanup": row["words_removed_by_cleanup"],
        "quality_flags": row["quality_flags"],
        "allowed_quality_flags": row["allowed_quality_flags"],
    }


def build_register_corpus(
    spec_path: Path,
    *,
    out_dir: Path,
    receipt_out: Path,
    timeout: int = 30,
    acquire_fn: Callable = acquire_inventory,
) -> dict:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if spec.get("schema_version") != 1:
        raise ValueError("spec schema_version must be 1")

    inventories = {
        str(key): Path(value)
        for key, value in (spec.get("inventories") or {}).items()
    }
    if not inventories:
        raise ValueError("spec requires at least one inventory")

    requested: list[dict] = []
    for register in spec.get("registers", []):
        register_id = str(register["register_id"])
        for partition in ("profile", "reserved_holdout", "support"):
            for row in register.get(partition, []):
                requested.append(
                    {
                        **row,
                        "register_id": register_id,
                        "partition": partition,
                    }
                )

    if not requested:
        raise ValueError("spec has no requested sources")

    seen_ids: set[tuple[str, str]] = set()
    for row in requested:
        key = (str(row["inventory"]), str(row["sample_id"]))
        if key in seen_ids:
            raise ValueError(f"duplicate inventory/sample request: {key}")
        seen_ids.add(key)
        if row["inventory"] not in inventories:
            raise ValueError(f"unknown inventory alias: {row['inventory']}")

    acquired: dict[tuple[str, str], dict] = {}
    acquisition_errors: list[dict] = []
    for alias, inventory_path in inventories.items():
        ids = {
            str(row["sample_id"])
            for row in requested
            if str(row["inventory"]) == alias
        }
        if not ids:
            continue
        runtime_dir = out_dir.parent / f"register-source-{alias}"
        runtime_manifest = out_dir.parent / f"register-source-{alias}-manifest.json"
        runtime = acquire_fn(
            inventory_path,
            out_dir=runtime_dir,
            manifest_out=runtime_manifest,
            sample_ids=ids,
            timeout=timeout,
        )
        for error in runtime.get("errors", []):
            safe_error = {
                key: value
                for key, value in error.items()
                if key not in {"url", "local_text_path", "raw_text", "canonical_text"}
            }
            acquisition_errors.append({"inventory": alias, **safe_error})
        for row in runtime.get("results", []):
            acquired[(alias, str(row["sample_id"]))] = row

    errors: list[dict] = list(acquisition_errors)
    local_rows: list[dict] = []
    out_dir.mkdir(parents=True, exist_ok=True)

    for request in requested:
        alias = str(request["inventory"])
        sample_id = str(request["sample_id"])
        source = acquired.get((alias, sample_id))
        if source is None:
            errors.append(
                {
                    "inventory": alias,
                    "sample_id": sample_id,
                    "error": "source-not-acquired",
                }
            )
            continue
        try:
            required_provenance = str(
                request.get("required_provenance", "natural-owner-confirmed")
            )
            required_modality = str(request.get("required_modality", "written"))
            if str(source.get("provenance")) != required_provenance:
                raise ValueError(
                    "unexpected provenance: "
                    f"expected={required_provenance} actual={source.get('provenance')}"
                )
            if str(source.get("modality")) != required_modality:
                raise ValueError(
                    "unexpected modality: "
                    f"expected={required_modality} actual={source.get('modality')}"
                )

            expected_source_sha = request.get(
                "expected_source_canonical_sha256"
            )
            if (
                expected_source_sha is not None
                and str(source.get("canonical_sha256")) != str(expected_source_sha)
            ):
                raise ValueError(
                    "source canonical hash drift: "
                    f"expected={expected_source_sha} "
                    f"actual={source.get('canonical_sha256')}"
                )
            expected_source_words = request.get("expected_source_word_count")
            if (
                expected_source_words is not None
                and int(source.get("word_count", 0)) != int(expected_source_words)
            ):
                raise ValueError(
                    "source word-count drift: "
                    f"expected={expected_source_words} "
                    f"actual={source.get('word_count')}"
                )
            expected_source_flags = request.get("expected_source_quality_flags")
            if expected_source_flags is not None:
                expected_flags = sorted(str(flag) for flag in expected_source_flags)
                actual_flags = sorted(
                    str(flag) for flag in source.get("quality_flags", [])
                )
                if actual_flags != expected_flags:
                    raise ValueError(
                        "source quality-flag drift: "
                        f"expected={expected_flags} actual={actual_flags}"
                    )

            source_text = Path(str(source["local_text_path"])).read_text(
                encoding="utf-8"
            )
            cleanup_rules = [
                str(rule) for rule in request.get("cleanup_rules", ["whole"])
            ]
            cleaned, effects = apply_cleanup_pipeline(source_text, cleanup_rules)
            expected_removed = request.get("expected_empty_person_label_lines_removed")
            if expected_removed is not None and (
                effects["empty_person_label_lines_removed"] != int(expected_removed)
            ):
                raise ValueError(
                    "unexpected empty-person-label removal count: "
                    f"expected={expected_removed} "
                    f"actual={effects['empty_person_label_lines_removed']}"
                )
            canon = canonicalize(cleaned)
            if canon.word_count <= 0:
                raise ValueError("cleanup-produced-zero-words")
            expected_canonical_sha = request.get("expected_canonical_sha256")
            if (
                expected_canonical_sha is not None
                and canon.sha256 != str(expected_canonical_sha)
            ):
                raise ValueError(
                    "cleaned canonical hash drift: "
                    f"expected={expected_canonical_sha} actual={canon.sha256}"
                )
            expected_words = request.get("expected_word_count")
            if (
                expected_words is not None
                and canon.word_count != int(expected_words)
            ):
                raise ValueError(
                    "cleaned word-count drift: "
                    f"expected={expected_words} actual={canon.word_count}"
                )
            allowed = {
                str(flag) for flag in request.get("allowed_quality_flags", [])
            }
            unexpected_flags = sorted(set(canon.quality_flags) - allowed)
            if unexpected_flags:
                raise ValueError(
                    f"unexpected quality flags after cleanup: {unexpected_flags}"
                )

            target = (
                out_dir
                / str(request["register_id"])
                / str(request["partition"])
                / f"{sample_id}.txt"
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(canon.text + "\n", encoding="utf-8")
            local_rows.append(
                {
                    "inventory": alias,
                    "register_id": str(request["register_id"]),
                    "partition": str(request["partition"]),
                    "sample_id": sample_id,
                    "source_group": str(source.get("source_group") or sample_id),
                    "site_group": source.get("site_group"),
                    "provenance": source.get("provenance"),
                    "modality": source.get("modality"),
                    "cleanup_rules": cleanup_rules,
                    "cleanup_effects": effects,
                    "source_html_sha256": source.get("source_html_sha256"),
                    "source_canonical_sha256": source.get("canonical_sha256"),
                    "expected_source_canonical_sha256": request.get(
                        "expected_source_canonical_sha256"
                    ),
                    "expected_source_word_count": request.get(
                        "expected_source_word_count"
                    ),
                    "expected_source_quality_flags": (
                        sorted(
                            str(flag)
                            for flag in request.get(
                                "expected_source_quality_flags", []
                            )
                        )
                        if request.get("expected_source_quality_flags") is not None
                        else None
                    ),
                    "canonical_sha256": canon.sha256,
                    "expected_canonical_sha256": request.get(
                        "expected_canonical_sha256"
                    ),
                    "expected_word_count": request.get("expected_word_count"),
                    "source_word_count": int(source.get("word_count", 0)),
                    "word_count": canon.word_count,
                    "words_removed_by_cleanup": max(
                        0, int(source.get("word_count", 0)) - canon.word_count
                    ),
                    "quality_flags": canon.quality_flags,
                    "allowed_quality_flags": sorted(allowed),
                    "local_text_path": str(target),
                }
            )
        except Exception as exc:
            errors.append(
                {
                    "inventory": alias,
                    "sample_id": sample_id,
                    "error": str(exc),
                }
            )

    if errors:
        receipt = {
            "schema_version": 1,
            "raw_or_canonical_prose_in_output": False,
            "status": "failed",
            "errors": errors,
            "rows": [_public_row(row) for row in local_rows],
        }
        receipt_out.parent.mkdir(parents=True, exist_ok=True)
        receipt_out.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return receipt

    source_groups: dict[str, set[str]] = collections.defaultdict(set)
    canonical_hashes: dict[str, set[str]] = collections.defaultdict(set)
    for row in local_rows:
        register_id = row["register_id"]
        group = row["source_group"]
        if group in source_groups[register_id]:
            raise ValueError(
                f"source_group appears in multiple partitions for {register_id}: {group}"
            )
        source_groups[register_id].add(group)
        sha = row["canonical_sha256"]
        if sha in canonical_hashes[register_id]:
            raise ValueError(
                f"duplicate canonical text inside register {register_id}: {sha}"
            )
        canonical_hashes[register_id].add(sha)

    register_receipts: dict[str, dict] = {}
    for register in spec.get("registers", []):
        register_id = str(register["register_id"])
        register_rows = [
            row for row in local_rows if row["register_id"] == register_id
        ]
        partitions = {}
        for partition in ("profile", "reserved_holdout", "support"):
            part_rows = [
                row for row in register_rows if row["partition"] == partition
            ]
            partitions[partition] = {
                **_partition_summary(part_rows),
                "samples": [
                    _public_row(row)
                    for row in sorted(part_rows, key=lambda value: value["sample_id"])
                ],
            }
        register_receipts[register_id] = {
            "status": register.get("status"),
            "target_voice": register.get("target_voice"),
            "register_labels": register.get("register_labels", []),
            "partitions": partitions,
            "gates": register.get("gates", {}),
            "known_limitations": register.get("known_limitations", []),
        }

    gate_errors: list[dict] = []
    for register_id, register_receipt in register_receipts.items():
        gates = register_receipt.get("gates") or {}
        profile = register_receipt["partitions"]["profile"]
        holdout = register_receipt["partitions"]["reserved_holdout"]

        checks = [
            (
                "minimum_profile_sources",
                profile["independent_source_count"],
                lambda actual, expected: actual >= expected,
            ),
            (
                "minimum_profile_words",
                profile["total_words"],
                lambda actual, expected: actual >= expected,
            ),
            (
                "maximum_largest_profile_source_fraction",
                profile["largest_source_fraction"],
                lambda actual, expected: actual is not None and actual <= expected,
            ),
            (
                "minimum_reserved_holdout_sources",
                holdout["independent_source_count"],
                lambda actual, expected: actual >= expected,
            ),
            (
                "minimum_reserved_holdout_words",
                holdout["total_words"],
                lambda actual, expected: actual >= expected,
            ),
            (
                "maximum_profile_thin_sources",
                profile["thin_under_250_count"],
                lambda actual, expected: actual <= expected,
            ),
            (
                "maximum_reserved_holdout_thin_sources",
                holdout["thin_under_250_count"],
                lambda actual, expected: actual <= expected,
            ),
        ]
        for gate_name, actual, predicate in checks:
            if gate_name not in gates:
                continue
            expected = gates[gate_name]
            if not predicate(actual, expected):
                gate_errors.append(
                    {
                        "register_id": register_id,
                        "gate": gate_name,
                        "expected": expected,
                        "actual": actual,
                    }
                )

    identity_rows = [
        {
            "register_id": row["register_id"],
            "partition": row["partition"],
            "sample_id": row["sample_id"],
            "source_group": row["source_group"],
            "source_canonical_sha256": row.get("source_canonical_sha256"),
            "canonical_sha256": row["canonical_sha256"],
            "word_count": row["word_count"],
        }
        for row in sorted(
            local_rows,
            key=lambda value: (
                value["register_id"],
                value["partition"],
                value["sample_id"],
            ),
        )
    ]
    receipt = {
        "schema_version": 1,
        "raw_or_canonical_prose_in_output": False,
        "status": (
            spec.get("status")
            if not gate_errors
            else "failed-register-gates"
        ),
        "purpose": spec.get("purpose"),
        "method_decision": spec.get("method_decision"),
        "corpus_identity_sha256": _sha256_json(identity_rows),
        "registers": register_receipts,
        "nonready_registers": spec.get("nonready_registers", []),
        "excluded_sources": spec.get("excluded_sources", []),
        "errors": gate_errors,
    }
    receipt_out.parent.mkdir(parents=True, exist_ok=True)
    receipt_out.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m pangram_lab.joel_register_corpus"
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
        result = build_register_corpus(
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
