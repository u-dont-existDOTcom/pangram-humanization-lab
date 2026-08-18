from __future__ import annotations

import collections
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable

from .surface_svm_equal_budget import _largest_eligible, _normalized_row
from .surface_svm_matched_cv import _aggregate_predictions, _hard_control_errors
from .surface_svm_pilot import assert_no_source_group_leakage, select_largest_documents


def _text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_text(row: dict) -> str:
    return Path(str(row["local_text_path"])).read_text(encoding="utf-8").strip()


def _cosine(a, b) -> float:
    import numpy as np

    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= 0:
        raise ValueError("cannot compute cosine for zero-norm embedding")
    return float(np.dot(a, b) / denom)


class LuarEmbedder:
    """Pinned LUAR-MUD one-document episode embedder with in-run deduplication."""

    def __init__(
        self,
        *,
        model_id: str,
        revision: str,
        max_token_length: int = 512,
        batch_size: int = 8,
        device: str = "cpu",
    ):
        try:
            import torch
            import transformers
            from transformers import AutoModel, AutoTokenizer
        except ImportError as exc:  # pragma: no cover - heavy optional environment
            raise RuntimeError("LUAR pilot requires torch and transformers") from exc

        self.torch = torch
        self.transformers_version = transformers.__version__
        self.model_id = model_id
        self.revision = revision
        self.max_token_length = max_token_length
        self.batch_size = batch_size
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            revision=revision,
            trust_remote_code=True,
        )
        self.model = AutoModel.from_pretrained(
            model_id,
            revision=revision,
            trust_remote_code=True,
            use_safetensors=True,
        )
        self.model.eval()
        self.model.to(device)
        self.cache: dict[str, object] = {}

    def embed_texts(self, texts: Iterable[str]) -> dict[str, object]:
        unique: list[tuple[str, str]] = []
        seen = set(self.cache)
        for text in texts:
            key = _text_sha256(text)
            if key in seen:
                continue
            seen.add(key)
            unique.append((key, text))

        torch = self.torch
        for start in range(0, len(unique), self.batch_size):
            chunk = unique[start : start + self.batch_size]
            chunk_texts = [text for _, text in chunk]
            tokenized = self.tokenizer(
                chunk_texts,
                max_length=self.max_token_length,
                padding=True,
                truncation=True,
                return_tensors="pt",
            )
            batch = len(chunk)
            input_ids = tokenized["input_ids"].reshape(batch, 1, -1).to(self.device)
            attention_mask = tokenized["attention_mask"].reshape(batch, 1, -1).to(self.device)
            with torch.inference_mode():
                output = self.model(input_ids=input_ids, attention_mask=attention_mask)
            if not hasattr(output, "ndim") or output.ndim != 2:
                raise ValueError(f"unexpected LUAR output shape/type: {type(output)!r}")
            if int(output.shape[0]) != batch:
                raise ValueError(f"unexpected LUAR batch dimension: {tuple(output.shape)}")
            values = output.detach().float().cpu().numpy()
            for (key, _), vector in zip(chunk, values):
                self.cache[key] = vector
        return self.cache

    def metadata(self) -> dict:
        config = self.model.config
        return {
            "model_id": self.model_id,
            "requested_revision": self.revision,
            "resolved_commit_hash": getattr(config, "_commit_hash", None),
            "upstream_transformer_revision": getattr(
                config, "upstream_transformer_revision", None
            ),
            "embedding_size": int(getattr(config, "embedding_size", 0) or 0),
            "max_token_length": self.max_token_length,
            "episode_length_for_document_embedding": 1,
            "device": self.device,
            "torch_version": self.torch.__version__,
            "transformers_version": self.transformers_version,
            "profile_rule": "arithmetic mean of raw one-document LUAR embeddings; nearest mean profile by cosine",
            "embeddings_persisted_in_receipt": False,
        }


def _row_key(row: dict) -> str:
    return _text_sha256(_read_text(row))


def nearest_profile_predictions(
    train_rows: list[dict],
    test_rows: list[dict],
    *,
    authors: list[str],
    embeddings: dict[str, object],
) -> list[dict]:
    import numpy as np

    profiles = {}
    for author in authors:
        vectors = [
            embeddings[_row_key(row)]
            for row in train_rows
            if str(row.get("speaker")) == author
        ]
        if not vectors:
            raise ValueError(f"no training embeddings for author: {author}")
        profiles[author] = np.mean(np.stack(vectors, axis=0), axis=0)

    predictions = []
    for row in test_rows:
        vector = embeddings[_row_key(row)]
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


def _meta(row: dict) -> dict:
    return {
        "sample_id": row.get("sample_id"),
        "source_group": row.get("source_group"),
        "speaker": row.get("speaker"),
        "word_count": int(row.get("word_count", 0)),
        "canonical_sha256": row.get("canonical_sha256"),
    }


