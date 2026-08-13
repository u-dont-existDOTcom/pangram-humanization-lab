from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .review_state import ReviewState


def result_review_metadata(result: dict[str, Any]) -> dict[str, Any]:
    variants = []
    sections = []
    for row in result.get("results", []):
        section_id = row.get("section_id")
        if section_id and section_id not in sections:
            sections.append(section_id)
        detector = row.get("detector") or {}
        variants.append({
            "id": row.get("id"),
            "section_id": section_id,
            "prediction_short": detector.get("prediction_short"),
            "fraction_human": detector.get("fraction_human"),
            "fraction_ai": detector.get("fraction_ai"),
            "fraction_ai_assisted": detector.get("fraction_ai_assisted"),
        })
    return {
        "experiment_id": result.get("experiment_id"),
        "audit_id": result.get("audit_id"),
        "sections": sections,
        "variants": variants,
    }


def register_result(root: Path | str, output_path: Path | str, source_ref: str, result: dict[str, Any]) -> dict[str, Any]:
    root = Path(root).resolve()
    output_path = Path(output_path)
    if not output_path.is_absolute():
        output_path = root / output_path
    source_path = str(output_path.relative_to(root))
    source_sha256 = hashlib.sha256(output_path.read_bytes()).hexdigest()
    return ReviewState(root).register(source_path, source_ref, source_sha256, result_review_metadata(result))
