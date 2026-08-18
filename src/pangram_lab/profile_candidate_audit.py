from __future__ import annotations

import collections
import json
import re
from pathlib import Path

_LABEL_RE = re.compile(
    r"^\s*(?P<label>Q|Question|Message by [^:]{1,60}|[A-Z][A-Za-z .'-]{1,50})\s*:\s*",
    re.MULTILINE,
)


def dialogue_label_tokens(text: str) -> list[str]:
    """Return unique label prefixes that triggered dialogue-like structure.

    Only the prefix before ``:`` is returned; surrounding prose is never
    included in metadata receipts.
    """
    seen: set[str] = set()
    out: list[str] = []
    for match in _LABEL_RE.finditer(text):
        label = re.sub(r"\s+", " ", match.group("label").strip())
        key = label.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(label)
    return out


def audit_acquired_candidates(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows: list[dict] = []
    errors = manifest.get("errors", [])
    for row in manifest.get("results", []):
        path = Path(row["local_text_path"])
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        labels = dialogue_label_tokens(text)
        rows.append(
            {
                "sample_id": row.get("sample_id"),
                "site_group": row.get("site_group"),
                "source_group": row.get("source_group"),
                "canonical_sha256": row.get("canonical_sha256"),
                "word_count": int(row.get("word_count", 0)),
                "redactions": row.get("redactions", {}),
                "quality_flags": row.get("quality_flags", []),
                "dialogue_label_tokens": labels,
                "dialogue_label_token_count": len(labels),
            }
        )

    by_site = collections.defaultdict(lambda: {"sample_count": 0, "total_words": 0})
    for row in rows:
        site = row.get("site_group") or "unknown"
        by_site[site]["sample_count"] += 1
        by_site[site]["total_words"] += int(row["word_count"])

    return {
        "schema_version": 1,
        "raw_or_canonical_prose_in_output": False,
        "sample_count": len(rows),
        "error_count": len(errors),
        "errors": errors,
        "site_totals": dict(sorted(by_site.items())),
        "samples": sorted(rows, key=lambda row: str(row.get("sample_id"))),
    }
