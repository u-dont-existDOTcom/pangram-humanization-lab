from __future__ import annotations

import collections
import json
import re
import statistics
import sys
from pathlib import Path
from typing import Any

from .corpus_acquire import canonicalize
from .luar_matched_pilot import LuarEmbedder, _cosine, _read_text, _row_key
from .surface_svm_equal_budget import _normalized_row

_AMBIGUOUS_SINGLE_WORD_RE = re.compile(
    r"^[A-Z][A-Za-zÀ-ÖØ-öø-ÿ.'’\-]{1,24}$"
)
_PREFIX_BLOCKING_FLAGS = {
    "possible-unremoved-dialogue",
    "possible-platform-chrome",
}


class TargetVerificationError(ValueError):
    pass


def _round(value: float | None) -> float | None:
    return None if value is None else round(float(value), 6)


def _validate_spec(spec: dict[str, Any]) -> None:
    if spec.get("schema_version") != 1:
        raise TargetVerificationError("spec schema_version must be 1")
    authors = spec.get("authors")
    if not isinstance(authors, list) or len(authors) < 3:
        raise TargetVerificationError("spec authors must contain at least three authors")
    if len(authors) != len(set(str(value) for value in authors)):
        raise TargetVerificationError("spec authors must be unique")
    target = str(spec.get("target_author") or "")
    if target not in authors:
        raise TargetVerificationError("target_author must be in authors")
    hard = str(spec.get("hard_negative") or "")
    if hard not in authors or hard == target:
        raise TargetVerificationError("hard_negative must be a non-target author")
    controls = [str(value) for value in spec.get("ordinary_controls", [])]
    if not controls or any(value not in authors or value == target for value in controls):
        raise TargetVerificationError("ordinary_controls must be non-target authors")
    budget = spec.get("word_budget_per_document")
    if not isinstance(budget, int) or budget <= 0:
        raise TargetVerificationError("word_budget_per_document must be positive")
    n_profile = spec.get("profile_documents_per_author")
    if not isinstance(n_profile, int) or n_profile <= 0:
        raise TargetVerificationError("profile_documents_per_author must be positive")


def prefix_audit(row: dict[str, Any]) -> dict[str, Any]:
    """Audit the exact normalized text boundary used by LUAR.

    Full-source heuristic flags remain metadata, but only problems surviving in
    the exact 50-word prefix block profile selection. This avoids discarding a
    long source because a later dialogue-shaped line never enters the measured
    boundary, while remaining conservative about the actual evaluated text.
    """

    text = _read_text(row)
    canon = canonicalize(text)
    blocking_flags = sorted(set(canon.quality_flags) & _PREFIX_BLOCKING_FLAGS)
    ambiguous_lines = [
        line.strip()
        for line in text.splitlines()
        if _AMBIGUOUS_SINGLE_WORD_RE.fullmatch(line.strip())
    ]
    quote_marker_lines = [
        line.strip() for line in text.splitlines() if line.strip().startswith(">")
    ]
    issues = []
    if blocking_flags:
        issues.append("blocking-prefix-quality-flag")
    if ambiguous_lines:
        issues.append("standalone-single-capitalized-word-line")
    if quote_marker_lines:
        issues.append("leading-quote-marker-line")
    return {
        "clean": not issues,
        "issues": issues,
        "prefix_quality_flags": canon.quality_flags,
        "blocking_prefix_quality_flags": blocking_flags,
        "ambiguous_single_word_line_count": len(ambiguous_lines),
        "leading_quote_marker_line_count": len(quote_marker_lines),
        "normalized_sha256": canon.sha256,
        "normalized_word_count": canon.word_count,
    }


