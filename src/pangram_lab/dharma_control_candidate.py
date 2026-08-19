from __future__ import annotations

import collections
import hashlib
import json
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable

from .blogger_discover import ATOM, _feed_url, _https_url, _root_from_url, fetch_atom
from .dharma_author_discover import _canonical_post_url, _entry_html, _speaker_labels
from .dharma_control_profiles import _EMPTY_EXPLICIT_BLOCK_ERROR, _sample_id
from .dharma_speaker_acquire import acquire_speaker_inventory


class ControlCandidateError(ValueError):
    pass


def _sha256_json(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _normalized_url(value: str) -> str:
    return _https_url(value).rstrip("/")


def _validate_spec(spec: dict[str, Any]) -> None:
    if spec.get("schema_version") != 1:
        raise ControlCandidateError("spec schema_version must be 1")
    if not isinstance(spec.get("blog"), str) or not spec["blog"].strip():
        raise ControlCandidateError("spec blog is required")
    target = spec.get("target")
    if not isinstance(target, dict):
        raise ControlCandidateError("spec target must be an object")
    for field in ("speaker", "author_id", "role"):
        if not isinstance(target.get(field), str) or not target[field].strip():
            raise ControlCandidateError(f"spec target.{field} is required")
    overlap = spec.get("overlap_speakers")
    if not isinstance(overlap, list) or not overlap:
        raise ControlCandidateError("spec overlap_speakers must be a non-empty list")
    if target["speaker"].casefold() in {str(value).casefold() for value in overlap}:
        raise ControlCandidateError("target speaker cannot also be an overlap speaker")

    network = spec.get("network") or {}
    for field in ("feed_page_size", "max_feed_pages", "timeout_seconds"):
        value = network.get(field)
        if not isinstance(value, int) or value <= 0:
            raise ControlCandidateError(f"spec network.{field} must be positive")
    spacing = network.get("source_request_spacing_seconds")
    if not isinstance(spacing, (int, float)) or spacing < 0:
        raise ControlCandidateError(
            "spec network.source_request_spacing_seconds must be nonnegative"
        )

    partition = spec.get("partition") or {}
    for field in ("reserved_holdout_count", "minimum_holdout_words_per_source"):
        value = partition.get(field)
        if not isinstance(value, int) or value <= 0:
            raise ControlCandidateError(f"spec partition.{field} must be positive")
    if not str(partition.get("selection_salt") or "").strip():
        raise ControlCandidateError("spec partition.selection_salt is required")


def discover_explicit_target_posts(
    spec: dict[str, Any],
    *,
    fetch_fn: Callable = fetch_atom,
) -> dict[str, Any]:
    """Scan the Blogger Atom archive once for target and overlap labels.

    The receipt retains only public-source metadata. The post body is inspected
    transiently to read explicit bold/strong/cite speaker labels and is never
    written to the result.
    """

    _validate_spec(spec)
    network = spec["network"]
    target = str(spec["target"]["speaker"])
    target_key = target.casefold()
    overlap_names = [str(value) for value in spec["overlap_speakers"]]
    overlap_by_key = {value.casefold(): value for value in overlap_names}

    root = _root_from_url(spec["blog"])
    feed_url = _feed_url(
        root,
        start_index=1,
        max_results=int(network["feed_page_size"]),
    )
    seen_feed_urls: set[str] = set()
    posts_by_url: dict[str, dict[str, Any]] = {}
    page_rows: list[dict[str, Any]] = []

    for page_number in range(1, int(network["max_feed_pages"]) + 1):
        if feed_url in seen_feed_urls:
            raise ControlCandidateError("Blogger feed pagination loop detected")
        seen_feed_urls.add(feed_url)
        body, feed_sha = fetch_fn(
            feed_url,
            timeout=int(network["timeout_seconds"]),
        )
        root_node = ET.fromstring(body)
        returned_next = None
        for link in root_node.findall(f"{ATOM}link"):
            if link.attrib.get("rel") == "next" and link.attrib.get("href"):
                returned_next = _https_url(link.attrib["href"])
                break

        entry_count = 0
        target_post_count = 0
        for entry in root_node.findall(f"{ATOM}entry"):
            entry_count += 1
            url = _canonical_post_url(entry)
            if not url:
                continue
            labels = _speaker_labels(_entry_html(entry))
            label_keys = [label.casefold() for label in labels]
            target_count = sum(1 for key in label_keys if key == target_key)
            if target_count <= 0:
                continue
            target_post_count += 1
            overlap_present = sorted(
                {
                    overlap_by_key[key]
                    for key in label_keys
                    if key in overlap_by_key
                },
                key=str.casefold,
            )
            normalized_url = _normalized_url(url)
            row = {
                "entry_id": (entry.findtext(f"{ATOM}id") or "").strip(),
                "title": (entry.findtext(f"{ATOM}title") or "").strip(),
                "published": (entry.findtext(f"{ATOM}published") or "").strip(),
                "url": normalized_url,
                "target_label_count": target_count,
                "overlap_speakers_present": overlap_present,
                "explicit_speaker_label_count": len(labels),
            }
            previous = posts_by_url.get(normalized_url)
            if previous is not None and previous != row:
                raise ControlCandidateError(
                    f"conflicting duplicate feed entry for {normalized_url}"
                )
            posts_by_url[normalized_url] = row

        page_rows.append(
            {
                "page_number": page_number,
                "feed_sha256": feed_sha,
                "entry_count": entry_count,
                "target_post_count": target_post_count,
                "next_present": bool(returned_next),
            }
        )
        if not returned_next:
            break
        feed_url = returned_next
    else:
        raise ControlCandidateError(
            f"Blogger feed paging exceeded max_feed_pages={network['max_feed_pages']}"
        )

    posts = sorted(
        posts_by_url.values(),
        key=lambda row: (row.get("published") or "", row["url"]),
    )
    return {
        "schema_version": 1,
        "raw_or_canonical_prose_in_output": False,
        "target_speaker": target,
        "overlap_speakers": overlap_names,
        "feed_pages": page_rows,
        "feed_page_count": len(page_rows),
        "target_explicit_post_count": len(posts),
        "target_posts": posts,
        "feed_snapshot_sha256": _sha256_json(page_rows),
        "target_post_set_sha256": _sha256_json(
            [
                {
                    "url": row["url"],
                    "entry_id": row["entry_id"],
                    "target_label_count": row["target_label_count"],
                    "overlap_speakers_present": row["overlap_speakers_present"],
                }
                for row in posts
            ]
        ),
    }


def build_candidate_inventory(
    spec: dict[str, Any], discovery: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    target = spec["target"]
    static_excludes = {
        _normalized_url(str(value)) for value in spec.get("static_exclude_urls", [])
    }
    selected = []
    rejected_overlap = []
    rejected_static = []
    rejected_name_only = []

    for post in discovery.get("target_posts", []):
        url = _normalized_url(str(post["url"]))
        if int(post.get("target_label_count", 0)) <= 0:
            rejected_name_only.append(url)
            continue
        if post.get("overlap_speakers_present"):
            rejected_overlap.append(
                {
                    "url": url,
                    "overlap_speakers_present": list(
                        post.get("overlap_speakers_present", [])
                    ),
                }
            )
            continue
        if url in static_excludes:
            rejected_static.append(url)
            continue
        entry_id = str(post.get("entry_id") or "")
        source_suffix = entry_id.rsplit("-", 1)[-1] if entry_id else _sha256_json(url)[:16]
        selected.append(
            {
                "sample_id": _sample_id(str(target["author_id"]), url),
                "source_group": f"dc-thread-{source_suffix}",
                "title": post.get("title"),
                "date": str(post.get("published") or "")[:10],
                "url": url,
                "extraction_mode": f"speaker-prefix:{target['speaker']}",
            }
        )

    inventory = {
        "sources": [
            {
                "source_id": f"dharma-candidate-{target['author_id']}",
                "site_group": "dharma-connection",
                "provenance": "public-human-control-explicit-speaker",
                "modality": "written",
                "registers": [
                    "dialogue-QA",
                    "research-conversational",
                    "philosophical",
                ],
                "known_threads": selected,
            }
        ]
    }
    census = {
        "target_speaker": target["speaker"],
        "author_id": target["author_id"],
        "role": target["role"],
        "discovered_explicit_posts": int(
            discovery.get("target_explicit_post_count", 0)
        ),
        "selected_nonoverlap_posts": len(selected),
        "rejected_dynamic_overlap_posts": len(rejected_overlap),
        "rejected_static_exclude_posts": len(rejected_static),
        "rejected_name_only_posts": len(rejected_name_only),
        "dynamic_overlap_rows": rejected_overlap,
        "static_exclude_urls_not_seen": sorted(
            static_excludes
            - {
                _normalized_url(str(post["url"]))
                for post in discovery.get("target_posts", [])
            }
        ),
        "selected_source_set_sha256": _sha256_json(
            [
                {
                    "sample_id": row["sample_id"],
                    "source_group": row["source_group"],
                    "url": row["url"],
                }
                for row in selected
            ]
        ),
    }
    return inventory, census


def paced_acquire_candidate(
    inventory_path: Path,
    *,
    out_dir: Path,
    manifest_dir: Path,
    spacing_seconds: float,
    timeout: int,
    acquire_fn: Callable = acquire_speaker_inventory,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    sample_ids = sorted(
        str(row["sample_id"])
        for source in inventory.get("sources", [])
        for row in source.get("known_threads", [])
    )
    results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    fetch_count = 0
    sleep_count = 0
    for index, sample_id in enumerate(sample_ids):
        if index:
            sleep_fn(float(spacing_seconds))
            sleep_count += 1
        runtime = acquire_fn(
            inventory_path,
            out_dir=out_dir,
            manifest_out=manifest_dir / f"{sample_id}.json",
            sample_ids={sample_id},
            timeout=timeout,
        )
        results.extend(runtime.get("results", []))
        errors.extend(runtime.get("errors", []))
        fetch_count += int(runtime.get("network_fetch_count", 0))
    return {
        "request_count": len(sample_ids),
        "sleep_count": sleep_count,
        "spacing_seconds": float(spacing_seconds),
        "network_fetch_count": fetch_count,
        "results": results,
        "errors": errors,
    }


def _partition_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_words = sum(int(row["word_count"]) for row in rows)
    largest_words = max((int(row["word_count"]) for row in rows), default=0)
    quality_flags = collections.Counter(
        str(flag) for row in rows for flag in row.get("quality_flags", [])
    )
    return {
        "source_count": len(rows),
        "total_words": total_words,
        "largest_source_words": largest_words,
        "largest_source_fraction": (
            round(largest_words / total_words, 6) if total_words else None
        ),
        "thin_under_250_count": sum(
            1 for row in rows if int(row["word_count"]) < 250
        ),
        "quality_flag_counts": dict(sorted(quality_flags.items())),
    }


def partition_candidate_rows(
    rows: list[dict[str, Any]], spec: dict[str, Any]
) -> dict[str, Any]:
    partition = spec["partition"]
    holdout_count = int(partition["reserved_holdout_count"])
    minimum_holdout_words = int(partition["minimum_holdout_words_per_source"])
    salt = str(partition["selection_salt"])

    by_hash: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for row in rows:
        by_hash[str(row["canonical_sha256"])].append(row)
    duplicate_groups = [
        {
            "canonical_sha256": sha,
            "sample_ids": sorted(str(row["sample_id"]) for row in grouped),
        }
        for sha, grouped in sorted(by_hash.items())
        if len(grouped) > 1
    ]
    unique_rows = [
        sorted(grouped, key=lambda row: str(row["sample_id"]))[0]
        for _, grouped in sorted(by_hash.items())
    ]

    eligible = [
        row for row in unique_rows if int(row["word_count"]) >= minimum_holdout_words
    ]
    ranked = sorted(
        eligible,
        key=lambda row: hashlib.sha256(
            (
                f"{salt}\t{row['source_group']}\t{row['canonical_sha256']}"
            ).encode("utf-8")
        ).hexdigest(),
    )
    holdout_ids = {
        str(row["sample_id"]) for row in ranked[:holdout_count]
    }
    holdout = [row for row in unique_rows if str(row["sample_id"]) in holdout_ids]
    profile = [row for row in unique_rows if str(row["sample_id"]) not in holdout_ids]

    def public(row: dict[str, Any], partition_name: str) -> dict[str, Any]:
        return {
            "partition": partition_name,
            "sample_id": row["sample_id"],
            "source_group": row["source_group"],
            "title": row.get("title"),
            "date": row.get("date"),
            "url": row.get("url"),
            "source_html_sha256": row.get("source_html_sha256"),
            "canonical_sha256": row["canonical_sha256"],
            "word_count": int(row["word_count"]),
            "target_marker_count": int(row.get("target_marker_count", 0)),
            "other_speaker_boundary_count": int(
                row.get("other_speaker_boundary_count", 0)
            ),
            "quality_flags": list(row.get("quality_flags", [])),
        }

    profile_public = [public(row, "profile") for row in profile]
    holdout_public = [public(row, "reserved_holdout") for row in holdout]
    return {
        "profile": {
            **_partition_summary(profile_public),
            "samples": sorted(profile_public, key=lambda row: row["sample_id"]),
        },
        "reserved_holdout": {
            **_partition_summary(holdout_public),
            "samples": sorted(holdout_public, key=lambda row: row["sample_id"]),
        },
        "eligible_holdout_source_count": len(eligible),
        "requested_holdout_source_count": holdout_count,
        "exact_duplicate_groups": duplicate_groups,
        "partition_identity_sha256": _sha256_json(
            [
                {
                    "sample_id": row["sample_id"],
                    "partition": row["partition"],
                    "canonical_sha256": row["canonical_sha256"],
                }
                for row in sorted(
                    [*profile_public, *holdout_public],
                    key=lambda item: item["sample_id"],
                )
            ]
        ),
    }


def _assert_metadata_only(value: Any, *, path: str = "$") -> None:
    forbidden = {
        "text",
        "raw_text",
        "canonical_text",
        "local_text_path",
        "embedding",
        "embeddings",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in forbidden:
                raise ControlCandidateError(
                    f"forbidden metadata key at {path}: {key}"
                )
            _assert_metadata_only(child, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_metadata_only(child, path=f"{path}[{index}]")


def run_candidate_extraction(
    spec_path: Path,
    *,
    out_dir: Path,
    receipt_out: Path,
    discovery_fn: Callable | None = None,
    acquire_fn: Callable = acquire_speaker_inventory,
    fetch_fn: Callable = fetch_atom,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    _validate_spec(spec)
    network = spec["network"]
    discovery = (
        discovery_fn(spec)
        if discovery_fn is not None
        else discover_explicit_target_posts(spec, fetch_fn=fetch_fn)
    )
    inventory, census = build_candidate_inventory(spec, discovery)
    runtime_dir = out_dir / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    inventory_path = runtime_dir / "candidate-inventory.json"
    inventory_path.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    acquisition = paced_acquire_candidate(
        inventory_path,
        out_dir=out_dir / "text",
        manifest_dir=runtime_dir / "sample-manifests",
        spacing_seconds=float(network["source_request_spacing_seconds"]),
        timeout=int(network["timeout_seconds"]),
        acquire_fn=acquire_fn,
        sleep_fn=sleep_fn,
    )

    empty_rejections = [
        row
        for row in acquisition["errors"]
        if row.get("error") == _EMPTY_EXPLICIT_BLOCK_ERROR
    ]
    hard_errors = [
        row
        for row in acquisition["errors"]
        if row.get("error") != _EMPTY_EXPLICIT_BLOCK_ERROR
    ]
    partitions = partition_candidate_rows(acquisition["results"], spec)
    guidance = spec["feasibility_guidance"]
    profile = partitions["profile"]
    holdout = partitions["reserved_holdout"]

    gates = {
        "no_hard_acquisition_errors": not hard_errors,
        "minimum_profile_sources": profile["source_count"]
        >= int(guidance["preferred_min_explicit_nonoverlap_posts"]),
        "minimum_profile_words": profile["total_words"]
        >= int(guidance["preferred_min_total_words"]),
        "maximum_profile_source_fraction": (
            profile["largest_source_fraction"] is not None
            and profile["largest_source_fraction"]
            <= float(guidance["preferred_max_largest_source_fraction"])
        ),
        "minimum_reserved_holdout_sources": holdout["source_count"]
        >= int(guidance["preferred_min_reserved_holdout_posts"]),
        "no_exact_duplicates": not partitions["exact_duplicate_groups"],
        "fresh_overlap_scan_completed": bool(discovery.get("feed_page_count")),
        "no_profile_holdout_source_group_overlap": not (
            {row["source_group"] for row in profile["samples"]}
            & {row["source_group"] for row in holdout["samples"]}
        ),
    }
    automated_pass = all(gates.values())
    manual_queue = sorted(
        [*profile["samples"], *holdout["samples"]],
        key=lambda row: (row["partition"], row["sample_id"]),
    )

    receipt = {
        "schema_version": 1,
        "date": spec.get("date"),
        "status": "candidate-extraction-complete-not-role-admission",
        "raw_or_canonical_prose_in_output": False,
        "purpose": spec.get("purpose"),
        "method_decision": spec.get("method_decision"),
        "target": spec["target"],
        "overlap_speakers": spec["overlap_speakers"],
        "discovery": {
            "feed_page_count": discovery.get("feed_page_count"),
            "target_explicit_post_count": discovery.get(
                "target_explicit_post_count"
            ),
            "feed_snapshot_sha256": discovery.get("feed_snapshot_sha256"),
            "target_post_set_sha256": discovery.get("target_post_set_sha256"),
        },
        "census": census,
        "acquisition": {
            "request_count": acquisition["request_count"],
            "network_fetch_count": acquisition["network_fetch_count"],
            "sleep_count": acquisition["sleep_count"],
            "spacing_seconds": acquisition["spacing_seconds"],
            "extracted_post_count": len(acquisition["results"]),
            "empty_explicit_rejection_count": len(empty_rejections),
            "hard_error_count": len(hard_errors),
            "empty_explicit_rejections": [
                {
                    "sample_id": row.get("sample_id"),
                    "url": row.get("url"),
                    "error": row.get("error"),
                }
                for row in empty_rejections
            ],
            "hard_errors": [
                {
                    key: value
                    for key, value in row.items()
                    if key not in {"local_text_path", "raw_text", "canonical_text"}
                }
                for row in hard_errors
            ],
        },
        "partitions": partitions,
        "automated_gates": gates,
        "automated_feasibility_pass": automated_pass,
        "manual_identity_and_quotation_review_required": True,
        "role_activation_ready": False,
        "manual_review_queue": manual_queue,
        "next_action": (
            "Audit identity continuity and quotation/copy contamination for every "
            "profile and holdout source. If those checks pass, admit the role in "
            "a separate metadata-only change before any new LUAR run."
        ),
        "forbidden_claims": spec.get("forbidden_claims", []),
    }
    _assert_metadata_only(receipt)
    receipt_out.parent.mkdir(parents=True, exist_ok=True)
    receipt_out.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m pangram_lab.dharma_control_candidate"
    )
    parser.add_argument(
        "spec",
        nargs="?",
        default="state/IDIOLECT-GREG-GOODE-CONTROL-EXTRACTION-SPEC-2026-08-19.json",
    )
    parser.add_argument(
        "--out-dir",
        default=".local/idiolect-corpus/greg-goode-control-candidate",
    )
    parser.add_argument(
        "--receipt-out",
        default=".local/idiolect-corpus/greg-goode-control-candidate-receipt.json",
    )
    args = parser.parse_args(argv)
    try:
        result = run_candidate_extraction(
            Path(args.spec),
            out_dir=Path(args.out_dir),
            receipt_out=Path(args.receipt_out),
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
