from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.assemble_romance_current import AssemblyError, apply_operations


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = PROJECT_ROOT / "work" / "romance-current-assembly"


def _write(root: Path, rel: str, text: str) -> str:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return rel


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _assemble_real() -> tuple[str, str, list[dict]]:
    baseline = (WORK_ROOT / "baseline.md").read_text(encoding="utf-8")
    spec = json.loads((WORK_ROOT / "assembly-spec.json").read_text(encoding="utf-8"))
    output, records = apply_operations(baseline, spec["operations"], WORK_ROOT)
    return baseline, output, records


def _native_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.startswith("[NATIVE ")]


def _section(text: str, start: str, end: str) -> str:
    assert text.count(start) == 1
    assert text.count(end) == 1
    start_at = text.index(start)
    end_at = text.index(end)
    assert start_at < end_at
    return text[start_at:end_at]


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


def test_full_assembly_preserves_all_native_markers() -> None:
    baseline, output, _ = _assemble_real()
    assert _native_lines(output) == _native_lines(baseline)


def test_full_assembly_preserves_hd_and_does_not_substitute_hale() -> None:
    _, output, _ = _assemble_real()
    assert "With Bee, Key, and H.D., there was always some sense" in output
    assert "With Bee, Key, and Hâle, there was always some sense" not in output


def test_full_assembly_contains_exact_owner_opening_and_closing() -> None:
    _, output, _ = _assemble_real()
    opening = (WORK_ROOT / "replacements" / "opening.md").read_text(encoding="utf-8").strip()
    closing = (WORK_ROOT / "replacements" / "closing.md").read_text(encoding="utf-8").strip()
    assert opening in output
    assert closing in output


def test_full_assembly_removes_superseded_aftercare() -> None:
    _, output, _ = _assemble_real()
    forbidden = [
        "Good sentence. Not exactly the whole curriculum.",
        "If the eros does fade, maybe the agape is enough to keep us together.",
        "I didn’t know what a crucible was either. It’s basically a container where things get heated until they change.",
        "Relationship itself can grow somebody who is not fully ready.",
        "Before entering something serious, have the conversation about flaws.",
        "That’s what I wish my dad had added. That’s what I’m trying to give you here.",
    ]
    for phrase in forbidden:
        assert phrase not in output


def test_locked_casual_section_is_byte_identical_to_baseline() -> None:
    baseline, output, _ = _assemble_real()
    start = "## Can Casual Sex or a Situationship Actually Be Honest?"
    end = "---\n\n# Should you be in a relationship at all?"
    assert _section(output, start, end) == _section(baseline, start, end)


def test_untouched_prefix_before_share_and_native_button_survive() -> None:
    baseline, output, _ = _assemble_real()
    share = "[Share](%%share_url%%)"
    button = "[NATIVE BUTTON — Subscribe now — %%checkout_url%%]"
    assert output[: output.index(share)] == baseline[: baseline.index(share)]
    assert button in baseline
    assert output.endswith(button + "\n") or output.endswith(button)
