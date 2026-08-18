from __future__ import annotations

import collections
import json
import random
from pathlib import Path


def select_largest_documents(rows: list[dict], speaker: str, count: int) -> list[dict]:
    eligible = [
        row for row in rows
        if row.get("speaker") == speaker and int(row.get("word_count", 0)) > 0
    ]
    eligible.sort(
        key=lambda row: (
            -int(row.get("word_count", 0)),
            str(row.get("source_group") or ""),
            str(row.get("sample_id") or ""),
        )
    )
    return eligible[:count]


def select_matched_test(rows: list[dict], *, min_authors_per_group: int = 2) -> list[dict]:
    grouped: dict[str, list[dict]] = collections.defaultdict(list)
    for row in rows:
        group = row.get("source_group")
        if group:
            grouped[str(group)].append(row)
    allowed = {
        group
        for group, items in grouped.items()
        if len({str(item.get("speaker")) for item in items if item.get("speaker")})
        >= min_authors_per_group
    }
    selected = [row for row in rows if str(row.get("source_group")) in allowed]
    selected.sort(key=lambda row: (str(row.get("source_group")), str(row.get("speaker"))))
    return selected


def assert_no_source_group_leakage(train_rows: list[dict], test_rows: list[dict]) -> None:
    train_groups = {str(row.get("source_group")) for row in train_rows if row.get("source_group")}
    test_groups = {str(row.get("source_group")) for row in test_rows if row.get("source_group")}
    overlap = sorted(train_groups & test_groups)
    if overlap:
        raise ValueError(f"source_group leakage across train/test: {overlap}")


def group_bootstrap_accuracy(
    predictions: list[dict],
    *,
    iterations: int,
    seed: int,
) -> dict:
    grouped: dict[str, list[dict]] = collections.defaultdict(list)
    for row in predictions:
        grouped[str(row["source_group"])].append(row)
    groups = sorted(grouped)
    if not groups:
        return {"groups": 0, "iterations": 0, "p2_5": None, "p97_5": None}

    rng = random.Random(seed)
    values: list[float] = []
    for _ in range(iterations):
        sampled_groups = [rng.choice(groups) for _ in groups]
        sampled = [row for group in sampled_groups for row in grouped[group]]
        correct = sum(1 for row in sampled if row["actual"] == row["predicted"])
        values.append(correct / len(sampled))
    values.sort()

    def percentile(p: float) -> float:
        if not values:
            return float("nan")
        pos = (len(values) - 1) * p
        lo = int(pos)
        hi = min(lo + 1, len(values) - 1)
        frac = pos - lo
        return values[lo] * (1 - frac) + values[hi] * frac

    return {
        "groups": len(groups),
        "iterations": iterations,
        "seed": seed,
        "p2_5": round(percentile(0.025), 6),
        "p97_5": round(percentile(0.975), 6),
    }


def _read_text(row: dict) -> str:
    path = Path(str(row["local_text_path"]))
    return path.read_text(encoding="utf-8")


def _feature_transformer(mode: str):
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.pipeline import FeatureUnion
    except ImportError as exc:  # pragma: no cover - exercised in optional env
        raise RuntimeError("surface SVM pilot requires scikit-learn") from exc

    char = TfidfVectorizer(analyzer="char", ngram_range=(2, 4))
    word = TfidfVectorizer(analyzer="word", ngram_range=(1, 2))
    if mode == "char+word":
        return FeatureUnion([("char", char), ("word", word)])
    if mode == "char":
        return char
    if mode == "word":
        return word
    raise ValueError(f"unsupported feature mode: {mode}")


