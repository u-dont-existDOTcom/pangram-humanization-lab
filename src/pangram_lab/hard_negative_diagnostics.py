from __future__ import annotations

import collections
import json
import math
import sys
from pathlib import Path
from typing import Any

TARGET_ROLE = "target-author"
HARD_NEGATIVE_ROLE = "owner-identified-hard-negative"
ORDINARY_CONTROL_ROLE = "ordinary-matched-control"
ACTIVE_STATUS = "active"


class HardNegativeDiagnosticError(ValueError):
    pass


def _round(value: float | None) -> float | None:
    return None if value is None else round(float(value), 6)


def _validate_role_spec(spec: dict[str, Any]) -> dict[str, Any]:
    if spec.get("schema_version") != 1:
        raise HardNegativeDiagnosticError("role spec schema_version must be 1")
    rows = spec.get("active_authors")
    if not isinstance(rows, list) or not rows:
        raise HardNegativeDiagnosticError("active_authors must be a non-empty list")

    names: list[str] = []
    role_by_author: dict[str, str] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise HardNegativeDiagnosticError(f"active_authors[{index}] must be an object")
        name = str(row.get("author") or "").strip()
        role = str(row.get("role") or "").strip()
        status = str(row.get("status") or ACTIVE_STATUS).strip()
        if not name or not role:
            raise HardNegativeDiagnosticError(
                f"active_authors[{index}] requires author and role"
            )
        if status != ACTIVE_STATUS:
            continue
        if name in role_by_author:
            raise HardNegativeDiagnosticError(f"duplicate active author: {name}")
        names.append(name)
        role_by_author[name] = role

    targets = [name for name in names if role_by_author[name] == TARGET_ROLE]
    hard_negatives = [
        name for name in names if role_by_author[name] == HARD_NEGATIVE_ROLE
    ]
    ordinary_controls = [
        name for name in names if role_by_author[name] == ORDINARY_CONTROL_ROLE
    ]
    if len(targets) != 1:
        raise HardNegativeDiagnosticError(
            f"expected exactly one active {TARGET_ROLE}, got {targets}"
        )
    if not hard_negatives:
        raise HardNegativeDiagnosticError("at least one active hard negative is required")
    if not ordinary_controls:
        raise HardNegativeDiagnosticError(
            "at least one active ordinary matched control is required"
        )

    minimum = spec.get("minimum_evidence") or {}
    return {
        "target": targets[0],
        "hard_negatives": hard_negatives,
        "ordinary_controls": ordinary_controls,
        "active_authors": names,
        "role_by_author": role_by_author,
        "minimum_ordinary_controls": int(
            minimum.get("ordinary_matched_controls_before_rewrite_degradation_claim", 2)
        ),
        "minimum_target_holdout_documents": int(
            minimum.get("minimum_target_holdout_documents", 4)
        ),
        "minimum_hard_negative_holdout_documents": int(
            minimum.get("minimum_hard_negative_holdout_documents", 3)
        ),
    }


def _validate_prediction(row: dict[str, Any], active_authors: list[str]) -> None:
    actual = str(row.get("actual") or "").strip()
    scores = row.get("cosine_scores")
    if not actual:
        raise HardNegativeDiagnosticError("prediction row requires actual")
    if not isinstance(scores, dict):
        raise HardNegativeDiagnosticError("prediction row requires cosine_scores")
    missing = [author for author in active_authors if author not in scores]
    if missing:
        raise HardNegativeDiagnosticError(
            f"prediction row missing scores for active authors: {missing}"
        )
    for author in active_authors:
        value = scores[author]
        if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise HardNegativeDiagnosticError(
                f"prediction score for {author} must be finite numeric"
            )


def _winner(scores: dict[str, Any], members: list[str], order: list[str]) -> tuple[str, float, float | None]:
    if not members:
        raise HardNegativeDiagnosticError("candidate set is empty")
    ordered = [author for author in order if author in members]
    if set(ordered) != set(members):
        raise HardNegativeDiagnosticError("candidate-set member missing from author order")
    ranked = sorted(
        ((author, float(scores[author]), order.index(author)) for author in ordered),
        key=lambda item: (-item[1], item[2]),
    )
    best_author, best_score, _ = ranked[0]
    runner_up = ranked[1][1] if len(ranked) > 1 else None
    return best_author, best_score, None if runner_up is None else best_score - runner_up


