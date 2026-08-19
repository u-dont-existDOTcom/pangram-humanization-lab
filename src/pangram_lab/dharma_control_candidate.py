from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit, urlunsplit

from .dharma_author_discover import discover_dharma_authors
from .dharma_control_profiles import (
    _EMPTY_EXPLICIT_BLOCK_ERROR,
    build_profile_inventory,
    summarize_profiles,
)
from .dharma_speaker_acquire import acquire_speaker_inventory


class ControlCandidateError(ValueError):
    pass


def _normalize_url(value: str) -> str:
    parts = urlsplit(str(value).strip())
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", ""))


def _sha256_lines(values: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(values)).encode("utf-8")).hexdigest()


def _explicit_post_map(discovery: dict[str, Any]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for row in discovery.get("target_posts", []):
        if int(row.get("target_label_count", 0)) <= 0:
            continue
        url = _normalize_url(str(row.get("url") or ""))
        if not url:
            continue
        output[url] = row
    return output


def _sanitize_metadata(value: Any) -> Any:
    """Remove runtime paths, raw URLs, and prose-bearing fields recursively."""

    forbidden_keys = {
        "url",
        "urls",
        "local_text_path",
        "raw_text",
        "canonical_text",
        "text",
        "content",
        "html",
    }
    if isinstance(value, dict):
        return {
            str(key): _sanitize_metadata(child)
            for key, child in value.items()
            if str(key) not in forbidden_keys
        }
    if isinstance(value, list):
        return [_sanitize_metadata(child) for child in value]
    return value


def _validate_spec(spec: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    if spec.get("schema_version") != 1:
        raise ControlCandidateError("spec schema_version must be 1")
    targets = spec.get("targets")
    if not isinstance(targets, list) or len(targets) != 1:
        raise ControlCandidateError("candidate spec must contain exactly one target")
    target = targets[0]
    if not isinstance(target, dict):
        raise ControlCandidateError("candidate target must be an object")
    for field in ("speaker", "author_id"):
        if not str(target.get(field) or "").strip():
            raise ControlCandidateError(f"candidate target requires {field}")
    blog = str(spec.get("blog") or "").strip()
    if not blog:
        raise ControlCandidateError("candidate spec requires blog")

    overlap_speakers = [
        str(value).strip()
        for value in spec.get("overlap_exclusion_speakers", ["Joel Rosenblum"])
        if str(value).strip()
    ]
    target_key = str(target["speaker"]).casefold()
    overlap_speakers = [
        value for value in overlap_speakers if value.casefold() != target_key
    ]
    if not overlap_speakers:
        raise ControlCandidateError("at least one overlap exclusion speaker is required")
    return target, overlap_speakers


def _candidate_flags(author: dict[str, Any]) -> dict[str, Any]:
    flags = [str(value) for value in author.get("feasibility_flags", [])]
    quantitative_blockers = {
        "fewer-than-preferred-independent-posts",
        "total-under-preferred-word-count",
        "largest-source-overconcentrated",
    }
    quality_flags = {
        "one-or-more-samples-require-manual-quality-review",
        "one-or-more-explicit-label-posts-had-zero-authored-words",
    }
    return {
        "quantitative_feasibility_pass": not any(
            flag in quantitative_blockers for flag in flags
        ),
        "manual_quality_review_required": any(flag in quality_flags for flag in flags),
        "quantitative_blockers": [
            flag for flag in flags if flag in quantitative_blockers
        ],
        "quality_review_flags": [flag for flag in flags if flag in quality_flags],
    }


def extract_control_candidate(
    spec_path: Path,
    *,
    out_dir: Path,
    receipt_out: Path,
    timeout: int = 30,
    discover_fn: Callable[..., dict[str, Any]] = discover_dharma_authors,
    acquire_fn: Callable[..., dict[str, Any]] = acquire_speaker_inventory,
) -> dict[str, Any]:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    target, overlap_speakers = _validate_spec(spec)
    target_speaker = str(target["speaker"])
    blog = str(spec["blog"])

    discoveries: dict[str, dict[str, Any]] = {}
    for speaker in [target_speaker, *overlap_speakers]:
        discoveries[speaker] = discover_fn(
            blog,
            target_speaker=speaker,
            timeout=timeout,
        )

    target_posts = _explicit_post_map(discoveries[target_speaker])
    overlap_post_maps = {
        speaker: _explicit_post_map(discoveries[speaker])
        for speaker in overlap_speakers
    }
    fresh_overlap_urls = sorted(
        {
            url
            for url in target_posts
            if any(url in mapping for mapping in overlap_post_maps.values())
        }
    )
    configured_exclusions = {
        _normalize_url(str(value))
        for value in target.get("exclude_urls", [])
        if str(value).strip()
    }
    effective_exclusions = sorted(configured_exclusions | set(fresh_overlap_urls))

    runtime_spec = copy.deepcopy(spec)
    runtime_spec["targets"][0]["exclude_urls"] = effective_exclusions
    runtime_spec["targets"][0]["exclude_urls_are_provisional"] = False
    runtime_spec["targets"][0]["fresh_complete_overlap_census_required_before_admission"] = False

    inventory, census_rows = build_profile_inventory(
        runtime_spec,
        {target_speaker: discoveries[target_speaker]},
    )
    work_dir = out_dir.parent
    work_dir.mkdir(parents=True, exist_ok=True)
    generated_spec = work_dir / "control-candidate-effective-spec.json"
    generated_inventory = work_dir / "control-candidate-inventory.json"
    acquisition_manifest = work_dir / "control-candidate-acquisition.json"
    generated_spec.write_text(
        json.dumps(runtime_spec, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    generated_inventory.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    runtime = acquire_fn(
        generated_inventory,
        out_dir=out_dir,
        manifest_out=acquisition_manifest,
        timeout=timeout,
    )
    empty_explicit_rejections = [
        row
        for row in runtime.get("errors", [])
        if row.get("error") == _EMPTY_EXPLICIT_BLOCK_ERROR
    ]
    hard_errors = [
        row
        for row in runtime.get("errors", [])
        if row.get("error") != _EMPTY_EXPLICIT_BLOCK_ERROR
    ]

    profile = summarize_profiles(
        runtime.get("results", []),
        runtime_spec,
        census_rows,
        empty_explicit_rejections=empty_explicit_rejections,
    )
    author = dict(profile.get("authors", {}).get(target_speaker, {}))
    author.update(_candidate_flags(author))

    seed_coverage = []
    for seed in spec.get("manual_seed_pages_for_retrieval_crosscheck", []):
        url = _normalize_url(str(seed.get("url") or ""))
        row = target_posts.get(url)
        seed_coverage.append(
            {
                "title_sha256": hashlib.sha256(
                    str(seed.get("title") or "").encode("utf-8")
                ).hexdigest(),
                "url_sha256": hashlib.sha256(url.encode("utf-8")).hexdigest(),
                "discovered_as_explicit_target_post": row is not None,
                "target_label_count": int(row.get("target_label_count", 0)) if row else 0,
                "excluded_as_fresh_overlap": url in fresh_overlap_urls,
            }
        )

    discovery_receipts = {}
    for speaker, discovery in discoveries.items():
        discovery_receipts[speaker] = {
            "target_post_count": int(discovery.get("target_post_count", 0)),
            "explicit_post_count": len(_explicit_post_map(discovery)),
            "feed_pages": [
                {
                    "page_number": row.get("page_number"),
                    "feed_sha256": row.get("feed_sha256"),
                    "target_post_count": row.get("target_post_count"),
                    "next_present": row.get("next_present"),
                }
                for row in discovery.get("feed_pages", [])
            ],
        }

    result: dict[str, Any] = {
        "schema_version": 1,
        "date": spec.get("date"),
        "status": (
            "candidate-extraction-complete-manual-review-pending"
            if not hard_errors
            else "candidate-extraction-failed"
        ),
        "raw_or_canonical_prose_in_output": False,
        "profile_admission_authorized": False,
        "profile_holdout_split_authorized": False,
        "target_speaker": target_speaker,
        "target_author_id": target.get("author_id"),
        "target_role": target.get("role"),
        "method_decision": spec.get("method_decision"),
        "discovery": discovery_receipts,
        "fresh_overlap": {
            "exclusion_speakers": overlap_speakers,
            "fresh_overlap_count": len(fresh_overlap_urls),
            "configured_exclusion_count": len(configured_exclusions),
            "effective_exclusion_count": len(effective_exclusions),
            "fresh_only_count": len(set(fresh_overlap_urls) - configured_exclusions),
            "configured_only_count": len(configured_exclusions - set(fresh_overlap_urls)),
            "fresh_overlap_set_identity_sha256": _sha256_lines(fresh_overlap_urls),
            "effective_exclusion_set_identity_sha256": _sha256_lines(effective_exclusions),
        },
        "manual_seed_coverage": seed_coverage,
        "candidate": author,
        "network_fetch_count": int(runtime.get("network_fetch_count", 0)),
        "hard_error_count": len(hard_errors),
        "hard_errors": _sanitize_metadata(hard_errors),
        "empty_explicit_rejection_count": len(empty_explicit_rejections),
        "candidate_ready_for_manual_quality_review": bool(
            not hard_errors and author.get("quantitative_feasibility_pass")
        ),
        "required_post_extraction_checks": spec.get(
            "required_post_extraction_checks", []
        ),
        "forbidden_claims": spec.get("forbidden_claims", []),
    }
    result = _sanitize_metadata(result)
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True)
    for forbidden in (
        "local_text_path",
        "raw_text",
        "canonical_text",
        "http://",
        "https://",
    ):
        if forbidden in encoded:
            raise ControlCandidateError(
                f"metadata-only receipt unexpectedly contains {forbidden}"
            )

    receipt_out.parent.mkdir(parents=True, exist_ok=True)
    receipt_out.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m pangram_lab.dharma_control_candidate"
    )
    parser.add_argument(
        "spec",
        nargs="?",
        default="state/IDIOLECT-GREG-GOODE-CONTROL-PROFILE-CANDIDATE-SPEC-2026-08-18.json",
    )
    parser.add_argument(
        "--out-dir",
        default=".local/idiolect-corpus/greg-goode-control-profile-candidate-text",
    )
    parser.add_argument(
        "--receipt-out",
        default=".local/idiolect-corpus/greg-goode-control-profile-candidate-receipt.json",
    )
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args(argv)

    try:
        result = extract_control_candidate(
            Path(args.spec),
            out_dir=Path(args.out_dir),
            receipt_out=Path(args.receipt_out),
            timeout=args.timeout,
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not result.get("hard_errors") else 1


if __name__ == "__main__":
    raise SystemExit(main())
