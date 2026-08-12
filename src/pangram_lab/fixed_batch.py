from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


FORMAT = "pangram-fixed-batch-v1"


def load_spec(path: Path, max_variants: int = 8) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("format") != FORMAT:
        raise ValueError(f"unsupported fixed-batch format; expected {FORMAT}")
    experiment_id = data.get("experiment_id")
    if not isinstance(experiment_id, str) or not experiment_id.strip():
        raise ValueError("experiment_id must be a non-empty string")
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
        if not isinstance(variant_id, str) or not variant_id.strip():
            raise ValueError("variant id must be a non-empty string")
        if variant_id in seen:
            raise ValueError(f"duplicate variant id: {variant_id}")
        seen.add(variant_id)
        if not isinstance(text, str) or not text:
            raise ValueError(f"variant {variant_id} text must be non-empty")
    return data


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
