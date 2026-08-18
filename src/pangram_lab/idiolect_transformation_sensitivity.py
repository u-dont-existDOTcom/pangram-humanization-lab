from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .luar_matched_pilot import LuarEmbedder, _cosine


def _git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _word_count(text: str) -> int:
    return len(text.split())


def extract_first_paragraph_under_heading(markdown: str, heading: str) -> str:
    """Extract the first prose paragraph under an exact level-3 Markdown heading."""
    pattern = re.compile(rf"^###\s+{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(markdown)
    if not match:
        raise ValueError(f"heading not found: {heading}")
    tail = markdown[match.end():]
    lines = tail.splitlines()
    paragraph: list[str] = []
    started = False
    for line in lines:
        stripped = line.strip()
        if not started:
            if not stripped:
                continue
            if stripped.startswith("#"):
                raise ValueError(f"no prose paragraph under heading: {heading}")
            started = True
            paragraph.append(stripped)
            continue
        if not stripped:
            break
        if stripped.startswith("#"):
            break
        paragraph.append(stripped)
    text = " ".join(paragraph).strip()
    if not text:
        raise ValueError(f"empty extracted paragraph: {heading}")
    return text


def _load_rows(paths: list[Path]) -> list[dict]:
    rows: list[dict] = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("errors"):
            raise ValueError(f"acquisition errors in {path}: {data['errors']}")
        rows.extend(data.get("results", []))
    return rows


def _read_row_text(row: dict) -> str:
    return Path(str(row["local_text_path"])).read_text(encoding="utf-8").strip()


def _build_profiles(spec: dict, rows: list[dict], embedder: LuarEmbedder) -> dict[str, object]:
    import numpy as np

    by_sample = {str(row.get("sample_id")): row for row in rows}
    requested: dict[str, list[str]] = spec["profile_sample_ids"]
    all_texts: list[str] = []
    selected: dict[str, list[dict]] = {}
    for author in spec["authors"]:
        sample_ids = [str(value) for value in requested[author]]
        missing = [sample_id for sample_id in sample_ids if sample_id not in by_sample]
        if missing:
            raise ValueError(f"missing profile samples for {author}: {missing}")
        author_rows = [by_sample[sample_id] for sample_id in sample_ids]
        if any(str(row.get("speaker")) != author for row in author_rows):
            raise ValueError(f"profile speaker mismatch for {author}")
        selected[author] = author_rows
        all_texts.extend(_read_row_text(row) for row in author_rows)

    embedder.embed_texts(all_texts)
    profiles: dict[str, object] = {}
    for author, author_rows in selected.items():
        vectors = [embedder.cache[_text_sha256(_read_row_text(row))] for row in author_rows]
        profiles[author] = np.mean(np.stack(vectors, axis=0), axis=0)
    return profiles


def _score_text(text: str, *, authors: list[str], profiles: dict[str, object], embedder: LuarEmbedder) -> dict:
    embedder.embed_texts([text])
    vector = embedder.cache[_text_sha256(text)]
    scores = {author: _cosine(vector, profiles[author]) for author in authors}
    ordered = sorted(authors, key=lambda author: scores[author], reverse=True)
    joel = "Joel Rosenblum"
    best_other = max(scores[author] for author in authors if author != joel)
    return {
        "predicted_author": ordered[0],
        "joel_cosine": round(float(scores[joel]), 6),
        "joel_margin_vs_best_other": round(float(scores[joel] - best_other), 6),
        "cosine_scores": {author: round(float(scores[author]), 6) for author in authors},
    }


def run_transformation_sensitivity(
    spec_path: Path,
    *,
    matched_manifest_path: Path,
    supplement_manifest_path: Path,
    control_manifest_path: Path,
    snapshot_path: Path,
    out_path: Path,
) -> dict:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    expected_snapshot = spec["source_snapshot"]["required_canonical_hash_set_sha256"]
    observed_snapshot = snapshot.get("canonical_hash_set_sha256")
    if observed_snapshot != expected_snapshot:
        raise ValueError(
            "canonical source snapshot drift: "
            f"expected {expected_snapshot}, observed {observed_snapshot}"
        )

    source_path = Path(spec["pair_source"]["path"])
    source_bytes = source_path.read_bytes()
    observed_blob = _git_blob_sha1(source_bytes)
    expected_blob = spec["pair_source"]["git_blob_sha1"]
    if observed_blob != expected_blob:
        raise ValueError(
            f"pair source drift: expected git blob {expected_blob}, observed {observed_blob}"
        )
    markdown = source_bytes.decode("utf-8")

    rows = _load_rows(
        [matched_manifest_path, supplement_manifest_path, control_manifest_path]
    )
    model = spec["model"]
    embedder = LuarEmbedder(
        model_id=str(model["model_id"]),
        revision=str(model["revision"]),
        max_token_length=int(model.get("max_token_length", 512)),
    )
    authors = [str(value) for value in spec["authors"]]
    profiles = _build_profiles(spec, rows, embedder)

    pair_results = []
    for pair in spec["pairs"]:
        original = extract_first_paragraph_under_heading(markdown, str(pair["original_heading"]))
        candidate = extract_first_paragraph_under_heading(markdown, str(pair["candidate_heading"]))
        original_score = _score_text(original, authors=authors, profiles=profiles, embedder=embedder)
        candidate_score = _score_text(candidate, authors=authors, profiles=profiles, embedder=embedder)
        pair_results.append(
            {
                "pair_id": pair["pair_id"],
                "transformation_class": pair["transformation_class"],
                "candidate_provenance": pair["candidate_provenance"],
                "original": {
                    "sha256": _text_sha256(original),
                    "word_count": _word_count(original),
                    **original_score,
                },
                "candidate": {
                    "sha256": _text_sha256(candidate),
                    "word_count": _word_count(candidate),
                    **candidate_score,
                },
                "delta": {
                    "joel_cosine": round(
                        candidate_score["joel_cosine"] - original_score["joel_cosine"], 6
                    ),
                    "joel_margin_vs_best_other": round(
                        candidate_score["joel_margin_vs_best_other"]
                        - original_score["joel_margin_vs_best_other"],
                        6,
                    ),
                    "prediction_changed": (
                        candidate_score["predicted_author"] != original_score["predicted_author"]
                    ),
                    "moved_toward_joel_by_margin": (
                        candidate_score["joel_margin_vs_best_other"]
                        > original_score["joel_margin_vs_best_other"]
                    ),
                },
            }
        )

    receipt = {
        "schema_version": 1,
        "status": "transformation-sensitivity-diagnostic-not-IER",
        "raw_pair_prose_in_output": False,
        "embeddings_persisted_in_output": False,
        "model": embedder.metadata(),
        "source_snapshot": {
            "canonical_hash_set_sha256": observed_snapshot,
            "pair_source_git_blob_sha1": observed_blob,
        },
        "authors": authors,
        "profile_documents_per_author": {
            author: len(spec["profile_sample_ids"][author]) for author in authors
        },
        "pairs": pair_results,
        "interpretation_guardrails": spec["interpretation_guardrails"],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="python -m pangram_lab.idiolect_transformation_sensitivity")
    parser.add_argument(
        "spec",
        nargs="?",
        default="state/IDIOLECT-TRANSFORMATION-SENSITIVITY-SPEC-2026-08-18.json",
    )
    parser.add_argument("--matched-manifest", required=True)
    parser.add_argument("--supplement-manifest", required=True)
    parser.add_argument("--control-manifest", required=True)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        result = run_transformation_sensitivity(
            Path(args.spec),
            matched_manifest_path=Path(args.matched_manifest),
            supplement_manifest_path=Path(args.supplement_manifest),
            control_manifest_path=Path(args.control_manifest),
            snapshot_path=Path(args.snapshot),
            out_path=Path(args.out),
        )
    except Exception as exc:
        print(str(exc))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