def _set_metrics(
    rows: list[dict[str, Any]],
    *,
    members: list[str],
    author_order: list[str],
    target: str,
    set_id: str,
    interpretation_role: str,
    may_not_be_headline_result: bool = False,
) -> dict[str, Any]:
    eligible = [row for row in rows if str(row.get("actual")) in members]
    labels = [author for author in author_order if author in members]
    matrix = {actual: collections.Counter() for actual in labels}
    correct = 0
    per_author_total = collections.Counter()
    per_author_correct = collections.Counter()
    predictions: list[dict[str, Any]] = []

    for row in eligible:
        actual = str(row["actual"])
        predicted, winning_score, winning_margin = _winner(
            row["cosine_scores"], members, author_order
        )
        is_correct = actual == predicted
        correct += int(is_correct)
        per_author_total[actual] += 1
        per_author_correct[actual] += int(is_correct)
        matrix[actual][predicted] += 1
        predictions.append(
            {
                "sample_id": row.get("sample_id"),
                "source_group": row.get("source_group"),
                "actual": actual,
                "predicted": predicted,
                "correct": is_correct,
                "winning_score": _round(winning_score),
                "winning_margin_over_runner_up": _round(winning_margin),
            }
        )

    documents = len(eligible)
    per_author = {}
    author_accuracies: list[float] = []
    for author in labels:
        total = int(per_author_total[author])
        author_correct = int(per_author_correct[author])
        accuracy = author_correct / total if total else None
        if accuracy is not None:
            author_accuracies.append(accuracy)
        per_author[author] = {
            "documents": total,
            "correct": author_correct,
            "accuracy": _round(accuracy),
        }

    return {
        "set_id": set_id,
        "interpretation_role": interpretation_role,
        "may_not_be_headline_result": may_not_be_headline_result,
        "candidate_members": labels,
        "documents": documents,
        "excluded_documents_with_actual_outside_set": len(rows) - documents,
        "accuracy": _round(correct / documents if documents else None),
        "balanced_accuracy": _round(
            sum(author_accuracies) / len(author_accuracies)
            if author_accuracies
            else None
        ),
        "target_accuracy": per_author.get(target, {}).get("accuracy"),
        "per_author": per_author,
        "confusion_matrix_labels": labels,
        "confusion_matrix_rows_actual_columns_predicted": [
            [int(matrix[actual][predicted]) for predicted in labels]
            for actual in labels
        ],
        "predictions": predictions,
    }


def _target_margin_rows(
    rows: list[dict[str, Any]],
    *,
    target: str,
    hard_negatives: list[str],
    ordinary_controls: list[str],
    active_authors: list[str],
) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        if str(row.get("actual")) != target:
            continue
        scores = {author: float(row["cosine_scores"][author]) for author in active_authors}
        ranked = sorted(
            active_authors,
            key=lambda author: (-scores[author], active_authors.index(author)),
        )
        full_winner = ranked[0]
        best_ordinary = max(
            ordinary_controls,
            key=lambda author: (scores[author], -active_authors.index(author)),
        )
        hard_rows = []
        for hard in hard_negatives:
            restricted_winner, _, _ = _winner(
                scores, [target, hard], active_authors
            )
            hard_rows.append(
                {
                    "author": hard,
                    "score": _round(scores[hard]),
                    "target_minus_hard_negative_margin": _round(
                        scores[target] - scores[hard]
                    ),
                    "restricted_winner": restricted_winner,
                }
            )
        ordinary_winner, _, _ = _winner(
            scores, [target, *ordinary_controls], active_authors
        )
        output.append(
            {
                "sample_id": row.get("sample_id"),
                "source_group": row.get("source_group"),
                "target_score": _round(scores[target]),
                "target_rank": ranked.index(target) + 1,
                "full_candidate_set_winner": full_winner,
                "hard_negative_comparisons": hard_rows,
                "best_ordinary_control": best_ordinary,
                "best_ordinary_control_score": _round(scores[best_ordinary]),
                "target_minus_best_ordinary_control_margin": _round(
                    scores[target] - scores[best_ordinary]
                ),
                "target_vs_ordinary_controls_restricted_winner": ordinary_winner,
            }
        )
    return output


