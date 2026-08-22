from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .call_budget import SectionCallCapReached
from .call_stats import CallStats
from .result_paths import new_result_envelope
from .text_sources import TextSourceError, validate_text_source


FORMAT = "pangram-fixed-batch-v1"
VALID_BUDGET_SCOPES = {"section", "aggregate"}


def load_spec(path: Path, max_variants: int = 8) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("format") != FORMAT:
        raise ValueError(f"unsupported fixed-batch format; expected {FORMAT}")
    experiment_id = data.get("experiment_id")
    if not isinstance(experiment_id, str) or not experiment_id.strip():
        raise ValueError("experiment_id must be a non-empty string")
    audit_id = data.get("audit_id")
    if audit_id is not None and (not isinstance(audit_id, str) or not audit_id.strip()):
        raise ValueError("audit_id must be a non-empty string when supplied")
    variants = data.get("variants")
    if not isinstance(variants, list) or not variants:
        raise ValueError("variants must be a non-empty list")
    if len(variants) > max_variants:
        raise ValueError(f"variant count {len(variants)} exceeds max {max_variants}")
    seen: set[str] = set()
    for variant in variants:
        if not isinstance(variant, dict):
            raise ValueError("each variant must be an object")
        variant_id = variant.get("id")
        text = variant.get("text")
        text_source = variant.get("text_source")
        if not isinstance(variant_id, str) or not variant_id.strip():
            raise ValueError("variant id must be a non-empty string")
        if variant_id in seen:
            raise ValueError(f"duplicate variant id: {variant_id}")
        seen.add(variant_id)
        has_inline_text = isinstance(text, str) and bool(text)
        has_text_source = text_source is not None
        if has_inline_text == has_text_source:
            raise ValueError(
                f"variant {variant_id} must provide exactly one of non-empty text or text_source"
            )
        if text is not None and not has_inline_text:
            raise ValueError(f"variant {variant_id} text must be non-empty when supplied")
        if has_text_source:
            try:
                validate_text_source(text_source)
            except TextSourceError as exc:
                raise ValueError(f"variant {variant_id} invalid text_source: {exc}") from exc
        section_id = variant.get("section_id")
        budget_scope = variant.get("budget_scope", "section")
        allow_exact_repeat = variant.get("allow_exact_repeat", False)
        if budget_scope not in VALID_BUDGET_SCOPES:
            raise ValueError(
                f"variant {variant_id} budget_scope must be one of {sorted(VALID_BUDGET_SCOPES)}"
            )
        if not isinstance(allow_exact_repeat, bool):
            raise ValueError(f"variant {variant_id} allow_exact_repeat must be boolean")
        if audit_id is not None and (not isinstance(section_id, str) or not section_id.strip()):
            raise ValueError(f"variant {variant_id} section_id must be a non-empty string for audit {audit_id}")
        if audit_id is None and section_id is not None:
            raise ValueError("section_id requires top-level audit_id")
        if audit_id is None and "budget_scope" in variant:
            raise ValueError("budget_scope requires top-level audit_id")
        if audit_id is None and "allow_exact_repeat" in variant:
            raise ValueError("allow_exact_repeat requires top-level audit_id")
    return data


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write(path: Path, aggregate: dict[str, Any]) -> None:
    path.write_text(json.dumps(aggregate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_batch(
    spec: dict[str, Any],
    *,
    client: Any,
    cache: Any,
    output_path: Path,
    call_ledger: Any | None = None,
) -> dict[str, Any]:
    experiment_id = spec["experiment_id"]
    aggregate = new_result_envelope(spec)
    stats = CallStats(call_ledger) if call_ledger is not None else None
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    for variant in spec["variants"]:
        variant_id = variant["id"]
        text = variant.get("text")
        if not isinstance(text, str) or not text:
            raise ValueError(f"variant {variant_id} text source was not resolved before run_batch")
        section_id = variant.get("section_id")
        budget_scope = variant.get("budget_scope", "section")
        allow_exact_repeat = variant.get("allow_exact_repeat", False)
        measurement_key = f"{experiment_id}_{variant_id}"
        try:
            if call_ledger is None:
                detector = client.detect_cached(text, cache, measurement_key=measurement_key)
            else:
                kwargs = {
                    "measurement_key": measurement_key,
                    "section_id": section_id,
                    "budget_scope": budget_scope,
                }
                # Preserve the established ordinary-client interface. The
                # repeat override is exceptional and is passed only when a
                # variant explicitly opts into it.
                if allow_exact_repeat:
                    kwargs["allow_exact_repeat"] = True
                detector = client.detect_cached(text, cache, **kwargs)
        except SectionCallCapReached:
            model = getattr(client, "model", "pangram-4")
            version = getattr(client, "expected_version", "4.0")
            handoff = call_ledger.write_handoff(
                section_id,
                model,
                version,
                completed_results=aggregate["results"],
            )
            aggregate["status"] = "section_call_cap_reached"
            aggregate["handoff_path"] = str(handoff)
            aggregate["call_accounting"] = stats.summary()
            _write(output_path, aggregate)
            raise
        row: dict[str, Any] = {
            "id": variant_id,
            "measurement_key": measurement_key,
            "text": text,
            "text_sha256": text_sha256(text),
            "detector": detector,
        }
        if variant.get("text_source") is not None:
            row["text_source"] = variant["text_source"]
        if section_id is not None:
            row["section_id"] = section_id
            row["budget_scope"] = budget_scope
        if allow_exact_repeat:
            row["allow_exact_repeat"] = True
        aggregate["results"].append(row)
        if stats is not None:
            stats.note(
                section_id,
                getattr(client, "model", "pangram-4"),
                getattr(client, "expected_version", "4.0"),
                measurement_key,
                detector,
            )
            aggregate["call_accounting"] = stats.summary()
        _write(output_path, aggregate)
    return aggregate
