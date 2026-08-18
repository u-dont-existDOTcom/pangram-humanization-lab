from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .surface_svm_matched_cv import _hard_control_errors, run_matched_cv
from .surface_svm_pilot import select_largest_documents


_WORD_RE = re.compile(r"\S+")


def centered_word_window(text: str, words: int) -> tuple[str, int, int]:
    """Return one deterministic centered whitespace-token window.

    The transform is intentionally simple and content-blind. It equalizes text
    budget without selecting author-favorable regions or using model feedback.
    """
    if words <= 0:
        raise ValueError("window word count must be positive")
    tokens = _WORD_RE.findall(text)
    total = len(tokens)
    if total < words:
        raise ValueError(f"document has {total} words, fewer than required window {words}")
    start = (total - words) // 2
    window = " ".join(tokens[start : start + words]) + "\n"
    return window, start, total


def _safe_name(value: object) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "sample")).strip("-")
    return text or "sample"


def _whitespace_token_count(row: dict) -> int:
    return len(_WORD_RE.findall(Path(str(row["local_text_path"])).read_text(encoding="utf-8")))


def _apply_short_training_exclusions(
    rows: list[dict],
    exclusions: list[dict],
    *,
    held_out_groups: set[str],
    required_words: int,
) -> tuple[list[dict], list[dict]]:
    """Apply only explicit, feasibility-driven exclusions to training-only rows.

    An exclusion is valid only if it names one unique row, that row cannot be a
    held-out test source group, and the live extracted text is genuinely too
    short for the precommitted window. This prevents outcome-driven filtering.
    """
    retained = list(rows)
    audit: list[dict] = []
    for exclusion in exclusions:
        sample_id = str(exclusion["sample_id"])
        matches = [row for row in retained if str(row.get("sample_id")) == sample_id]
        if len(matches) != 1:
            raise ValueError(f"short-training exclusion {sample_id} matched {len(matches)} rows")
        row = matches[0]
        source_group = str(row.get("source_group") or "")
        if source_group in held_out_groups:
            raise ValueError(f"short-training exclusion {sample_id} is a held-out test row")
        live_words = _whitespace_token_count(row)
        if live_words >= required_words:
            raise ValueError(
                f"short-training exclusion {sample_id} has {live_words} words; "
                f"it is not shorter than required window {required_words}"
            )
        retained.remove(row)
        audit.append(
            {
                "sample_id": row.get("sample_id"),
                "source_group": row.get("source_group"),
                "speaker": row.get("speaker"),
                "source_word_count_reported": int(row.get("word_count", 0)),
                "source_whitespace_token_count": live_words,
                "required_window_words": required_words,
                "reason": exclusion.get("reason") or "training-only-source-shorter-than-precommitted-window",
                "model_outcome_used_for_exclusion": False,
            }
        )
    return retained, audit


