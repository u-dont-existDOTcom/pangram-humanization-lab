from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "live_smoke.py"


def load_module():
    spec = importlib.util.spec_from_file_location("authorial_flow_live_smoke_script", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_heartbeat_smoke_observes_silent_child_without_waiting_for_output(tmp_path):
    mod = load_module()
    report = mod.run_heartbeat_check(
        artifact_root=tmp_path / "artifacts",
        sleep_seconds=0.22,
        heartbeat_seconds=0.05,
    )
    assert report["status"] == "pass"
    assert report["heartbeat_count"] >= 2
    assert max(report["heartbeat_gaps_seconds"]) <= 0.12
    assert report["returncode"] == 0


def test_parser_never_submits_pangram_without_explicit_submit_flag():
    mod = load_module()
    args = mod.build_parser().parse_args(["--pangram"])
    assert args.pangram is True
    assert args.pangram_submit is False


def test_report_redaction_removes_known_secret_values():
    mod = load_module()
    value = {"headers": {"Authorization": "Bearer secret-key"}, "text": "secret-key appears"}
    redacted = mod.redact(value, ["secret-key"])
    assert "secret-key" not in str(redacted)


def test_default_codex_models_use_supported_sol_then_cli_default(monkeypatch):
    mod=load_module()
    monkeypatch.delenv('AUTHORIAL_CODEX_MODELS',raising=False)
    args=mod.build_parser().parse_args(['--codex'])
    assert args.codex_models == 'gpt-5.6-sol,'


def test_runtime_schema_inventory_passes_local_preflight():
    mod=load_module()

    report=mod.validate_runtime_schema_inventory()

    assert report['status']=='pass'
    assert report['schema_count'] >= 8
    assert report['invalid']==[]