def fit_and_evaluate(
    train_rows: list[dict],
    test_rows: list[dict],
    *,
    authors: list[str],
    feature_mode: str,
    C: float = 1.0,
    bootstrap_iterations: int = 10000,
    bootstrap_seed: int = 260800926,
) -> dict:
    try:
        import sklearn
        from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score
        from sklearn.pipeline import Pipeline
        from sklearn.svm import LinearSVC
    except ImportError as exc:  # pragma: no cover - exercised in optional env
        raise RuntimeError("surface SVM pilot requires scikit-learn") from exc

    x_train = [_read_text(row) for row in train_rows]
    y_train = [str(row["speaker"]) for row in train_rows]
    x_test = [_read_text(row) for row in test_rows]
    y_test = [str(row["speaker"]) for row in test_rows]

    model = Pipeline(
        [
            ("features", _feature_transformer(feature_mode)),
            ("classifier", LinearSVC(C=C)),
        ]
    )
    model.fit(x_train, y_train)
    predicted = model.predict(x_test)
    scores = model.decision_function(x_test)
    classes = [str(value) for value in model.named_steps["classifier"].classes_]

    prediction_rows: list[dict] = []
    for idx, (row, actual, guess) in enumerate(zip(test_rows, y_test, predicted)):
        raw_scores = scores[idx]
        if getattr(raw_scores, "ndim", 0) == 0:
            score_map = {classes[0]: round(float(raw_scores), 6)}
        else:
            score_map = {
                label: round(float(value), 6)
                for label, value in zip(classes, raw_scores)
            }
        prediction_rows.append(
            {
                "sample_id": row.get("sample_id"),
                "source_group": row.get("source_group"),
                "actual": actual,
                "predicted": str(guess),
                "correct": actual == str(guess),
                "decision_scores": score_map,
            }
        )

    per_author = {}
    for author in authors:
        indices = [idx for idx, actual in enumerate(y_test) if actual == author]
        correct = sum(1 for idx in indices if y_test[idx] == str(predicted[idx]))
        per_author[author] = {
            "documents": len(indices),
            "correct": correct,
            "accuracy": round(correct / len(indices), 6) if indices else None,
        }

    matrix = confusion_matrix(y_test, predicted, labels=authors).tolist()
    return {
        "feature_mode": feature_mode,
        "classifier": "LinearSVC",
        "C": C,
        "sklearn_version": sklearn.__version__,
        "vectorizer_defaults": {
            "lowercase": True,
            "norm": "l2",
            "use_idf": True,
            "smooth_idf": True,
            "sublinear_tf": False,
            "word_token_pattern": "(?u)\\b\\w\\w+\\b",
        },
        "accuracy": round(float(accuracy_score(y_test, predicted)), 6),
        "balanced_accuracy": round(float(balanced_accuracy_score(y_test, predicted)), 6),
        "macro_f1": round(float(f1_score(y_test, predicted, labels=authors, average="macro", zero_division=0)), 6),
        "per_author": per_author,
        "confusion_matrix": {
            "labels": authors,
            "rows_actual_columns_predicted": matrix,
        },
        "group_bootstrap_accuracy_95pct": group_bootstrap_accuracy(
            prediction_rows,
            iterations=bootstrap_iterations,
            seed=bootstrap_seed,
        ),
        "predictions": prediction_rows,
    }


def _metadata_row(row: dict, *, word_key: str = "word_count") -> dict:
    return {
        "sample_id": row.get("sample_id"),
        "source_group": row.get("source_group"),
        "speaker": row.get("speaker"),
        "word_count": int(row.get(word_key, 0)),
        "canonical_sha256": row.get("canonical_sha256") or row.get("profile_canonical_sha256"),
    }