def _normalize_rows(
    rows: list[dict],
    *,
    out_dir: Path,
    words: int,
) -> tuple[list[dict], list[dict]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    normalized: list[dict] = []
    audit: list[dict] = []
    for index, row in enumerate(rows, start=1):
        source_path = Path(str(row["local_text_path"]))
        text = source_path.read_text(encoding="utf-8")
        try:
            window, start, total = centered_word_window(text, words)
        except ValueError as exc:
            raise ValueError(
                f"{row.get('sample_id')} ({row.get('speaker')}, {row.get('source_group')}): {exc}"
            ) from exc
        normalized_sha = hashlib.sha256(window.encode("utf-8")).hexdigest()
        sample_id = str(row.get("sample_id") or f"sample-{index}")
        target = out_dir / f"{index:03d}-{_safe_name(sample_id)}-{normalized_sha[:12]}.txt"
        target.write_text(window, encoding="utf-8")

        transformed = dict(row)
        transformed["local_text_path"] = str(target)
        transformed["word_count"] = words
        transformed["canonical_sha256"] = normalized_sha
        normalized.append(transformed)
        audit.append(
            {
                "sample_id": row.get("sample_id"),
                "source_group": row.get("source_group"),
                "speaker": row.get("speaker"),
                "source_word_count_reported": int(row.get("word_count", 0)),
                "source_whitespace_token_count": total,
                "window_word_count": words,
                "window_start_token_index_zero_based": start,
                "source_canonical_sha256": row.get("canonical_sha256"),
                "window_sha256": normalized_sha,
            }
        )
    return normalized, audit


def _write_manifest(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"schema_version": 1, "results": rows, "errors": []}, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


def run_length_normalized(
    spec_path: Path,
    *,
    matched_manifest_path: Path,
    supplement_manifest_path: Path,
    control_manifest_path: Path,
    out_path: Path,
) -> dict:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    words = int(spec["length_normalization"]["window_words"])
    strategy = str(spec["length_normalization"]["strategy"])
    if strategy != "centered-whitespace-token-window":
        raise ValueError(f"unsupported length-normalization strategy: {strategy}")

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

    authors = [str(value) for value in spec["authors"]]
    n_train = int(spec["fold_training"]["documents_per_author"])
    held_out_groups = {str(value) for value in spec["held_out_source_groups"]}

    # The first live feasibility run established that one Joel training-only
    # source contains fewer than 50 extracted words. Preserve the 50-word
    # precommit and exclude only that named, non-test row. The runtime verifies
    # the exclusion remains genuinely necessary before applying it.
    matched_rows, short_training_exclusions = _apply_short_training_exclusions(
        list(matched.get("results", [])),
        list(spec["length_normalization"].get("short_training_exclusions", [])),
        held_out_groups=held_out_groups,
        required_words=words,
    )

    # Preserve the previous pilot's deterministic control-document ranking, but
    # select the new feasible per-author depth before changing word_count to 50.
    selected_controls: list[dict] = []
    for author in authors:
        if author == "Joel Rosenblum":
            continue
        selected = select_largest_documents(controls.get("results", []), author, n_train)
        if len(selected) != n_train:
            raise ValueError(f"expected {n_train} control documents for {author}, got {len(selected)}")
        selected_controls.extend(selected)

    supplement_ids = set(spec["joel_supplement_sample_ids"])
    selected_supplement = [
        row for row in supplement.get("results", []) if row.get("sample_id") in supplement_ids
    ]
    if {row.get("sample_id") for row in selected_supplement} != supplement_ids:
        missing = sorted(supplement_ids - {row.get("sample_id") for row in selected_supplement})
        raise ValueError(f"missing Joel supplement samples: {missing}")

    work_dir = out_path.parent / "surface-svm-length-normalized-50w"
    normalized_matched, audit_matched = _normalize_rows(
        matched_rows, out_dir=work_dir / "matched", words=words
    )
    normalized_supplement, audit_supplement = _normalize_rows(
        selected_supplement, out_dir=work_dir / "supplement", words=words
    )
    normalized_controls, audit_controls = _normalize_rows(
        selected_controls, out_dir=work_dir / "controls", words=words
    )

    matched_out = work_dir / "matched-manifest.json"
    supplement_out = work_dir / "supplement-manifest.json"
    controls_out = work_dir / "control-manifest.json"
    _write_manifest(matched_out, normalized_matched)
    _write_manifest(supplement_out, normalized_supplement)
    _write_manifest(controls_out, normalized_controls)

    receipt = run_matched_cv(
        spec_path,
        matched_manifest_path=matched_out,
        supplement_manifest_path=supplement_out,
        control_manifest_path=controls_out,
        out_path=out_path,
    )
    receipt["pilot_status"] = "matched-platform-length-normalized-50w-not-IER"
    receipt["length_normalization"] = {
        "strategy": strategy,
        "window_words": words,
        "training_words_per_author_per_fold": words * n_train,
        "test_words_per_document": words,
        "control_selection_occurs_before_normalization": True,
        "normalization_is_content_blind": True,
        "short_training_exclusions": short_training_exclusions,
        "documented_control_exclusions_before_selection": [
            {
                "sample_id": row.get("sample_id"),
                "speaker": row.get("speaker"),
                "error": row.get("error"),
            }
            for row in documented_control_exclusions
        ],
        "window_audit": audit_matched + audit_supplement + audit_controls,
    }
    receipt["interpretation_guardrails"] = spec["interpretation"]
    out_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="python -m pangram_lab.surface_svm_length_normalized")
    parser.add_argument(
        "spec",
        nargs="?",
        default="state/IDIOLECT-SURFACE-SVM-LENGTH-NORMALIZED-50W-SPEC-2026-08-18.json",
    )
    parser.add_argument("--matched-manifest", required=True)
    parser.add_argument("--supplement-manifest", required=True)
    parser.add_argument("--control-manifest", required=True)
    parser.add_argument("--out", default=".local/idiolect-corpus/surface-svm-length-normalized-50w-receipt.json")
    args = parser.parse_args(argv)

    try:
        result = run_length_normalized(
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
