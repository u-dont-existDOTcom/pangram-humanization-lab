#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "state/experiments/spiritual-bypassing-r13-interaction-2026-08-13-results.json"
OUT = ROOT / "experiments/spiritual-bypassing-b-localize-r1-2026-08-13.json"
EXPECTED_SHA256 = "192f8d3d34f05a39208451b5ce740c569a546a3a66467818261c63561eab12a9"

SECTION_IDS = [
    "opening",
    "dark-side",
    "metta",
    "true-insight",
    "alternatives",
    "postscript",
]


def main() -> int:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    selected = next(row for row in source["results"] if row["id"] == "ALT_INVITATIONAL")
    if selected["text_sha256"] != EXPECTED_SHA256:
        raise SystemExit(f"owner-selected B hash mismatch: {selected['text_sha256']}")

    parts = [part.strip() for part in selected["text"].split("\n---\n")]
    if len(parts) != len(SECTION_IDS):
        raise SystemExit(f"expected {len(SECTION_IDS)} boundaries, got {len(parts)}")

    spec = {
        "format": "pangram-fixed-batch-v1",
        "experiment_id": "spiritual-bypassing-b-localize-r1-2026-08-13",
        "audit_id": "spiritual-bypassing-b-improve-2026-08-13",
        "variants": [
            {
                "id": section_id.upper().replace("-", "_"),
                "section_id": section_id,
                "text": text,
            }
            for section_id, text in zip(SECTION_IDS, parts)
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
