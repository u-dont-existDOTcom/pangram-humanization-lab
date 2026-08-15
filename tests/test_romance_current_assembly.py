from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts.assemble_romance_current import AssemblyError, apply_operations


def _write(root: Path, rel: str, text: str) -> str:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return rel


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_replace_exact_requires_one_match(tmp_path: Path) -> None:
    replacement = _write(tmp_path, "replacement.txt", "NEW")
    op = {"id": "x", "type": "replace_exact", "old": "OLD", "replacement_file": replacement}

    with pytest.raises(AssemblyError, match="exactly once"):
        apply_operations("no match", [op], tmp_path)

    with pytest.raises(AssemblyError, match="exactly once"):
        apply_operations("OLD and OLD", [op], tmp_path)


def test_delete_exact_requires_one_match(tmp_path: Path) -> None:
    op = {"id": "x", "type": "delete_exact", "old": "DELETE"}

    with pytest.raises(AssemblyError, match="exactly once"):
        apply_operations("nothing", [op], tmp_path)

    with pytest.raises(AssemblyError, match="exactly once"):
        apply_operations("DELETE DELETE", [op], tmp_path)


def test_replace_between_preserves_anchors(tmp_path: Path) -> None:
    replacement = _write(tmp_path, "replacement.txt", "NEW INTERIOR")
    op = {
        "id": "between",
        "type": "replace_between",
        "start_anchor": "START",
        "end_anchor": "END",
        "replacement_file": replacement,
    }

    out, records = apply_operations("before STARTold interiorEND after", [op], tmp_path)

    assert out == "before STARTNEW INTERIOREND after"
    assert records[0]["id"] == "between"


def test_replace_section_replaces_start_through_before_next_heading(tmp_path: Path) -> None:
    replacement = _write(tmp_path, "section.md", "# A\n\nnew\n\n")
    op = {
        "id": "section",
        "type": "replace_section",
        "start_anchor": "# A",
        "end_anchor": "# B",
        "replacement_file": replacement,
    }

    out, _ = apply_operations("prefix\n# A\n\nold\n\n# B\n\nkeep", [op], tmp_path)

    assert out == "prefix\n# A\n\nnew\n\n# B\n\nkeep"


def test_operation_manifest_records_old_and_new_sha256(tmp_path: Path) -> None:
    replacement = _write(tmp_path, "replacement.txt", "NEW")
    op = {"id": "x", "type": "replace_exact", "old": "OLD", "replacement_file": replacement}

    out, records = apply_operations("before OLD after", [op], tmp_path)

    assert out == "before NEW after"
    assert records == [
        {
            "id": "x",
            "type": "replace_exact",
            "old_sha256": _sha("OLD"),
            "new_sha256": _sha("NEW"),
            "old_bytes": 3,
            "new_bytes": 3,
        }
    ]
