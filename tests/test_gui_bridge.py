from __future__ import annotations

import hashlib
import json
import subprocess
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

from pangram_lab import gui_bridge
from pangram_lab.call_budget import PangramCallLedger


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _source_markdown() -> bytes:
    return (
        "Draft-only header\n\n"
        "# Introduction\n\n"
        "Visible **opening** with [a source](https://example.test/private).\n\n"
        "**[EXISTING NATIVE EDITOR PLACEHOLDER]**\n\n"
        "## What follows\n\n"
        "- First item\n"
        "2. Second `item`\n\n"
        "---\n"
    ).encode("utf-8")


def _visible_text() -> str:
    return (
        "Introduction\n\n"
        "Visible opening with a source.\n\n"
        "What follows\n\n"
        "First item\n"
        "Second item\n"
    )


def _request_dict(operation: str = "recover", *, request_id: str | None = None) -> dict:
    raw = _source_markdown()
    text = _visible_text()
    value = {
        "schema_version": 1,
        "request_id": request_id or str(uuid.uuid4()),
        "operation": operation,
    }
    if operation != "verify":
        value |= {
            "source": {
                "repository": "u-dont-existDOTcom/joel-articles",
                "ref": "refs/heads/agent/somatic-example",
                "commit": "a" * 40,
                "path": "articles/somatic-therapies/example.md",
                "file_sha256": _sha(raw),
                "text_sha256": _sha(text.encode("utf-8")),
                "text_word_count": len(text.split()),
            },
            "extraction_profile": gui_bridge.EXTRACTION_PROFILE,
            "audit_id": "somatic-test",
            "section_id": "whole-article",
        }
    if operation == "measure":
        value["call_cap"] = 2
    return value


def _raw_request(operation: str = "recover", *, request_id: str | None = None) -> bytes:
    return (json.dumps(_request_dict(operation, request_id=request_id)) + "\n").encode()


class _SourceClient:
    def fetch_blob(self, _source: gui_bridge.SourceSpec) -> bytes:
        return _source_markdown()


class _FakeGitSync:
    instances: list["_FakeGitSync"] = []

    def __init__(self, *_args, **_kwargs):
        self.calls: list[tuple[tuple[Path, ...], str]] = []
        self.__class__.instances.append(self)

    def sync_paths(self, paths, reason):
        self.calls.append((tuple(Path(path) for path in paths), reason))


def _write_completed_cache(root: Path, request: gui_bridge.BridgeRequest) -> Path:
    assert request.source is not None
    text_sha = request.source.text_sha256
    directory = root / "state" / "gui-runs" / "pangram-4" / text_sha
    directory.mkdir(parents=True, exist_ok=True)
    report_body = b"stored report body\n"
    report_pdf = b"%PDF-1.4\ntest evidence\n"
    (directory / "report-body.txt").write_bytes(report_body)
    (directory / "report.pdf").write_bytes(report_pdf)
    receipt = {
        "status": "complete",
        "transport": "local_playwright",
        "model": "pangram-4",
        "input_sha256": text_sha,
        "word_count": request.source.text_word_count,
        "source": {
            "repository": request.source.repository,
            "source_commit": request.source.commit,
            "source_path": request.source.path,
            "source_file_sha256": request.source.file_sha256,
        },
        "parsed": {
            "detector_stage": "STAGE_SUCCESS",
            "detector_version": "4.0",
            "summary_source": "stored_history_structured_result",
            "structured_result_field_path": ["response", "overall"],
            "summary": {
                "fraction_ai": 0.8451970816,
                "fraction_ai_assisted": 0.0,
                "fraction_human": 0.1548029035,
            },
            "headline": "AI Detected",
            "prediction_short": "AI",
            "segments": [],
        },
        "history_api_exact_identity": {
            "authorized_text_sha256": text_sha,
            "stored_text_sha256": text_sha,
            "exact_text_sha256": text_sha,
            "transport_match_mode": "exact_utf8",
        },
        "report_body_sha256": _sha(report_body),
        "report_pdf_sha256": _sha(report_pdf),
        "detector_submission_attempted": True,
    }
    (directory / "result.json").write_text(json.dumps(receipt) + "\n", encoding="utf-8")
    return directory


