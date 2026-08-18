from __future__ import annotations

import collections
import json
from pathlib import Path

from .surface_svm_pilot import (
    assert_no_source_group_leakage,
    fit_and_evaluate,
    group_bootstrap_accuracy,
    select_largest_documents,
)


def _metadata_row(row: dict) -> dict:
    return {
        "sample_id": row.get("sample_id"),
        "source_group": row.get("source_group"),
        "speaker": row.get("speaker"),
        "word_count": int(row.get("word_count", 0)),
        "canonical_sha256": row.get("canonical_sha256"),
    }


def _aggregate_predictions(predictions: list[dict], authors: list[str], *, iterations: int, seed: int) -> dict:
    try:
        from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("matched-platform surface SVM CV requires scikit-learn") from exc

    actual = [str(row["actual"]) for row in predictions]
    predicted = [str(row["predicted"]) for row in predictions]
    per_author = {}
    for author in authors:
        indices = [idx for idx, value in enumerate(actual) if value == author]
        correct = sum(1 for idx in indices if actual[idx] == predicted[idx])
        per_author[author] = {
            "documents": len(indices),
            "correct": correct,
            "accuracy": round(correct / len(indices), 6) if indices else None,
        }

    return {
        "accuracy": round(float(accuracy_score(actual, predicted)), 6),
        "balanced_accuracy": round(float(balanced_accuracy_score(actual, predicted)), 6),
        "macro_f1": round(
            float(f1_score(actual, predicted, labels=authors, average="macro", zero_division=0)),
            6,
        ),
        "per_author": per_author,
        "confusion_matrix": {
            "labels": authors,
            "rows_actual_columns_predicted": confusion_matrix(actual, predicted, labels=authors).tolist(),
        },
        "group_bootstrap_accuracy_95pct": group_bootstrap_accuracy(
            predictions,
            iterations=iterations,
            seed=seed,
        ),
        "predictions": predictions,
    }


