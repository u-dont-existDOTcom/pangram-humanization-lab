from __future__ import annotations

import json
from pathlib import Path

import pytest

from pangram_lab import gui_local as local
from pangram_lab import gui_local_structured as structured


class EmptyLocator:
    def count(self) -> int:
        return 0


class BodyLocator:
    def inner_text(self) -> str:
        return "authenticated Pangram shell"


class FakePage:
    def __init__(self) -> None:
        self.url = "about:blank"

    def goto(self, url: str, **_kwargs) -> None:
        self.url = url

    def locator(self, selector: str):
        if selector == "body":
            return BodyLocator()
        if selector == "a[href]":
            return EmptyLocator()
        raise AssertionError(f"unexpected selector: {selector}")

    def wait_for_timeout(self, _milliseconds: int) -> None:
        return None

    def screenshot(self, **_kwargs) -> None:
        return None


class FakeContext:
    def __init__(self, page: FakePage) -> None:
        self.pages = [page]
        self.listeners = []

    def on(self, event: str, listener) -> None:
        assert event == "response"
        self.listeners.append(listener)

    def remove_listener(self, event: str, listener) -> None:
        assert event == "response"
        if listener in self.listeners:
            self.listeners.remove(listener)


def test_read_only_recovery_persists_exact_no_match_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    text = "exact frozen recovery text"
    input_path = tmp_path / "input.txt"
    input_path.write_text(text, encoding="utf-8")
    output_root = tmp_path / "evidence"

    page = FakePage()
    context = FakeContext(page)
    closed: list[bool] = []
    persisted: list[tuple[Path, dict[str, object]]] = []

    monkeypatch.setattr(
        local,
        "_launch_persistent_context",
        lambda _config: (object(), context, page),
    )
    monkeypatch.setattr(
        local,
        "_close_local_session",
        lambda *_args: closed.append(True),
    )
    monkeypatch.setattr(
        local,
        "normalize_context_tabs",
        lambda _context, keep=None, **_kwargs: keep or page,
    )
    monkeypatch.setattr(
        local,
        "wait_for_authenticated_detector_input",
        lambda _page: object(),
    )

    config = local.LocalPlaywrightConfig(profile_dir=tmp_path / "profile")
    with pytest.raises(RuntimeError, match="no exact-matching Pangram stored history record"):
        structured.recover_existing_report(
            config,
            input_path,
            output_root=output_root,
            evidence_callback=lambda directory, receipt: persisted.append(
                (directory, dict(receipt))
            ),
        )

    item = local._prepare_inputs(
        [input_path],
        output_root=output_root,
        force=True,
        expected_sha256=None,
    )[0]
    directory = Path(str(item["directory"]))
    failure_path = directory / "failure.json"

    assert closed == [True]
    assert failure_path.is_file()
    assert not (directory / "result.json").exists()

    failure = json.loads(failure_path.read_text(encoding="utf-8"))
    assert failure["detector_submission_attempted"] is False
    assert failure["stage"] == "scan_history_candidates"
    assert failure["evidence_source"] == "recovered_existing_report"
    assert failure["read_only_recovery"] is True
    assert failure["exact_history_api_record_found"] is False
    assert failure["history_list_candidate_count"] == 0

    assert len(persisted) == 1
    persisted_directory, persisted_failure = persisted[0]
    assert persisted_directory == directory
    assert persisted_failure["detector_submission_attempted"] is False
    assert persisted_failure["read_only_recovery"] is True