def test_trusted_extraction_profile_preserves_visible_structure() -> None:
    text, counts = gui_bridge.extract_reader_visible(
        _source_markdown().decode(), gui_bridge.EXTRACTION_PROFILE
    )
    assert text == _visible_text()
    assert counts == {
        "excluded_native_editor_placeholders": 1,
        "excluded_link_destinations": 1,
        "excluded_non_prose_thematic_breaks": 1,
        "retained_heading_text_lines": 2,
        "retained_list_text_lines": 2,
    }
    assert "https://" not in text
    assert "**" not in text


@pytest.mark.parametrize("operation", ["verify", "recover", "localize", "measure"])
def test_fixed_schema_accepts_only_supported_operations(operation: str) -> None:
    request = gui_bridge.parse_request(_raw_request(operation))
    assert request.operation == operation
    assert request.source is None if operation == "verify" else request.source is not None


@pytest.mark.parametrize(
    "mutation,match",
    [
        (lambda value: value.update({"shell": "rm -rf /"}), "unsupported field"),
        (lambda value: value["source"].update({"repository": "attacker/repo"}), "trusted registry"),
        (lambda value: value["source"].update({"path": "scripts/payload.md"}), "trusted prefixes"),
        (lambda value: value["source"].update({"path": "articles/../payload.md"}), "normalized"),
        (lambda value: value["source"].update({"ref": "main"}), "fully qualified"),
        (lambda value: value.update({"extraction_profile": "request-provided-code"}), "fixed named"),
    ],
)
def test_schema_rejects_code_fields_and_untrusted_source_coordinates(mutation, match: str) -> None:
    value = _request_dict("measure")
    mutation(value)
    with pytest.raises(gui_bridge.RequestValidationError, match=match):
        gui_bridge.parse_request(json.dumps(value).encode())


@pytest.mark.parametrize(
    "raw,match",
    [
        (b'{"schema_version":1,"schema_version":1}', "duplicate JSON key"),
        (b'{"schema_version":NaN}', "non-finite"),
        (b"\xef\xbb\xbf{}", "BOM"),
        (b"\xff", "valid UTF-8"),
        (b'{"x":"\\u0001"}', "control"),
    ],
)
def test_schema_rejects_noncanonical_json(raw: bytes, match: str) -> None:
    with pytest.raises(gui_bridge.RequestValidationError, match=match):
        gui_bridge.parse_request(raw)


def test_source_tree_rejects_symlink_even_under_allowlisted_path(monkeypatch) -> None:
    request = gui_bridge.parse_request(_raw_request("recover"))
    assert request.source is not None
    responses = iter(
        [
            "1" * 40 + "\n",
            "040000\ttree\t" + "2" * 40 + "\n",
            "040000\ttree\t" + "3" * 40 + "\n",
            "120000\tblob\t" + "4" * 40 + "\n",
        ]
    )
    client = gui_bridge.GitHubSourceClient()
    monkeypatch.setattr(
        client,
        "_run",
        lambda *_args, **_kwargs: SimpleNamespace(stdout=next(responses)),
    )
    with pytest.raises(gui_bridge.BridgeBlocked, match="regular Git blob"):
        client.verify_regular_blob(request.source)


