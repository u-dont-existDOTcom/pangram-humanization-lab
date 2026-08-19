from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit, urlunsplit

from .corpus_acquire import fetch_bytes
from .dharma_author_discover import discover_dharma_authors
from .dharma_control_profiles import (
    _EMPTY_EXPLICIT_BLOCK_ERROR,
    build_profile_inventory,
    summarize_profiles,
)
from .dharma_speaker_acquire import (
    BloggerVisibleTextParser,
    acquire_speaker_inventory,
    extract_speaker_prefix,
)


class ControlCandidateError(ValueError):
    pass


def _normalize_url(value: str) -> str:
    parts = urlsplit(str(value).strip())
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", "")
    )


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

    exclusions = spec.get("post_extraction_exclusions", [])
    if exclusions is not None and not isinstance(exclusions, list):
        raise ControlCandidateError("post_extraction_exclusions must be a list")
    seen_exclusions: set[str] = set()
    for index, row in enumerate(exclusions or []):
        if not isinstance(row, dict):
            raise ControlCandidateError(
                f"post_extraction_exclusions[{index}] must be an object"
            )
        sample_id = str(row.get("sample_id") or "").strip()
        expected_sha = str(row.get("expected_canonical_sha256") or "").strip()
        if not sample_id or len(expected_sha) != 64:
            raise ControlCandidateError(
                f"post_extraction_exclusions[{index}] requires sample_id and "
                "64-character expected_canonical_sha256"
            )
        if sample_id in seen_exclusions:
            raise ControlCandidateError(
                f"duplicate post-extraction exclusion: {sample_id}"
            )
        seen_exclusions.add(sample_id)
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
        "manual_quality_review_required": any(
            flag in quality_flags for flag in flags
        ),
        "quantitative_blockers": [
            flag for flag in flags if flag in quantitative_blockers
        ],
        "quality_review_flags": [flag for flag in flags if flag in quality_flags],
    }


def _visible_text(body: bytes) -> str:
    parser = BloggerVisibleTextParser()
    parser.feed(body.decode("utf-8", errors="replace"))
    return parser.text()


def _speaker_marker_count(visible: str, speaker: str) -> int:
    prefix = speaker.casefold() + ":"
    return sum(
        1
        for line in visible.splitlines()
        if " ".join(line.split()).casefold().startswith(prefix)
    )


def _seed_page_observation(
    seed: dict[str, Any],
    *,
    target_speaker: str,
    overlap_speakers: list[str],
    page_fetch_fn: Callable[..., tuple[bytes, str]],
    timeout: int,
) -> dict[str, Any]:
    url = _normalize_url(str(seed.get("url") or ""))
    if not url:
        raise ControlCandidateError("manual seed page requires url")
    body, source_html_sha256 = page_fetch_fn(url, timeout=timeout)
    visible = _visible_text(body)

    speakers = [target_speaker, *overlap_speakers]
    marker_counts = {
        speaker: _speaker_marker_count(visible, speaker) for speaker in speakers
    }
    target_words = 0
    target_extraction_error = None
    if marker_counts[target_speaker]:
        try:
            extraction = extract_speaker_prefix(visible, target_speaker)
            target_words = int(extraction.get("word_count", 0))
        except ValueError as exc:
            target_extraction_error = str(exc)

    overlap_present = [
        speaker for speaker in overlap_speakers if marker_counts[speaker] > 0
    ]
    return {
        "title": str(seed.get("title") or ""),
        "url": url,
        "url_sha256": hashlib.sha256(url.encode("utf-8")).hexdigest(),
        "source_html_sha256": source_html_sha256,
        "target_marker_count": marker_counts[target_speaker],
        "target_word_count": target_words,
        "target_extraction_error": target_extraction_error,
        "overlap_speakers_present": overlap_present,
        "speaker_marker_counts": marker_counts,
    }


