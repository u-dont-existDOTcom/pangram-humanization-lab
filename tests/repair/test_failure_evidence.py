import json
from pathlib import Path

from authorial_flow.artifacts import ArtifactStore
from authorial_flow.failures import FailureClass, FailureRecord
from authorial_flow.models.common import ModelAttempt, ProviderFailure
from authorial_flow.repair.evidence import build_failure_evidence


def test_provider_failure_bundle_dereferences_attempts_schema_and_runtime_state(tmp_path: Path):
    store = ArtifactStore(tmp_path / "artifacts")
    stdout_ref = store.put_text("wrapper output pangram-secret", "stdout.txt", {"stream":"stdout"}).sha256
    stderr_ref = store.put_text("schema mismatch brave-secret", "stderr.txt", {"stream":"stderr"}).sha256
    schema = {
        "type":"object",
        "required":["verdict"],
        "properties":{"verdict":{"type":"string"}},
        "additionalProperties":False,
    }
    exc = ProviderFailure(
        "claude", "pressure_reader", "request-123",
        [ModelAttempt("claude-opus-5", 0, stdout_ref, stderr_ref, "parse/schema: ValueError")],
        schema=schema,
    )
    record = FailureRecord(
        originating_node="generation",
        failure_code=str(exc),
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        provider_attempt_refs=(stdout_ref, stderr_ref),
        source_hash="source-sha",
        program_hash="program-sha",
        local_gate_state={"regressions_hard_pass":True},
    )
    bundle = build_failure_evidence(
        record=record,
        failure_class=FailureClass.PROVIDER_PLUMBING,
        state={
            "thread_id":"thread-abc",
            "checkpoint_id":"checkpoint-7",
            "phase":"generation",
            "task_mode":"P3",
            "source_provenance":"AI_FROM_OWNER_INPUTS",
            "repair_attempt":2,
            "accepted_moves":["first move"],
        },
        exc=exc,
        store=store,
        program_version="commit-xyz",
        event_context={"kind":"heartbeat","node":"generation"},
        secret_values=["pangram-secret", "brave-secret"],
    )
    assert bundle.failure_class == "PROVIDER_PLUMBING"
    assert bundle.thread_id == "thread-abc"
    assert bundle.checkpoint_id == "checkpoint-7"
    assert bundle.program_version == "commit-xyz"
    assert bundle.expected_schema == schema
    assert bundle.provider == "claude"
    assert bundle.role == "pressure_reader"
    assert bundle.request_id == "request-123"
    assert bundle.provider_attempts[0].model == "claude-opus-5"
    assert bundle.provider_attempts[0].stdout_ref == stdout_ref
    assert bundle.provider_attempts[0].stderr_ref == stderr_ref
    assert "wrapper output" in bundle.provider_attempts[0].stdout_text
    assert "schema mismatch" in bundle.provider_attempts[0].stderr_text
    dumped = bundle.model_dump_json()
    assert "pangram-secret" not in dumped
    assert "brave-secret" not in dumped
    assert "[REDACTED]" in dumped
    assert bundle.suggested_test_command


def test_failure_bundle_bounds_large_provider_artifacts(tmp_path: Path):
    store = ArtifactStore(tmp_path / "artifacts")
    huge = "x" * 20000
    stdout_ref = store.put_text(huge, "stdout.txt", {}).sha256
    exc = ProviderFailure(
        "claude", "writer", "request-big",
        [ModelAttempt("claude-opus-5", 1, stdout_ref, "", "nonzero exit")],
        schema={"type":"object"},
    )
    record = FailureRecord(originating_node="generation", failure_code=str(exc))
    bundle = build_failure_evidence(
        record=record,
        failure_class=FailureClass.PROVIDER_PLUMBING,
        state={"thread_id":"thread-big"},
        exc=exc,
        store=store,
        program_version="v",
    )
    assert len(bundle.provider_attempts[0].stdout_text) < len(huge)
    assert bundle.provider_attempts[0].stdout_text.endswith("[TRUNCATED]")


def test_guarded_node_persists_evidence_bundle_as_repair_ref(tmp_path: Path, monkeypatch):
    from authorial_flow.runtime import RuntimeServices, _guarded_node

    store = ArtifactStore(tmp_path / "artifacts")
    out_ref = store.put_text("bad structured output", "stdout.txt", {}).sha256
    exc = ProviderFailure(
        "claude", "pressure_reader", "request-runtime",
        [ModelAttempt("claude-opus-5", 0, out_ref, "", "parse/schema: ValueError")],
        schema={"type":"object","required":["verdict"]},
    )
    services = RuntimeServices.for_tests(claude=object(), codex=object(), pangram=None, artifact_store=store)
    monkeypatch.setenv("PANGRAM_API_KEY", "runtime-secret")

    def boom(_state):
        raise exc

    update = _guarded_node("generation", boom, services)({
        "thread_id":"same-thread",
        "source_hash":"source-hash",
        "task_mode":"P3",
        "source_provenance":"AI_FROM_OWNER_INPUTS",
        "program_version":"program-hash",
        "final_local_gates":{"regressions_hard_pass":True},
    })
    artifact = store.find(update["failure_record_ref"])
    assert artifact is not None
    payload = json.loads(artifact.path.read_text())
    assert payload["format"] == "authorial-flow-repair-evidence-v1"
    assert payload["thread_id"] == "same-thread"
    assert payload["expected_schema"]["required"] == ["verdict"]
    assert "bad structured output" in payload["provider_attempts"][0]["stdout_text"]
    assert update["failure_class"] == "PROVIDER_PLUMBING"
