from __future__ import annotations

import json
from pathlib import Path

import pytest

from pangram_lab import gui_local as local
from pangram_lab import gui_local_structured as structured


UUID = "aaaaaaaa-1111-2222-3333-bbbbbbbbbbbb"
API_URL = f"https://web.pangram.com/api/history/{UUID}/"


class FakeResponse:
    def __init__(self, url: str, payload: dict):
        self.url = url
        self.headers = {"content-type": "application/json"}
        self._payload = payload

    def json(self):
        return self._payload


class FakeLocator:
    def __init__(self, body: str = ""):
        self.body = body

    def inner_text(self):
        return self.body


class FakeField:
    def __init__(self):
        self.value = None

    def fill(self, value: str):
        self.value = value


class FakePage:
    def __init__(self):
        self.url = "about:blank"
        self.body = "current report shell"
        self.context = None

    def goto(self, url: str, **_kwargs):
        self.url = url

    def locator(self, selector: str):
        assert selector == "body"
        return FakeLocator(self.body)

    def wait_for_timeout(self, _milliseconds: int):
        return None

    def screenshot(self, **_kwargs):
        return None


class FakeContext:
    def __init__(self, page: FakePage):
        self.pages = [page]
        self.listeners = []
        page.context = self

    def on(self, event: str, listener):
        assert event == "response"
        self.listeners.append(listener)

    def remove_listener(self, event: str, listener):
        assert event == "response"
        if listener in self.listeners:
            self.listeners.remove(listener)

    def emit(self, response: FakeResponse):
        for listener in tuple(self.listeners):
            listener(response)


class FakeButton:
    def __init__(self, context: FakeContext, payload: dict):
        self.context = context
        self.payload = payload
        self.clicks = 0

    def click(self):
        self.clicks += 1
        self.context.emit(FakeResponse(API_URL, self.payload))


def _payload(text: str) -> dict:
    return {
        "uuid": UUID,
        "prompt": text,
        "model_id": "pangram-4",
        "response": {
            "overall": {
                "stage": "STAGE_SUCCESS",
                "version": "4.0",
                "fraction_ai": 0.1,
                "fraction_ai_assisted": 0.0,
                "fraction_human": 0.9,
                "headline": "Mostly Human Written",
                "prediction_short": "Human",
            }
        },
    }


def test_run_inputs_reserves_before_click_and_completes_from_exact_history_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = "one two three four"
    input_path = tmp_path / "input.txt"
    input_path.write_text(text, encoding="utf-8")
    output_root = tmp_path / "evidence"

    page = FakePage()
    context = FakeContext(page)
    field = FakeField()
    button = FakeButton(context, _payload(text))
    closed = []
    persisted = []

    monkeypatch.setattr(local, "_launch_persistent_context", lambda _config: (object(), context, page))
    monkeypatch.setattr(local, "_close_local_session", lambda *_args: closed.append(True))
    monkeypatch.setattr(local, "normalize_context_tabs", lambda _context, keep=None, **_kwargs: keep or page)
    monkeypatch.setattr(local, "wait_for_authenticated_detector_input", lambda _page: field)
    monkeypatch.setattr(local.gui_core, "detection_button", lambda _page: button)

    def fake_pdf(_page, path: Path):
        path.write_bytes(b"%PDF-1.4\n")
        return "test_pdf"

    monkeypatch.setattr(local, "capture_report_pdf", fake_pdf)

    config = local.LocalPlaywrightConfig(profile_dir=tmp_path / "profile")
    results = structured.run_inputs(
        config,
        [input_path],
        output_root=output_root,
        evidence_callback=lambda directory, receipt: persisted.append((directory, dict(receipt))),
    )

    assert field.value == text
    assert button.clicks == 1
    assert closed == [True]
    assert len(results) == 1
    result = results[0]
    assert result["status"] == "complete"
    assert result["parsed"]["summary_source"] == "stored_history_structured_result"
    assert result["parsed"]["summary"]["fraction_human"] == 0.9
    assert result["history_api_exact_identity"]["transport_match_mode"] == "exact_utf8"
    assert result["report_url"] == "https://www.pangram.com/history/<uuid>"
    assert UUID not in json.dumps(result)

    directory = local.gui_core.measurement_dir(output_root, result["input_sha256"])
    reservation = json.loads((directory / "submission-reservation.json").read_text(encoding="utf-8"))
    assert reservation["status"] == "paid_gui_submission_reserved"
    assert reservation["detector_submission_attempted"] is False
    assert (directory / "result.json").is_file()
    assert [receipt["status"] for _directory, receipt in persisted] == [
        "paid_gui_submission_reserved",
        "complete",
    ]


def test_incomplete_reservation_blocks_repeat_before_browser_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_path = tmp_path / "input.txt"
    input_path.write_text("alpha beta", encoding="utf-8")
    output_root = tmp_path / "evidence"
    item = local._prepare_inputs([input_path], output_root=output_root, force=False, expected_sha256=None)[0]
    directory = Path(str(item["directory"]))
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "submission-reservation.json").write_text("{}\n", encoding="utf-8")

    def forbidden_launch(_config):
        raise AssertionError("browser must not launch when incomplete reservation exists")

    monkeypatch.setattr(local, "_launch_persistent_context", forbidden_launch)
    config = local.LocalPlaywrightConfig(profile_dir=tmp_path / "profile")
    with pytest.raises(RuntimeError, match="durable paid-submission reservation"):
        structured.run_inputs(config, [input_path], output_root=output_root)


def test_record_listener_rejects_nonmatching_history_text() -> None:
    records = []
    listener = structured._record_listener("authorized text", records)
    listener(FakeResponse(API_URL, _payload("different text")))
    assert records == []
