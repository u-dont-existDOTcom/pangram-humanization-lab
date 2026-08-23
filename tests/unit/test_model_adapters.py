from pathlib import Path
import json
import pytest
from authorial_flow.artifacts import ArtifactStore
from authorial_flow.models.common import (
    FailureKind, ModelCall, ProviderFailure, classify_attempt_failure,
    extract_json_object, stable_request_id,
)
from authorial_flow.models.claude_cli import ClaudeCLI
from authorial_flow.process_runner import ProcessResult


def test_request_identity_changes_with_prompt_or_schema():
    a = stable_request_id("claude", "role", "p", {"type": "object"})
    b = stable_request_id("claude", "role", "q", {"type": "object"})
    assert a != b


def test_json_extractor_accepts_wrapped_payload():
    assert extract_json_object('prefix {"verdict":"PASS"} suffix') == {"verdict": "PASS"}


def test_json_extractor_rejects_ambiguous_objects():
    with pytest.raises(ValueError):
        extract_json_object('{"a":1} then {"b":2}')


class FakeRunner:
    def __init__(self, results):
        self.results = list(results)
        self.specs = []
    def run(self, spec):
        self.specs.append(spec)
        return self.results.pop(0)


def _result(code, stdout="", stderr=""):
    return ProcessResult(code, stdout, stderr, 123, 0.1, "exit")


def test_claude_falls_back_and_persists_attempts(tmp_path: Path):
    runner = FakeRunner([
        _result(1, stderr="bad model"),
        _result(0, stdout=json.dumps({"result": '{"verdict":"PASS"}', "model":"claude-fable-5"})),
    ])
    store = ArtifactStore(tmp_path / "artifacts")
    adapter = ClaudeCLI(models=["claude-opus-5", "claude-fable-5"], base_env={"PATH":"/bin", "PANGRAM_API_KEY":"secret", "BRAVE_SEARCH_API_KEY":"brave-secret"})
    call = ModelCall(prompt="judge", schema={"type":"object"}, role="edge")
    got = adapter.call(call, runner, store)
    assert got.parsed == {"verdict":"PASS"}
    assert got.model == "claude-fable-5"
    assert len(got.attempts) == 2
    assert all("PANGRAM_API_KEY" not in spec.env for spec in runner.specs)
    assert all("BRAVE_SEARCH_API_KEY" not in spec.env for spec in runner.specs)
    assert all(a.stdout_ref or a.stderr_ref for a in got.attempts)
    assert runner.specs[0].operation.provider == "claude"
    assert runner.specs[0].operation.model == "claude-opus-5"
    assert runner.specs[0].operation.role == "edge"
    assert runner.specs[0].operation.cancelable is True


def test_claude_all_failures_raise_provider_failure(tmp_path: Path):
    runner = FakeRunner([_result(1, stderr="one"), _result(1, stderr="two")])
    adapter = ClaudeCLI(models=["a","b"], base_env={"PATH":"/bin"})
    with pytest.raises(ProviderFailure) as exc:
        adapter.call(ModelCall(prompt="x", schema={"type":"object"}, role="r"), runner, ArtifactStore(tmp_path/"a"))
    assert len(exc.value.attempts) == 2
    assert "one" not in str(exc.value)


def test_codex_uses_schema_constrained_command(tmp_path: Path):
    from authorial_flow.models.codex_cli import CodexCLI

    class CodexRunner:
        def __init__(self): self.specs=[]
        def run(self, spec):
            self.specs.append(spec)
            out = Path(spec.argv[spec.argv.index("--output-last-message") + 1])
            out.write_text('{"verdict":"PASS"}')
            return _result(0, stdout="ok")

    runner=CodexRunner()
    got=CodexCLI(models=["gpt-5.6-sol"], base_env={"PATH":"/bin", "PANGRAM_API_KEY":"secret", "BRAVE_SEARCH_API_KEY":"brave-secret"}).call(
        ModelCall(prompt="judge", schema={"type":"object","required":["verdict"]}, role="edge"),
        runner,
        ArtifactStore(tmp_path/"artifacts"),
    )
    assert got.parsed == {"verdict":"PASS"}
    argv=runner.specs[0].argv
    assert "--sandbox" in argv and argv[argv.index("--sandbox")+1] == "read-only"
    assert argv[-1] == "-"
    assert "PANGRAM_API_KEY" not in runner.specs[0].env
    assert "BRAVE_SEARCH_API_KEY" not in runner.specs[0].env
    assert runner.specs[0].operation.provider == "codex"
    assert runner.specs[0].operation.model == "gpt-5.6-sol"
    assert runner.specs[0].operation.role == "edge"
    assert runner.specs[0].operation.cancelable is True


