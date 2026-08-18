from __future__ import annotations

import collections
import json
from pathlib import Path

from .surface_svm_pilot import (
    assert_no_source_group_leakage,
    fit_and_evaluate,
    group_bootstrap_accuracy,
    select_matched_test,
)


MODEL_MODES = [
    ("paper-described-char2-4-word1-2-linear-svm", "char+word"),
    ("char2-4-only-sensitivity", "char"),
    ("word1-2-only-sensitivity", "word"),
]


def build_leave_one_group_out_folds(
    rows: list[dict],
    *,
    authors: list[str],
    min_authors_per_group: int = 2,
) -> list[dict]:
    """Build deterministic matched-platform leave-one-source-group-out folds.

    Only source groups containing at least ``min_authors_per_group`` are eligible.
    Every eligible source group becomes the held-out fold exactly once. All
    remaining eligible groups become training data for that fold. A fold is
    invalid if removing its held-out group leaves any candidate author without
    training text.
    """
    matched = select_matched_test(rows, min_authors_per_group=min_authors_per_group)
    groups = sorted({str(row["source_group"]) for row in matched if row.get("source_group")})
    if len(groups) < 2:
        raise ValueError("leave-one-group-out evaluation requires at least two matched source groups")

    allowed_authors = set(authors)
    unexpected = sorted({str(row.get("speaker")) for row in matched if row.get("speaker")} - allowed_authors)
    if unexpected:
        raise ValueError(f"unexpected authors in matched tranche: {unexpected}")

    folds: list[dict] = []
    for held_out_group in groups:
        test_rows = [row for row in matched if str(row.get("source_group")) == held_out_group]
        train_rows = [row for row in matched if str(row.get("source_group")) != held_out_group]
        train_authors = {str(row.get("speaker")) for row in train_rows if row.get("speaker")}
        missing = sorted(allowed_authors - train_authors)
        if missing:
            raise ValueError(
                f"held-out source group {held_out_group} leaves authors without training text: {missing}"
            )
        assert_no_source_group_leakage(train_rows, test_rows)
        folds.append(
            {
                "held_out_source_group": held_out_group,
                "train_rows": sorted(
                    train_rows,
                    key=lambda row: (str(row.get("source_group")), str(row.get("speaker"))),
                ),
                "test_rows": sorted(test_rows, key=lambda row: str(row.get("speaker"))),
            }
        )
    return folds


def _metadata_row(row: dict) -> dict:
    return {
        "sample_id": row.get("sample_id"),
        "source_group": row.get("source_group"),
        "speaker": row.get("speaker"),
        "word_count": int(row.get("word_count", 0)),
        "canonical_sha256": row.get("canonical_sha256"),
    }


def _author_counts(rows: list[dict], authors: list[str]) -> dict[str, int]:
    counts = collections.Counter(str(row.get("speaker")) for row in rows if row.get("speaker"))
    return {author: int(counts.get(author, 0)) for author in authors}


def _aggregate_predictions(
    predictions: list[dict],
    *,
    authors: list[str],
    bootstrap_iterations: int,
    bootstrap_seed: int,
) -> dict:
    try:
        from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score
    except ImportError as exc:  # pragma: no cover - optional research environment
        raise RuntimeError("matched-platform SVM pilot requires scikit-learn") from exc

    y_true = [str(row["actual"]) for row in predictions]
    y_pred = [str(row["predicted"]) for row in predictions]
    per_author = {}
    for author in authors:
        indices = [idx for idx, actual in enumerate(y_true) if actual == author]
        correct = sum(1 for idx in indices if y_true[idx] == y_pred[idx])
        per_author[author] = {
            "documents": len(indices),
            "correct": correct,
            "accuracy": round(correct / len(indices), 6) if indices else None,
        }

    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 6),
        "balanced_accuracy": round(float(balanced_accuracy_score(y_true, y_pred)), 6),
        "macro_f1": round(
            float(f1_score(y_true, y_pred, labels=authors, average="macro", zero_division=0)),
            6,
        ),
        "per_author": per_author,
        "confusion_matrix": {
            "labels": authors,
            "rows_actual_columns_predicted": confusion_matrix(y_true, y_pred, labels=authors).tolist(),
        },
        "group_bootstrap_accuracy_95pct": group_bootstrap_accuracy(
            predictions,
            iterations=bootstrap_iterations,
            seed=bootstrap_seed,
        ),
        "predictions": predictions,
    }


