from __future__ import annotations

import collections
import json
from pathlib import Path

from .idiolect import _content_light_features, _cosine, _mean_unit
from .luar_matched_pilot import _equal50_folds, _whole_folds
from .surface_svm_pilot import group_bootstrap_accuracy


def _read_text(row: dict) -> str:
    return Path(str(row["local_text_path"])).read_text(encoding="utf-8").strip()


def nearest_content_light_predictions(
    train_rows: list[dict],
    test_rows: list[dict],
    *,
    authors: list[str],
) -> list[dict]:
    profiles = {}
    for author in authors:
        vectors = [
            _content_light_features(_read_text(row))
            for row in train_rows
            if str(row.get("speaker")) == author
        ]
        if not vectors:
            raise ValueError(f"no content-light training vectors for author: {author}")
        profiles[author] = _mean_unit(vectors)
        if not profiles[author]:
            raise ValueError(f"empty content-light profile for author: {author}")

    predictions = []
    for row in test_rows:
        vector = _content_light_features(_read_text(row))
        scores = {author: _cosine(vector, profiles[author]) for author in authors}
        best_author = authors[0]
        best_score = scores[best_author]
        for author in authors[1:]:
            if scores[author] > best_score:
                best_author = author
                best_score = scores[author]
        actual = str(row.get("speaker"))
        predictions.append(
            {
                "sample_id": row.get("sample_id"),
                "source_group": row.get("source_group"),
                "actual": actual,
                "predicted": best_author,
                "correct": actual == best_author,
                "cosine_scores": {
                    author: round(float(scores[author]), 6) for author in authors
                },
            }
        )
    return predictions


def _metrics(predictions: list[dict], authors: list[str], *, iterations: int, seed: int) -> dict:
    if not predictions:
        raise ValueError("at least one prediction is required")
    label_index = {author: idx for idx, author in enumerate(authors)}
    matrix = [[0 for _ in authors] for _ in authors]
    per_author = {}
    correct_total = 0

    for row in predictions:
        actual = str(row["actual"])
        predicted = str(row["predicted"])
        if actual not in label_index or predicted not in label_index:
            raise ValueError(f"unknown author label in prediction: {actual!r}/{predicted!r}")
        matrix[label_index[actual]][label_index[predicted]] += 1
        if actual == predicted:
            correct_total += 1

    recalls = []
    f1s = []
    for idx, author in enumerate(authors):
        tp = matrix[idx][idx]
        actual_total = sum(matrix[idx])
        predicted_total = sum(matrix[row][idx] for row in range(len(authors)))
        recall = tp / actual_total if actual_total else 0.0
        precision = tp / predicted_total if predicted_total else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
        recalls.append(recall)
        f1s.append(f1)
        per_author[author] = {
            "documents": actual_total,
            "correct": tp,
            "accuracy": round(recall, 6) if actual_total else None,
        }

    accuracy = correct_total / len(predictions)
    return {
        "accuracy": round(accuracy, 6),
        "balanced_accuracy": round(sum(recalls) / len(authors), 6),
        "macro_f1": round(sum(f1s) / len(authors), 6),
        "per_author": per_author,
        "confusion_matrix": {
            "labels": authors,
            "rows_actual_columns_predicted": matrix,
        },
        "group_bootstrap_accuracy_95pct": group_bootstrap_accuracy(
            predictions,
            iterations=iterations,
            seed=seed,
        ),
        "predictions": predictions,
    }