def test_cache_hit_returns_exact_score_without_measurement(monkeypatch, tmp_path: Path) -> None:
    request = gui_bridge.parse_request(_raw_request("recover"))
    _write_completed_cache(tmp_path, request)
    PangramCallLedger(tmp_path, "somatic-test", cap=2).reserve_paid_call(
        section_id="different-section",
        model="pangram-4",
        version="4.0",
        measurement_key="gui:" + "f" * 64,
        text_sha256="f" * 64,
        word_count=1,
    )
    measured: list[object] = []
    monkeypatch.setattr(gui_bridge, "GitSync", _FakeGitSync)
    executor = gui_bridge.BridgeExecutor(
        tmp_path,
        source_client=_SourceClient(),
        cache_root=tmp_path / "inputs",
        measure_runner=lambda *_args: measured.append(True),
    )

    result = executor.execute(request)

    assert result["outcome"] == "cache_hit"
    assert result["request_submission_attempted"] is False
    assert result["score"] == {
        "fraction_ai": 0.8451970816,
        "fraction_ai_assisted": 0.0,
        "fraction_human": 0.1548029035,
        "stage": "STAGE_SUCCESS",
        "version": "4.0",
        "headline": "AI Detected",
        "prediction_short": "AI",
        "source": "response.overall",
    }
    assert measured == []
    assert (tmp_path / result["artifacts"]["localization"]["path"]).is_file()
    executor.execute(request)
    ledger = PangramCallLedger(tmp_path, "somatic-test", cap=2)
    assert ledger.section_summary(
        "whole-article", "pangram-4", "4.0"
    )["cache_hits"] == 1


def test_first_read_only_cache_request_does_not_invent_paid_cap(
    monkeypatch, tmp_path: Path
) -> None:
    request = gui_bridge.parse_request(_raw_request("recover"))
    _write_completed_cache(tmp_path, request)
    monkeypatch.setattr(gui_bridge, "GitSync", _FakeGitSync)
    gui_bridge.BridgeExecutor(
        tmp_path,
        source_client=_SourceClient(),
        cache_root=tmp_path / "inputs",
    ).execute(request)
    assert not (
        tmp_path / "state" / "pangram-call-ledgers" / "somatic-test.json"
    ).exists()


def test_ambiguous_reservation_recovers_before_any_repeat(monkeypatch, tmp_path: Path) -> None:
    request = gui_bridge.parse_request(_raw_request("measure"))
    assert request.source is not None
    directory = (
        tmp_path / "state" / "gui-runs" / "pangram-4" / request.source.text_sha256
    )
    directory.mkdir(parents=True)
    (directory / "reservation.json").write_text("{}\n", encoding="utf-8")
    events: list[str] = []

    def recover(*_args) -> None:
        events.append("recover")
        _write_completed_cache(tmp_path, request)

    monkeypatch.setattr(gui_bridge, "GitSync", _FakeGitSync)
    executor = gui_bridge.BridgeExecutor(
        tmp_path,
        source_client=_SourceClient(),
        cache_root=tmp_path / "inputs",
        recover_runner=recover,
        measure_runner=lambda *_args: events.append("measure"),
    )

    result = executor.execute(request)

    assert events == ["recover"]
    assert result["outcome"] == "recovered"
    assert result["request_submission_attempted"] is False


def test_ambiguous_recovery_failure_blocks_repeat(monkeypatch, tmp_path: Path) -> None:
    request = gui_bridge.parse_request(_raw_request("measure"))
    assert request.source is not None
    directory = (
        tmp_path / "state" / "gui-runs" / "pangram-4" / request.source.text_sha256
    )
    directory.mkdir(parents=True)
    (directory / "reservation.json").write_text("{}\n", encoding="utf-8")
    measured: list[object] = []

    def recover(*_args) -> None:
        raise gui_bridge.BridgeBlocked("recover_failed", "still ambiguous", ambiguous=True)

    monkeypatch.setattr(gui_bridge, "GitSync", _FakeGitSync)
    executor = gui_bridge.BridgeExecutor(
        tmp_path,
        source_client=_SourceClient(),
        cache_root=tmp_path / "inputs",
        recover_runner=recover,
        measure_runner=lambda *_args: measured.append(True),
    )

    with pytest.raises(gui_bridge.BridgeBlocked) as caught:
        executor.execute(request)
    assert caught.value.ambiguous is True
    assert measured == []


