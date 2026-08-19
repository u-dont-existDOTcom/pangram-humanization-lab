from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).parents[1]


def _source(relative: str, *, compile_python: bool = True) -> str:
    path = ROOT / relative
    value = path.read_text(encoding="utf-8")
    if compile_python:
        compile(value, str(path), "exec")
    return value


def test_recover_resume_wrapper_uses_exact_api_recovery_and_paid_runner() -> None:
    source = _source(
        "scripts/pangram_local_romance_recover_resume_safe.sh",
        compile_python=False,
    )
    assert "pangram_local_romance_recover_part1_api.py" in source
    assert "pangram_local_romance_paid_api.py --execute" in source
    assert "pangram_local_romance_recover_part1_history.py 2>&1 | tee" not in source
    assert "pangram_local_romance_paid.py --execute 2>&1 | tee" not in source


def test_paid_api_runner_attaches_record_listener_before_detector_click() -> None:
    source = _source("scripts/pangram_local_romance_paid_api.py")
    listener = 'on("response", listener)'
    click = "button.click()"
    assert listener in source
    assert click in source
    assert source.index(listener) < source.index(click)
    assert "match_exact_history_record" in source
    assert "record.input_sha256 != digest" in source
    assert "parsed_word_count" not in source


def test_part1_api_recovery_has_no_detector_click_path() -> None:
    source = _source("scripts/pangram_local_romance_recover_part1_api.py")
    assert "match_exact_history_record" in source
    assert "button.click()" not in source
    assert "detection_button" not in source
