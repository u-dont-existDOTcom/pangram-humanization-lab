from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .dharma_author_discover import discover_dharma_authors
from .dharma_speaker_acquire import acquire_speaker_inventory


def _sample_id(author_id: str, url: str) -> str:
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    slug = re.sub(r"\.html$", "", slug)
    slug = re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")
    return f"dcp-{author_id}-{slug}"[:180]


def build_profile_inventory(spec: dict, discoveries: dict[str, dict]) -> tuple[dict, list[dict]]:
    sources: list[dict] = []
    census_rows: list[dict] = []
    for target in spec.get("targets", []):
        speaker = target["speaker"]
        author_id = target["author_id"]
        exclude = {url.rstrip("/") for url in target.get("exclude_urls", [])}
        discovery = discoveries[speaker]
        posts = []
        rejected_name_only = 0
        rejected_overlap = 0
        for post in discovery.get("target_posts", []):
            url = post["url"].rstrip("/")
            if int(post.get("target_label_count", 0)) <= 0:
                rejected_name_only += 1
                continue
            if url in exclude:
                rejected_overlap += 1
                continue
            posts.append(
                {
                    "sample_id": _sample_id(author_id, url),
                    "source_group": f"dc-thread-{post['entry_id'].rsplit('-', 1)[-1]}",
                    "title": post.get("title"),
                    "date": (post.get("published") or "")[:10],
                    "url": post["url"],
                    "extraction_mode": f"speaker-prefix:{speaker}",
                }
            )
        sources.append(
            {
                "source_id": f"dharma-profile-{author_id}",
                "site_group": "dharma-connection",
                "provenance": "public-human-control-explicit-speaker",
                "modality": "written",
                "registers": ["dialogue-QA", "research-conversational", "philosophical"],
                "known_threads": posts,
            }
        )
        census_rows.append(
            {
                "speaker": speaker,
                "author_id": author_id,
                "discovered_name_or_label_posts": int(discovery.get("target_post_count", 0)),
                "selected_explicit_nonoverlap_posts": len(posts),
                "rejected_name_only_posts": rejected_name_only,
                "rejected_overlap_posts": rejected_overlap,
            }
        )
    return {"sources": sources}, census_rows


def summarize_profiles(results: list[dict], spec: dict, census_rows: list[dict]) -> dict:
    by_speaker: dict[str, list[dict]] = {}
    for row in results:
        by_speaker.setdefault(row["speaker"], []).append(row)

    guidance = spec.get("feasibility_guidance", {})
    min_posts = int(guidance.get("preferred_min_explicit_nonoverlap_posts", 4))
    min_words = int(guidance.get("preferred_min_total_words", 1000))
    max_fraction = float(guidance.get("preferred_max_largest_source_fraction", 0.7))

    census_by = {row["speaker"]: row for row in census_rows}
    authors = {}
    for target in spec.get("targets", []):
        speaker = target["speaker"]
        rows = sorted(by_speaker.get(speaker, []), key=lambda row: row["source_group"])
        total_words = sum(int(row["word_count"]) for row in rows)
        largest = max((int(row["word_count"]) for row in rows), default=0)
        largest_fraction = round(largest / total_words, 6) if total_words else None
        flags = []
        if len(rows) < min_posts:
            flags.append("fewer-than-preferred-independent-posts")
        if total_words < min_words:
            flags.append("total-under-preferred-word-count")
        if largest_fraction is not None and largest_fraction > max_fraction:
            flags.append("largest-source-overconcentrated")
        if any(row.get("quality_flags") for row in rows):
            flags.append("one-or-more-samples-require-manual-quality-review")
        authors[speaker] = {
            **census_by.get(speaker, {}),
            "extracted_post_count": len(rows),
            "total_words": total_words,
            "largest_source_words": largest,
            "largest_source_fraction": largest_fraction,
            "feasibility_flags": flags,
            "samples": [
                {
                    "sample_id": row["sample_id"],
                    "source_group": row["source_group"],
                    "canonical_sha256": row["canonical_sha256"],
                    "word_count": row["word_count"],
                    "target_marker_count": row["target_marker_count"],
                    "quality_flags": row["quality_flags"],
                }
                for row in rows
            ],
        }
    return {
        "schema_version": 1,
        "raw_or_canonical_prose_in_output": False,
        "authors": authors,
    }


def extract_control_profiles(
    spec_path: Path,
    *,
    out_dir: Path,
    receipt_out: Path,
    timeout: int = 30,
) -> dict:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    discoveries = {
        target["speaker"]: discover_dharma_authors(
            spec["blog"], target_speaker=target["speaker"], timeout=timeout
        )
        for target in spec.get("targets", [])
    }
    inventory, census_rows = build_profile_inventory(spec, discoveries)
    local_inventory = out_dir.parent / "dharma-control-profile-generated-inventory.json"
    local_inventory.parent.mkdir(parents=True, exist_ok=True)
    local_inventory.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    acquisition_manifest = out_dir.parent / "dharma-control-profile-acquisition.json"
    runtime = acquire_speaker_inventory(
        local_inventory,
        out_dir=out_dir,
        manifest_out=acquisition_manifest,
        timeout=timeout,
    )
    if runtime.get("errors"):
        return {
            "schema_version": 1,
            "raw_or_canonical_prose_in_output": False,
            "errors": runtime["errors"],
            "authors": {},
        }
    receipt = summarize_profiles(runtime.get("results", []), spec, census_rows)
    receipt["errors"] = []
    receipt_out.parent.mkdir(parents=True, exist_ok=True)
    receipt_out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="python -m pangram_lab.dharma_control_profiles")
    parser.add_argument(
        "spec",
        nargs="?",
        default="state/IDIOLECT-DHARMA-CONTROL-PROFILE-SPEC-2026-08-18.json",
    )
    parser.add_argument("--out-dir", default=".local/idiolect-corpus/dharma-control-profile-text")
    parser.add_argument("--receipt-out", default=".local/idiolect-corpus/dharma-control-profile-receipt.json")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args(argv)

    result = extract_control_profiles(
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
