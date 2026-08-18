from __future__ import annotations

import collections
import hashlib
import json
import re
from pathlib import Path

from .surface_svm_matched_cv import _aggregate_predictions, _hard_control_errors
from .surface_svm_pilot import assert_no_source_group_leakage, fit_and_evaluate

_WORD_RE = re.compile(r"\b[\w’'-]+\b", flags=re.UNICODE)


def prefix_exact_words(text: str, words: int) -> str:
    """Return original characters through the end of the Nth word token.

    Punctuation/spacing before that boundary are preserved exactly; no prose is
    reconstructed from tokens.
    """
    matches = list(_WORD_RE.finditer(text))
    if len(matches) < words:
        raise ValueError(f"text has {len(matches)} words, needs at least {words}")
    return text[: matches[words - 1].end()].strip()


def _normalized_row(row: dict, *, words: int, out_dir: Path, prefix: str) -> dict:
    source_path = Path(str(row["local_text_path"]))
    text = source_path.read_text(encoding="utf-8")
    normalized = prefix_exact_words(text, words)
    if len(_WORD_RE.findall(normalized)) != words:
        raise ValueError(f"normalization failed exact word budget for {row.get('sample_id')}")
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(row.get("sample_id") or "sample"))
    path = out_dir / f"{prefix}-{safe}.txt"
    path.write_text(normalized + "\n", encoding="utf-8")
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return {
        **row,
        "local_text_path": str(path),
        "original_word_count": int(row.get("word_count", 0)),
        "word_count": words,
        "canonical_sha256": digest,
    }


def _largest_eligible(rows: list[dict], speaker: str, *, count: int, min_words: int) -> list[dict]:
    eligible = [
        row
        for row in rows
        if row.get("speaker") == speaker and int(row.get("word_count", 0)) >= min_words
    ]
    eligible.sort(
        key=lambda row: (
            -int(row.get("word_count", 0)),
            str(row.get("source_group") or ""),
            str(row.get("sample_id") or ""),
        )
    )
    return eligible[:count]


def _meta(row: dict) -> dict:
    return {
        "sample_id": row.get("sample_id"),
        "source_group": row.get("source_group"),
        "speaker": row.get("speaker"),
        "original_word_count": int(row.get("original_word_count", row.get("word_count", 0))),
        "normalized_word_count": int(row.get("word_count", 0)),
        "normalized_sha256": row.get("canonical_sha256"),
    }