def run_logo_pilot(manifest_path: Path, spec_path: Path, out_path: Path) -> dict:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("errors"):
        raise ValueError(f"matched Dharma acquisition contains errors: {manifest['errors']}")

    authors = [str(value) for value in spec["authors"]]
    selection = spec["selection"]
    min_authors = int(selection["min_authors_per_group"])
    rows = manifest.get("results", [])
    matched = select_matched_test(rows, min_authors_per_group=min_authors)
    groups = sorted({str(row.get("source_group")) for row in matched if row.get("source_group")})
    if len(matched) != int(selection["expected_documents"]):
        raise ValueError(
            f"expected {selection['expected_documents']} matched documents, got {len(matched)}"
        )
    if len(groups) != int(selection["expected_source_groups"]):
        raise ValueError(
            f"expected {selection['expected_source_groups']} matched source groups, got {len(groups)}"
        )

    folds = build_leave_one_group_out_folds(
        rows,
        authors=authors,
        min_authors_per_group=min_authors,
    )
    if len(folds) != len(groups):
        raise ValueError("each matched source group must be held out exactly once")

    bootstrap = spec["evaluation"]["group_bootstrap_accuracy"]
    model_outputs: dict[str, dict] = {}
    for model_id, feature_mode in MODEL_MODES:
        all_predictions: list[dict] = []
        fold_outputs: list[dict] = []
        sklearn_versions: set[str] = set()
        for fold in folds:
            result = fit_and_evaluate(
                fold["train_rows"],
                fold["test_rows"],
                authors=authors,
                feature_mode=feature_mode,
                C=1.0,
                bootstrap_iterations=1,
                bootstrap_seed=int(bootstrap["seed"]),
            )
            sklearn_versions.add(str(result["sklearn_version"]))
            all_predictions.extend(result["predictions"])
            fold_outputs.append(
                {
                    "held_out_source_group": fold["held_out_source_group"],
                    "train_documents": len(fold["train_rows"]),
                    "test_documents": len(fold["test_rows"]),
                    "train_documents_per_author": _author_counts(fold["train_rows"], authors),
                    "test_documents_per_author": _author_counts(fold["test_rows"], authors),
                    "accuracy": result["accuracy"],
                    "balanced_accuracy": result["balanced_accuracy"],
                    "macro_f1": result["macro_f1"],
                }
            )

        if len(sklearn_versions) != 1:
            raise ValueError(f"inconsistent sklearn versions across folds: {sorted(sklearn_versions)}")
        aggregate = _aggregate_predictions(
            all_predictions,
            authors=authors,
            bootstrap_iterations=int(bootstrap["iterations"]),
            bootstrap_seed=int(bootstrap["seed"]),
        )
        model_outputs[model_id] = {
            "feature_mode": feature_mode,
            "classifier": "LinearSVC",
            "C": 1.0,
            "sklearn_version": next(iter(sklearn_versions)),
            "folds": fold_outputs,
            **aggregate,
        }

    receipt = {
        "schema_version": 1,
        "raw_or_canonical_prose_in_output": False,
        "pilot_status": "matched-platform-leave-one-source-group-out-original-authorship-pilot-not-IER",
        "instrument_id": spec["instrument_id"],
        "authors": authors,
        "chance_accuracy": spec["interpretation"]["chance_accuracy"],
        "matched_documents": [_metadata_row(row) for row in matched],
        "matched_document_count": len(matched),
        "matched_source_groups": groups,
        "fold_count": len(folds),
        "source_group_leakage": False,
        "fold_design": [
            {
                "held_out_source_group": fold["held_out_source_group"],
                "training_source_groups": sorted(
                    {str(row["source_group"]) for row in fold["train_rows"]}
                ),
                "train_documents_per_author": _author_counts(fold["train_rows"], authors),
                "test_documents_per_author": _author_counts(fold["test_rows"], authors),
            }
            for fold in folds
        ],
        "models": model_outputs,
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

    parser = argparse.ArgumentParser(prog="python -m pangram_lab.dharma_logo_svm")
    parser.add_argument("manifest")
    parser.add_argument(
        "--spec",
        default="state/IDIOLECT-DHARMA-LOGO-SVM-SPEC-2026-08-18.json",
    )
    parser.add_argument(
        "--out",
        default=".local/idiolect-corpus/dharma-logo-svm-receipt.json",
    )
    args = parser.parse_args(argv)

    try:
        receipt = run_logo_pilot(Path(args.manifest), Path(args.spec), Path(args.out))
    except Exception as exc:
        print(str(exc))
        return 1
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
