from __future__ import annotations

import json
from pathlib import Path

import pytest

from authorial_flow.config import RuntimeConfig
from authorial_flow.diagnostics import (
    DIAGNOSTIC_FORMAT,
    build_diagnostic_record,
    load_queued_diagnostics,
    queue_diagnostic,
    safely_publish_diagnostic,
)


SECRET = "SECRET-SENTINEL-DO-NOT-PUBLISH"
PROSE = "PROSE-SENTINEL-DO-NOT-PUBLISH"


def _config(tmp_path: Path) -> RuntimeConfig:
    root = tmp_path / "repo"
    root.mkdir()
    state = root / ".state"
    state.mkdir()
    (state / "current-thread.json").write_text(
        json.dumps(
            {
                "thread_id": "a" * 64,
                "source_sha256": "b" * 64,
                "source": f"/home/joel/Téléchargements/{PROSE}.md",
            }
        ),
        encoding="utf-8",
    )
    (state / "events.jsonl").write_text(
        json.dumps(
            {
                "sequence": 1,
                "time": 1786518306.0,
                "kind": "machine-failure",
                "source": PROSE,
                "exception_message": SECRET,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return RuntimeConfig.from_root(root)


def test_diagnostic_record_allowlists_live_smoke_and_excludes_sensitive_inputs(
    tmp_path: Path, monkeypatch,
) -> None:
    cfg = _config(tmp_path)
    monkeypatch.setenv("PANGRAM_API_KEY", SECRET)
    report = cfg.state_dir / "live-smoke" / "install-report.json"
    report.parent.mkdir()
    report.write_text(
        json.dumps(
            {
                "format": "authorial-flow-live-smoke-v1",
                "credential_required": "PANGRAM_API_KEY",
                "credential_status_code": 401,
                "error": {"type": "HTTPStatusError", "message": SECRET},
                "results": {
                    "claude": {
                        "provider": "claude",
                        "resolved_model": "claude-opus-5",
                        "status": "pass",
                        "attempt_count": 1,
                        "duration_seconds": 9.5,
                        "stdout_ref": "c" * 64,
                        "stderr_ref": "",
                    },
                    "codex": {
                        "provider": "codex",
                        "resolved_model": "gpt-5.6-sol",
                        "status": "fail",
                        "failure_kind": "INVALID_SCHEMA",
                        "capability_signature": "d" * 64,
                        "detail": f"schema error {SECRET}",
                        "stderr": SECRET,
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    package = cfg.state_dir / "evidence" / "bounded.zip"
    package.parent.mkdir()
    package.write_bytes(b"local evidence bytes")

    record = build_diagnostic_record(
        cfg,
        phase="installer-live-smoke",
        outcome="credential_required",
        result={
            "status": "bounded_machine_stop",
            "failure_class": "PROVIDER_PLUMBING",
            "failure_origin_node": "provider-smoke",
            "accepted_moves": [PROSE],
            "branch_memory": [{"candidate": PROSE, "reason": SECRET}],
            "retry_count": 4,
            "rollback_count": 2,
            "uncovered_required_count": 6,
            "failure_record_ref": "e" * 64,
            "evidence_package_path": str(package),
        },
        report_path=report,
        command=[".venv/bin/python", "scripts/live_smoke.py", "--pangram", SECRET],
        returncode=3,
        now=1786518307.0,
    )

    assert record["format"] == DIAGNOSTIC_FORMAT
    assert record["created_utc"] == 1786518307.0
    assert record["phase"] == "installer-live-smoke"
    assert record["outcome"] == "credential_required"
    assert record["command_kind"] == "live_smoke"
    assert record["returncode"] == 3
    assert record["thread"] == {"thread_id": "a" * 64, "source_sha256": "b" * 64}
    assert record["failure"] == {
        "class": "PROVIDER_PLUMBING",
        "origin_node": "provider-smoke",
        "repair_outcome": "",
    }
    assert record["counts"] == {
        "accepted_moves": 1,
        "retry_count": 4,
        "rollback_count": 2,
        "uncovered_required_count": 6,
        "event_count": 1,
    }
    assert record["providers"]["claude"] == {
        "provider": "claude",
        "model": "claude-opus-5",
        "status": "pass",
        "failure_kind": "",
        "capability_signature": "",
        "attempt_count": 1,
    }
    assert record["providers"]["codex"]["failure_kind"] == "INVALID_SCHEMA"
    assert record["providers"]["pangram"]["status"] == "credential_required"
    assert record["artifacts"]["failure_evidence_sha256"] == "e" * 64
    assert len(record["artifacts"]["local_package_sha256"]) == 64
    assert record["privacy"]["schema_version"] == 1
    assert len(record["run_id"]) == 64

    encoded = json.dumps(record, ensure_ascii=False, sort_keys=True)
    for forbidden in (
        SECRET,
        PROSE,
        "/home/joel",
        "Téléchargements",
        str(package),
        "local evidence bytes",
        "schema error",
        "HTTPStatusError",
        "PANGRAM_API_KEY",
    ):
        assert forbidden not in encoded


def test_unknown_free_form_values_are_hashed_not_copied(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    record = build_diagnostic_record(
        cfg,
        phase=f"unknown-phase-{SECRET}",
        outcome=f"unknown-outcome-{PROSE}",
        result={
            "status": f"unknown-status-{SECRET}",
            "failure_class": f"unknown-class-{PROSE}",
            "failure_origin_node": f"unknown-node-{SECRET}",
            "repair_outcome": f"unknown-repair-{PROSE}",
        },
        now=1.0,
    )
    encoded = json.dumps(record, sort_keys=True)
    assert record["phase"] == "UNCLASSIFIED"
    assert record["outcome"] == "UNCLASSIFIED"
    assert record["failure"]["class"] == "UNCLASSIFIED"
    assert record["failure"]["origin_node"] == "UNCLASSIFIED"
    assert record["failure"]["repair_outcome"] == "UNCLASSIFIED"
    assert set(record["unclassified_sha256"]) == {
        "phase",
        "outcome",
        "failure_class",
        "failure_origin_node",
        "repair_outcome",
    }
    assert SECRET not in encoded
    assert PROSE not in encoded


def test_queue_is_atomic_private_and_idempotent(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    record = build_diagnostic_record(
        cfg,
        phase="manual-status",
        outcome="snapshot",
        now=2.0,
    )
    first = queue_diagnostic(cfg, record)
    second = queue_diagnostic(cfg, record)

    assert first == second
    assert first.name == f"{record['run_id']}.json"
    assert json.loads(first.read_text(encoding="utf-8")) == record
    assert first.stat().st_mode & 0o777 == 0o600
    assert load_queued_diagnostics(cfg) == (first,)
    assert not list(first.parent.glob("*.tmp"))


def test_queue_rejects_non_allowlisted_or_tampered_records(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    record = build_diagnostic_record(cfg, phase="manual-status", outcome="snapshot", now=2.0)
    with_extra_field = {**record, "raw_error": SECRET}
    with pytest.raises(ValueError, match="invalid diagnostic record"):
        queue_diagnostic(cfg, with_extra_field)

    tampered = json.loads(json.dumps(record))
    tampered["failure"]["class"] = SECRET
    with pytest.raises(ValueError, match="invalid diagnostic record"):
        queue_diagnostic(cfg, tampered)

    assert load_queued_diagnostics(cfg) == ()


def test_nonblocking_facade_never_exposes_or_raises_publication_failure(
    tmp_path: Path, monkeypatch,
) -> None:
    import authorial_flow.diagnostics as diagnostics

    cfg = _config(tmp_path)
    monkeypatch.setattr(
        diagnostics,
        "publish_diagnostic",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError(SECRET)),
    )
    result = safely_publish_diagnostic(
        cfg,
        phase="runtime-run",
        outcome="accepted",
        result={"accepted_moves": [PROSE]},
    )
    assert result.status == "publication_unavailable"
    assert result.failure_kind == "LOCAL_FAILURE"
    assert result.commit_sha == ""
    encoded = json.dumps(result.__dict__, sort_keys=True)
    assert SECRET not in encoded
    assert PROSE not in encoded


def test_nonblocking_facade_survives_unreadable_local_diagnostics_state(
    tmp_path: Path, monkeypatch,
) -> None:
    import authorial_flow.diagnostics as diagnostics

    cfg = _config(tmp_path)
    monkeypatch.setattr(
        diagnostics,
        "publish_diagnostic",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError(SECRET)),
    )
    monkeypatch.setattr(
        diagnostics,
        "load_queued_diagnostics",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError(SECRET)),
    )
    monkeypatch.setattr(
        diagnostics,
        "_write_status",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError(SECRET)),
    )

    publication = safely_publish_diagnostic(
        cfg, phase="manual-status", outcome="snapshot", result={},
    )

    assert publication.status == "publication_unavailable"
    assert publication.queued_count == 0


def test_keyboard_interrupt_reaches_cli_boundary(tmp_path: Path, monkeypatch) -> None:
    import authorial_flow.diagnostics as diagnostics

    cfg = _config(tmp_path)
    monkeypatch.setattr(
        diagnostics,
        "publish_diagnostic",
        lambda *args, **kwargs: (_ for _ in ()).throw(KeyboardInterrupt()),
    )

    with pytest.raises(KeyboardInterrupt):
        safely_publish_diagnostic(
            cfg, phase="runtime-resume", outcome="interrupted", result={},
        )