def run_matched_cv(
    spec_path: Path,
    *,
    matched_manifest_path: Path,
    supplement_manifest_path: Path,
    control_manifest_path: Path,
    out_path: Path,
) -> dict:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    authors = [str(value) for value in spec["authors"]]
    matched = json.loads(matched_manifest_path.read_text(encoding="utf-8"))
    supplement = json.loads(supplement_manifest_path.read_text(encoding="utf-8"))
    controls = json.loads(control_manifest_path.read_text(encoding="utf-8"))

    if matched.get("errors"):
        raise ValueError(f"matched acquisition errors: {matched['errors']}")
    if supplement.get("errors"):
        raise ValueError(f"supplement acquisition errors: {supplement['errors']}")
    if controls.get("errors"):
        raise ValueError(f"control acquisition errors: {controls['errors']}")

    matched_rows = matched.get("results", [])
    supplement_ids = set(spec["joel_supplement_sample_ids"])
    supplement_rows = [
        row for row in supplement.get("results", []) if row.get("sample_id") in supplement_ids
    ]
    if {row.get("sample_id") for row in supplement_rows} != supplement_ids:
        missing = sorted(supplement_ids - {row.get("sample_id") for row in supplement_rows})
        raise ValueError(f"missing Joel supplement samples: {missing}")
    if any(row.get("speaker") and row.get("speaker") != "Joel Rosenblum" for row in supplement_rows):
        raise ValueError("Joel supplement contains a non-Joel speaker row")
    for row in supplement_rows:
        row["speaker"] = "Joel Rosenblum"

    n_train = int(spec["fold_training"]["documents_per_author"])
    control_training: dict[str, list[dict]] = {}
    for author in authors:
        if author == "Joel Rosenblum":
            continue
        selected = select_largest_documents(controls.get("results", []), author, n_train)
        if len(selected) != n_train:
            raise ValueError(f"expected {n_train} control documents for {author}, got {len(selected)}")
        control_training[author] = selected

    held_out_groups = [str(value) for value in spec["held_out_source_groups"]]
    matched_group_set = {str(row.get("source_group")) for row in matched_rows}
    missing_groups = [group for group in held_out_groups if group not in matched_group_set]
    if missing_groups:
        raise ValueError(f"held-out source groups missing from matched manifest: {missing_groups}")

    model_specs = spec["models"]
    fold_records: list[dict] = []
    model_predictions: dict[str, list[dict]] = {row["model_id"]: [] for row in model_specs}
    model_meta: dict[str, dict] = {}

    for fold_index, held_out_group in enumerate(held_out_groups, start=1):
        test_rows = [row for row in matched_rows if str(row.get("source_group")) == held_out_group]
        if len({str(row.get("speaker")) for row in test_rows}) < 2:
            raise ValueError(f"held-out group lacks at least two authors: {held_out_group}")

        joel_train = [
            row
            for row in matched_rows
            if row.get("speaker") == "Joel Rosenblum"
            and str(row.get("source_group")) != held_out_group
        ] + [dict(row) for row in supplement_rows]
        if len(joel_train) != n_train:
            raise ValueError(
                f"fold {held_out_group}: expected {n_train} Joel training documents, got {len(joel_train)}"
            )

        train_rows = list(joel_train)
        for author in authors:
            if author == "Joel Rosenblum":
                continue
            train_rows.extend(control_training[author])

        counts = collections.Counter(str(row.get("speaker")) for row in train_rows)
        if any(counts[author] != n_train for author in authors):
            raise ValueError(f"fold {held_out_group}: unbalanced training classes: {dict(counts)}")
        assert_no_source_group_leakage(train_rows, test_rows)

        fold_record = {
            "fold_index": fold_index,
            "held_out_source_group": held_out_group,
            "test_documents": [_metadata_row(row) for row in test_rows],
            "training": {
                author: {
                    "document_count": sum(1 for row in train_rows if row.get("speaker") == author),
                    "total_words": sum(
                        int(row.get("word_count", 0))
                        for row in train_rows
                        if row.get("speaker") == author
                    ),
                    "source_groups": sorted(
                        str(row.get("source_group"))
                        for row in train_rows
                        if row.get("speaker") == author
                    ),
                }
                for author in authors
            },
            "models": {},
        }

        for model_spec in model_specs:
            model_id = str(model_spec["model_id"])
            result = fit_and_evaluate(
                train_rows,
                test_rows,
                authors=authors,
                feature_mode=str(model_spec["feature_mode"]),
                C=float(model_spec.get("C", 1.0)),
                bootstrap_iterations=1,
                bootstrap_seed=fold_index,
            )
            fold_record["models"][model_id] = {
                "accuracy": result["accuracy"],
                "balanced_accuracy": result["balanced_accuracy"],
                "macro_f1": result["macro_f1"],
                "per_author": result["per_author"],
            }
            model_predictions[model_id].extend(result["predictions"])
            model_meta.setdefault(
                model_id,
                {
                    "feature_mode": result["feature_mode"],
                    "classifier": result["classifier"],
                    "C": result["C"],
                    "sklearn_version": result["sklearn_version"],
                    "vectorizer_defaults": result["vectorizer_defaults"],
                },
            )

        fold_records.append(fold_record)

    bootstrap = spec["evaluation"]["group_bootstrap_accuracy"]
    aggregate_models = {}
    for model_spec in model_specs:
        model_id = str(model_spec["model_id"])
        aggregate = _aggregate_predictions(
            model_predictions[model_id],
            authors,
            iterations=int(bootstrap["iterations"]),
            seed=int(bootstrap["seed"]),
        )
        aggregate_models[model_id] = {**model_meta[model_id], **aggregate}

    all_test_predictions = next(iter(model_predictions.values())) if model_predictions else []
    if len(all_test_predictions) != 10:
        raise ValueError(f"expected 10 aggregate held-out predictions, got {len(all_test_predictions)}")

    receipt = {
        "schema_version": 1,
        "raw_or_canonical_prose_in_output": False,
        "pilot_status": "matched-platform-leave-one-source-group-out-not-IER",
        "authors": authors,
        "chance_accuracy": spec["interpretation"]["chance_accuracy"],
        "fold_count": len(fold_records),
        "documents_per_author_per_fold": n_train,
        "source_group_leakage": False,
        "folds": fold_records,
        "aggregate_models": aggregate_models,
        "interpretation_guardrails": spec["interpretation"],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="python -m pangram_lab.surface_svm_matched_cv")
    parser.add_argument(
        "spec",
        nargs="?",
        default="state/IDIOLECT-SURFACE-SVM-MATCHED-PLATFORM-CV-SPEC-2026-08-18.json",
    )
    parser.add_argument("--matched-manifest", required=True)
    parser.add_argument("--supplement-manifest", required=True)
    parser.add_argument("--control-manifest", required=True)
    parser.add_argument("--out", default=".local/idiolect-corpus/surface-svm-matched-cv-receipt.json")
    args = parser.parse_args(argv)

    try:
        result = run_matched_cv(
            Path(args.spec),
            matched_manifest_path=Path(args.matched_manifest),
            supplement_manifest_path=Path(args.supplement_manifest),
            control_manifest_path=Path(args.control_manifest),
            out_path=Path(args.out),
        )
    except Exception as exc:
        print(str(exc))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
