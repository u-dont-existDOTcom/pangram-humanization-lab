from __future__ import annotations

import collections
import hashlib
import json
import re
import sys
from pathlib import Path

from .corpus_acquire import acquire_inventory, canonicalize, word_count
from .joel_legacy_profile import apply_cleanup_rule

_WORD_RE = re.compile(r"\b[\w’'-]+\b", flags=re.UNICODE)


def prefix_to_word_budget(text: str, budget: int | None) -> str:
    """Return a deterministic authored-text prefix capped at ``budget`` words.

    The cut includes punctuation and separators after the final retained word,
    but never includes the next word. A ``None`` budget preserves the complete
    cleaned document. This is a balancing view, not a new canonical source.
    """

    text = text.strip()
    if budget is None:
        return text
    if budget <= 0:
        raise ValueError("word budget must be positive")
    matches = list(_WORD_RE.finditer(text))
    if len(matches) <= budget:
        return text
    return text[: matches[budget].start()].rstrip()


def _fraction(value: int, total: int) -> float | None:
    return round(value / total, 6) if total else None


def _hash_set_sha(rows: list[dict]) -> str:
    payload = "\n".join(
        f"{row['sample_id']}\t{row['canonical_sha256']}\t{row['word_count']}"
        for row in sorted(rows, key=lambda item: item["sample_id"])
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _duplicate_groups(rows: list[dict]) -> list[dict]:
    by_hash: dict[str, list[str]] = collections.defaultdict(list)
    for row in rows:
        by_hash[str(row["profile_canonical_sha256"])].append(str(row["sample_id"]))
    return [
        {"canonical_sha256": sha, "sample_ids": sorted(sample_ids)}
        for sha, sample_ids in sorted(by_hash.items())
        if len(sample_ids) > 1
    ]


def _public_document_row(row: dict) -> dict:
    return {
        key: value
        for key, value in row.items()
        if key not in {"local_text_path", "text"}
    }


def _validate_spec(spec: dict) -> None:
    if spec.get("schema_version") != 1:
        raise ValueError("spec schema_version must be 1")
    documents = spec.get("documents")
    views = spec.get("views")
    if not isinstance(documents, list) or not documents:
        raise ValueError("spec documents must be a non-empty list")
    if not isinstance(views, list) or not views:
        raise ValueError("spec views must be a non-empty list")

    sample_ids = [str(row.get("sample_id") or "") for row in documents]
    if any(not value for value in sample_ids):
        raise ValueError("every document requires sample_id")
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError("document sample_ids must be unique")

    view_ids = [str(row.get("view_id") or "") for row in views]
    if any(not value for value in view_ids):
        raise ValueError("every view requires view_id")
    if len(view_ids) != len(set(view_ids)):
        raise ValueError("view_ids must be unique")

    known = set(sample_ids)
    for view in views:
        members = [str(value) for value in view.get("sample_ids", [])]
        if not members:
            raise ValueError(f"view {view.get('view_id')} requires sample_ids")
        if len(members) != len(set(members)):
            raise ValueError(f"view {view.get('view_id')} repeats a sample_id")
        missing = sorted(set(members) - known)
        if missing:
            raise ValueError(f"view {view.get('view_id')} references unknown samples: {missing}")
        budget = view.get("word_budget_per_source")
        if budget is not None and (not isinstance(budget, int) or budget <= 0):
            raise ValueError(f"view {view.get('view_id')} has invalid word budget")


def _build_view(
    view_spec: dict,
    documents_by_id: dict[str, dict],
    *,
    out_dir: Path,
) -> dict:
    view_id = str(view_spec["view_id"])
    budget = view_spec.get("word_budget_per_source")
    require_exact = bool(view_spec.get("require_exact_budget", False))
    view_dir = out_dir / "views" / view_id
    view_dir.mkdir(parents=True, exist_ok=True)

    view_rows: list[dict] = []
    for sample_id in view_spec["sample_ids"]:
        source = documents_by_id[str(sample_id)]
        source_text = Path(source["local_text_path"]).read_text(encoding="utf-8").strip()
        if require_exact and budget is not None and word_count(source_text) < budget:
            raise ValueError(
                f"view {view_id}: {sample_id} has fewer than required {budget} words"
            )
        visible = prefix_to_word_budget(source_text, budget)
        canon = canonicalize(visible)
        if require_exact and budget is not None and canon.word_count != budget:
            raise ValueError(
                f"view {view_id}: {sample_id} expected {budget} words, got {canon.word_count}"
            )
        local_path = view_dir / f"{sample_id}.txt"
        local_path.write_text(canon.text + "\n", encoding="utf-8")
        view_rows.append(
            {
                "sample_id": sample_id,
                "source_group": source["source_group"],
                "site_group": source["site_group"],
                "primary_register": source["primary_register"],
                "review_status": source["review_status"],
                "role": source["role"],
                "word_count": canon.word_count,
                "canonical_sha256": canon.sha256,
                "source_profile_word_count": source["profile_word_count"],
                "source_profile_canonical_sha256": source[
                    "profile_canonical_sha256"
                ],
                "local_text_path": str(local_path),
            }
        )

    total_words = sum(int(row["word_count"]) for row in view_rows)
    largest_words = max((int(row["word_count"]) for row in view_rows), default=0)
    by_site: collections.Counter[str] = collections.Counter()
    by_register: collections.Counter[str] = collections.Counter()
    for row in view_rows:
        by_site[str(row["site_group"])] += int(row["word_count"])
        by_register[str(row["primary_register"])] += int(row["word_count"])

    pending = sum(
        1 for row in view_rows if "pending" in str(row["review_status"]).casefold()
    )
    public_rows = [_public_document_row(row) for row in view_rows]
    return {
        "view_id": view_id,
        "status": view_spec.get("status"),
        "source_count": len(view_rows),
        "site_group_count": len(by_site),
        "primary_register_count": len(by_register),
        "word_budget_per_source": budget,
        "require_exact_budget": require_exact,
        "all_sources_exact_budget": bool(
            budget is not None
            and view_rows
            and all(int(row["word_count"]) == budget for row in view_rows)
        ),
        "total_words": total_words,
        "largest_source_words": largest_words,
        "largest_source_fraction": _fraction(largest_words, total_words),
        "pending_manual_audit_count": pending,
        "site_groups": {
            key: {
                "word_count": value,
                "fraction": _fraction(value, total_words),
            }
            for key, value in sorted(by_site.items())
        },
        "primary_registers": {
            key: {
                "word_count": value,
                "fraction": _fraction(value, total_words),
            }
            for key, value in sorted(by_register.items())
        },
        "canonical_hash_set_sha256": _hash_set_sha(public_rows),
        "documents": public_rows,
    }


def build_register_corpus(
    spec_path: Path,
    *,
    out_dir: Path,
    receipt_out: Path,
    timeout: int = 30,
) -> dict:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    _validate_spec(spec)

    document_specs = list(spec["documents"])
    sample_ids = {str(row["sample_id"]) for row in document_specs}
    raw_out = out_dir / "source-text"
    source_manifest = out_dir / "source-manifest.json"
    runtime = acquire_inventory(
        Path(spec["source_inventory"]),
        out_dir=raw_out,
        manifest_out=source_manifest,
        sample_ids=sample_ids,
        timeout=timeout,
    )
    if runtime.get("errors"):
        raise ValueError(f"source acquisition errors: {runtime['errors']}")

    acquired = {str(row["sample_id"]): row for row in runtime.get("results", [])}
    missing = sorted(sample_ids - set(acquired))
    if missing:
        raise ValueError(f"source acquisition omitted samples: {missing}")

    full_dir = out_dir / "full-cleaned"
    full_dir.mkdir(parents=True, exist_ok=True)
    documents: list[dict] = []
    for row_spec in document_specs:
        sample_id = str(row_spec["sample_id"])
        source = acquired[sample_id]
        expected_site = str(row_spec.get("site_group") or "")
        if expected_site and str(source.get("site_group")) != expected_site:
            raise ValueError(
                f"{sample_id}: site_group drift: expected {expected_site}, got {source.get('site_group')}"
            )
        source_text = Path(source["local_text_path"]).read_text(encoding="utf-8")
        cleaned = apply_cleanup_rule(source_text, str(row_spec["cleanup_rule"]))
        canon = canonicalize(cleaned)
        if canon.word_count <= 0:
            raise ValueError(f"{sample_id}: cleanup produced zero words")
        local_path = full_dir / f"{sample_id}.txt"
        local_path.write_text(canon.text + "\n", encoding="utf-8")
        documents.append(
            {
                "sample_id": sample_id,
                "source_group": source.get("source_group"),
                "site_group": source.get("site_group"),
                "date": source.get("date"),
                "source_html_sha256": source.get("source_html_sha256"),
                "source_canonical_sha256": source.get("canonical_sha256"),
                "source_word_count": int(source.get("word_count", 0)),
                "cleanup_rule": row_spec["cleanup_rule"],
                "profile_canonical_sha256": canon.sha256,
                "profile_word_count": canon.word_count,
                "words_removed_by_cleanup": max(
                    0, int(source.get("word_count", 0)) - canon.word_count
                ),
                "quality_flags_after_cleanup": canon.quality_flags,
                "redactions_after_cleanup": canon.redactions,
                "primary_register": row_spec["primary_register"],
                "registers": list(row_spec.get("registers", [])),
                "review_status": row_spec["review_status"],
                "role": row_spec["role"],
                "local_text_path": str(local_path),
            }
        )

    duplicate_groups = _duplicate_groups(documents)
    if duplicate_groups:
        raise ValueError(f"exact duplicate cleaned documents: {duplicate_groups}")

    documents_by_id = {str(row["sample_id"]): row for row in documents}
    views = [
        _build_view(view_spec, documents_by_id, out_dir=out_dir)
        for view_spec in spec["views"]
    ]
    public_documents = [_public_document_row(row) for row in documents]
    receipt = {
        "schema_version": 1,
        "date": spec.get("date"),
        "raw_or_canonical_prose_in_output": False,
        "corpus_status": spec.get("corpus_status"),
        "method_decision": spec.get("method_decision"),
        "method_note": spec.get("method_note"),
        "source_inventory": spec.get("source_inventory"),
        "document_count": len(public_documents),
        "pending_manual_audit_count": sum(
            1
            for row in public_documents
            if "pending" in str(row["review_status"]).casefold()
        ),
        "exact_duplicate_groups": [],
        "full_cleaned_hash_set_sha256": hashlib.sha256(
            "\n".join(
                f"{row['sample_id']}\t{row['profile_canonical_sha256']}\t{row['profile_word_count']}"
                for row in sorted(public_documents, key=lambda item: item["sample_id"])
            ).encode("utf-8")
        ).hexdigest(),
        "documents": public_documents,
        "views": views,
        "excluded_or_deferred": spec.get("excluded_or_deferred", []),
        "blocking_reasons": spec.get("blocking_reasons", []),
        "benchmark_eligible": False,
        "interpretation_rule": spec.get("interpretation_rule"),
    }
    encoded = json.dumps(receipt, ensure_ascii=False, sort_keys=True)
    for forbidden in ("local_text_path", "canonical_text", "raw_text"):
        if forbidden in encoded:
            raise ValueError(f"receipt unexpectedly contains {forbidden}")

    receipt_out.parent.mkdir(parents=True, exist_ok=True)
    receipt_out.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m pangram_lab.joel_register_corpus"
    )
    parser.add_argument(
        "spec",
        nargs="?",
        default="state/IDIOLECT-JOEL-REGISTER-CORPUS-SPEC-2026-08-18.json",
    )
    parser.add_argument(
        "--out-dir", default=".local/idiolect-corpus/joel-register-corpus"
    )
    parser.add_argument(
        "--receipt-out",
        default=".local/idiolect-corpus/joel-register-corpus-receipt.json",
    )
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args(argv)

    try:
        result = build_register_corpus(
            Path(args.spec),
            out_dir=Path(args.out_dir),
            receipt_out=Path(args.receipt_out),
            timeout=args.timeout,
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
