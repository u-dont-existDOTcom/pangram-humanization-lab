from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from . import idiolect
from . import idiolect_pangram_prescreen as base


def select_cache_text(
    data: dict[str, Any], *, expected_sha256: str
) -> tuple[str | None, str]:
    """Select the exact cache input before the detector-returned copy.

    The cache directory is keyed from the submitted text. Pangram's returned
    `result.text` can differ byte-for-byte from that input through transport or
    normalization even when it represents the same visible prose. For this
    calibration, feature extraction must use the exact submitted text whenever
    it is preserved in the cache record.
    """

    submitted = data.get("text")
    if isinstance(submitted, str) and submitted.strip():
        if base._sha256_text(submitted) == expected_sha256:
            return submitted, "top_level_submitted_text_hash_match"

    result = data.get("result")
    returned = result.get("text") if isinstance(result, dict) else None
    if isinstance(returned, str) and returned.strip():
        if base._sha256_text(returned) == expected_sha256:
            return returned, "result_text_hash_match"

    if isinstance(submitted, str) and submitted.strip():
        return None, "top_level_submitted_text_hash_mismatch"
    if isinstance(returned, str) and returned.strip():
        return None, "result_text_hash_mismatch"
    return None, "missing_text"


def collect_cache_rows(
    repo_root: Path,
    *,
    evidence_ref: str,
    cache_root: str,
    accepted_prefixes: list[str],
    minimum_words: int,
    profile: idiolect.AuthorProfile,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    resolved_sha = base.resolve_ref(repo_root, evidence_ref)
    paths = [
        line.strip()
        for line in base._git(
            repo_root,
            "ls-tree",
            "-r",
            "--name-only",
            resolved_sha,
            "--",
            cache_root,
        ).splitlines()
        if line.strip().endswith(".json")
    ]

    excluded = {
        "not_successful_pangram4_v4": 0,
        "measurement_key_out_of_scope": 0,
        "missing_text": 0,
        "top_level_submitted_text_hash_mismatch": 0,
        "result_text_hash_mismatch": 0,
        "under_minimum_words": 0,
        "unknown_article_family": 0,
        "duplicate_same_label": 0,
        "duplicate_label_conflict": 0,
        "invalid_json": 0,
    }
    text_source_counts: dict[str, int] = {}
    by_text_sha: dict[str, dict[str, Any]] = {}
    conflict_shas: set[str] = set()

    for path in paths:
        try:
            data = json.loads(base._git_show(repo_root, resolved_sha, path))
        except Exception:
            excluded["invalid_json"] += 1
            continue
        if not isinstance(data, dict) or not base._is_successful_v4(data):
            excluded["not_successful_pangram4_v4"] += 1
            continue
        key = str(data.get("measurement_key") or Path(path).stem)
        if not any(key.startswith(prefix) for prefix in accepted_prefixes):
            excluded["measurement_key_out_of_scope"] += 1
            continue

        parts = path.split("/")
        expected_sha = parts[3] if len(parts) > 4 else ""
        text, source = select_cache_text(data, expected_sha256=expected_sha)
        if text is None:
            excluded[source] = excluded.get(source, 0) + 1
            continue
        text_source_counts[source] = text_source_counts.get(source, 0) + 1

        text_sha = base._sha256_text(text)
        words = len(idiolect._tokens(text))
        if words < minimum_words:
            excluded["under_minimum_words"] += 1
            continue
        family = base._article_family(key)
        if family is None:
            excluded["unknown_article_family"] += 1
            continue

        result = data["result"]
        channels = idiolect._feature_channels(text)
        row = {
            "text_sha256": text_sha,
            "measurement_keys": [key],
            "article_family": family,
            "word_count": words,
            "prediction_short": str(result.get("prediction_short") or ""),
            "fraction_ai": float(result.get("fraction_ai", 0.0)),
            "fraction_ai_assisted": float(result.get("fraction_ai_assisted", 0.0)),
            "strict_full_human": base._strict_human(result),
            "headline_human": base._headline_human(result),
            "surface_profile_similarity": idiolect._cosine(
                profile.surface, channels["surface"]
            ),
            "content_light_profile_similarity": idiolect._cosine(
                profile.content_light, channels["content_light"]
            ),
        }

        previous = by_text_sha.get(text_sha)
        if previous is None:
            by_text_sha[text_sha] = row
            continue
        same_label = all(
            previous[field] == row[field]
            for field in (
                "prediction_short",
                "fraction_ai",
                "fraction_ai_assisted",
                "strict_full_human",
                "headline_human",
            )
        )
        if not same_label:
            conflict_shas.add(text_sha)
            excluded["duplicate_label_conflict"] += 1
            continue
        previous["measurement_keys"].append(key)
        excluded["duplicate_same_label"] += 1

    for sha in conflict_shas:
        by_text_sha.pop(sha, None)

    rows = sorted(by_text_sha.values(), key=lambda row: row["text_sha256"])
    return rows, {
        "evidence_ref_requested": evidence_ref,
        "evidence_ref_resolved_sha": resolved_sha,
        "cache_text_identity_version": "submitted-text-first-hash-bound-v2",
        "cache_json_file_count": len(paths),
        "unique_eligible_text_count": len(rows),
        "text_source_counts": dict(sorted(text_source_counts.items())),
        "excluded": excluded,
    }


def run(
    spec_path: Path,
    *,
    repo_root: Path,
    profile_source_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    original = base.collect_cache_rows
    base.collect_cache_rows = collect_cache_rows
    try:
        result = base.run(
            spec_path,
            repo_root=repo_root,
            profile_source_path=profile_source_path,
            out_path=out_path,
        )
    finally:
        base.collect_cache_rows = original
    result["cache_text_identity_version"] = "submitted-text-first-hash-bound-v2"
    out_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m pangram_lab.idiolect_pangram_prescreen_v2"
    )
    parser.add_argument(
        "spec",
        nargs="?",
        default="state/IDIOLECT-PANGRAM-PRESCREEN-SPEC-2026-08-19.json",
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--profile-source", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        result = run(
            Path(args.spec),
            repo_root=Path(args.repo_root),
            profile_source_path=Path(args.profile_source),
            out_path=Path(args.out),
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    primary = result["primary_strict_full_human"]
    print(
        json.dumps(
            {
                "status": result["status"],
                "pangram_calls_made": result["pangram_calls_made"],
                "eligible_texts": result["cache"]["unique_eligible_text_count"],
                "strict_substitution_authorized": primary[
                    "substitution_authorized"
                ],
                "strict_heldout_cleared": primary["heldout_cleared_count"],
                "strict_false_safe": primary["heldout_false_safe_count"],
                "strict_false_safe_upper_95": primary[
                    "one_sided_95pct_false_safe_upper_bound"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