def analyze_condition(
    rows: list[dict[str, Any]], spec: dict[str, Any]
) -> dict[str, Any]:
    roles = _validate_role_spec(spec)
    for row in rows:
        if not isinstance(row, dict):
            raise HardNegativeDiagnosticError("prediction rows must be objects")
        _validate_prediction(row, roles["active_authors"])

    target = roles["target"]
    active = roles["active_authors"]
    hard = roles["hard_negatives"]
    ordinary = roles["ordinary_controls"]

    hard_sets = {
        author: _set_metrics(
            rows,
            members=[target, author],
            author_order=active,
            target=target,
            set_id=f"target-vs-hard-negative:{author}",
            interpretation_role="hard-neighbor discrimination diagnostic",
        )
        for author in hard
    }
    ordinary_set = _set_metrics(
        rows,
        members=[target, *ordinary],
        author_order=active,
        target=target,
        set_id="target-vs-ordinary-controls",
        interpretation_role="ordinary same-topic/platform discrimination diagnostic",
    )
    without_hard = _set_metrics(
        rows,
        members=[author for author in active if author not in hard],
        author_order=active,
        target=target,
        set_id="without-hard-negative-sensitivity",
        interpretation_role="candidate-set sensitivity analysis only",
        may_not_be_headline_result=True,
    )
    full = _set_metrics(
        rows,
        members=active,
        author_order=active,
        target=target,
        set_id="full-active-candidate-set",
        interpretation_role="primary closed-set diagnostic",
    )

    direct_target_to_hard = collections.Counter()
    direct_hard_to_target = collections.Counter()
    for prediction in full["predictions"]:
        actual = prediction["actual"]
        predicted = prediction["predicted"]
        if actual == target and predicted in hard:
            direct_target_to_hard[predicted] += 1
        if actual in hard and predicted == target:
            direct_hard_to_target[actual] += 1

    target_docs = sum(1 for row in rows if str(row.get("actual")) == target)
    hard_docs = {
        author: sum(1 for row in rows if str(row.get("actual")) == author)
        for author in hard
    }
    blockers = []
    if len(ordinary) < roles["minimum_ordinary_controls"]:
        blockers.append(
            f"only {len(ordinary)} active ordinary matched control(s); requires "
            f"{roles['minimum_ordinary_controls']}"
        )
    if target_docs < roles["minimum_target_holdout_documents"]:
        blockers.append(
            f"only {target_docs} target holdout documents; requires "
            f"{roles['minimum_target_holdout_documents']}"
        )
    for author, count in hard_docs.items():
        if count < roles["minimum_hard_negative_holdout_documents"]:
            blockers.append(
                f"only {count} hard-negative holdout documents for {author}; requires "
                f"{roles['minimum_hard_negative_holdout_documents']}"
            )

    return {
        "document_count": len(rows),
        "target_author": target,
        "hard_negative_authors": hard,
        "ordinary_matched_controls": ordinary,
        "full_active_candidate_set": full,
        "target_vs_hard_negatives": hard_sets,
        "target_vs_ordinary_controls": ordinary_set,
        "without_hard_negative_sensitivity": without_hard,
        "target_document_margins": _target_margin_rows(
            rows,
            target=target,
            hard_negatives=hard,
            ordinary_controls=ordinary,
            active_authors=active,
        ),
        "direct_full_set_confusions": {
            "target_to_hard_negative": dict(sorted(direct_target_to_hard.items())),
            "hard_negative_to_target": dict(sorted(direct_hard_to_target.items())),
        },
        "rewrite_degradation_interpretation_ready": not blockers,
        "readiness_blockers": blockers,
        "interpretation_guardrail": (
            "A target-to-hard-negative winner flip is not independently an "
            "idiolect-erasure verdict. Interpret hard-negative, ordinary-control, "
            "and full-set results separately."
        ),
    }


def analyze_prediction_bundle(
    bundle: dict[str, Any], spec: dict[str, Any]
) -> dict[str, Any]:
    conditions = bundle.get("conditions")
    if not isinstance(conditions, dict) or not conditions:
        raise HardNegativeDiagnosticError(
            "prediction bundle requires non-empty conditions object"
        )
    output = {}
    for condition, rows in conditions.items():
        if not isinstance(rows, list):
            raise HardNegativeDiagnosticError(
                f"condition {condition} predictions must be a list"
            )
        output[str(condition)] = analyze_condition(rows, spec)
    return {
        "schema_version": 1,
        "status": "hard-negative-stratified-diagnostic-not-IER-not-calibrated",
        "raw_or_canonical_prose_in_output": False,
        "conditions": output,
        "forbidden_claims": spec.get("forbidden_claims", []),
    }


def _assert_metadata_only(value: Any, *, path: str = "$") -> None:
    forbidden_keys = {
        "text",
        "raw_text",
        "canonical_text",
        "local_text_path",
        "embedding",
        "embeddings",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in forbidden_keys:
                raise HardNegativeDiagnosticError(
                    f"forbidden output/input key at {path}: {key}"
                )
            _assert_metadata_only(child, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_metadata_only(child, path=f"{path}[{index}]")


def run(
    spec_path: Path,
    prediction_bundle_path: Path,
    *,
    out_path: Path,
) -> dict[str, Any]:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    bundle = json.loads(prediction_bundle_path.read_text(encoding="utf-8"))
    _assert_metadata_only(bundle)
    result = analyze_prediction_bundle(bundle, spec)
    _assert_metadata_only(result)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m pangram_lab.hard_negative_diagnostics"
    )
    parser.add_argument(
        "spec",
        nargs="?",
        default="state/IDIOLECT-CONTROL-AUTHOR-ROLE-SPEC-2026-08-18.json",
    )
    parser.add_argument("predictions")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    try:
        result = run(
            Path(args.spec),
            Path(args.predictions),
            out_path=Path(args.out),
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