def run_equal_budget(
    spec_path: Path,
    *,
    matched_manifest_path: Path,
    supplement_manifest_path: Path,
    control_manifest_path: Path,
    working_dir: Path,
    out_path: Path,
) -> dict:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    authors = [str(value) for value in spec["authors"]]
    word_budget = int(spec["word_budget_per_document"])
    n_train = int(spec["documents_per_author_per_fold"])

    matched = json.loads(matched_manifest_path.read_text(encoding="utf-8"))
    supplement = json.loads(supplement_manifest_path.read_text(encoding="utf-8"))
    controls = json.loads(control_manifest_path.read_text(encoding="utf-8"))
    if matched.get("errors"):
        raise ValueError(f"matched acquisition errors: {matched['errors']}")
    if supplement.get("errors"):
        raise ValueError(f"supplement acquisition errors: {supplement['errors']}")
    hard_control_errors, documented_control_exclusions = _hard_control_errors(controls.get("errors", []))
    if hard_control_errors:
        raise ValueError(f"control acquisition errors: {hard_control_errors}")

    matched_rows = matched.get("results", [])
    supplement_id = str(spec["joel_supplement_sample_id"])
    supplement_matches = [row for row in supplement.get("results", []) if row.get("sample_id") == supplement_id]
    if len(supplement_matches) != 1:
        raise ValueError(f"expected one Joel supplement {supplement_id}, got {len(supplement_matches)}")
    joel_supplement = dict(supplement_matches[0])
    joel_supplement["speaker"] = "Joel Rosenblum"
    if int(joel_supplement.get("word_count", 0)) < word_budget:
        raise ValueError("Joel supplement is shorter than word budget")

    control_training: dict[str, list[dict]] = {}
    for author in authors:
        if author == "Joel Rosenblum":
            continue
        selected = _largest_eligible(
            controls.get("results", []), author, count=n_train, min_words=word_budget
        )
        if len(selected) != n_train:
            raise ValueError(f"expected {n_train} >= {word_budget}-word docs for {author}, got {len(selected)}")
        control_training[author] = selected

    held_out_groups = [str(value) for value in spec["held_out_source_groups"]]
    model_specs = spec["models"]
    model_predictions: dict[str, list[dict]] = {row["model_id"]: [] for row in model_specs}
    model_meta: dict[str, dict] = {}
    folds = []

    for fold_index, held_out_group in enumerate(held_out_groups, start=1):
        raw_test = [row for row in matched_rows if str(row.get("source_group")) == held_out_group]
        if len({str(row.get("speaker")) for row in raw_test}) < 2:
            raise ValueError(f"held-out group lacks at least two authors: {held_out_group}")
        if any(int(row.get("word_count", 0)) < word_budget for row in raw_test):
            short = [row.get("sample_id") for row in raw_test if int(row.get("word_count", 0)) < word_budget]
            raise ValueError(f"held-out docs shorter than {word_budget}: {short}")

        raw_joel = [
            row
            for row in matched_rows
            if row.get("speaker") == "Joel Rosenblum"
            and str(row.get("source_group")) != held_out_group
            and int(row.get("word_count", 0)) >= word_budget
        ]
        raw_joel.append(dict(joel_supplement))
        if len(raw_joel) != n_train:
            raise ValueError(
                f"fold {held_out_group}: expected {n_train} eligible Joel docs, got {len(raw_joel)}"
            )

        train_rows = []
        for row in raw_joel:
            train_rows.append(
                _normalized_row(
                    row,
                    words=word_budget,
                    out_dir=working_dir / f"fold-{fold_index}" / "train",
                    prefix="joel",
                )
            )
        for author in authors:
            if author == "Joel Rosenblum":
                continue
            for row in control_training[author]:
                train_rows.append(
                    _normalized_row(
                        row,
                        words=word_budget,
                        out_dir=working_dir / f"fold-{fold_index}" / "train",
                        prefix=re.sub(r"[^a-z]+", "-", author.casefold()).strip("-"),
                    )
                )

        test_rows = [
            _normalized_row(
                row,
                words=word_budget,
                out_dir=working_dir / f"fold-{fold_index}" / "test",
                prefix="heldout",
            )
            for row in raw_test
        ]

        counts = collections.Counter(str(row.get("speaker")) for row in train_rows)
        if any(counts[author] != n_train for author in authors):
            raise ValueError(f"fold {held_out_group}: unbalanced training documents: {dict(counts)}")
        word_totals = collections.Counter()
        for row in train_rows:
            word_totals[str(row["speaker"])] += int(row["word_count"])
        expected_words = n_train * word_budget
        if any(word_totals[author] != expected_words for author in authors):
            raise ValueError(f"fold {held_out_group}: unequal training word totals: {dict(word_totals)}")
        assert_no_source_group_leakage(train_rows, test_rows)

        fold = {
            "fold_index": fold_index,
            "held_out_source_group": held_out_group,
            "training": {
                author: {
                    "document_count": counts[author],
                    "normalized_total_words": word_totals[author],
                    "documents": [_meta(row) for row in train_rows if row.get("speaker") == author],
                }
                for author in authors
            },
            "test_documents": [_meta(row) for row in test_rows],
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
            fold["models"][model_id] = {
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
        folds.append(fold)

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

    if any(len(rows) != 10 for rows in model_predictions.values()):
        raise ValueError("expected exactly 10 aggregate held-out predictions per model")

    receipt = {
        "schema_version": 1,
        "raw_or_canonical_prose_in_output": False,
        "pilot_status": "matched-platform-equal-50-word-budget-not-IER",
        "authors": authors,
        "word_budget_per_document": word_budget,
        "documents_per_author_per_fold": n_train,
        "training_words_per_author_per_fold": n_train * word_budget,
        "fold_count": len(folds),
        "source_group_leakage": False,
        "documented_control_exclusions": [
            {
                "sample_id": row.get("sample_id"),
                "speaker": row.get("speaker"),
                "error": row.get("error"),
            }
            for row in documented_control_exclusions
        ],
        "folds": folds,
        "aggregate_models": aggregate_models,
        "interpretation_guardrails": spec["interpretation"],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="python -m pangram_lab.surface_svm_equal_budget")
    parser.add_argument(
        "spec",
        nargs="?",
        default="state/IDIOLECT-SURFACE-SVM-EQUAL-50W-SPEC-2026-08-18.json",
    )
    parser.add_argument("--matched-manifest", required=True)
    parser.add_argument("--supplement-manifest", required=True)
    parser.add_argument("--control-manifest", required=True)
    parser.add_argument("--working-dir", default=".local/idiolect-corpus/surface-svm-equal-50w")
    parser.add_argument("--out", default=".local/idiolect-corpus/surface-svm-equal-50w-receipt.json")
    args = parser.parse_args(argv)

    try:
        result = run_equal_budget(
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
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
