from __future__ import annotations

import hashlib
from pathlib import Path

from pangram_lab import gui_browserbase as gui


def test_prepare_measurement_is_content_addressed_and_artifact_paths_are_stable(tmp_path: Path) -> None:
    text = "alpha beta gamma"
    input_path = tmp_path / "input.txt"
    input_path.write_text(text, encoding="utf-8")
    output_root = tmp_path / "runs"

    item = gui.prepare_measurement(input_path, output_root=output_root, force=False)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert item["input_sha256"] == digest
    assert item["word_count"] == 3
    assert Path(str(item["directory"])) == output_root / gui.MODEL_ID / digest

    paths = gui.artifact_paths(Path(str(item["directory"])))
    assert paths["result"].name == "result.json"
    assert paths["failure"].name == "failure.json"
    assert paths["pdf"].name == "report.pdf"


def test_completed_result_and_ambiguous_failure_are_separate_states(tmp_path: Path) -> None:
    text = "one two"
    input_path = tmp_path / "input.txt"
    input_path.write_text(text, encoding="utf-8")
    output_root = tmp_path / "runs"
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    directory = gui.measurement_dir(output_root, digest)
    directory.mkdir(parents=True)

    (directory / "failure.json").write_text(
        '{"status":"failed","runner_version":"pangram-gui-browserbase-v1",'
        '"detector_submission_attempted":true}\n',
        encoding="utf-8",
    )
    assert gui.ambiguous_submission_exists(output_root, digest) is True
    assert gui.completed_result_exists(output_root, digest) is False

    (directory / "result.json").write_text(
        '{"status":"complete","runner_version":"pangram-gui-browserbase-v1"}\n',
        encoding="utf-8",
    )
    assert gui.completed_result_exists(output_root, digest) is True


def test_report_text_parser_does_not_invent_missing_summary_fields() -> None:
    parsed = gui.parse_report_text("Human Written 12 Words\nhello world")
    assert parsed["summary"]["fraction_ai"] is None
    assert parsed["summary"]["fraction_human"] is None
    assert parsed["segments"][0]["label"] == "Human Written"
    assert parsed["segments"][0]["word_count"] == 12