def run_pilot(
    spec_path: Path,
    *,
    joel_receipt_path: Path,
    control_manifest_path: Path,
    test_manifest_path: Path,
    out_path: Path,
) -> dict:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    authors = [str(value) for value in spec["authors"]]
    n_train = int(spec["training"]["documents_per_author"])

    joel_receipt = json.loads(joel_receipt_path.read_text(encoding="utf-8"))
    control_manifest = json.loads(control_manifest_path.read_text(encoding="utf-8"))
    test_manifest = json.loads(test_manifest_path.read_text(encoding="utf-8"))

    joel_rows = []
    for row in joel_receipt.get("samples", []):
        joel_rows.append(
            {
                **row,
                "speaker": "Joel Rosenblum",
                "word_count": int(row.get("profile_word_count", 0)),
                "canonical_sha256": row.get("profile_canonical_sha256"),
            }
        )
    if len(joel_rows) != n_train:
        raise ValueError(f"expected {n_train} Joel profile documents, got {len(joel_rows)}")

    train_rows = list(joel_rows)
    for speaker in authors:
        if speaker == "Joel Rosenblum":
            continue
        selected = select_largest_documents(control_manifest.get("results", []), speaker, n_train)
        if len(selected) != n_train:
            raise ValueError(f"expected {n_train} training documents for {speaker}, got {len(selected)}")
        train_rows.extend(selected)

    test_rows = select_matched_test(test_manifest.get("results", []), min_authors_per_group=2)
    expected_docs = int(spec["held_out_test"]["expected_documents"])
    expected_groups = int(spec["held_out_test"]["expected_source_groups"])
    if len(test_rows) != expected_docs:
        raise ValueError(f"expected {expected_docs} held-out documents, got {len(test_rows)}")
    actual_groups = {str(row.get("source_group")) for row in test_rows}
    if len(actual_groups) != expected_groups:
        raise ValueError(f"expected {expected_groups} held-out source groups, got {len(actual_groups)}")

    assert_no_source_group_leakage(train_rows, test_rows)
    class_counts = collections.Counter(str(row["speaker"]) for row in train_rows)
    if any(class_counts[author] != n_train for author in authors):
        raise ValueError(f"unbalanced training class counts: {dict(class_counts)}")

    bootstrap = spec["evaluation"]["group_bootstrap_accuracy"]
    model_modes = [
        ("paper-described-char2-4-word1-2-linear-svm", "char+word"),
        ("char2-4-only-sensitivity", "char"),
        ("word1-2-only-sensitivity", "word"),
    ]
    results = {}
    for model_id, mode in model_modes:
        results[model_id] = fit_and_evaluate(
            train_rows,
            test_rows,
            authors=authors,
            feature_mode=mode,
            C=1.0,
            bootstrap_iterations=int(bootstrap["iterations"]),
            bootstrap_seed=int(bootstrap["seed"]),
        )

    receipt = {
        "schema_version": 1,
        "raw_or_canonical_prose_in_output": False,
        "pilot_status": "closed-set-original-authorship-pilot-not-IER",
        "authors": authors,
        "chance_accuracy": spec["interpretation"]["chance_accuracy"],
        "train_documents_per_author": n_train,
        "training_documents": [_metadata_row(row) for row in train_rows],
        "held_out_documents": [_metadata_row(row) for row in test_rows],
        "held_out_source_groups": sorted(actual_groups),
        "source_group_leakage": False,
        "models": results,
        "interpretation_guardrails": spec["interpretation"],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="python -m pangram_lab.surface_svm_pilot")
    parser.add_argument("spec", nargs="?", default="state/IDIOLECT-SURFACE-SVM-PILOT-SPEC-2026-08-18.json")
    parser.add_argument("--joel-receipt", required=True)
    parser.add_argument("--control-manifest", required=True)
    parser.add_argument("--test-manifest", required=True)
    parser.add_argument("--out", default=".local/idiolect-corpus/surface-svm-pilot-receipt.json")
    args = parser.parse_args(argv)

    try:
        receipt = run_pilot(
            Path(args.spec),
            joel_receipt_path=Path(args.joel_receipt),
            control_manifest_path=Path(args.control_manifest),
            test_manifest_path=Path(args.test_manifest),
            out_path=Path(args.out),
        )
    except Exception as exc:
        print(str(exc))
        return 1
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