def _inject_seed_observations(
    discoveries: dict[str, dict[str, Any]],
    observations: list[dict[str, Any]],
    *,
    target_speaker: str,
    overlap_speakers: list[str],
) -> None:
    for observation in observations:
        url = str(observation["url"])
        seed_id = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
        title = str(observation.get("title") or "")
        for speaker in [target_speaker, *overlap_speakers]:
            marker_count = int(
                observation.get("speaker_marker_counts", {}).get(speaker, 0)
            )
            if marker_count <= 0:
                continue
            discovery = discoveries[speaker]
            existing = _explicit_post_map(discovery)
            if url in existing:
                continue
            discovery.setdefault("target_posts", []).append(
                {
                    "entry_id": f"tag:manual-seed-post-{seed_id}",
                    "title": title,
                    "published": "",
                    "url": url,
                    "raw_target_occurrences": marker_count,
                    "target_label_count": marker_count,
                    "explicit_speaker_labels": [speaker],
                    "source_route": "manual-seed-direct-page-preflight",
                }
            )
            discovery["target_post_count"] = int(
                discovery.get("target_post_count", 0)
            ) + 1


def _apply_post_extraction_exclusions(
    rows: list[dict[str, Any]],
    exclusions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    by_id = {str(row["sample_id"]): row for row in exclusions}
    kept: list[dict[str, Any]] = []
    applied: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    seen: set[str] = set()

    for row in rows:
        sample_id = str(row.get("sample_id") or "")
        rule = by_id.get(sample_id)
        if rule is None:
            kept.append(row)
            continue
        seen.add(sample_id)
        expected = str(rule["expected_canonical_sha256"])
        actual = str(row.get("canonical_sha256") or "")
        if actual != expected:
            errors.append(
                {
                    "sample_id": sample_id,
                    "error": "post-extraction exclusion canonical hash drift",
                    "expected_canonical_sha256": expected,
                    "actual_canonical_sha256": actual,
                }
            )
            kept.append(row)
            continue
        applied.append(
            {
                "sample_id": sample_id,
                "canonical_sha256": actual,
                "word_count": int(row.get("word_count", 0)),
                "quality_flags": list(row.get("quality_flags", [])),
                "reason": str(rule.get("reason") or ""),
            }
        )

    for sample_id in sorted(set(by_id) - seen):
        errors.append(
            {
                "sample_id": sample_id,
                "error": "configured post-extraction exclusion sample not acquired",
                "expected_canonical_sha256": str(
                    by_id[sample_id]["expected_canonical_sha256"]
                ),
            }
        )
    return kept, applied, errors


def _split_readiness(
    samples: list[dict[str, Any]],
    split_spec: dict[str, Any],
) -> dict[str, Any]:
    profile_documents = int(split_spec.get("profile_documents", 4))
    holdout_documents = int(split_spec.get("holdout_documents", 2))
    required = profile_documents + holdout_documents
    budgets = sorted(
        {
            int(value)
            for value in split_spec.get("word_budgets", [150, 180, 250])
            if int(value) > 0
        }
    )
    rows = []
    for budget in budgets:
        eligible = [
            row for row in samples if int(row.get("word_count", 0)) >= budget
        ]
        clean = [row for row in eligible if not row.get("quality_flags")]
        rows.append(
            {
                "word_budget": budget,
                "required_document_count": required,
                "eligible_document_count": len(eligible),
                "clean_eligible_document_count": len(clean),
                "eligible_sample_ids": sorted(
                    str(row.get("sample_id")) for row in eligible
                ),
                "eligible_hash_set_sha256": _sha256_lines(
                    [
                        f"{row.get('sample_id')}\t{row.get('canonical_sha256')}"
                        for row in eligible
                    ]
                ),
                "supply_pass": len(eligible) >= required,
                "clean_only_supply_pass": len(clean) >= required,
            }
        )
    return {
        "profile_documents": profile_documents,
        "holdout_documents": holdout_documents,
        "required_document_count": required,
        "budgets": rows,
    }


def extract_control_candidate(
    spec_path: Path,
    *,
    out_dir: Path,
    receipt_out: Path,
    timeout: int = 30,
    discover_fn: Callable[..., dict[str, Any]] = discover_dharma_authors,
    acquire_fn: Callable[..., dict[str, Any]] = acquire_speaker_inventory,
    page_fetch_fn: Callable[..., tuple[bytes, str]] = fetch_bytes,
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

    initial_target_posts = _explicit_post_map(discoveries[target_speaker])
    seed_observations: list[dict[str, Any]] = []
    for seed in spec.get("manual_seed_pages_for_retrieval_crosscheck", []):
        url = _normalize_url(str(seed.get("url") or ""))
        if url in initial_target_posts:
            continue
        seed_observations.append(
            _seed_page_observation(
                seed,
                target_speaker=target_speaker,
                overlap_speakers=overlap_speakers,
                page_fetch_fn=page_fetch_fn,
                timeout=timeout,
            )
        )
    _inject_seed_observations(
        discoveries,
        seed_observations,
        target_speaker=target_speaker,
        overlap_speakers=overlap_speakers,
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
    runtime_spec["targets"][0][
        "fresh_complete_overlap_census_required_before_admission"
    ] = False

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

    filtered_rows, applied_exclusions, exclusion_errors = (
        _apply_post_extraction_exclusions(
            list(runtime.get("results", [])),
            list(spec.get("post_extraction_exclusions", [])),
        )
    )
    hard_errors.extend(exclusion_errors)

    profile = summarize_profiles(
        filtered_rows,
        runtime_spec,
        census_rows,
        empty_explicit_rejections=empty_explicit_rejections,
    )
    author = dict(profile.get("authors", {}).get(target_speaker, {}))
    author.update(_candidate_flags(author))
    split_readiness = _split_readiness(
        list(author.get("samples", [])),
        dict(spec.get("split_readiness", {})),
    )

    observed_by_url = {str(row["url"]): row for row in seed_observations}
    seed_coverage = []
    for seed in spec.get("manual_seed_pages_for_retrieval_crosscheck", []):
        url = _normalize_url(str(seed.get("url") or ""))
        row = target_posts.get(url)
        observation = observed_by_url.get(url)
        seed_coverage.append(
            {
                "title_sha256": hashlib.sha256(
                    str(seed.get("title") or "").encode("utf-8")
                ).hexdigest(),
                "url_sha256": hashlib.sha256(url.encode("utf-8")).hexdigest(),
                "discovered_as_explicit_target_post": url in initial_target_posts,
                "direct_page_preflight_used": observation is not None,
                "direct_page_target_marker_count": int(
                    observation.get("target_marker_count", 0)
                )
                if observation
                else None,
                "direct_page_target_word_count": int(
                    observation.get("target_word_count", 0)
                )
                if observation
                else None,
                "direct_page_overlap_speakers_present": list(
                    observation.get("overlap_speakers_present", [])
                )
                if observation
                else [],
                "source_html_sha256": observation.get("source_html_sha256")
                if observation
                else None,
                "selected_as_explicit_target_post": row is not None,
                "target_label_count": int(row.get("target_label_count", 0))
                if row
                else 0,
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
            "effective_exclusion_set_identity_sha256": _sha256_lines(
                effective_exclusions
            ),
        },
        "manual_seed_coverage": seed_coverage,
        "manual_seed_direct_page_fetch_count": len(seed_observations),
        "post_extraction_exclusions_applied": applied_exclusions,
        "candidate": author,
        "split_readiness": split_readiness,
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
        default=(
            "state/"
            "IDIOLECT-GREG-GOODE-CONTROL-PROFILE-CANDIDATE-SPEC-2026-08-18.json"
        ),
    )
    parser.add_argument(
        "--out-dir",
        default=(
            ".local/idiolect-corpus/"
            "greg-goode-control-profile-candidate-text"
        ),
    )
    parser.add_argument(
        "--receipt-out",
        default=(
            ".local/idiolect-corpus/"
            "greg-goode-control-profile-candidate-receipt.json"
        ),
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