def test_durable_paid_ledger_reservation_also_forces_recovery(monkeypatch, tmp_path: Path) -> None:
    request = gui_bridge.parse_request(_raw_request("measure"))
    assert request.source is not None
    ledger = PangramCallLedger(tmp_path, "somatic-test", cap=2)
    ledger.reserve_paid_call(
        section_id="whole-article",
        model="pangram-4",
        version="4.0",
        measurement_key=f"gui:{request.source.text_sha256}",
        text_sha256=request.source.text_sha256,
        word_count=request.source.text_word_count,
    )
    events: list[str] = []

    def recover(*_args) -> None:
        events.append("recover")
        _write_completed_cache(tmp_path, request)

    monkeypatch.setattr(gui_bridge, "GitSync", _FakeGitSync)
    result = gui_bridge.BridgeExecutor(
        tmp_path,
        source_client=_SourceClient(),
        cache_root=tmp_path / "inputs",
        recover_runner=recover,
        measure_runner=lambda *_args: events.append("measure"),
    ).execute(request)

    assert events == ["recover"]
    assert result["outcome"] == "recovered"


def test_paid_reservation_is_found_across_audit_and_section_names(tmp_path: Path) -> None:
    request = gui_bridge.parse_request(_raw_request("measure"))
    assert request.source is not None
    other = PangramCallLedger(tmp_path, "different-audit", cap=2)
    other.reserve_paid_call(
        section_id="different-section",
        model="pangram-4",
        version="4.0",
        measurement_key=f"gui:{request.source.text_sha256}",
        text_sha256=request.source.text_sha256,
        word_count=request.source.text_word_count,
    )
    state = gui_bridge._ambiguous_state(tmp_path, request, request.source.text_sha256)
    assert state is not None
    assert state["recover_before_repeat_required"] is True
    assert state["recovery_target_source"] == "paid_call_ledger"
    assert state["call_ledger_paths"] == [
        "state/pangram-call-ledgers/different-audit.json"
    ]


@pytest.mark.parametrize(
    "sections",
    [
        {"broken": []},
        {"broken": {"events": {}}},
        {"broken": {"events": ["not-an-event"]}},
    ],
)
def test_malformed_ledger_structure_fails_ambiguous(
    tmp_path: Path, sections: object
) -> None:
    request = gui_bridge.parse_request(_raw_request("measure"))
    assert request.source is not None
    ledger = tmp_path / "state" / "pangram-call-ledgers" / "broken.json"
    ledger.parent.mkdir(parents=True)
    ledger.write_text(json.dumps({"sections": sections}))
    with pytest.raises(gui_bridge.BridgeBlocked) as caught:
        gui_bridge._ambiguous_state(tmp_path, request, request.source.text_sha256)
    assert caught.value.ambiguous is True
    assert caught.value.code == "call_ledger_invalid"


def test_paid_call_reservation_is_idempotent_by_measurement_key(tmp_path: Path) -> None:
    ledger = PangramCallLedger(tmp_path, "audit", cap=2)
    kwargs = {
        "section_id": "section",
        "model": "pangram-4",
        "version": "4.0",
        "measurement_key": "gui:" + "a" * 64,
        "text_sha256": "a" * 64,
        "word_count": 1200,
    }
    first = ledger.reserve_paid_call(**kwargs)
    second = ledger.reserve_paid_call(**kwargs)
    assert first["paid_api_calls"] == second["paid_api_calls"] == 1
    assert first["reservation_created"] is True
    assert second["reservation_created"] is False
    with pytest.raises(ValueError, match="different text"):
        ledger.reserve_paid_call(**(kwargs | {"text_sha256": "b" * 64}))


def test_recover_uses_existing_audit_cap_instead_of_defaulting_to_six(tmp_path: Path) -> None:
    request = gui_bridge.parse_request(_raw_request("recover"))
    ledger = PangramCallLedger(tmp_path, "somatic-test", cap=2)
    ledger.record_cache_hit("old", "pangram-4", "4.0", "gui:old", "a" * 64)
    loaded = gui_bridge.BridgeExecutor(tmp_path, source_client=_SourceClient())._ledger(request)
    assert loaded.cap == 2