def _whole_folds(spec: dict, matched_rows: list[dict], supplement_rows: list[dict], control_rows: list[dict]):
    authors = [str(value) for value in spec["authors"]]
    condition = spec["conditions"]["whole_document"]
    n_train = int(condition["documents_per_author_per_fold"])
    supplement_ids = set(condition["joel_supplement_sample_ids"])
    supplements = [dict(row) for row in supplement_rows if row.get("sample_id") in supplement_ids]
    if {row.get("sample_id") for row in supplements} != supplement_ids:
        raise ValueError("missing one or more whole-document Joel supplements")
    for row in supplements:
        row["speaker"] = "Joel Rosenblum"

    control_training = {}
    for author in authors:
        if author == "Joel Rosenblum":
            continue
        selected = select_largest_documents(control_rows, author, n_train)
        if len(selected) != n_train:
            raise ValueError(f"expected {n_train} whole control documents for {author}")
        control_training[author] = selected

    folds = []
    for held_out_group in spec["held_out_source_groups"]:
        test_rows = [
            row for row in matched_rows if str(row.get("source_group")) == held_out_group
        ]
        if len({str(row.get("speaker")) for row in test_rows}) < 2:
            raise ValueError(f"held-out group lacks two authors: {held_out_group}")
        joel = [
            row
            for row in matched_rows
            if row.get("speaker") == "Joel Rosenblum"
            and str(row.get("source_group")) != held_out_group
        ] + [dict(row) for row in supplements]
        if len(joel) != n_train:
            raise ValueError(
                f"whole fold {held_out_group}: expected {n_train} Joel docs, got {len(joel)}"
            )
        train_rows = list(joel)
        for author in authors:
            if author != "Joel Rosenblum":
                train_rows.extend(control_training[author])
        counts = collections.Counter(str(row.get("speaker")) for row in train_rows)
        if any(counts[author] != n_train for author in authors):
            raise ValueError(f"unbalanced whole-document classes: {dict(counts)}")
        assert_no_source_group_leakage(train_rows, test_rows)
        folds.append((str(held_out_group), train_rows, test_rows))
    return folds


def _equal50_folds(
    spec: dict,
    matched_rows: list[dict],
    supplement_rows: list[dict],
    control_rows: list[dict],
    *,
    working_dir: Path,
):
    authors = [str(value) for value in spec["authors"]]
    condition = spec["conditions"]["equal_50_word"]
    n_train = int(condition["documents_per_author_per_fold"])
    budget = int(condition["word_budget_per_document"])
    supplement_ids = set(condition["joel_supplement_sample_ids"])
    supplements = [dict(row) for row in supplement_rows if row.get("sample_id") in supplement_ids]
    if {row.get("sample_id") for row in supplements} != supplement_ids:
        raise ValueError("missing equal-50-word Joel supplement")
    for row in supplements:
        row["speaker"] = "Joel Rosenblum"

    control_training = {}
    for author in authors:
        if author == "Joel Rosenblum":
            continue
        selected = _largest_eligible(
            control_rows, author, count=n_train, min_words=budget
        )
        if len(selected) != n_train:
            raise ValueError(f"expected {n_train} >= {budget}-word docs for {author}")
        control_training[author] = selected

    folds = []
    for fold_index, held_out_group in enumerate(spec["held_out_source_groups"], start=1):
        raw_test = [
            row for row in matched_rows if str(row.get("source_group")) == held_out_group
        ]
        if any(int(row.get("word_count", 0)) < budget for row in raw_test):
            raise ValueError(f"equal-50 held-out group has short document: {held_out_group}")
        raw_joel = [
            row
            for row in matched_rows
            if row.get("speaker") == "Joel Rosenblum"
            and str(row.get("source_group")) != held_out_group
            and int(row.get("word_count", 0)) >= budget
        ] + [dict(row) for row in supplements]
        if len(raw_joel) != n_train:
            raise ValueError(
                f"equal-50 fold {held_out_group}: expected {n_train} Joel docs, got {len(raw_joel)}"
            )

        train_rows = []
        for row in raw_joel:
            train_rows.append(
                _normalized_row(
                    row,
                    words=budget,
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
                        words=budget,
                        out_dir=working_dir / f"fold-{fold_index}" / "train",
                        prefix=hashlib.sha256(author.encode()).hexdigest()[:8],
                    )
                )
        test_rows = [
            _normalized_row(
                row,
                words=budget,
                out_dir=working_dir / f"fold-{fold_index}" / "test",
                prefix="heldout",
            )
            for row in raw_test
        ]
        counts = collections.Counter(str(row.get("speaker")) for row in train_rows)
        if any(counts[author] != n_train for author in authors):
            raise ValueError(f"unbalanced equal-50 classes: {dict(counts)}")
        totals = collections.Counter()
        for row in train_rows:
            totals[str(row.get("speaker"))] += int(row.get("word_count", 0))
        expected_words = n_train * budget
        if any(totals[author] != expected_words for author in authors):
            raise ValueError(f"unequal equal-50 word totals: {dict(totals)}")
        assert_no_source_group_leakage(train_rows, test_rows)
        folds.append((str(held_out_group), train_rows, test_rows))
    return folds


