from __future__ import annotations

import json
from pathlib import Path

from authorial_flow.artifacts import ArtifactStore
from authorial_flow.authority import Authority, AuthorityUnit
from authorial_flow.config import RuntimeConfig
from authorial_flow.events import EventJournal
from authorial_flow.models.common import ModelResult
from authorial_flow.nodes.fidelity import FidelityResult
from authorial_flow.runtime import RuntimeServices, build_runtime_dependencies


class SequenceAdapter:
    def __init__(self, provider: str, responses: dict[str, object]):
        self.provider = provider
        self.responses = responses
        self.calls = []

    def call(self, call, runner, store):
        self.calls.append(call)
        response = self.responses[call.role]
        if callable(response):
            response = response(call)
        return ModelResult(
            provider=self.provider,
            role=call.role,
            request_id=call.request_id or f"{self.provider}-{call.role}",
            model=f"fake-{self.provider}",
            cli_version="fake",
            parsed=response,
            text=response if isinstance(response, str) else json.dumps(response),
            stdout_ref="runner-stdout-must-not-appear",
            stderr_ref="runner-stderr-must-not-appear",
        )


def _flow(tmp_path: Path, writer_responses: list[str]):
    root = Path(__file__).resolve().parents[2]
    store = ArtifactStore(tmp_path / ".state" / "artifacts")
    writer = iter(writer_responses)
    claude = SequenceAdapter("claude", {"writer": lambda _call: next(writer)})
    codex = SequenceAdapter("codex", {
        "fidelity_guard": {
            "verdict": "PASS",
            "confidence": 0.99,
            "failure_type": "none",
            "reason": "meaning preserved",
            "covered_unit_ids": ["u1"],
        },
    })
    services = RuntimeServices.for_tests(
        claude=claude,
        codex=codex,
        pangram=None,
        artifact_store=store,
    )
    journal = EventJournal(tmp_path / ".state" / "events.jsonl")
    services.journal = journal
    services.work_feed.journal = journal
    unit = AuthorityUnit(
        id="u1",
        text="The live question remains unresolved.",
        authority=Authority.OWNER_GROUNDED,
    )
    unit_ref = store.put_text(
        json.dumps(unit.model_dump(mode="json")),
        "json",
        {"kind": "authority-unit"},
    ).sha256
    source_ref = store.put_text("The live question remains unresolved.", "md", {"kind": "source"}).sha256
    state = {
        "source_ref": source_ref,
        "atom_refs": [unit_ref],
        "atom_coverage": {"u1": False},
        "accepted_moves": [],
        "accepted_move_coverage": [],
        "coverage_reconciliation_required": False,
        "section_job": "follow the live question",
        "task_mode": "P2S",
        "source_provenance": "OWNER_DRAFT",
        "retry_count": 0,
        "rollback_count": 0,
    }
    deps = build_runtime_dependencies(
        RuntimeConfig.from_root(tmp_path),
        project_root=root,
        services=services,
    )
    return deps, services, state


def test_fake_flow_prints_complete_operational_sequence_and_exact_current_passage(tmp_path, monkeypatch):
    deps, services, state = _flow(tmp_path, ["Rejected proposal.", "Accepted proposal."])
    local_results = iter([
        FidelityResult("FAIL", reason="invented relation"),
        FidelityResult("PASS"),
    ])
    monkeypatch.setattr("authorial_flow.runtime.relation_guard", lambda _source, _candidate: next(local_results))

    first = deps.generation(state)
    state.update(first)
    second = deps.generation(state)

    rows = services.journal.read_since(0).events
    kinds = [row["kind"] for row in rows if row["kind"] in {
        "proposal.complete", "guard.result", "generation.retry",
        "move.accepted", "passage.current",
    }]
    assert kinds == [
        "proposal.complete", "guard.result", "generation.retry",
        "proposal.complete", "guard.result", "guard.result", "move.accepted", "passage.current",
    ]
    passage = [row for row in rows if row["kind"] == "passage.current"][-1]
    assert passage["accepted_moves"] == second["accepted_moves"]
    assert passage["text"].encode("utf-8") == " ".join(second["accepted_moves"]).encode("utf-8")

    proposals = [row for row in rows if row["kind"] == "proposal.complete"]
    assert [row["text"] for row in proposals] == ["Rejected proposal.", "Accepted proposal."]
    assert "runner-stdout" not in json.dumps(proposals)
    assert "runner-stderr" not in json.dumps(proposals)


def test_multiple_span_proposal_is_visible_but_never_accepted(tmp_path):
    deps, services, state = _flow(tmp_path, ["First advance. Second advance."])

    update = deps.generation(state)
    rows = services.journal.read_since(0).events

    assert update["status"] == "continue_generation"
    assert [row["kind"] for row in rows if row["kind"] == "proposal.complete"] == ["proposal.complete"]
    assert not [row for row in rows if row["kind"] == "move.accepted"]
    assert [row for row in rows if row["kind"] == "generation.retry"][-1]["stage"] == "atomicity"