class _VerifyExecutor:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, request: gui_bridge.BridgeRequest) -> dict:
        self.calls += 1
        assert request.operation == "verify"
        return {
            "status": "complete",
            "outcome": "verified",
            "request_submission_attempted": False,
            "verification": {"verified": True, "submitted": False},
            "ambiguity": None,
            "blocked": None,
        }


def test_worker_publishes_result_and_restart_resumes_idempotently(tmp_path: Path) -> None:
    request_id = str(uuid.uuid4())
    raw = _raw_request("verify", request_id=request_id)
    queue_path = f"state/pangram-gui-bridge/requests/{request_id}.json"
    first_executor = _VerifyExecutor()
    first = gui_bridge.BridgeWorker(
        tmp_path, first_executor, git_sync=_FakeGitSync()
    ).process(queue_path, "a" * 40, raw)
    result_path = (
        tmp_path / "state" / "pangram-gui-bridge" / "results" / f"{request_id}.json"
    )
    assert first["status"] == "complete"
    assert json.loads(result_path.read_text())["outcome"] == "verified"

    restarted_executor = _VerifyExecutor()
    second = gui_bridge.BridgeWorker(
        tmp_path, restarted_executor, git_sync=_FakeGitSync()
    ).process(queue_path, "a" * 40, raw)
    assert second["request_sha256"] == first["request_sha256"]
    assert first_executor.calls == 1
    assert restarted_executor.calls == 0


def test_worker_retries_same_request_after_nonterminal_failure(tmp_path: Path) -> None:
    request_id = str(uuid.uuid4())
    raw = _raw_request("verify", request_id=request_id)
    queue_path = f"state/pangram-gui-bridge/requests/{request_id}.json"

    class FailingExecutor:
        def execute(self, _request):
            raise RuntimeError("temporary failure")

    first = gui_bridge.BridgeWorker(
        tmp_path, FailingExecutor(), git_sync=_FakeGitSync()
    ).process(queue_path, "a" * 40, raw)
    assert first["status"] == "failed"

    restarted = _VerifyExecutor()
    second = gui_bridge.BridgeWorker(
        tmp_path, restarted, git_sync=_FakeGitSync()
    ).process(queue_path, "a" * 40, raw)
    assert second["status"] == "complete"
    assert restarted.calls == 1


def test_worker_reports_paid_finalization_failure_as_ambiguous_with_identity(
    tmp_path: Path,
) -> None:
    request_id = str(uuid.uuid4())
    raw = _raw_request("measure", request_id=request_id)
    request = gui_bridge.parse_request(raw)
    assert request.source is not None
    reservation = (
        tmp_path
        / "state"
        / "pangram-gui-bridge"
        / "paid-reservations"
        / f"{request.source.text_sha256}.json"
    )
    reservation.parent.mkdir(parents=True)
    reservation.write_text(
        json.dumps(
            {
                "text_sha256": request.source.text_sha256,
                "reserved_at_utc": "2026-08-27T12:00:00Z",
            }
        )
    )

    class FinalizationFailure:
        def execute(self, _request):
            raise RuntimeError("evidence publication failed after runner return")

    queue_path = f"state/pangram-gui-bridge/requests/{request_id}.json"
    result = gui_bridge.BridgeWorker(
        tmp_path, FinalizationFailure(), git_sync=_FakeGitSync()
    ).process(queue_path, "a" * 40, raw)
    assert result["status"] == "ambiguous"
    assert result["request_submission_attempted"] is None
    assert result["input"]["text_sha256"] == request.source.text_sha256
    assert result["ambiguity"]["bridge_reservation_path"].endswith(
        f"{request.source.text_sha256}.json"
    )