def _run_condition(
    name: str,
    folds,
    *,
    authors: list[str],
    bootstrap_iterations: int,
    bootstrap_seed: int,
) -> dict:
    aggregate_predictions = []
    fold_receipts = []
    for fold_index, (held_out_group, train_rows, test_rows) in enumerate(folds, start=1):
        predictions = nearest_content_light_predictions(
            train_rows,
            test_rows,
            authors=authors,
        )
        aggregate_predictions.extend(predictions)
        fold_metrics = _metrics(predictions, authors, iterations=1, seed=fold_index)
        fold_receipts.append(
            {
                "fold_index": fold_index,
                "held_out_source_group": held_out_group,
                "training_document_counts": {
                    author: sum(
                        1 for row in train_rows if str(row.get("speaker")) == author
                    )
                    for author in authors
                },
                "held_out_document_count": len(test_rows),
                "accuracy": fold_metrics["accuracy"],
                "predictions": predictions,
            }
        )
    if len(aggregate_predictions) != 10:
        raise ValueError(f"{name}: expected 10 aggregate predictions, got {len(aggregate_predictions)}")
    aggregate = _metrics(
        aggregate_predictions,
        authors,
        iterations=bootstrap_iterations,
        seed=bootstrap_seed,
    )
    return {
        "condition": name,
        "fold_count": len(fold_receipts),
        "folds": fold_receipts,
        "aggregate": aggregate,
    }


def run_content_light_control(
    spec_path: Path,
    *,
    matched_manifest_path: Path,
    supplement_manifest_path: Path,
    control_manifest_path: Path,
    working_dir: Path,
    out_path: Path,
) -> dict:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    matched = json.loads(matched_manifest_path.read_text(encoding="utf-8"))
    supplement = json.loads(supplement_manifest_path.read_text(encoding="utf-8"))
    controls = json.loads(control_manifest_path.read_text(encoding="utf-8"))
    for label, data in (
        ("matched", matched),
        ("supplement", supplement),
        ("control", controls),
    ):
        if data.get("errors"):
            raise ValueError(f"{label} acquisition errors: {data['errors']}")

    authors = [str(value) for value in spec["authors"]]
    fold_spec = {
        "authors": authors,
        "held_out_source_groups": spec["held_out_source_groups"],
        "conditions": spec["conditions"],
    }
    whole = _whole_folds(
        fold_spec,
        matched.get("results", []),
        supplement.get("results", []),
        controls.get("results", []),
    )
    equal50 = _equal50_folds(
        fold_spec,
        matched.get("results", []),
        supplement.get("results", []),
        controls.get("results", []),
        working_dir=working_dir / "equal50",
    )

    bootstrap = spec["evaluation"]["group_bootstrap_accuracy"]
    receipt = {
        "schema_version": 1,
        "raw_or_canonical_prose_in_output": False,
        "pilot_status": "content-light-matched-control-not-IER",
        "authors": authors,
        "source_group_leakage": False,
        "algorithm": spec["algorithm"],
        "conditions": {
            "whole_document": _run_condition(
                "whole_document",
                whole,
                authors=authors,
                bootstrap_iterations=int(bootstrap["iterations"]),
                bootstrap_seed=int(bootstrap["seed"]),
            ),
            "equal_50_word": _run_condition(
                "equal_50_word",
                equal50,
                authors=authors,
                bootstrap_iterations=int(bootstrap["iterations"]),
                bootstrap_seed=int(bootstrap["seed"]) + 1,
            ),
        },
        "interpretation_guardrails": spec["interpretation"],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="python -m pangram_lab.content_light_matched_control")
    parser.add_argument(
        "spec",
        nargs="?",
        default="state/IDIOLECT-CONTENT-LIGHT-MATCHED-CONTROL-SPEC-2026-08-18.json",
    )
    parser.add_argument("--matched-manifest", required=True)
    parser.add_argument("--supplement-manifest", required=True)
    parser.add_argument("--control-manifest", required=True)
    parser.add_argument("--working-dir", default=".local/idiolect-corpus/content-light-control")
    parser.add_argument("--out", default=".local/idiolect-corpus/content-light-control-receipt.json")
    args = parser.parse_args(argv)

    try:
        receipt = run_content_light_control(
            Path(args.spec),
            matched_manifest_path=Path(args.matched_manifest),
            supplement_manifest_path=Path(args.supplement_manifest),
            control_manifest_path=Path(args.control_manifest),
            working_dir=Path(args.working_dir),
            out_path=Path(args.out),
        )
    except Exception as exc:
        print(str(exc))
        return 1
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
