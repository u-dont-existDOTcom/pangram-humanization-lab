from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.assemble_romance_current import AssemblyError, apply_operations


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = PROJECT_ROOT / "work" / "romance-current-assembly"
SCRIPT = PROJECT_ROOT / "scripts" / "assemble_romance_current.py"


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
        "Seeing someone’s highest potential is different from ignoring what is actually there.",
        "The next two tools reach in different directions. Imagination lets us examine futures we haven't lived. Psychedelics can sometimes get past defenses hiding what is already here. Either one can also give idealization better scenery.",
        "I didn’t know what a crucible was either. It’s basically a container where things get heated until they change.",
        "It shouldn’t be that serious. It really can be.",
        "Relationship itself can grow somebody who is not fully ready.",
        "Before entering something serious, have the conversation about flaws.",
        "That’s what I wish my dad had added. That’s what I’m trying to give you here.",
    ]
    for phrase in forbidden:
        assert phrase not in output
    assert "A tiny thing can end up carrying way more emotional weight than it should." in output


def test_vows_bible_rewrite_is_spoken_and_exact() -> None:
    _, output, _ = _assemble_real()
    old = (
        "We also find something like my warning in the New & Old Testaments. Ecclesiastes 5:4–6 explicitly states "
        "that it is better not to make a vow than to make one and not fulfill it, warning that God will be angry "
        "with your words and destroy your work if you say to the priest, \"I didn’t mean what I promised.\" It's also "
        "interesting that promising itself is almost an indicator of dishonesty: Matthew 5:33–37 (and parallel James "
        "5:12) teaches that believers should let their \"Yes\" be \"Yes\" and their \"No\" be \"No,\" warning that anything "
        "beyond this comes from evil."
    )
    replacement = (
        "We also find something like my warning in the New & Old Testaments. Ecclesiastes 5:4–6 says it is better not "
        "to make a vow than to make one and fail to keep it. If you tell the priest you didn’t mean what you promised, "
        "the passage warns that God will be angry and destroy your work.\n\n"
        "Matthew 5:33–37 and James 5:12 are stranger still beside wedding vows: let your “Yes” be “Yes” and your “No” "
        "be “No,” and anything beyond that comes from evil. To me, the extra promise itself starts to look suspicious. "
        "If your yes is trustworthy, why does it need another layer?"
    )
    assert old not in output
    assert replacement in output


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


def test_cli_materializes_output_manifest_and_diff(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.md"
    replacement = tmp_path / "replacement.md"
    spec = tmp_path / "spec.json"
    output = tmp_path / "current.md"
    manifest = tmp_path / "manifest.json"
    diff = tmp_path / "current.diff"

    baseline.write_text("A OLD B\n", encoding="utf-8")
    replacement.write_text("NEW", encoding="utf-8")
    spec.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "operations": [
                    {
                        "id": "replace",
                        "type": "replace_exact",
                        "old": "OLD",
                        "replacement_file": "replacement.md",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--baseline",
            str(baseline),
            "--spec",
            str(spec),
            "--output",
            str(output),
            "--manifest",
            str(manifest),
            "--diff",
            str(diff),
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    assert output.read_text(encoding="utf-8") == "A NEW B\n"
    manifest_obj = json.loads(manifest.read_text(encoding="utf-8"))
    assert manifest_obj["baseline_sha256"] == _sha("A OLD B\n")
    assert manifest_obj["final_sha256"] == _sha("A NEW B\n")
    assert manifest_obj["operation_count"] == 1
    assert manifest_obj["operations"][0]["id"] == "replace"
    diff_text = diff.read_text(encoding="utf-8")
    assert "-A OLD B" in diff_text
    assert "+A NEW B" in diff_text