def test_duplicate_request_id_with_different_bytes_is_blocked(tmp_path: Path) -> None:
    request_id = str(uuid.uuid4())
    queue_path = f"state/pangram-gui-bridge/requests/{request_id}.json"
    worker = gui_bridge.BridgeWorker(tmp_path, _VerifyExecutor(), git_sync=_FakeGitSync())
    worker.process(queue_path, "a" * 40, _raw_request("verify", request_id=request_id))
    changed = json.dumps(
        {
            "schema_version": 1,
            "request_id": request_id,
            "operation": "verify",
        },
        separators=(",", ":"),
    ).encode()
    result = worker.process(queue_path, "b" * 40, changed)
    assert result["status"] == "blocked"
    assert result["blocked"]["code"] == "duplicate_request_id_conflict"


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def test_queue_accepts_additions_then_refuses_modified_requests(tmp_path: Path) -> None:
    bare = tmp_path / "origin.git"
    local = tmp_path / "local"
    _git(tmp_path, "init", "--bare", str(bare))
    local.mkdir()
    _git(local, "init", "-b", "agent/pangram-local-playwright-gpt-20260818")
    _git(local, "config", "user.email", "bridge-test@example.test")
    _git(local, "config", "user.name", "Bridge Test")
    (local / "README.md").write_text("base\n")
    _git(local, "add", "README.md")
    _git(local, "commit", "-m", "base")
    _git(local, "remote", "add", "origin", str(bare))
    _git(local, "push", "origin", "HEAD:refs/heads/agent/pangram-local-playwright-gpt-20260818")
    _git(local, "switch", "-c", "automation/pangram-gui-bridge-queue")
    request_id = str(uuid.uuid4())
    relative = Path("state/pangram-gui-bridge/requests") / f"{request_id}.json"
    path = local / relative
    path.parent.mkdir(parents=True)
    path.write_bytes(_raw_request("verify", request_id=request_id))
    _git(local, "add", relative.as_posix())
    _git(local, "commit", "-m", "enqueue")
    _git(local, "push", "origin", "HEAD:refs/heads/automation/pangram-gui-bridge-queue")
    _git(local, "switch", "agent/pangram-local-playwright-gpt-20260818")

    reader = gui_bridge.QueueReader(local)
    batch = reader.poll()
    assert batch.request_paths == (relative.as_posix(),)
    assert reader.read(batch.head_commit, relative.as_posix()).startswith(b"{")
    reader.write_cursor(batch.head_commit)

    _git(local, "switch", "automation/pangram-gui-bridge-queue")
    path.write_text("{}\n")
    _git(local, "add", relative.as_posix())
    _git(local, "commit", "-m", "illegal mutation")
    _git(local, "push", "origin", "HEAD:refs/heads/automation/pangram-gui-bridge-queue")
    _git(local, "switch", "agent/pangram-local-playwright-gpt-20260818")
    with pytest.raises(gui_bridge.QueueTopologyError, match="append-only"):
        reader.poll()


def test_queue_rejects_add_then_modify_before_first_poll(tmp_path: Path) -> None:
    bare = tmp_path / "origin.git"
    local = tmp_path / "local"
    _git(tmp_path, "init", "--bare", str(bare))
    local.mkdir()
    _git(local, "init", "-b", "agent/pangram-local-playwright-gpt-20260818")
    _git(local, "config", "user.email", "bridge-test@example.test")
    _git(local, "config", "user.name", "Bridge Test")
    (local / "README.md").write_text("base\n")
    _git(local, "add", "README.md")
    _git(local, "commit", "-m", "base")
    _git(local, "remote", "add", "origin", str(bare))
    _git(local, "switch", "-c", "automation/pangram-gui-bridge-queue")
    request_id = str(uuid.uuid4())
    relative = Path("state/pangram-gui-bridge/requests") / f"{request_id}.json"
    path = local / relative
    path.parent.mkdir(parents=True)
    path.write_bytes(_raw_request("verify", request_id=request_id))
    _git(local, "add", relative.as_posix())
    _git(local, "commit", "-m", "enqueue")
    path.write_text("{}\n")
    _git(local, "add", relative.as_posix())
    _git(local, "commit", "-m", "mutate before poll")
    _git(local, "push", "origin", "HEAD:refs/heads/automation/pangram-gui-bridge-queue")
    _git(local, "switch", "agent/pangram-local-playwright-gpt-20260818")

    with pytest.raises(gui_bridge.QueueTopologyError, match="append-only"):
        gui_bridge.QueueReader(local).poll()
