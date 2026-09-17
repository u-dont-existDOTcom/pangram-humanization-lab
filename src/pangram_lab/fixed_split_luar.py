from __future__ import annotations

import collections
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from .dharma_author_discover import discover_dharma_authors
from .dharma_control_profiles import _sample_id
from .dharma_speaker_acquire import acquire_speaker_inventory
from .hard_negative_diagnostics import analyze_condition
from .joel_register_corpus_network import build_network_register_corpus
from .luar_matched_pilot import LuarEmbedder, _cosine, _read_text, _row_key
from .surface_svm_equal_budget import _normalized_row
from .surface_svm_matched_cv import _aggregate_predictions


class FixedSplitLuarError(ValueError):
    pass


def _sha256_json(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _metadata_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "sample_id": row.get("sample_id"),
        "source_group": row.get("source_group"),
        "speaker": row.get("speaker"),
        "partition": row.get("partition"),
        "source_word_count": int(row.get("source_word_count", 0)),
        "source_canonical_sha256": row.get("source_canonical_sha256"),
        "word_count": int(row.get("word_count", 0)),
        "canonical_sha256": row.get("canonical_sha256"),
        "source_quality_flags": list(row.get("source_quality_flags", [])),
        "normalized_quality_flags": list(row.get("quality_flags", [])),
    }


def _selected_ids(author_spec: dict[str, Any]) -> tuple[list[str], list[str]]:
    profile = [str(value) for value in author_spec.get("profile_sample_ids", [])]
    holdout = [str(value) for value in author_spec.get("holdout_sample_ids", [])]
    if not profile or not holdout:
        raise FixedSplitLuarError(
            f"author {author_spec.get('speaker')} requires profile and holdout IDs"
        )
    if set(profile) & set(holdout):
        raise FixedSplitLuarError(
            f"author {author_spec.get('speaker')} repeats a source across partitions"
        )
    return profile, holdout


