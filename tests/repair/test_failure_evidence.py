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


def test_guarded_node_normalizes_returned_machine_failure_with_safe_evidence(tmp_path: Path):
    from authorial_flow.runtime import RuntimeServices, _guarded_node

    store=ArtifactStore(tmp_path/'artifacts')
    services=RuntimeServices.for_tests(
        claude=object(),codex=object(),pangram=None,artifact_store=store,
    )

    update=_guarded_node('generation',lambda _state:{
        'status':'machine_failure','phase':'generation',
        'failure_class':'POLICY_CONTRADICTION',
        'generation_boundary_id':'b'*64,'decision_boundary_id':'a'*64,
        'generation_rejection_class':'UNSAFE_ARRIVAL_ROLLBACK',
        'uncovered_required_count':6,
    },services)({
        'thread_id':'same-thread','source_hash':'source-hash',
        'program_version':'program-hash','accepted_moves':['private article prose'],
    })

    assert update['failure_class']=='POLICY_CONTRADICTION'
    assert update['failure_origin_node']=='generation'
    assert update['failure_record_ref']==update['last_error_ref']
    artifact=store.find(update['failure_record_ref'])
    assert artifact is not None
    payload=json.loads(artifact.path.read_text())
    assert payload['failure_class']=='POLICY_CONTRADICTION'
    assert payload['originating_node']=='generation'
    assert payload['decision_trace']['uncovered_required_count']==6
    assert 'private article prose' not in artifact.path.read_text()


def test_failure_decision_trace_contains_only_content_safe_controller_facts(tmp_path: Path):
    store=ArtifactStore(tmp_path/'artifacts')
    secret='TRACE-SECRET-4927'
    record=FailureRecord(originating_node='generation',failure_code='policy contradiction')
    bundle=build_failure_evidence(
        record=record,
        failure_class='POLICY_CONTRADICTION',
        state={
            'accepted_moves':['raw accepted prose'],
            'candidate_text':'raw candidate prose',
            'raw_prompt':f'hidden {secret}',
            'generation_boundary_id':'b'*64,
            'decision_boundary_id':'b'*64,
            'uncovered_required_count':4,
            'committed_pressure':{'state':'NATURAL_STOP','confidence':0.91,'boundary_id':'b'*64,'live_pressure':'raw pressure prose'},
            'pressure_votes':[{'state':'NATURAL_STOP','confidence':0.9,'provider':'codex','why':'raw rationale'}],
            'entry_edge_result':{'verdict':'STOP_BEFORE_CANDIDATE','confidence':0.96,'boundary_id':'b'*64,'reason':'raw edge prose'},
            'proposal_ref':'c'*64,
            'generation_rejection_class':'STOP_BEFORE_CANDIDATE',
            'retry_count':4,'rollback_count':1,
        },
        exc=RuntimeError(f'controller stop {secret}'),store=store,secret_values=[secret],
    )

    trace=bundle.decision_trace
    assert trace['boundary_id']=='b'*64
    assert trace['candidate_sha256']=='c'*64
    assert trace['uncovered_required_count']==4
    assert trace['edge']['verdict']=='STOP_BEFORE_CANDIDATE'
    dumped=json.dumps(trace)
    for forbidden in ('raw accepted prose','raw candidate prose','raw pressure prose','raw edge prose',secret):
        assert forbidden not in dumped
