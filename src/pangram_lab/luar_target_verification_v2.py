from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from . import luar_target_verification as base


def historical_matched_prefix_exception(
    audit: dict[str, Any],
    *,
    current_canonical_sha256: str | None,
    historical_canonical_sha256: str | None,
) -> tuple[bool, str | None]:
    """Allow one narrow historical-target false-positive class.

    The old synchronized exact-50 LUAR pilot already evaluated these exact
    Joel target sources. If the current *full canonical source hash* is still
    byte-identical to that frozen source and the exact 50-word prefix trips
    only the generic ``possible-unremoved-dialogue`` heuristic, preserve that
    source as a historical control instead of silently changing the evaluated
    text or globally weakening the cleanliness gate.

    Any source drift, platform-chrome signal, ambiguous standalone-name line,
    quote-marker line, or additional prefix issue fails closed.
    """

    if not current_canonical_sha256 or not historical_canonical_sha256:
        return False, None
    if current_canonical_sha256 != historical_canonical_sha256:
        return False, None
    if int(audit.get("ambiguous_single_word_line_count", 0)) != 0:
        return False, None
    if int(audit.get("leading_quote_marker_line_count", 0)) != 0:
        return False, None
    if list(audit.get("issues", [])) != ["blocking-prefix-quality-flag"]:
        return False, None
    if list(audit.get("blocking_prefix_quality_flags", [])) != [
        "possible-unremoved-dialogue"
    ]:
        return False, None
    return (
        True,
        "hash-matched-historical-exact50-target-generic-dialogue-heuristic-only",
    )