def _author_specs(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = spec.get("authors")
    if not isinstance(rows, list) or len(rows) < 4:
        raise FixedSplitLuarError("fixed split requires at least four authors")
    output: dict[str, dict[str, Any]] = {}
    for row in rows:
        speaker = str(row.get("speaker") or "").strip()
        if not speaker or speaker in output:
            raise FixedSplitLuarError(f"invalid or duplicate speaker: {speaker!r}")
        _selected_ids(row)
        output[speaker] = row
    return output


def _validate_spec(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if spec.get("schema_version") != 1:
        raise FixedSplitLuarError("spec schema_version must be 1")
    budget = int(spec.get("word_budget_per_document", 0))
    if budget < 50:
        raise FixedSplitLuarError("word budget must be at least 50")
    expected_profile = int(spec.get("profile_documents_per_author", 0))
    expected_holdout = int(spec.get("holdout_documents_per_author", 0))
    authors = _author_specs(spec)
    for speaker, row in authors.items():
        profile, holdout = _selected_ids(row)
        if len(profile) != expected_profile or len(holdout) != expected_holdout:
            raise FixedSplitLuarError(
                f"{speaker}: expected {expected_profile}+{expected_holdout} documents"
            )
    return authors


def _expected_hashes(author_spec: dict[str, Any]) -> dict[str, str]:
    return {
        str(key): str(value)
        for key, value in (author_spec.get("expected_canonical_sha256") or {}).items()
    }


def _verify_selected_rows(
    rows: list[dict[str, Any]],
    *,
    author_spec: dict[str, Any],
) -> list[dict[str, Any]]:
    speaker = str(author_spec["speaker"])
    profile_ids, holdout_ids = _selected_ids(author_spec)
    expected_ids = profile_ids + holdout_ids
    by_id = {str(row.get("sample_id")): dict(row) for row in rows}
    missing = [sample_id for sample_id in expected_ids if sample_id not in by_id]
    if missing:
        raise FixedSplitLuarError(f"{speaker}: missing selected samples: {missing}")

    expected_hashes = _expected_hashes(author_spec)
    selected: list[dict[str, Any]] = []
    for sample_id in expected_ids:
        row = by_id[sample_id]
        actual_hash = str(row.get("canonical_sha256") or "")
        expected_hash = expected_hashes.get(sample_id)
        if expected_hash and actual_hash != expected_hash:
            raise FixedSplitLuarError(
                f"{speaker}/{sample_id}: canonical hash drift: "
                f"expected={expected_hash} actual={actual_hash}"
            )
        row["speaker"] = speaker
        row["partition"] = (
            "profile" if sample_id in set(profile_ids) else "reserved_holdout"
        )
        row["source_word_count"] = int(row.get("word_count", 0))
        row["source_canonical_sha256"] = actual_hash
        row["source_quality_flags"] = list(row.get("quality_flags", []))
        selected.append(row)
    return selected


def _acquire_joel(
    spec: dict[str, Any],
    author_spec: dict[str, Any],
    *,
    working_dir: Path,
    timeout: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source_spec = Path(str(spec["sources"]["joel_register_spec"]))
    out_dir = working_dir / "joel-source-text"
    receipt_path = working_dir / "joel-source-receipt.json"
    receipt = build_network_register_corpus(
        source_spec,
        out_dir=out_dir,
        receipt_out=receipt_path,
        timeout=timeout,
    )
    if receipt.get("errors"):
        raise FixedSplitLuarError(f"Joel acquisition errors: {receipt['errors']}")

    register = receipt["registers"]["philosophical-research-dialogue"]
    rows: list[dict[str, Any]] = []
    for partition in ("profile", "reserved_holdout"):
        for meta in register["partitions"][partition]["samples"]:
            sample_id = str(meta["sample_id"])
            rows.append(
                {
                    **meta,
                    "speaker": "Joel Rosenblum",
                    "partition": partition,
                    "local_text_path": str(
                        out_dir
                        / "philosophical-research-dialogue"
                        / partition
                        / f"{sample_id}.txt"
                    ),
                }
            )
    return _verify_selected_rows(rows, author_spec=author_spec), receipt


def _acquire_dharma_controls(
    spec: dict[str, Any],
    author_specs: list[dict[str, Any]],
    *,
    working_dir: Path,
    timeout: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    queue_path = Path(str(spec["sources"]["control_queue"]))
    manifest_path = working_dir / "dharma-controls-acquisition.json"
    runtime = acquire_speaker_inventory(
        queue_path,
        out_dir=working_dir / "dharma-control-text",
        manifest_out=manifest_path,
        timeout=timeout,
    )
    hard_errors = [
        row
        for row in runtime.get("errors", [])
        if row.get("error")
        != "target-speaker-marker-found-but-no-authored-words"
    ]
    if hard_errors:
        raise FixedSplitLuarError(f"Dharma control acquisition errors: {hard_errors}")

    output: list[dict[str, Any]] = []
    for author_spec in author_specs:
        output.extend(
            _verify_selected_rows(
                runtime.get("results", []),
                author_spec=author_spec,
            )
        )
    metadata = {
        "network_fetch_count": runtime.get("network_fetch_count"),
        "hard_error_count": len(hard_errors),
        "document_count": len(runtime.get("results", [])),
    }
    return output, metadata


def _greg_url_map(
    source_spec: dict[str, Any],
    *,
    timeout: int,
) -> dict[str, dict[str, Any]]:
    target = source_spec["targets"][0]
    speaker = str(target["speaker"])
    author_id = str(target["author_id"])
    discovery = discover_dharma_authors(
        str(source_spec["blog"]),
        target_speaker=speaker,
        timeout=timeout,
    )
    posts: dict[str, dict[str, Any]] = {}
    for post in discovery.get("target_posts", []):
        if int(post.get("target_label_count", 0)) <= 0:
            continue
        sample_id = _sample_id(author_id, str(post["url"]))
        posts[sample_id] = post
    for seed in source_spec.get("manual_seed_pages_for_retrieval_crosscheck", []):
        url = str(seed["url"])
        sample_id = _sample_id(author_id, url)
        posts.setdefault(
            sample_id,
            {
                "entry_id": f"tag:manual-seed-{seed['url_sha256'][:24]}",
                "title": seed.get("title"),
                "published": "",
                "url": url,
                "target_label_count": 1,
            },
        )
    return posts


def _acquire_greg(
    spec: dict[str, Any],
    author_spec: dict[str, Any],
    *,
    working_dir: Path,
    timeout: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source_spec_path = Path(str(spec["sources"]["greg_candidate_source_spec"]))
    result_path = Path(str(spec["sources"]["greg_candidate_result"]))
    source_spec = json.loads(source_spec_path.read_text(encoding="utf-8"))
    frozen_result = json.loads(result_path.read_text(encoding="utf-8"))
    posts = _greg_url_map(source_spec, timeout=timeout)

    profile_ids, holdout_ids = _selected_ids(author_spec)
    expected_ids = profile_ids + holdout_ids
    missing = [sample_id for sample_id in expected_ids if sample_id not in posts]
    if missing:
        raise FixedSplitLuarError(f"Greg URL discovery omitted selected samples: {missing}")

    frozen_samples = {
        str(row["sample_id"]): row
        for row in frozen_result["candidate"]["samples"]
    }
    inventory_rows = []
    for sample_id in expected_ids:
        post = posts[sample_id]
        frozen = frozen_samples[sample_id]
        inventory_rows.append(
            {
                "sample_id": sample_id,
                "source_group": frozen["source_group"],
                "title": post.get("title"),
                "date": (post.get("published") or "")[:10],
                "url": post["url"],
                "extraction_mode": "speaker-prefix:Greg Goode",
            }
        )
    inventory = {
        "sources": [
            {
                "source_id": "dharma-fixed-greg-goode",
                "site_group": "dharma-connection",
                "provenance": "public-human-control-explicit-speaker",
                "modality": "written",
                "registers": [
                    "dialogue-QA",
                    "research-conversational",
                    "philosophical",
                ],
                "known_threads": inventory_rows,
            }
        ]
    }
    inventory_path = working_dir / "greg-fixed-inventory.json"
    manifest_path = working_dir / "greg-fixed-acquisition.json"
    inventory_path.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    runtime = acquire_speaker_inventory(
        inventory_path,
        out_dir=working_dir / "greg-source-text",
        manifest_out=manifest_path,
        timeout=timeout,
    )
    if runtime.get("errors"):
        raise FixedSplitLuarError(f"Greg acquisition errors: {runtime['errors']}")
    rows = _verify_selected_rows(runtime.get("results", []), author_spec=author_spec)
    return rows, {
        "network_fetch_count": runtime.get("network_fetch_count"),
        "document_count": len(rows),
        "frozen_candidate_artifact": frozen_result.get("artifact"),
    }


def acquire_fixed_split_sources(
    spec: dict[str, Any],
    *,
    working_dir: Path,
    timeout: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    authors = _validate_spec(spec)
    joel = authors["Joel Rosenblum"]
    stian = authors["Stian Gudmundsen Høiland"]
    david = authors["David Vardy"]
    greg = authors["Greg Goode"]

    joel_rows, joel_receipt = _acquire_joel(
        spec, joel, working_dir=working_dir, timeout=timeout
    )
    control_rows, control_receipt = _acquire_dharma_controls(
        spec,
        [stian, david],
        working_dir=working_dir,
        timeout=timeout,
    )
    greg_rows, greg_receipt = _acquire_greg(
        spec, greg, working_dir=working_dir, timeout=timeout
    )
    rows = joel_rows + control_rows + greg_rows

    by_author_partition = collections.Counter(
        (str(row["speaker"]), str(row["partition"])) for row in rows
    )
    expected_profile = int(spec["profile_documents_per_author"])
    expected_holdout = int(spec["holdout_documents_per_author"])
    for speaker in authors:
        if by_author_partition[(speaker, "profile")] != expected_profile:
            raise FixedSplitLuarError(f"{speaker}: wrong profile document count")
        if by_author_partition[(speaker, "reserved_holdout")] != expected_holdout:
            raise FixedSplitLuarError(f"{speaker}: wrong holdout document count")

    profile_groups = {
        str(row["source_group"])
        for row in rows
        if row["partition"] == "profile"
    }
    holdout_groups = {
        str(row["source_group"])
        for row in rows
        if row["partition"] == "reserved_holdout"
    }
    leakage = sorted(profile_groups & holdout_groups)
    if leakage:
        raise FixedSplitLuarError(f"profile/holdout source-group leakage: {leakage}")

    return rows, {
        "joel": {
            "corpus_identity_sha256": joel_receipt.get("corpus_identity_sha256"),
            "source_acquisition": joel_receipt.get("source_acquisition"),
        },
        "dharma_controls": control_receipt,
        "greg": greg_receipt,
        "source_group_leakage": leakage,
    }


def normalize_fixed_split(
    rows: list[dict[str, Any]],
    *,
    budget: int,
    out_dir: Path,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if int(row.get("word_count", 0)) < budget:
            raise FixedSplitLuarError(
                f"{row.get('sample_id')}: source has fewer than {budget} words"
            )
        value = _normalized_row(
            row,
            words=budget,
            out_dir=out_dir / str(row["partition"]),
            prefix=hashlib.sha256(
                f"{row['speaker']}:{row['partition']}".encode("utf-8")
            ).hexdigest()[:10],
        )
        value["partition"] = row["partition"]
        value["source_word_count"] = row["source_word_count"]
        value["source_canonical_sha256"] = row["source_canonical_sha256"]
        value["source_quality_flags"] = list(row.get("source_quality_flags", []))
        normalized.append(value)
    return normalized


def _profile_vectors(
    rows: list[dict[str, Any]],
    *,
    authors: list[str],
    embeddings: dict[str, Any],
) -> dict[str, Any]:
    import numpy as np

    profiles = {}
    for author in authors:
        vectors = [
            embeddings[_row_key(row)]
            for row in rows
            if row["partition"] == "profile" and row["speaker"] == author
        ]
        if not vectors:
            raise FixedSplitLuarError(f"no profile embeddings for {author}")
        profiles[author] = np.mean(np.stack(vectors, axis=0), axis=0)
    return profiles


def _profile_cosine_matrix(
    profiles: dict[str, Any], authors: list[str]
) -> dict[str, Any]:
    return {
        "labels": authors,
        "rows": [
            [round(_cosine(profiles[left], profiles[right]), 6) for right in authors]
            for left in authors
        ],
    }


def _predictions(
    holdouts: list[dict[str, Any]],
    *,
    authors: list[str],
    profiles: dict[str, Any],
    embeddings: dict[str, Any],
) -> list[dict[str, Any]]:
    predictions = []
    for row in holdouts:
        vector = embeddings[_row_key(row)]
        scores = {
            author: round(_cosine(vector, profiles[author]), 6)
            for author in authors
        }
        predicted = max(authors, key=lambda author: (scores[author], -authors.index(author)))
        actual = str(row["speaker"])
        predictions.append(
            {
                "sample_id": row["sample_id"],
                "source_group": row["source_group"],
                "actual": actual,
                "predicted": predicted,
                "correct": actual == predicted,
                "cosine_scores": scores,
            }
        )
    return predictions


def _role_spec(spec: dict[str, Any]) -> dict[str, Any]:
    role_rows = []
    for row in spec["authors"]:
        role = str(row["role"])
        if role == "ordinary-matched-control-candidate":
            role = "ordinary-matched-control"
        role_rows.append(
            {
                "author": row["speaker"],
                "role": role,
                "status": "active",
            }
        )
    return {
        "schema_version": 1,
        "active_authors": role_rows,
        "minimum_evidence": {
            "ordinary_matched_controls_before_rewrite_degradation_claim": 2,
            "minimum_target_holdout_documents": 4,
            "minimum_hard_negative_holdout_documents": 3,
        },
        "forbidden_claims": list(spec.get("interpretation_rules", [])),
    }


def run_fixed_split_luar(
    spec_path: Path,
    *,
    working_dir: Path,
    out_path: Path,
    timeout: int = 45,
) -> dict[str, Any]:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    author_specs = _validate_spec(spec)
    authors = [str(row["speaker"]) for row in spec["authors"]]
    rows, acquisition = acquire_fixed_split_sources(
        spec,
        working_dir=working_dir,
        timeout=timeout,
    )
    normalized = normalize_fixed_split(
        rows,
        budget=int(spec["word_budget_per_document"]),
        out_dir=working_dir / "normalized-150",
    )
    profile_rows = [row for row in normalized if row["partition"] == "profile"]
    holdout_rows = [
        row for row in normalized if row["partition"] == "reserved_holdout"
    ]

    model_spec = spec["model"]
    embedder = LuarEmbedder(
        model_id=str(model_spec["model_id"]),
        revision=str(model_spec["revision"]),
        max_token_length=int(model_spec.get("max_token_length", 512)),
        batch_size=int(model_spec.get("batch_size", 8)),
        device=str(model_spec.get("device", "cpu")),
    )
    embedder.embed_texts(_read_text(row) for row in normalized)
    profiles = _profile_vectors(
        profile_rows,
        authors=authors,
        embeddings=embedder.cache,
    )
    predictions = _predictions(
        holdout_rows,
        authors=authors,
        profiles=profiles,
        embeddings=embedder.cache,
    )
    reporting = spec.get("reporting", {})
    aggregate = _aggregate_predictions(
        predictions,
        authors,
        iterations=int(reporting.get("bootstrap_iterations", 10000)),
        seed=int(reporting.get("bootstrap_seed", 20260819)),
    )
    hard_negative = analyze_condition(predictions, _role_spec(spec))

    source_rows = [_metadata_row(row) for row in normalized]
    source_snapshot_sha = _sha256_json(source_rows)
    result = {
        "schema_version": 1,
        "date": spec.get("date"),
        "status": "four-author-fixed-split-original-diagnostic-not-IER-not-calibrated",
        "raw_or_canonical_prose_in_output": False,
        "embeddings_persisted_in_output": False,
        "method_decision": spec.get("method_decision"),
        "word_budget_per_document": spec["word_budget_per_document"],
        "authors": [
            {"speaker": row["speaker"], "role": row["role"]}
            for row in spec["authors"]
        ],
        "model": embedder.metadata(),
        "source_snapshot_sha256": source_snapshot_sha,
        "source_group_leakage": acquisition.get("source_group_leakage"),
        "acquisition": acquisition,
        "documents": source_rows,
        "profile_cosine_matrix": _profile_cosine_matrix(profiles, authors),
        "predictions": predictions,
        "aggregate": aggregate,
        "hard_negative_strata": hard_negative,
        "readiness": {
            "rewrite_degradation_ready": False,
            "blockers": [
                "only two natural heldouts per author",
                "Greg contains one flagged profile source and remains provisional",
                "all results are philosophical/research-dialogue only",
                "no calibrated abstention or stability rule",
                "no aligned within-register rewrites were tested",
            ],
        },
        "interpretation_rules": spec.get("interpretation_rules", []),
    }
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True)
    for forbidden in (
        "local_text_path",
        "raw_text",
        "canonical_text",
        "http://",
        "https://",
        "embedding",
        "embeddings",
    ):
        if forbidden in encoded:
            raise FixedSplitLuarError(
                f"metadata-only result unexpectedly contains {forbidden}"
            )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m pangram_lab.fixed_split_luar"
    )
    parser.add_argument(
        "spec",
        nargs="?",
        default="state/IDIOLECT-FOUR-AUTHOR-FIXED-SPLIT-SPEC-2026-08-19.json",
    )
    parser.add_argument(
        "--working-dir",
        default=".local/idiolect-corpus/four-author-fixed-split",
    )
    parser.add_argument(
        "--out",
        default=".local/idiolect-corpus/four-author-fixed-split-result.json",
    )
    parser.add_argument("--timeout", type=int, default=45)
    args = parser.parse_args(argv)

    try:
        result = run_fixed_split_luar(
            Path(args.spec),
            working_dir=Path(args.working_dir),
            out_path=Path(args.out),
            timeout=args.timeout,
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