def test_claude_structured_call_includes_expected_schema_in_stdin(tmp_path: Path):
    schema = {
        "type": "object",
        "required": ["verdict", "confidence"],
        "properties": {
            "verdict": {"type": "string", "enum": ["PASS", "FAIL"]},
            "confidence": {"type": "number"},
        },
        "additionalProperties": False,
    }
    runner = FakeRunner([
        _result(0, stdout=json.dumps({"result": '{"verdict":"PASS","confidence":0.9}', "model":"claude-opus-5"})),
    ])
    adapter = ClaudeCLI(
        models=["claude-opus-5"],
        base_env={"PATH":"/bin", "PANGRAM_API_KEY":"secret", "BRAVE_SEARCH_API_KEY":"brave-secret"},
    )
    got = adapter.call(
        ModelCall(prompt="judge this edge", schema=schema, role="pressure_reader"),
        runner,
        ArtifactStore(tmp_path / "artifacts"),
    )
    assert got.parsed == {"verdict":"PASS","confidence":0.9}
    sent = runner.specs[0].input_text or ""
    assert "judge this edge" in sent
    assert json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(",", ":")) in sent
    assert "return exactly one json object" in sent.lower()
    assert "PANGRAM_API_KEY" not in runner.specs[0].env
    assert "BRAVE_SEARCH_API_KEY" not in runner.specs[0].env


def test_all_pydantic_structured_output_schemas_are_recursively_codex_strict():
    from authorial_flow.nodes.developmental import ArchitectureCard
    from authorial_flow.research.base import ResearchQuestion
    from authorial_flow.research.evidence import ResearchSummary

    def assert_strict(node, path='root'):
        if isinstance(node, dict):
            if node.get('type') == 'object':
                assert node.get('additionalProperties') is False, path
            for key,value in node.items():
                assert_strict(value,f'{path}.{key}')
        elif isinstance(node, list):
            for index,value in enumerate(node):
                assert_strict(value,f'{path}[{index}]')

    for model in (ArchitectureCard, ResearchQuestion, ResearchSummary):
        assert_strict(model.model_json_schema(),model.__name__)


@pytest.mark.parametrize(('text','expected'),[
    ('401 unauthorized; please log in',FailureKind.AUTH),
    ('model does not exist',FailureKind.UNSUPPORTED_MODEL),
    ('invalid JSON schema: required property missing',FailureKind.INVALID_SCHEMA),
    ('parse/schema: ValueError',FailureKind.STRUCTURED_CONTRACT),
    ('request timed out while provider was overloaded',FailureKind.TRANSIENT),
    ('stream disconnected before completion: error sending request for url',FailureKind.TRANSIENT),
    ('temporary failure in name resolution',FailureKind.TRANSIENT),
    ('provider returned 503 service unavailable',FailureKind.TRANSIENT),
    ('unexpected failure',FailureKind.UNKNOWN),
])
def test_provider_failure_classification_is_deterministic(text,expected):
    assert classify_attempt_failure(returncode=1,stdout='',stderr=text,error='') is expected


def test_auth_failure_stops_equivalent_claude_fallbacks(tmp_path: Path):
    runner=FakeRunner([_result(1,stderr='401 unauthorized; login required')])
    adapter=ClaudeCLI(models=['claude-opus-5','claude-fable-5'],base_env={'PATH':'/bin'})

    with pytest.raises(ProviderFailure) as exc:
        adapter.call(ModelCall(prompt='x',schema={'type':'object'},role='r'),runner,ArtifactStore(tmp_path/'a'))

    assert len(runner.specs)==1
    assert exc.value.attempts[0].failure_kind==FailureKind.AUTH.value
    assert exc.value.attempts[0].capability_signature


def test_duplicate_model_profile_is_not_retried_after_unsupported_model(tmp_path: Path):
    runner=FakeRunner([
        _result(1,stderr='model does not exist'),
        _result(0,stdout=json.dumps({'result':'{"verdict":"PASS"}','model':'b'})),
    ])
    adapter=ClaudeCLI(models=['a','a','b'],base_env={'PATH':'/bin'})

    got=adapter.call(
        ModelCall(prompt='x',schema={'type':'object'},role='r'),runner,ArtifactStore(tmp_path/'a'),
    )

    assert [spec.operation.model for spec in runner.specs]==['a','b']
    assert got.attempts[0].failure_kind==FailureKind.UNSUPPORTED_MODEL.value


def test_invalid_schema_fails_preflight_without_spawning_provider(tmp_path: Path):
    runner=FakeRunner([])
    adapter=ClaudeCLI(models=['a','b'],base_env={'PATH':'/bin'})
    invalid={
        'type':'object','additionalProperties':False,
        'properties':{},'required':'missing',
    }

    with pytest.raises(ProviderFailure) as exc:
        adapter.call(ModelCall(prompt='x',schema=invalid,role='r'),runner,ArtifactStore(tmp_path/'a'))

    assert runner.specs==[]
    assert len(exc.value.attempts)==1
    assert exc.value.attempts[0].failure_kind==FailureKind.INVALID_SCHEMA.value