def _run_condition(
    name: str,
    folds,
    *,
    authors: list[str],
    embedder: LuarEmbedder,
    bootstrap_iterations: int,
    bootstrap_seed: int,
) -> dict:
    all_rows = []
    for _, train_rows, test_rows in folds:
        all_rows.extend(train_rows)
        all_rows.extend(test_rows)
    embedder.embed_texts(_read_text(row) for row in all_rows)

    aggregate_predictions = []
    fold_receipts = []
    for fold_index, (held_out_group, train_rows, test_rows) in enumerate(folds, start=1):
        predictions = nearest_profile_predictions(
            train_rows,
            test_rows,
            authors=authors,
            embeddings=embedder.cache,
        )
        aggregate_predictions.extend(predictions)
        fold_metric = _aggregate_predictions(
            predictions,
            authors,
            iterations=1,
            seed=fold_index,
        )
        fold_receipts.append(
            {
                "fold_index": fold_index,
                "held_out_source_group": held_out_group,
                "training_documents": [_meta(row) for row in train_rows],
                "held_out_documents": [_meta(row) for row in test_rows],
                "accuracy": fold_metric["accuracy"],
                "predictions": predictions,
            }
        )

    if len(aggregate_predictions) != 10:
        raise ValueError(f"{name}: expected 10 aggregate predictions, got {len(aggregate_predictions)}")
    aggregate = _aggregate_predictions(
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


def run_luar_pilot(
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
    if matched.get("errors"):
        raise ValueError(f"matched acquisition errors: {matched['errors']}")
    if supplement.get("errors"):
        raise ValueError(f"supplement acquisition errors: {supplement['errors']}")
    hard_errors, documented_control_exclusions = _hard_control_errors(
        controls.get("errors", [])
    )
    if hard_errors:
        raise ValueError(f"control acquisition errors: {hard_errors}")

    authors = [str(value) for value in spec["authors"]]
    matched_rows = matched.get("results", [])
    supplement_rows = supplement.get("results", [])
    control_rows = controls.get("results", [])

    whole = _whole_folds(spec, matched_rows, supplement_rows, control_rows)
    equal50 = _equal50_folds(
        spec,
        matched_rows,
        supplement_rows,
        control_rows,
        working_dir=working_dir / "equal50",
    )

    model_spec = spec["model"]
    embedder = LuarEmbedder(
        model_id=model_spec["model_id"],
        revision=model_spec["revision"],
        max_token_length=int(model_spec["max_token_length"]),
        batch_size=8,
        device="cpu",
    )
    metadata = embedder.metadata()
    expected_embedding = int(model_spec["embedding_size"])
    if metadata["embedding_size"] not in {0, expected_embedding}:
        raise ValueError(
            f"LUAR embedding size mismatch: {metadata['embedding_size']} != {expected_embedding}"
        )
    upstream = metadata.get("upstream_transformer_revision")
    expected_upstream = model_spec.get("upstream_backbone_revision_from_model_config")
    if upstream and expected_upstream and upstream != expected_upstream:
        raise ValueError(f"LUAR upstream revision mismatch: {upstream} != {expected_upstream}")

    bootstrap = spec["evaluation"]["group_bootstrap_accuracy"]
    conditions = {
        "whole_document": _run_condition(
            "whole_document",
            whole,
            authors=authors,
            embedder=embedder,
            bootstrap_iterations=int(bootstrap["iterations"]),
            bootstrap_seed=int(bootstrap["seed"]),
        ),
        "equal_50_word": _run_condition(
            "equal_50_word",
            equal50,
            authors=authors,
            embedder=embedder,
            bootstrap_iterations=int(bootstrap["iterations"]),
            bootstrap_seed=int(bootstrap["seed"]) + 1,
        ),
    }

    receipt = {
        "schema_version": 1,
        "raw_or_canonical_prose_in_output": False,
        "embeddings_persisted_in_output": False,
        "pilot_status": "luar-mean-profile-nearest-cosine-pilot-not-IER",
        "authors": authors,
        "model": metadata,
        "unique_document_embeddings_computed": len(embedder.cache),
        "source_group_leakage": False,
        "documented_control_exclusions": [
            {
                "sample_id": row.get("sample_id"),
                "speaker": row.get("speaker"),
                "error": row.get("error"),
            }
            for row in documented_control_exclusions
        ],
        "conditions": conditions,
        "interpretation_guardrails": spec["interpretation"],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="python -m pangram_lab.luar_matched_pilot")
    parser.add_argument(
        "spec",
        nargs="?",
        default="state/IDIOLECT-LUAR-MATCHED-PILOT-SPEC-2026-08-18.json",
    )
    parser.add_argument("--matched-manifest", required=True)
    parser.add_argument("--supplement-manifest", required=True)
    parser.add_argument("--control-manifest", required=True)
    parser.add_argument("--working-dir", default=".local/idiolect-corpus/luar-matched-pilot")
    parser.add_argument("--out", default=".local/idiolect-corpus/luar-matched-pilot-receipt.json")
    args = parser.parse_args(argv)

    try:
        receipt = run_luar_pilot(
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