def normalize_matched_targets(
    spec: dict[str, Any],
    dharma_rows: list[dict[str, Any]],
    *,
    working_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    budget = int(spec["word_budget_per_document"])
    target = str(spec["target_author"])
    row_by_id = base._row_map(dharma_rows)
    normalized_rows = []
    drift_rows = []
    historical = spec.get("historical_matched_target_hashes", {})

    for index, sample_id in enumerate(
        spec["matched_dharma_target_sample_ids"], start=1
    ):
        source = row_by_id.get(str(sample_id))
        if source is None:
            raise base.TargetVerificationError(
                f"missing matched target source: {sample_id}"
            )
        if str(source.get("speaker")) != target:
            raise base.TargetVerificationError(
                f"{sample_id}: expected target speaker {target}, "
                f"got {source.get('speaker')}"
            )
        if int(source.get("word_count", 0)) < budget:
            raise base.TargetVerificationError(
                f"{sample_id}: target source shorter than {budget}"
            )

        normalized, audit = base._normalize_row(
            source,
            words=budget,
            out_dir=working_dir / "matched-targets",
            prefix=f"m{index}",
        )
        expected = historical.get(str(sample_id))
        current = source.get("canonical_sha256")
        exception_applied = False
        exception_reason = None
        if not audit["clean"]:
            exception_applied, exception_reason = historical_matched_prefix_exception(
                audit,
                current_canonical_sha256=(str(current) if current else None),
                historical_canonical_sha256=(str(expected) if expected else None),
            )
            if not exception_applied:
                raise base.TargetVerificationError(
                    f"{sample_id}: matched target exact-{budget} prefix failed "
                    f"cleanliness: {audit['issues']}"
                )

        audit["historical_exact50_exception_applied"] = exception_applied
        audit["historical_exact50_exception_reason"] = exception_reason
        audit["admitted_for_named_target_verification"] = bool(
            audit["clean"] or exception_applied
        )
        normalized["prefix_audit"] = audit
        normalized["speaker"] = target
        normalized["source_quality_flags"] = list(
            source.get("quality_flags", [])
        )
        normalized["source_canonical_sha256"] = current
        normalized_rows.append(normalized)
        drift_rows.append(
            {
                "sample_id": sample_id,
                "historical_canonical_sha256": expected,
                "current_canonical_sha256": current,
                "canonical_drift": bool(expected and expected != current),
                "historical_exact50_exception_applied": exception_applied,
                "historical_exact50_exception_reason": exception_reason,
                "prefix_blocking_quality_flags": list(
                    audit.get("blocking_prefix_quality_flags", [])
                ),
            }
        )
    return normalized_rows, drift_rows


def normalize_independent_joel(
    spec: dict[str, Any],
    tafka_rows: list[dict[str, Any]],
    *,
    working_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Select clean exact-50 TAFKA sources without weakening prefix gates.

    The independent stratum is a sensitivity analysis, so it should not be
    forced through a source whose exact evaluated prefix is structurally
    ambiguous. Candidate-order fallbacks are predeclared in the spec, and a
    source selected into the Joel profile cannot also become a held-out
    original.
    """

    budget = int(spec["word_budget_per_document"])
    target = str(spec["target_author"])
    row_by_id = base._row_map(tafka_rows)
    profile_count = int(spec["profile_documents_per_author"])
    holdout_count = int(spec.get("independent_joel_holdout_count", 2))

    def choose(candidate_ids, count, label, excluded_ids):
        selected = []
        for index, sample_id in enumerate(candidate_ids, start=1):
            sample_id = str(sample_id)
            if sample_id in excluded_ids:
                continue
            source = row_by_id.get(sample_id)
            if source is None or int(source.get("word_count", 0)) < budget:
                continue
            source = dict(source)
            source["speaker"] = target
            normalized, audit = base._normalize_row(
                source,
                words=budget,
                out_dir=working_dir / label,
                prefix=f"j{index}",
            )
            if not audit["clean"]:
                continue
            normalized["speaker"] = target
            normalized["source_quality_flags"] = list(
                source.get("quality_flags", [])
            )
            normalized["source_canonical_sha256"] = source.get(
                "canonical_sha256"
            )
            selected.append(normalized)
            excluded_ids.add(sample_id)
            if len(selected) == count:
                break
        if len(selected) != count:
            raise base.TargetVerificationError(
                f"independent Joel {label}: only {len(selected)} clean "
                f"exact-{budget} documents; requires {count}"
            )
        return selected

    used: set[str] = set()
    profile = choose(
        spec.get(
            "independent_joel_profile_candidate_order",
            spec.get("independent_joel_profile_sample_ids", []),
        ),
        profile_count,
        "independent-profile",
        used,
    )
    holdout = choose(
        spec.get(
            "independent_joel_holdout_candidate_order",
            spec.get("independent_joel_holdout_sample_ids", []),
        ),
        holdout_count,
        "independent-holdout",
        used,
    )
    return profile, holdout


def run_target_verification(
    spec_path: Path,
    *,
    dharma_manifest_path: Path,
    tafka_manifest_path: Path,
    working_dir: Path,
    out_path: Path,
) -> dict[str, Any]:
    """Run v1 with narrow source-admission hooks installed."""

    original_matched = base.normalize_matched_targets
    original_independent = base.normalize_independent_joel
    base.normalize_matched_targets = normalize_matched_targets
    base.normalize_independent_joel = normalize_independent_joel
    try:
        result = base.run_target_verification(
            spec_path,
            dharma_manifest_path=dharma_manifest_path,
            tafka_manifest_path=tafka_manifest_path,
            working_dir=working_dir,
            out_path=out_path,
        )
    finally:
        base.normalize_matched_targets = original_matched
        base.normalize_independent_joel = original_independent

    result["target_prefix_admission_version"] = (
        "historical-hash-bound-exact50-dialogue-heuristic-exception-v1"
    )
    result["independent_joel_selection_version"] = (
        "predeclared-clean-exact50-fallback-selection-v1"
    )
    out_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m pangram_lab.luar_target_verification_v2"
    )
    parser.add_argument(
        "spec",
        nargs="?",
        default=(
            "state/IDIOLECT-FOUR-AUTHOR-TARGET-VERIFICATION-SPEC-2026-08-19.json"
        ),
    )
    parser.add_argument("--dharma-manifest", required=True)
    parser.add_argument("--tafka-manifest", required=True)
    parser.add_argument(
        "--working-dir",
        default=".local/idiolect-corpus/four-author-target-verification",
    )
    parser.add_argument(
        "--out",
        default=(
            ".local/idiolect-corpus/four-author-target-verification-result.json"
        ),
    )
    args = parser.parse_args(argv)
    try:
        result = run_target_verification(
            Path(args.spec),
            dharma_manifest_path=Path(args.dharma_manifest),
            tafka_manifest_path=Path(args.tafka_manifest),
            working_dir=Path(args.working_dir),
            out_path=Path(args.out),
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