def _normalize_row(
    row: dict[str, Any],
    *,
    words: int,
    out_dir: Path,
    prefix: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    normalized = _normalized_row(row, words=words, out_dir=out_dir, prefix=prefix)
    audit = prefix_audit(normalized)
    if int(audit["normalized_word_count"]) != words:
        raise TargetVerificationError(
            f"{row.get('sample_id')}: normalized word count drift"
        )
    normalized["prefix_audit"] = audit
    return normalized, audit


def _public_meta(row: dict[str, Any]) -> dict[str, Any]:
    audit = dict(row.get("prefix_audit") or {})
    return {
        "sample_id": row.get("sample_id"),
        "source_group": row.get("source_group"),
        "speaker": row.get("speaker"),
        "source_canonical_sha256": row.get("source_canonical_sha256")
        or row.get("original_canonical_sha256")
        or row.get("canonical_source_sha256"),
        "original_word_count": int(
            row.get("original_word_count", row.get("source_word_count", row.get("word_count", 0)))
        ),
        "normalized_word_count": int(row.get("word_count", 0)),
        "normalized_sha256": row.get("canonical_sha256"),
        "source_quality_flags": list(row.get("source_quality_flags", row.get("quality_flags", []))),
        "prefix_audit": audit,
    }


def _row_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    output = {}
    for row in rows:
        sample_id = str(row.get("sample_id") or "")
        if not sample_id:
            continue
        if sample_id in output:
            raise TargetVerificationError(f"duplicate acquired sample_id: {sample_id}")
        output[sample_id] = row
    return output


def select_control_profiles(
    spec: dict[str, Any],
    dharma_rows: list[dict[str, Any]],
    *,
    working_dir: Path,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    budget = int(spec["word_budget_per_document"])
    count = int(spec["profile_documents_per_author"])
    row_by_id = _row_map(dharma_rows)
    selected: dict[str, list[dict[str, Any]]] = {}
    receipt: dict[str, Any] = {}

    for author, candidate_ids in spec["control_profile_candidate_order"].items():
        picked = []
        reviewed = []
        for index, sample_id in enumerate(candidate_ids, start=1):
            source = row_by_id.get(str(sample_id))
            if source is None:
                reviewed.append(
                    {"sample_id": sample_id, "selected": False, "reason": "not-acquired"}
                )
                continue
            if str(source.get("speaker")) != str(author):
                raise TargetVerificationError(
                    f"{sample_id}: expected speaker {author}, got {source.get('speaker')}"
                )
            if int(source.get("word_count", 0)) < budget:
                reviewed.append(
                    {
                        "sample_id": sample_id,
                        "selected": False,
                        "reason": "under-word-budget",
                        "word_count": int(source.get("word_count", 0)),
                    }
                )
                continue
            normalized, audit = _normalize_row(
                source,
                words=budget,
                out_dir=working_dir / "controls" / re.sub(r"[^A-Za-z0-9]+", "-", author),
                prefix=f"c{index}",
            )
            if not audit["clean"]:
                reviewed.append(
                    {
                        "sample_id": sample_id,
                        "selected": False,
                        "reason": "exact-prefix-cleanliness-failed",
                        "prefix_audit": audit,
                        "source_quality_flags": list(source.get("quality_flags", [])),
                    }
                )
                continue
            normalized["speaker"] = author
            normalized["source_quality_flags"] = list(source.get("quality_flags", []))
            normalized["source_canonical_sha256"] = source.get("canonical_sha256")
            picked.append(normalized)
            reviewed.append(
                {
                    "sample_id": sample_id,
                    "selected": True,
                    "prefix_audit": audit,
                    "source_quality_flags": list(source.get("quality_flags", [])),
                }
            )
            if len(picked) == count:
                break
        if len(picked) != count:
            raise TargetVerificationError(
                f"{author}: only {len(picked)} clean exact-{budget} profile docs; requires {count}"
            )
        selected[author] = picked
        receipt[author] = {
            "selected": [_public_meta(row) for row in picked],
            "candidate_review": reviewed,
        }
    return selected, receipt


def normalize_matched_targets(
    spec: dict[str, Any],
    dharma_rows: list[dict[str, Any]],
    *,
    working_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    budget = int(spec["word_budget_per_document"])
    target = str(spec["target_author"])
    row_by_id = _row_map(dharma_rows)
    normalized_rows = []
    drift_rows = []
    historical = spec.get("historical_matched_target_hashes", {})
    for index, sample_id in enumerate(spec["matched_dharma_target_sample_ids"], start=1):
        source = row_by_id.get(str(sample_id))
        if source is None:
            raise TargetVerificationError(f"missing matched target source: {sample_id}")
        if str(source.get("speaker")) != target:
            raise TargetVerificationError(
                f"{sample_id}: expected target speaker {target}, got {source.get('speaker')}"
            )
        if int(source.get("word_count", 0)) < budget:
            raise TargetVerificationError(f"{sample_id}: target source shorter than {budget}")
        normalized, audit = _normalize_row(
            source,
            words=budget,
            out_dir=working_dir / "matched-targets",
            prefix=f"m{index}",
        )
        if not audit["clean"]:
            raise TargetVerificationError(
                f"{sample_id}: matched target exact-{budget} prefix failed cleanliness: {audit['issues']}"
            )
        normalized["speaker"] = target
        normalized["source_quality_flags"] = list(source.get("quality_flags", []))
        normalized["source_canonical_sha256"] = source.get("canonical_sha256")
        normalized_rows.append(normalized)
        expected = historical.get(str(sample_id))
        drift_rows.append(
            {
                "sample_id": sample_id,
                "historical_canonical_sha256": expected,
                "current_canonical_sha256": source.get("canonical_sha256"),
                "canonical_drift": bool(expected and expected != source.get("canonical_sha256")),
            }
        )
    return normalized_rows, drift_rows


def normalize_independent_joel(
    spec: dict[str, Any],
    tafka_rows: list[dict[str, Any]],
    *,
    working_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    budget = int(spec["word_budget_per_document"])
    target = str(spec["target_author"])
    row_by_id = _row_map(tafka_rows)

    def build(ids, label):
        output = []
        for index, sample_id in enumerate(ids, start=1):
            source = row_by_id.get(str(sample_id))
            if source is None:
                raise TargetVerificationError(f"missing independent Joel source: {sample_id}")
            if int(source.get("word_count", 0)) < budget:
                raise TargetVerificationError(f"{sample_id}: independent Joel source shorter than {budget}")
            source = dict(source)
            source["speaker"] = target
            normalized, audit = _normalize_row(
                source,
                words=budget,
                out_dir=working_dir / label,
                prefix=f"j{index}",
            )
            if not audit["clean"]:
                raise TargetVerificationError(
                    f"{sample_id}: independent Joel exact-{budget} prefix failed cleanliness: {audit['issues']}"
                )
            normalized["speaker"] = target
            normalized["source_quality_flags"] = list(source.get("quality_flags", []))
            normalized["source_canonical_sha256"] = source.get("canonical_sha256")
            output.append(normalized)
        return output

    return (
        build(spec["independent_joel_profile_sample_ids"], "independent-profile"),
        build(spec["independent_joel_holdout_sample_ids"], "independent-holdout"),
    )


def _mean_profile(rows: list[dict[str, Any]], embeddings: dict[str, Any]):
    import numpy as np

    if not rows:
        raise TargetVerificationError("cannot build empty profile")
    vectors = [embeddings[_row_key(row)] for row in rows]
    return np.mean(np.stack(vectors, axis=0), axis=0)


def _profile_matrix(profiles: dict[str, Any], authors: list[str]) -> dict[str, dict[str, float]]:
    return {
        left: {right: _round(_cosine(profiles[left], profiles[right])) for right in authors}
        for left in authors
    }


def _score_target(
    row: dict[str, Any],
    *,
    profiles: dict[str, Any],
    authors: list[str],
    target: str,
    hard_negative: str,
    ordinary_controls: list[str],
    embeddings: dict[str, Any],
) -> dict[str, Any]:
    vector = embeddings[_row_key(row)]
    scores = {author: float(_cosine(vector, profiles[author])) for author in authors}
    ranked = sorted(authors, key=lambda author: (-scores[author], authors.index(author)))
    winner = ranked[0]
    margins = {
        author: _round(scores[target] - scores[author])
        for author in authors
        if author != target
    }
    best_ordinary = max(ordinary_controls, key=lambda author: scores[author])
    return {
        "sample_id": row.get("sample_id"),
        "source_group": row.get("source_group"),
        "actual": target,
        "predicted": winner,
        "correct": winner == target,
        "target_rank": ranked.index(target) + 1,
        "cosine_scores": {author: _round(scores[author]) for author in authors},
        "target_minus_competitor_margin": margins,
        "target_minus_hard_negative_margin": margins[hard_negative],
        "best_ordinary_control": best_ordinary,
        "target_minus_best_ordinary_margin": _round(scores[target] - scores[best_ordinary]),
        "heldout": _public_meta(row),
    }


def _margin_summary(predictions: list[dict[str, Any]], competitor: str) -> dict[str, Any]:
    values = [
        float(row["target_minus_competitor_margin"][competitor])
        for row in predictions
    ]
    return {
        "count": len(values),
        "positive_count": sum(value > 0 for value in values),
        "negative_count": sum(value < 0 for value in values),
        "zero_count": sum(value == 0 for value in values),
        "minimum": _round(min(values)) if values else None,
        "median": _round(statistics.median(values)) if values else None,
        "mean": _round(statistics.fmean(values)) if values else None,
        "maximum": _round(max(values)) if values else None,
    }


def _stratum_summary(
    predictions: list[dict[str, Any]],
    *,
    authors: list[str],
    target: str,
) -> dict[str, Any]:
    count = len(predictions)
    winner_counts = collections.Counter(str(row["predicted"]) for row in predictions)
    return {
        "document_count": count,
        "target_top1_correct": sum(bool(row["correct"]) for row in predictions),
        "target_top1_accuracy": _round(
            sum(bool(row["correct"]) for row in predictions) / count if count else None
        ),
        "winner_counts": {author: int(winner_counts[author]) for author in authors},
        "target_margin_by_competitor": {
            author: _margin_summary(predictions, author)
            for author in authors
            if author != target
        },
    }


def run_target_verification(
    spec_path: Path,
    *,
    dharma_manifest_path: Path,
    tafka_manifest_path: Path,
    working_dir: Path,
    out_path: Path,
) -> dict[str, Any]:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    _validate_spec(spec)
    dharma = json.loads(dharma_manifest_path.read_text(encoding="utf-8"))
    tafka = json.loads(tafka_manifest_path.read_text(encoding="utf-8"))
    if dharma.get("errors"):
        raise TargetVerificationError(f"Dharma acquisition errors: {dharma['errors']}")
    if tafka.get("errors"):
        raise TargetVerificationError(f"TAFKA acquisition errors: {tafka['errors']}")

    authors = [str(value) for value in spec["authors"]]
    target = str(spec["target_author"])
    hard = str(spec["hard_negative"])
    ordinary = [str(value) for value in spec["ordinary_controls"]]

    controls, control_receipt = select_control_profiles(
        spec,
        list(dharma.get("results", [])),
        working_dir=working_dir,
    )
    matched_targets, drift = normalize_matched_targets(
        spec,
        list(dharma.get("results", [])),
        working_dir=working_dir,
    )
    independent_profile, independent_holdouts = normalize_independent_joel(
        spec,
        list(tafka.get("results", [])),
        working_dir=working_dir,
    )

    all_rows = list(matched_targets) + list(independent_profile) + list(independent_holdouts)
    for rows in controls.values():
        all_rows.extend(rows)

    model_spec = spec["model"]
    embedder = LuarEmbedder(
        model_id=model_spec["model_id"],
        revision=model_spec["revision"],
        max_token_length=int(model_spec["max_token_length"]),
        batch_size=8,
        device="cpu",
    )
    embedder.embed_texts(_read_text(row) for row in all_rows)
    model_meta = embedder.metadata()
    config = embedder.model.config
    upstream = (
        getattr(config, "transformer_revision", None)
        or getattr(config, "upstream_transformer_revision", None)
    )
    model_meta["upstream_transformer_revision"] = upstream
    model_meta["config_revision_field"] = (
        "transformer_revision"
        if getattr(config, "transformer_revision", None)
        else "upstream_transformer_revision"
        if getattr(config, "upstream_transformer_revision", None)
        else None
    )
    expected_upstream = model_spec.get("upstream_backbone_revision_from_model_config")
    if expected_upstream and upstream != expected_upstream:
        raise TargetVerificationError(
            f"LUAR upstream revision mismatch: {upstream} != {expected_upstream}"
        )
    expected_embedding = int(model_spec["embedding_size"])
    if int(model_meta.get("embedding_size") or 0) not in {0, expected_embedding}:
        raise TargetVerificationError("LUAR embedding size mismatch")

    control_profiles = {
        author: _mean_profile(rows, embedder.cache) for author, rows in controls.items()
    }

    matched_predictions = []
    matched_folds = []
    for index, heldout in enumerate(matched_targets, start=1):
        joel_train = [row for row in matched_targets if row is not heldout]
        if len(joel_train) != int(spec["profile_documents_per_author"]):
            raise TargetVerificationError("matched Joel fold has wrong profile document count")
        profiles = {target: _mean_profile(joel_train, embedder.cache), **control_profiles}
        prediction = _score_target(
            heldout,
            profiles=profiles,
            authors=authors,
            target=target,
            hard_negative=hard,
            ordinary_controls=ordinary,
            embeddings=embedder.cache,
        )
        matched_predictions.append(prediction)
        matched_folds.append(
            {
                "fold_index": index,
                "heldout_sample_id": heldout.get("sample_id"),
                "target_profile_documents": [_public_meta(row) for row in joel_train],
                "profile_cosine_matrix": _profile_matrix(profiles, authors),
                "prediction": prediction,
            }
        )

    independent_profiles = {
        target: _mean_profile(independent_profile, embedder.cache),
        **control_profiles,
    }
    independent_predictions = [
        _score_target(
            row,
            profiles=independent_profiles,
            authors=authors,
            target=target,
            hard_negative=hard,
            ordinary_controls=ordinary,
            embeddings=embedder.cache,
        )
        for row in independent_holdouts
    ]

    receipt = {
        "schema_version": 1,
        "date": spec.get("date"),
        "status": "target-centric-four-author-exact50-verification-not-IER",
        "raw_or_canonical_prose_in_output": False,
        "embeddings_persisted_in_output": False,
        "method_decision": spec.get("method_decision"),
        "authors": authors,
        "roles": {
            target: "target-author",
            hard: "owner-identified-hard-negative",
            **{author: "ordinary-matched-control" for author in ordinary},
        },
        "word_budget_per_document": int(spec["word_budget_per_document"]),
        "profile_documents_per_author": int(spec["profile_documents_per_author"]),
        "model": model_meta,
        "unique_document_embeddings_computed": len(embedder.cache),
        "control_profile_selection": control_receipt,
        "matched_target_source_drift": drift,
        "strata": {
            "matched_dharma": {
                "design": spec["strata"]["matched_dharma"],
                "fold_count": len(matched_folds),
                "folds": matched_folds,
                "summary": _stratum_summary(
                    matched_predictions, authors=authors, target=target
                ),
            },
            "independent_tafka": {
                "design": spec["strata"]["independent_tafka"],
                "target_profile_documents": [_public_meta(row) for row in independent_profile],
                "profile_cosine_matrix": _profile_matrix(independent_profiles, authors),
                "predictions": independent_predictions,
                "summary": _stratum_summary(
                    independent_predictions, authors=authors, target=target
                ),
            },
        },
        "interpretation_guardrails": spec["interpretation"],
    }
    _assert_metadata_only(receipt)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt


def _assert_metadata_only(value: Any, *, path: str = "$") -> None:
    forbidden_keys = {
        "text",
        "raw_text",
        "canonical_text",
        "local_text_path",
        "embedding",
        "embeddings",
        "vector",
        "vectors",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in forbidden_keys:
                raise TargetVerificationError(f"forbidden output key at {path}: {key}")
            _assert_metadata_only(child, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_metadata_only(child, path=f"{path}[{index}]")


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m pangram_lab.luar_target_verification"
    )
    parser.add_argument(
        "spec",
        nargs="?",
        default="state/IDIOLECT-FOUR-AUTHOR-TARGET-VERIFICATION-SPEC-2026-08-19.json",
    )
    parser.add_argument("--dharma-manifest", required=True)
    parser.add_argument("--tafka-manifest", required=True)
    parser.add_argument(
        "--working-dir",
        default=".local/idiolect-corpus/four-author-target-verification",
    )
    parser.add_argument(
        "--out",
        default=".local/idiolect-corpus/four-author-target-verification-result.json",
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
