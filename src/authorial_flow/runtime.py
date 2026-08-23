from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import os
import time
from pathlib import Path
from typing import Any, Callable

import httpx

from .artifacts import ArtifactStore
from .authority import Authority, AuthorityUnit
from .candidates import CandidateRecord
from .config import RuntimeConfig
from .decision_trace import build_decision_trace
from .events import EventJournal
from .failures import FailureRecord, classify_failure
from .graph import GraphDependencies
from .learning import LearningStore
from .modes import choose_mode, TaskMode
from .models.claude_cli import ClaudeCLI
from .models.codex_cli import CodexCLI
from .models.common import ModelCall
from .models.pangram import PangramClient
from .pause import PauseController
from .project import ProjectInputs
from .nodes.cold_audit import AuditDefect, ColdAuditResult
from .nodes.boundary import generation_boundary_id
from .nodes.developmental import ArchitectureCard, build_developmental_result
from .nodes.detector_search import detector_node
from .nodes.fidelity import relation_guard
from .nodes.flow import is_natural_arrival, judge_full_edge
from .nodes.generate import candidate_semantic_spans, writer_payload
from .nodes.owner_interrupt import capture_owner_response, research_adoption_payload
from .nodes.owner_interrupt import supervisor_pause_node
from .nodes.repair import repair_node
from .nodes.pressure import CommittedPressure, PressureVote, commit_pressure
from .nodes.regression import suite_identity
from .nodes.stopping import decide_stop
from .pause import OwnerPauseRequested
from .process_runner import ProcessRunner
from .source_provenance import SourceProvenance, classify_provenance
from .research.base import ResearchQuestion
from .research.evidence import EvidenceRecord, ResearchSummary
from .routing import (
    route_after_cold_audit,
    route_after_detector,
    route_after_freeze,
    route_after_owner_learning,
    route_after_regressions,
    route_after_repair,
    route_after_representation,
    route_generation,
)
from .work_feed import WorkFeed
from .supervisor import (
    CoverageReconciliationBlocked,
    SupervisorSessionStore,
    build_supervisor_snapshot,
    persist_supervisor_snapshot,
)


PRESSURE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "state": {"type": "string", "enum": ["OPEN", "NATURAL_STOP", "AMBIGUOUS"]},
        "confidence": {"type": "number"}, "live_pressure": {"type": "string"},
        "previous_move_function": {"type": "string"},
        "already_settled": {"type": "array", "items": {"type": "string"}},
        "backward_reopen_risks": {"type": "array", "items": {"type": "string"}},
        "why_stop_might_be_natural": {"type": "string"},
    },
    "required": ["state", "confidence", "live_pressure", "previous_move_function", "already_settled", "backward_reopen_risks", "why_stop_might_be_natural"],
}
EDGE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "verdict": {"type": "string", "enum": ["PASS", "FAIL", "STOP_BEFORE_CANDIDATE"]},
        "confidence": {"type": "number"}, "failure_type": {"type": "string"},
        "reason": {"type": "string"}, "challenge": {"type": "string"},
    },
    "required": ["verdict", "confidence", "failure_type", "reason", "challenge"],
}
FIDELITY_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "verdict": {"type": "string", "enum": ["PASS", "FAIL"]},
        "confidence": {"type": "number"}, "failure_type": {"type": "string"},
        "reason": {"type": "string"},
        "covered_unit_ids": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["verdict", "confidence", "failure_type", "reason", "covered_unit_ids"],
}
REPRESENTATION_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "section_job": {"type": "string"},
        "semantic_sanity": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "status": {"type": "string", "enum": ["PASS", "FAIL"]},
                "defect_types": {"type": "array", "items": {"type": "string"}},
                "research_trigger": {"type": "boolean"},
                "recommended_escalation": {
                    "type": "string",
                    "enum": ["BASIC", "P3", "P4", "RESEARCH", "OWNER"],
                },
                "owner_question": {"type": "string"},
            },
            "required": ["status", "defect_types", "research_trigger", "recommended_escalation", "owner_question"],
        },
        "units": {
            "type": "array", "items": {
                "type": "object", "additionalProperties": False,
                "properties": {"id": {"type": "string"}, "text": {"type": "string"}, "reason": {"type": "string"}},
                "required": ["id", "text", "reason"],
            }
        },
    },
    "required": ["section_job", "semantic_sanity", "units"],
}
DEVELOPMENTAL_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "architecture_card": ArchitectureCard.model_json_schema(),
        "corrected_units": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "id": {"type": "string"}, "text": {"type": "string"},
                "disposition": {"type": "string"}, "reason": {"type": "string"},
                "origin": {"type": "string"},
            },
            "required": ["id", "text", "disposition", "reason", "origin"],
        }},
        "owner_position_diverges": {"type": "boolean"},
        "unresolved_authorial": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "unit_id": {"type": "string"},
                "question": {"type": "string"},
                "interpretations": {"type": "array", "items": {"type": "string"}},
                "material_consequence": {"type": "string"},
            },
            "required": ["unit_id", "question", "interpretations", "material_consequence"],
        }},
    },
    "required": ["architecture_card", "corrected_units", "owner_position_diverges", "unresolved_authorial"],
}
RESEARCH_QUESTION_SCHEMA = ResearchQuestion.model_json_schema()
RESEARCH_SUMMARY_SCHEMA = ResearchSummary.model_json_schema()

COLD_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "defects": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {"code": {"type": "string"}, "detail": {"type": "string"}, "severity": {"type": "string"}},
            "required": ["code", "detail", "severity"],
        }},
        "semantic_sanity": {"type": "boolean"}, "curious_reader_chain": {"type": "boolean"},
        "stopping_point_ok": {"type": "boolean"}, "fidelity_ok": {"type": "boolean"},
    },
    "required": ["defects", "semantic_sanity", "curious_reader_chain", "stopping_point_ok", "fidelity_ok"],
}

MOVE_COVERAGE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"moves": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "properties": {
            "index": {"type": "integer"},
            "move_sha256": {"type": "string"},
            "covered_unit_ids": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["index", "move_sha256", "covered_unit_ids"],
    }}},
    "required": ["moves"],
}

MOVE_COVERAGE_CHECK_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "verdict": {"type": "string", "enum": ["PASS", "FAIL"]},
        "reason": {"type": "string"},
    },
    "required": ["verdict", "reason"],
}


def runtime_schema_inventory() -> dict[str, dict[str, Any]]:
    """Return every structured contract used by the live graph for local preflight."""
    return {
        "pressure": PRESSURE_SCHEMA,
        "edge": EDGE_SCHEMA,
        "fidelity": FIDELITY_SCHEMA,
        "representation": REPRESENTATION_SCHEMA,
        "developmental": DEVELOPMENTAL_SCHEMA,
        "research_question": RESEARCH_QUESTION_SCHEMA,
        "research_summary": RESEARCH_SUMMARY_SCHEMA,
        "cold_audit": COLD_SCHEMA,
        "move_coverage": MOVE_COVERAGE_SCHEMA,
        "move_coverage_check": MOVE_COVERAGE_CHECK_SCHEMA,
    }

_DIRECTION_SCOPES = {"CURRENT_ARTICLE", "GENERAL_RULE_CANDIDATE"}
_DIRECTION_STAGES = {
    "representation", "developmental", "research", "generation",
    "cold_audit", "cold_revision", "entry_edge", "full_edge",
    "fidelity_guard", "detector_variant_fidelity", "detector_variant_audit",
}


def _emit(services: RuntimeServices, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    if services.journal is not None and services.work_feed.journal is not services.journal:
        services.work_feed.journal = services.journal
    return services.work_feed.emit(kind, payload)


def _applicable_owner_directives(
    state: dict[str, Any],
    stage: str,
    *,
    include_next_attempt: bool = False,
) -> list[dict[str, str]]:
    if stage not in _DIRECTION_STAGES:
        return []
    consumed = {str(value) for value in state.get("consumed_directive_ids") or []}
    rows: list[dict[str, str]] = []
    for raw in list(state.get("owner_directives") or [])[-20:]:
        if not isinstance(raw, dict):
            continue
        directive_id = str(raw.get("id") or "")[:128]
        instruction = str(raw.get("instruction") or "").strip()[:4000]
        scope = str(raw.get("scope") or "")
        if not directive_id or not instruction:
            continue
        persistent = scope in _DIRECTION_SCOPES
        next_attempt = (
            include_next_attempt
            and scope == "NEXT_ATTEMPT"
            and directive_id not in consumed
            and not bool(raw.get("consumed"))
        )
        if not (persistent or next_attempt):
            continue
        rows.append({
            "id": directive_id,
            "instruction": instruction,
            "scope": scope,
            "restart_depth": str(raw.get("restart_depth") or "CURRENT_STAGE"),
            "reason": str(raw.get("reason") or "")[:2000],
        })
    return rows


def _owner_direction_block(
    state: dict[str, Any],
    stage: str,
    *,
    include_next_attempt: bool = False,
) -> tuple[str, list[dict[str, str]]]:
    directives = _applicable_owner_directives(
        state,
        stage,
        include_next_attempt=include_next_attempt,
    )
    if not directives:
        return "", []
    block = "\n\nCONFIRMED OWNER DIRECTIONS:\n" + json.dumps(
        directives,
        ensure_ascii=False,
        indent=2,
    )
    return block, directives


def _consume_next_attempt_directives(
    state: dict[str, Any],
    update: dict[str, Any],
    directives: list[dict[str, str]],
) -> dict[str, Any]:
    next_ids = {
        row["id"]
        for row in directives
        if row.get("scope") == "NEXT_ATTEMPT"
    }
    if not next_ids:
        return update
    consumed = list(dict.fromkeys([
        *(str(value) for value in state.get("consumed_directive_ids") or []),
        *sorted(next_ids),
    ]))
    owner_directives = []
    for raw in state.get("owner_directives") or []:
        if not isinstance(raw, dict):
            continue
        owner_directives.append({
            **raw,
            "consumed": bool(raw.get("consumed")) or str(raw.get("id") or "") in next_ids,
        })
    return {
        **update,
        "consumed_directive_ids": consumed,
        "owner_directives": owner_directives,
    }


def _safe_rejected_proposals(
    state: dict[str, Any],
    store: ArtifactStore,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw in list(state.get("rejected_proposals") or [])[-20:]:
        if not isinstance(raw, dict):
            continue
        proposal_ref = str(raw.get("proposal_ref") or "")
        proposal_sha = str(raw.get("proposal_sha256") or "")
        if not proposal_ref or proposal_ref != proposal_sha:
            continue
        found = store.find(proposal_ref)
        if found is None:
            continue
        text = found.path.read_text(encoding="utf-8")
        if sha256(text.encode("utf-8")).hexdigest() != proposal_sha:
            continue
        rows.append({
            "proposal_sha256": proposal_sha,
            "text": text[:8000],
            "reason": str(raw.get("reason") or "")[:2000],
        })
    return rows


def _read_prompt(project_root: Path, name: str) -> str:
    return (project_root / "src" / "authorial_flow" / "prompts" / name).read_text(encoding="utf-8")


def _artifact_text(store: ArtifactStore, ref: str) -> str:
    found = store.find(ref)
    if found is None:
        raise RuntimeError(f"artifact not found: {ref}")
    return found.path.read_text(encoding="utf-8")


def _artifact_json(store: ArtifactStore, ref: str) -> Any:
    return json.loads(_artifact_text(store, ref))


def _put_json(store: ArtifactStore, value: Any, kind: str, **metadata: Any) -> str:
    return store.put_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", "json",
        {"kind": kind, **metadata},
    ).sha256


def _authority_for(provenance: SourceProvenance) -> Authority:
    return {
        SourceProvenance.OWNER_FINAL: Authority.OWNER_LOCKED,
        SourceProvenance.OWNER_DRAFT: Authority.OWNER_GROUNDED,
        SourceProvenance.SOURCE_POOL: Authority.OWNER_GROUNDED,
        SourceProvenance.AI_FROM_OWNER_INPUTS: Authority.AI_PROVISIONAL,
        SourceProvenance.MIXED: Authority.AI_PROVISIONAL,
        SourceProvenance.RESEARCH_PROVISIONAL: Authority.RESEARCH_PROVISIONAL,
    }[provenance]


@dataclass
class RuntimeServices:
    claude: Any
    codex: Any
    pangram: Any | None
    runner: ProcessRunner
    artifact_store: ArtifactStore
    learning_store: LearningStore
    pause_controller: PauseController
    work_feed: WorkFeed
    journal: EventJournal | None = None
    repair_cycle: Callable[[dict[str, Any]], dict[str, Any]] | None = None
    research_provider: Any | None = None
    research_fetcher: Any | None = None
    pangram_factory: Callable[[], Any | None] | None = None
    research_provider_factory: Callable[[], Any | None] | None = None

    def ensure_pangram(self) -> Any | None:
        if self.pangram is None and self.pangram_factory is not None:
            self.pangram = self.pangram_factory()
        return self.pangram

    def ensure_research_provider(self) -> Any | None:
        if self.research_provider is None and self.research_provider_factory is not None:
            self.research_provider = self.research_provider_factory()
        return self.research_provider

    @classmethod
    def for_tests(cls, *, claude: Any, codex: Any, pangram: Any | None, artifact_store: ArtifactStore) -> "RuntimeServices":
        pause_controller = PauseController()
        work_feed = WorkFeed(journal=None, renderer=lambda _line: None)
        return cls(
            claude=claude, codex=codex, pangram=pangram,
            runner=ProcessRunner(
                heartbeat_seconds=10,
                pause_controller=pause_controller,
                on_start=lambda payload: work_feed.emit("model.start", payload),
                on_heartbeat=work_feed.heartbeat,
            ),
            artifact_store=artifact_store,
            learning_store=LearningStore(artifact_store.root.parent),
            pause_controller=pause_controller,
            work_feed=work_feed,
            journal=None,
        )

    @classmethod
    def from_config(
        cls, config: RuntimeConfig, *,
        pangram_key_provider: Callable[[], str] | None = None,
        research_key_provider: Callable[[], str] | None = None,
    ) -> "RuntimeServices":
        journal = EventJournal(config.event_path)
        pause_controller = PauseController()
        secret_names = (
            "PANGRAM_API_KEY",
            "BRAVE_SEARCH_API_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
        )
        work_feed = WorkFeed(
            journal=journal,
            renderer=lambda line: print(line, flush=True),
            secret_values=lambda: [os.environ.get(name, "") for name in secret_names],
            silent_seconds=config.heartbeat_seconds,
        )
        runner = ProcessRunner(
            heartbeat_seconds=config.heartbeat_seconds,
            pause_controller=pause_controller,
            on_start=lambda payload: work_feed.emit("model.start", payload),
            on_heartbeat=work_feed.heartbeat,
        )
        store = ArtifactStore(config.artifact_dir)
        claude_models = [m.strip() for m in os.environ.get("AUTHORIAL_CLAUDE_MODELS", "claude-opus-5,claude-fable-5").split(",") if m.strip()]
        codex_models: list[str | None] = [m.strip() or None for m in os.environ.get("AUTHORIAL_CODEX_MODELS", "gpt-5.6-sol,").split(",")]
        claude = ClaudeCLI(claude_models, timeout_seconds=config.model_timeout_seconds)
        codex = CodexCLI(codex_models, timeout_seconds=config.model_timeout_seconds)
        def make_pangram() -> Any | None:
            key = (os.environ.get("PANGRAM_API_KEY") or "").strip()
            if not key and pangram_key_provider is not None:
                key = pangram_key_provider().strip()
            if not key:
                return None
            return PangramClient(
                key,
                httpx.Client(
                    base_url=os.environ.get("PANGRAM_BASE_URL", "https://text.external-api.pangram.com"),
                    timeout=config.pangram_timeout_seconds,
                ),
            )

        def make_research_provider() -> Any | None:
            from .research.discovery import BraveSearchProvider
            key=(os.environ.get("BRAVE_SEARCH_API_KEY") or "").strip()
            if not key and research_key_provider is not None:
                key=research_key_provider().strip()
            if not key:
                return None
            return BraveSearchProvider(key)

        return cls(
            claude=claude, codex=codex, pangram=None, runner=runner,
            artifact_store=store, learning_store=LearningStore(config.state_dir), journal=journal,
            pause_controller=pause_controller, work_feed=work_feed,
            research_provider=None, pangram_factory=make_pangram,
            research_provider_factory=make_research_provider,
        )


def seed_initial_state(
    config: RuntimeConfig, *, project_root: Path, source_path: Path, services: RuntimeServices,
    requested_operation: str | None = None,
) -> dict[str, Any]:
    project = project_root / "project"
    source_path = source_path.resolve()
    store = services.artifact_store
    source_text = source_path.read_text(encoding="utf-8")
    metadata_path = project / "SOURCE_METADATA.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.is_file() and source_path == (project / "INPUT.md").resolve() else {}
    operation = requested_operation or str(metadata.get("requested_operation") or "humanize")
    project_inputs = ProjectInputs.load(project)
    refs = {
        "source_ref": store.put_text(source_text, "md", {"kind": "source-snapshot", "path": str(source_path)}).sha256,
        "requirements_ref": store.put_text((project / "REQUIREMENTS.md").read_text(encoding="utf-8"), "md", {"kind": "requirements"}).sha256,
        "author_context_ref": store.put_text((project / "AUTHOR_CONTEXT.md").read_text(encoding="utf-8"), "md", {"kind": "author-context"}).sha256,
        "owner_gold_ref": store.put_text((project / "HUMAN-FLOW-GOLD.json").read_text(encoding="utf-8"), "json", {"kind": "owner-flow-gold", "writer_visible": False}).sha256,
        "semantic_gold_ref": store.put_text((project / "SEMANTIC-RELATION-GOLD.json").read_text(encoding="utf-8"), "json", {"kind": "semantic-gold", "writer_visible": False}).sha256,
        "diagnostic_positive_ref": store.put_text((project / "SOURCE-FLOW-POSITIVE.json").read_text(encoding="utf-8"), "json", {"kind": "positive-diagnostic", "writer_visible": False}).sha256,
    }
    return {
        **refs,
        "project_id": project_inputs.manifest_hash[:16],
        "protected_input_hashes": dict(project_inputs.hashes),
        "regression_version": "1",
        "source_hash": sha256(source_text.encode()).hexdigest(),
        "requested_operation": operation,
        "source_metadata": metadata,
        "accepted_moves": [], "atom_coverage": {}, "branch_memory": [],
        "accepted_move_coverage": [],
        "coverage_reconciliation_required": False,
        "owner_directives": [],
        "consumed_directive_ids": [],
        "rejected_proposals": [],
        "owner_authority_corrections": [],
        "move_index": 0, "retry_count": 0, "rollback_count": 0,
        "status": "start", "phase": "bootstrap",
    }


def _run_regressions(state: dict[str, Any], services: RuntimeServices) -> dict[str, Any]:
    from .nodes.flow import judge_edge_locally
    from .nodes.fidelity import relation_guard as local_relation_guard

    owner = _artifact_json(services.artifact_store, state["owner_gold_ref"])
    semantic = _artifact_json(services.artifact_store, state["semantic_gold_ref"])
    positives = _artifact_json(services.artifact_store, state["diagnostic_positive_ref"])
    owner_rows = []
    for case in owner.get("cases", []):
        got = judge_edge_locally(case["accepted_moves"], case["candidate"]).verdict
        owner_rows.append({"id": case["id"], "expected": case["expected"], "got": got, "pass": got == case["expected"]})
    # Owner labels captured during prior interrupts are authoritative for this project too.
    from .learning import LearningKind
    for rec in services.learning_store.records():
        if rec.project_id != str(state.get("project_id") or ""):
            continue
        if rec.kind not in {LearningKind.LOCAL_EDGE, LearningKind.STOP_BEFORE}:
            continue
        payload = rec.payload
        expected = str(payload.get("verdict") or "")
        if not payload.get("accepted_moves") or not payload.get("candidate") or not expected:
            continue
        got = judge_edge_locally(list(payload["accepted_moves"]), str(payload["candidate"])).verdict
        owner_rows.append({"id": rec.id, "expected": expected, "got": got, "pass": got == expected, "source": "owner-learning"})

    semantic_rows = []
    src = semantic.get("source", _artifact_text(services.artifact_store, state["source_ref"]))
    for case in semantic.get("cases", []):
        got = local_relation_guard(src, case["candidate"]).verdict
        semantic_rows.append({"id": case["id"], "expected": case["expected"], "got": got, "pass": got == case["expected"]})
    positive_rows = []
    for case in positives.get("cases", []):
        got = judge_edge_locally(case["accepted_moves"], case["candidate"]).verdict
        positive_rows.append({"id": case["id"], "expected": case["expected"], "got": got, "pass": got == case["expected"]})
    hard = all(r["pass"] for r in owner_rows + semantic_rows)
    payload = {
        "owner_suite": {"identity": suite_identity(owner)[0], "results": owner_rows},
        "semantic_suite": {"identity": suite_identity(semantic)[0], "results": semantic_rows},
        "positive_diagnostic": {"authoritative": False, "identity": suite_identity(positives)[0], "results": positive_rows},
        "hard_pass": hard,
    }
    ref = _put_json(services.artifact_store, payload, "regression-run")
    return {
        "phase": "regressions", "status": "regressions_passed" if hard else "machine_failure",
        "final_local_gates": {**dict(state.get("final_local_gates") or {}), "regressions_hard_pass": hard},
        "regression_result_ref": ref,
    }


def _actionable_developmental_ambiguity(raw: dict[str, Any]) -> tuple[str, str]:
    """Return a stable unit id and a complete owner-facing question.

    A nonempty model marker is not enough to interrupt the owner. The handoff must retain
    the competing meanings and explain why the choice matters. Invalid payloads are
    machine-contract failures; they must never degrade into a generic owner question.
    """
    unit_id = str(raw.get("unit_id") or "").strip()
    question = str(raw.get("question") or "").strip()
    interpretations = [
        str(value).strip()
        for value in raw.get("interpretations") or []
        if str(value).strip()
    ]
    material_consequence = str(raw.get("material_consequence") or "").strip()
    if not unit_id or not question or len(interpretations) < 2 or not material_consequence:
        raise ValueError("developmental ambiguity contract is not actionable")
    options = " ".join(
        f"Option {index}: {value}" for index, value in enumerate(interpretations, 1)
    )
    return unit_id, f"{question} {options} Why it matters: {material_consequence}"


def _developmental_apply(
    *, state: dict[str, Any], services: RuntimeServices, project_root: Path,
    source: str, requirements: str, context: str, units: list[AuthorityUnit],
    role: str = "developmental", research_context: dict[str, Any] | None = None,
) -> tuple[list[AuthorityUnit], str, bool, tuple[dict[str, Any], ...]]:
    prompt = _read_prompt(project_root, "developmental_architecture.md")
    if str(state.get("task_mode") or "") == "P4":
        prompt += "\n\n" + _read_prompt(project_root, "p4_reconstruction.md")
    payload = {
        "task_mode": state.get("task_mode", ""),
        "source_provenance": state.get("source_provenance", ""),
        "semantic_sanity": _artifact_json(services.artifact_store, state["semantic_sanity_ref"]),
        "units": [u.model_dump(mode="json") for u in units],
        "requirements": requirements,
        "author_context": context,
        "source": source,
        "research": research_context or {},
    }
    direction_block, _ = _owner_direction_block(state, "developmental")
    result = services.codex.call(
        ModelCall(
            prompt + "\n\nDEVELOPMENTAL INPUT:\n"
            + json.dumps(payload, ensure_ascii=False, indent=2)
            + direction_block,
            DEVELOPMENTAL_SCHEMA,
            role,
        ),
        services.runner, services.artifact_store,
    )
    parsed = dict(result.parsed)
    card = ArchitectureCard.model_validate(parsed["architecture_card"])
    corrected = [dict(row) for row in parsed.get("corrected_units") or []]
    dev = build_developmental_result(
        units, corrected, card=card, owner_position_changed=bool(parsed.get("owner_position_diverges")),
    )
    original = {u.id: u for u in units}
    active: list[AuthorityUnit] = []
    for row in corrected:
        if str(row.get("disposition") or "").lower() in {"omit", "drop", "remove", "bank"}:
            continue
        rid = str(row.get("id") or "")
        prior = original.get(rid)
        origin = str(row.get("origin") or "")
        authority = prior.authority if prior is not None else (
            Authority.RESEARCH_PROVISIONAL if origin == "research_candidate" else Authority.AI_PROVISIONAL
        )
        active.append(AuthorityUnit(
            id=rid or f"dev-{len(active)+1:03d}", text=str(row.get("text") or "").strip(),
            authority=authority, exact_lock=bool(prior.exact_lock) if prior else False,
            reason=str(row.get("reason") or "developmental reconstruction"),
        ))
    dev_ref = _put_json(services.artifact_store, {
        "architecture_card": card.model_dump(mode="json"),
        "corrected_units": corrected,
        "owner_position_diverges": bool(parsed.get("owner_position_diverges")),
        "unresolved_authorial": list(parsed.get("unresolved_authorial") or []),
    }, "developmental-result", role=role)
    unresolved = tuple(dict(row) for row in parsed.get("unresolved_authorial") or [])
    return active, dev_ref, bool(parsed.get("owner_position_diverges")), unresolved


def _research_escalation(
    *, state: dict[str, Any], services: RuntimeServices, project_root: Path,
    source: str, requirements: str, context: str, units: list[AuthorityUnit],
) -> tuple[str, str, str, list[AuthorityUnit], bool]:
    from .research.discovery import BraveSearchProvider, DirectURLProvider
    from .research.fetch import HTTPFetcher

    research_direction_block, _ = _owner_direction_block(state, "research")
    question_result = services.codex.call(
        ModelCall(
            "Form one bounded research question for the exact material uncertainty. Do not broaden into a literature review.\n\n"
            + json.dumps({
                "semantic_sanity": _artifact_json(services.artifact_store, state["semantic_sanity_ref"]),
                "source": source,
            }, ensure_ascii=False, indent=2)
            + research_direction_block,
            RESEARCH_QUESTION_SCHEMA, "research_question",
        ), services.runner, services.artifact_store,
    )
    question = ResearchQuestion.model_validate(question_result.parsed)
    provider = services.research_provider
    if provider is None:
        direct = DirectURLProvider(source + "\n" + question.query)
        if direct.urls:
            provider = direct
        else:
            provider = services.ensure_research_provider()
    if provider is None:
        raise RuntimeError("material research is required but no discovery provider is configured; set BRAVE_SEARCH_API_KEY")
    fetcher = services.research_fetcher or HTTPFetcher()
    hits=provider.search(question.query or question.uncertainty, limit=5)
    hits=sorted(hits, key=lambda hit: (not bool(getattr(hit, "primary_hint", False)), hit.url))[:5]
    sources=[fetcher.fetch(hit.url) for hit in hits]
    source_payload=[]
    for item in sources:
        body=item.body
        if len(body)>30000:
            body=body[:30000]
        source_payload.append({
            "url": item.final_url, "body_sha256": item.body_sha256,
            "access_level": str(item.access_level), "access_limitation": item.access_limitation,
            "body": body,
        })
    evidence_result=services.codex.call(
        ModelCall(
            "Assess only what these retrieved sources support or resist for the bounded question. Keep source support separate from system inference.\n\n"
            + json.dumps({"question": question.model_dump(mode="json"), "sources": source_payload}, ensure_ascii=False, indent=2)
            + research_direction_block,
            RESEARCH_SUMMARY_SCHEMA, "research_evidence",
        ), services.runner, services.artifact_store,
    )
    summary_payload=dict(evidence_result.parsed)
    summary_payload.setdefault("question", question.uncertainty)
    summary_payload.setdefault("material_consequence", question.material_consequence)
    summary=ResearchSummary.model_validate(summary_payload)
    research_ref=_put_json(services.artifact_store, {
        "question": question.model_dump(mode="json"),
        "sources": [{
            "url": item.final_url, "body_sha256": item.body_sha256,
            "access_level": str(item.access_level), "access_limitation": item.access_limitation,
        } for item in sources],
        "summary": summary.model_dump(mode="json"),
    }, "research-result")
    faithful_ref=_put_json(services.artifact_store, {
        "units": [u.model_dump(mode="json") for u in units],
        "position": "faithful inherited/owner-grounded route before research adoption",
    }, "faithful-position")
    alternative_units, alternative_ref, diverges, _ = _developmental_apply(
        state=state, services=services, project_root=project_root, source=source,
        requirements=requirements, context=context, units=units,
        role="research_developmental", research_context={
            "research_ref": research_ref, "summary": summary.model_dump(mode="json")
        },
    )
    # The caller may adopt a non-divergent evidence repair directly. A materially different
    # position remains separate until an explicit owner adoption interrupt resolves it.
    return faithful_ref, alternative_ref, research_ref, alternative_units, diverges



def _resume_owner_position_choice(state: dict[str, Any], store: ArtifactStore) -> dict[str, Any] | None:
    adopted_ref=str(state.get("adopted_alternative_ref") or "")
    kept_ref=str(state.get("kept_faithful_position_ref") or "")
    if not adopted_ref and not kept_ref:
        return None

    units: list[AuthorityUnit]=[]
    if adopted_ref:
        payload=_artifact_json(store,adopted_ref)
        for index,row in enumerate(payload.get("corrected_units") or [],1):
            if str(row.get("disposition") or "").lower() in {"omit","drop","remove","bank"}:
                continue
            text=str(row.get("text") or "").strip()
            if not text:
                continue
            units.append(AuthorityUnit(
                id=str(row.get("id") or f"owner-adopted-{index:03d}"),
                text=text,authority=Authority.OWNER_GROUNDED,exact_lock=False,
                reason=str(row.get("reason") or "owner-adopted researched position"),
            ))
    else:
        payload=_artifact_json(store,kept_ref)
        units=[AuthorityUnit.model_validate(row) for row in payload.get("units") or []]

    if not units:
        raise RuntimeError("owner position choice resolved to no semantic units")
    refs=[_put_json(store,u.model_dump(mode="json"),"authority-unit",writer_visible=True) for u in units]
    return {
        "phase":"representation","status":"represented",
        "accepted_moves":[],"accepted_move_coverage":[],
        "coverage_reconciliation_required":False,"accepted_prefix_hash":"",
        "move_index":0,"retry_count":0,"rollback_count":0,
        "task_mode":str(state.get("task_mode") or "P3"),
        "source_provenance":str(state.get("source_provenance") or ""),
        "section_job":str(state.get("section_job") or "develop the thought from its live pressure"),
        "atom_refs":refs,"atom_coverage":{u.id:False for u in units},
        "semantic_sanity_ref":str(state.get("semantic_sanity_ref") or ""),
        "developmental_ref":adopted_ref or str(state.get("developmental_ref") or ""),
        "faithful_position_ref":str(state.get("faithful_position_ref") or kept_ref),
        "better_reasoned_alternative_ref":str(state.get("better_reasoned_alternative_ref") or adopted_ref),
        "research_ref":str(state.get("research_ref") or ""),
        "adopted_alternative_ref":"","kept_faithful_position_ref":"",
        "active_interrupt_kind":"",
    }

_SEMANTIC_ESCALATIONS = {"BASIC", "P3", "P4", "RESEARCH", "OWNER"}


def _normalized_semantic_escalation(
    sanity: dict[str, Any],
    *,
    owner_resolved: bool,
) -> tuple[str, str]:
    """Return the next required action and a fail-closed diagnostic code."""
    status = str(sanity.get("status") or "").upper()
    escalation = str(sanity.get("recommended_escalation") or "").upper()
    owner_question = str(sanity.get("owner_question") or "").strip()
    research_required = bool(sanity.get("research_trigger"))
    if escalation not in _SEMANTIC_ESCALATIONS:
        return "OWNER", "UNKNOWN_ESCALATION"
    if status == "PASS":
        if escalation != "BASIC" or research_required or owner_question:
            return "OWNER", "CONTRADICTORY_PASS"
        return "BASIC", ""
    if status != "FAIL":
        return "OWNER", "UNKNOWN_SANITY_STATUS"
    if escalation == "BASIC":
        return "OWNER", "FAIL_WITHOUT_ACTION"
    # A developmental route may need to construct the concrete alternative before
    # its owner question is meaningful. Research-plus-owner ambiguity, by contrast,
    # must be owner-grounded before any source-role search proceeds.
    owner_first = escalation == "OWNER" or (owner_question and research_required)
    if owner_first and not owner_resolved:
        return "OWNER", ""
    if research_required:
        return "RESEARCH", ""
    if escalation == "OWNER":
        # A checkpointed owner answer resolves only the owner action. It does not
        # rewrite the model's semantic-sanity result into an artificial PASS.
        return "BASIC", ""
    return escalation, ""


def _representation_node(state: dict[str, Any], services: RuntimeServices, project_root: Path) -> dict[str, Any]:
    store = services.artifact_store
    owner_choice=_resume_owner_position_choice(state,store)
    if owner_choice is not None:
        return owner_choice
    source = _artifact_text(store, state["source_ref"])
    requirements = _artifact_text(store, state["requirements_ref"])
    context = _artifact_text(store, state["author_context_ref"])
    provenance = classify_provenance(source, metadata=dict(state.get("source_metadata") or {})).provenance
    prompt = _read_prompt(project_root, "represent.md") + "\n\n" + _read_prompt(project_root, "semantic_sanity.md")
    prompt += "\n\nSOURCE PROVENANCE:\n" + provenance.value
    prompt += "\n\nREQUESTED OPERATION:\n" + str(state.get("requested_operation") or "humanize")
    prompt += "\n\nREQUIREMENTS:\n" + requirements + "\n\nAUTHOR CONTEXT:\n" + context + "\n\nSOURCE:\n" + source
    direction_block, _ = _owner_direction_block(state, "representation")
    prompt += direction_block
    corrections = []
    for raw in list(state.get("owner_authority_corrections") or [])[-20:]:
        if not isinstance(raw, dict):
            continue
        correction_id = str(raw.get("id") or "")[:128]
        instruction = str(raw.get("instruction") or "").strip()[:4000]
        if correction_id and instruction:
            corrections.append({
                "id": correction_id,
                "instruction": instruction,
                "reason": str(raw.get("reason") or "")[:2000],
            })
    if corrections:
        prompt += "\n\nCONFIRMED OWNER MEANING CORRECTIONS:\n" + json.dumps(
            corrections,
            ensure_ascii=False,
            indent=2,
        )
    resolved_answer=str(state.get("resolved_authorial_answer") or "").strip()
    if resolved_answer:
        prompt += "\n\nOWNER AUTHORITY RESOLUTION (controls the open meaning):\n" + resolved_answer
    result = services.codex.call(ModelCall(prompt, REPRESENTATION_SCHEMA, "representation"), services.runner, store)
    parsed = dict(result.parsed)
    sanity = dict(parsed["semantic_sanity"])
    mode = choose_mode(
        str(state.get("requested_operation") or "humanize"), provenance,
        semantic_sanity=sanity.get("status") == "PASS",
    )
    base_authority = _authority_for(provenance)
    units: list[AuthorityUnit] = []
    for index, row in enumerate(parsed.get("units") or [], 1):
        text = str(row.get("text") or "").strip()
        if not text:
            continue
        units.append(AuthorityUnit(
            id=str(row.get("id") or f"u{index:03d}"), text=text,
            authority=base_authority,
            exact_lock=base_authority is Authority.OWNER_LOCKED,
            reason=str(row.get("reason") or "representation"),
        ))
    if resolved_answer:
        target_id=str(state.get("open_authorial_unit_id") or "")
        replaced=False
        updated_units=[]
        for unit in units:
            if target_id and unit.id==target_id:
                updated_units.append(AuthorityUnit(
                    id=unit.id,text=resolved_answer,authority=Authority.OWNER_GROUNDED,
                    exact_lock=False,reason="owner-resolved authorial ambiguity",
                ))
                replaced=True
            else:
                updated_units.append(unit)
        if not replaced:
            updated_units.append(AuthorityUnit(
                id=target_id or "owner-resolution",text=resolved_answer,authority=Authority.OWNER_GROUNDED,
                exact_lock=False,reason="owner-resolved authorial ambiguity",
            ))
        units=updated_units
        # The answer resolves only the owner action. Research or developmental work
        # signalled by the same sanity result remains pending on this resumed pass.
        sanity={**sanity,"owner_question":""}

    if corrections:
        correction_ids = {row["id"] for row in corrections}
        units = [unit for unit in units if unit.id not in correction_ids]
        units.extend(AuthorityUnit(
            id=row["id"],
            text=row["instruction"],
            authority=Authority.OWNER_GROUNDED,
            exact_lock=False,
            reason="owner supervisor meaning correction",
        ) for row in corrections)

    if not units:
        raise RuntimeError("representation produced no semantic units")

    sanity_ref = _put_json(store, sanity, "semantic-sanity")
    working_state = {
        **state, "semantic_sanity_ref": sanity_ref, "source_provenance": provenance.value,
        "task_mode": mode.mode.value,
    }
    developmental_ref=""
    faithful_position_ref=""
    better_reasoned_alternative_ref=""
    research_ref=""
    escalation, escalation_error = _normalized_semantic_escalation(
        sanity,
        owner_resolved=bool(resolved_answer),
    )
    if escalation_error:
        return {
            "phase": "representation",
            "status": "owner_ambiguity_required",
            "source_provenance": provenance.value,
            "task_mode": mode.mode.value,
            "semantic_sanity_ref": sanity_ref,
            "semantic_escalation_error": escalation_error,
            "interrupt_payload": {
                "kind": "AUTHORIAL_AMBIGUITY",
                "question": str(sanity.get("owner_question") or (
                    "Semantic sanity failed without a valid bounded escalation. "
                    "Which meaning and source role should control?"
                )),
            },
        }

    if sanity.get("status") == "FAIL" and escalation in {"P3", "P4"}:
        if not mode.substantive_permission:
            return {
                "phase":"representation", "status":"owner_ambiguity_required",
                "source_provenance":provenance.value, "task_mode":mode.mode.value,
                "semantic_sanity_ref":sanity_ref,
                "interrupt_payload":{
                    "kind":"AUTHORIAL_AMBIGUITY",
                    "question":str(sanity.get("owner_question") or (
                        "The thought appears to need a substantive correction, but this mode preserves the owner's position. Which meaning should control?"
                    )),
                },
            }
        # The explicit semantic-sanity recommendation controls repair depth only when the active mode
        # already carries substantive authority.
        working_state["task_mode"] = escalation
        active, developmental_ref, diverges, unresolved = _developmental_apply(
            state=working_state, services=services, project_root=project_root, source=source,
            requirements=requirements, context=context, units=units,
        )
        if unresolved:
            unit_id, owner_question = _actionable_developmental_ambiguity(unresolved[0])
            return {
                "phase":"representation", "status":"owner_ambiguity_required",
                "source_provenance":provenance.value, "task_mode":escalation,
                "semantic_sanity_ref":sanity_ref, "open_authorial_unit_id":unit_id,
                "interrupt_payload":{
                    "kind":"AUTHORIAL_AMBIGUITY",
                    "question":str(sanity.get("owner_question") or owner_question),
                    "unit_id":unit_id,
                },
            }
        if diverges:
            faithful_position_ref=_put_json(store,{
                "units":[u.model_dump(mode="json") for u in units],
                "position":"faithful route before owner adoption",
            },"faithful-position")
            better_reasoned_alternative_ref=developmental_ref
            faithful_refs=[_put_json(store,u.model_dump(mode="json"),"authority-unit",writer_visible=True) for u in units]
            return {
                "phase":"representation", "status":"owner_ambiguity_required",
                "source_provenance":provenance.value, "task_mode":escalation,
                "semantic_sanity_ref":sanity_ref, "developmental_ref":developmental_ref,
                "faithful_position_ref":faithful_position_ref,
                "better_reasoned_alternative_ref":better_reasoned_alternative_ref,
                "atom_refs":faithful_refs, "atom_coverage":{u.id:False for u in units},
                "section_job":str(parsed.get("section_job") or "develop the thought from its live pressure"),
                "interrupt_payload":{
                    "kind":"AUTHORIAL_AMBIGUITY",
                    "question":str(sanity.get("owner_question") or "A proposed correction changes the owner's position. Which meaning is actually yours?"),
                },
            }
        if active:
            units=active
    elif sanity.get("status") == "FAIL" and escalation == "RESEARCH":
        if not mode.research_permission:
            return {
                "phase":"representation", "status":"owner_ambiguity_required",
                "source_provenance":provenance.value, "task_mode":mode.mode.value,
                "semantic_sanity_ref":sanity_ref,
                "interrupt_payload":{
                    "kind":"AUTHORIAL_AMBIGUITY",
                    "question":"The source needs substantive source-role research, but this mode does not authorize it. Which meaning should control?",
                },
            }
        faithful_position_ref, better_reasoned_alternative_ref, research_ref, research_units, diverges = _research_escalation(
            state=working_state, services=services, project_root=project_root, source=source,
            requirements=requirements, context=context, units=units,
        )
        if diverges:
            faithful_refs=[_put_json(store,u.model_dump(mode="json"),"authority-unit",writer_visible=True) for u in units]
            adoption_state={
                **working_state,
                "faithful_position_ref":faithful_position_ref,
                "better_reasoned_alternative_ref":better_reasoned_alternative_ref,
            }
            return {
                "phase":"representation", "status":"research_adoption_required",
                "source_provenance":provenance.value, "task_mode":mode.mode.value,
                "semantic_sanity_ref":sanity_ref, "research_ref":research_ref,
                "faithful_position_ref":faithful_position_ref,
                "better_reasoned_alternative_ref":better_reasoned_alternative_ref,
                "atom_refs":faithful_refs, "atom_coverage":{u.id:False for u in units},
                "section_job":str(parsed.get("section_job") or "develop the thought from its live pressure"),
                "interrupt_payload":research_adoption_payload(adoption_state),
            }
        if research_units:
            units=research_units
    elif sanity.get("status") == "FAIL" and escalation == "OWNER":
        return {
            "phase":"representation", "status":"owner_ambiguity_required",
            "source_provenance":provenance.value, "task_mode":mode.mode.value,
            "semantic_sanity_ref":sanity_ref,
            "interrupt_payload":{"kind":"AUTHORIAL_AMBIGUITY", "question":str(sanity.get("owner_question") or "Which meaning should control?")},
        }

    refs=[]
    for unit in units:
        refs.append(_put_json(store, unit.model_dump(mode="json"), "authority-unit", writer_visible=True))
    return {
        "phase": "representation", "status": "represented",
        "accepted_moves": [], "accepted_move_coverage": [],
        "coverage_reconciliation_required": False, "accepted_prefix_hash": "",
        "move_index": 0, "retry_count": 0, "rollback_count": 0,
        "source_provenance": provenance.value, "task_mode": str(working_state.get("task_mode") or mode.mode.value),
        "section_job": str(parsed.get("section_job") or "develop the thought from its live pressure"),
        "atom_refs": refs, "atom_coverage": {u.id: False for u in units},
        "semantic_sanity_ref": sanity_ref,
        "escalation_reason": ", ".join(sanity.get("defect_types") or []),
        "developmental_ref": developmental_ref,
        "faithful_position_ref": faithful_position_ref,
        "better_reasoned_alternative_ref": better_reasoned_alternative_ref,
        "research_ref": research_ref,
        "resolved_authorial_answer":"" if resolved_answer else str(state.get("resolved_authorial_answer") or ""),
        "active_interrupt_kind":"" if resolved_answer else str(state.get("active_interrupt_kind") or ""),
    }

def _load_units(state: dict[str, Any], store: ArtifactStore) -> list[AuthorityUnit]:
    return [AuthorityUnit.model_validate(_artifact_json(store, ref)) for ref in state.get("atom_refs") or []]


def _pressure_vote(services: RuntimeServices, project_root: Path, provider: str, accepted: str) -> PressureVote:
    prompt = _read_prompt(project_root, "pressure.md") + "\n\nACCEPTED PROSE:\n" + accepted
    adapter = services.codex if provider == "codex" else services.claude
    result = adapter.call(ModelCall(prompt, PRESSURE_SCHEMA, "pressure_reader"), services.runner, services.artifact_store)
    row = dict(result.parsed)
    return PressureVote(
        state=row["state"], confidence=float(row["confidence"]), live_pressure=row["live_pressure"],
        previous_move_function=row["previous_move_function"], already_settled=tuple(row["already_settled"]),
        backward_reopen_risks=tuple(row["backward_reopen_risks"]),
        why_stop_might_be_natural=row["why_stop_might_be_natural"], provider=provider,
    )


def _validated_move_coverage(
    moves: list[str],
    rows: Any,
    known_unit_ids: set[str],
    *,
    require_indices: bool = False,
) -> list[dict[str, Any]] | None:
    if isinstance(rows, dict):
        rows = rows.get("moves")
    if not isinstance(rows, list) or len(rows) != len(moves):
        return None
    validated: list[dict[str, Any]] = []
    for index, (move, row) in enumerate(zip(moves, rows, strict=True)):
        if not isinstance(row, dict):
            return None
        if (require_indices and row.get("index") != index) or (
            "index" in row and row.get("index") != index
        ):
            return None
        digest = str(row.get("move_sha256") or "")
        if digest != sha256(move.encode("utf-8")).hexdigest():
            return None
        covered = row.get("covered_unit_ids")
        if not isinstance(covered, list) or any(not isinstance(item, str) for item in covered):
            return None
        if not set(covered).issubset(known_unit_ids):
            return None
        validated.append({
            "move_sha256": digest,
            "covered_unit_ids": sorted(set(covered)),
        })
    return validated


def _reconcile_move_coverage(
    state: dict[str, Any],
    services: RuntimeServices,
    project_root: Path,
) -> dict[str, list[dict[str, Any]]]:
    moves = [str(move) for move in state.get("accepted_moves") or []]
    units = _load_units(state, services.artifact_store)
    known = {unit.id for unit in units}
    mapping_input = {
        "authority_units": [unit.model_dump(mode="json") for unit in units],
        "accepted_moves": [
            {
                "index": index,
                "move_sha256": sha256(move.encode("utf-8")).hexdigest(),
                "text": move,
            }
            for index, move in enumerate(moves)
        ],
    }
    direction_block, _ = _owner_direction_block(state, "fidelity_guard")
    proposed = services.codex.call(ModelCall(
        "Reconstruct exact per-move authority coverage. Return one row for every numbered move; "
        "do not infer unknown authority IDs.\n\n"
        + json.dumps(mapping_input, ensure_ascii=False, indent=2)
        + direction_block,
        MOVE_COVERAGE_SCHEMA,
        "coverage_reconciliation",
    ), services.runner, services.artifact_store).parsed
    rows = _validated_move_coverage(
        moves,
        proposed,
        known,
        require_indices=True,
    )
    if rows is None:
        raise CoverageReconciliationBlocked("coverage reconciliation did not validate locally")
    check_input = {
        "source": _artifact_text(services.artifact_store, state["source_ref"]),
        "authority_units": [unit.model_dump(mode="json") for unit in units],
        "accepted_moves": moves,
        "proposed_mapping": rows,
    }
    checked = services.codex.call(ModelCall(
        "Independently check whether this per-move coverage mapping is complete and exact. "
        "Fail on any unsupported or missing unit attribution.\n\n"
        + json.dumps(check_input, ensure_ascii=False, indent=2)
        + direction_block,
        MOVE_COVERAGE_CHECK_SCHEMA,
        "coverage_reconciliation_check",
    ), services.runner, services.artifact_store).parsed
    if str(checked.get("verdict") or "") != "PASS":
        reason = str(checked.get("reason") or "independent coverage check failed")
        raise CoverageReconciliationBlocked(reason)
    return {"moves": [
        {"index": index, **row}
        for index, row in enumerate(rows)
    ]}


def _generation_node(state: dict[str, Any], services: RuntimeServices, project_root: Path, config: RuntimeConfig) -> dict[str, Any]:
    store = services.artifact_store
    units = _load_units(state, store)
    coverage = dict(state.get("atom_coverage") or {})
    units_for_stop = [u.model_copy(update={"disposition": "used" if coverage.get(u.id) else "unresolved"}) for u in units]
    moves = list(state.get("accepted_moves") or [])
    boundary_id = generation_boundary_id(
        moves,
        coverage,
        graph_version=str(state.get("graph_version") or ""),
        program_version=str(state.get("program_version") or ""),
    )
    if int(state.get("retry_count", 0)) >= config.writer_attempts:
        return {
            "status":"machine_failure","phase":"generation","failure_class":"GENERATION_DEAD_END",
            "budget":"writer_attempts","budget_limit":config.writer_attempts,
            "generation_boundary_id":boundary_id,"decision_boundary_id":boundary_id,
        }
    if len(moves) >= config.max_moves:
        return {
            "status":"machine_failure","phase":"generation","failure_class":"GENERATION_DEAD_END",
            "budget":"accepted_moves","budget_limit":config.max_moves,
            "generation_boundary_id":boundary_id,"decision_boundary_id":boundary_id,
        }

    if moves:
        accepted = " ".join(moves)
        pressure = commit_pressure([
            _pressure_vote(services, project_root, "codex", accepted),
            _pressure_vote(services, project_root, "claude", accepted),
        ])
    else:
        opening = PressureVote("OPEN", 1.0, "Begin from the real pressure or question", provider="controller")
        pressure = CommittedPressure("OPEN", 1.0, opening.live_pressure, (opening,), "opening move")

    stop = decide_stop(pressure, units_for_stop)
    pressure_votes_state = [{
        "state": vote.state,
        "confidence": vote.confidence,
        "provider": vote.provider,
        "boundary_id": boundary_id,
    } for vote in pressure.votes]
    uncovered_required_count = sum(
        1 for unit in units
        if unit.must_preserve and not bool(coverage.get(unit.id))
    )
    pressure_state = {
        "state": pressure.state, "confidence": pressure.confidence, "live_pressure": pressure.live_pressure,
        "rationale": pressure.rationale, "boundary_id": boundary_id,
    }
    if stop.action == "STOP":
        return {"status": "generated", "phase": "generation", "committed_pressure": pressure_state,
                "stop_result": {"action": stop.action, "reason": stop.reason},
                "generation_boundary_id":boundary_id,"decision_boundary_id":boundary_id,
                "pressure_votes":pressure_votes_state,
                "uncovered_required_count":uncovered_required_count}
    if stop.action == "ROLLBACK" and moves:
        if int(state.get("rollback_count", 0)) >= config.max_rollbacks:
            return {"status": "machine_failure", "phase": "generation", "failure_class": "GENERATION_DEAD_END"}
        ledger = _validated_move_coverage(
            moves,
            state.get("accepted_move_coverage"),
            set(coverage),
        )
        if ledger is None:
            reconciled = _reconcile_move_coverage(state, services, project_root)
            ledger = _validated_move_coverage(
                moves,
                reconciled,
                set(coverage),
                require_indices=True,
            )
        if ledger is None:
            raise CoverageReconciliationBlocked("automatic rollback needs validated per-move coverage")
        retained_ledger = ledger[:-1]
        retained_units = {
            unit_id
            for row in retained_ledger
            for unit_id in row["covered_unit_ids"]
        }
        retained_coverage = {unit_id: unit_id in retained_units for unit_id in coverage}
        next_boundary_id = generation_boundary_id(
            moves[:-1], retained_coverage,
            graph_version=str(state.get("graph_version") or ""),
            program_version=str(state.get("program_version") or ""),
        )
        return {
            "status": "continue_generation", "phase": "generation",
            "accepted_moves": moves[:-1], "rollback_count": int(state.get("rollback_count", 0)) + 1,
            "accepted_move_coverage": retained_ledger,
            "coverage_reconciliation_required": False,
            "atom_coverage": retained_coverage,
            "accepted_prefix_hash": sha256(" ".join(moves[:-1]).encode("utf-8")).hexdigest(),
            "committed_pressure": pressure_state,
            "pressure_votes":pressure_votes_state,
            "uncovered_required_count":uncovered_required_count,
            "generation_boundary_id":next_boundary_id,"decision_boundary_id":boundary_id,
            "branch_memory": [{"kind": "rollback_before_stop", "removed": moves[-1], "unresolved_required": list(stop.unresolved_required)}],
        }

    promoted = services.learning_store.promoted_rules()
    direction_block, applied_directives = _owner_direction_block(
        state,
        "generation",
        include_next_attempt=True,
    )
    payload = writer_payload(
        str(state.get("section_job") or ""),
        units,
        moves,
        pressure_state,
        promoted,
        owner_directives=applied_directives,
        rejected_proposals=_safe_rejected_proposals(state, store),
    )
    writer_prompt = (
        _read_prompt(project_root, "writer.md")
        + "\n\nWRITER INPUT (NO RAW SOURCE / NO OWNER REGRESSION EXAMPLES):\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + direction_block
    )
    result = services.claude.call(ModelCall(writer_prompt, None, "writer"), services.runner, store)
    candidate = str(result.parsed if isinstance(result.parsed, str) else result.text).strip().strip("`").strip()
    proposal_ref = store.put_text(
        candidate,
        "md",
        {"kind": "writer-proposal", "node": "generation", "move_index": len(moves) + 1},
    ).sha256
    _emit(services, "proposal.complete", {
        "node": "generation",
        "proposal_ref": proposal_ref,
        "proposal_sha256": proposal_ref,
        "text": candidate,
    })

    def checkpoint(update: dict[str, Any]) -> dict[str, Any]:
        return _consume_next_attempt_directives(state, update, applied_directives)

    def retry(stage: str, reason: str, **update: Any) -> dict[str, Any]:
        retry_count = int(state.get("retry_count", 0)) + 1
        _emit(services, "generation.retry", {
            "node": "generation",
            "stage": stage,
            "reason": reason,
            "retry_count": retry_count,
            "proposal_ref": proposal_ref,
        })
        return checkpoint({
            "status": "continue_generation",
            "phase": "generation",
            "retry_count": retry_count,
            "proposal_ref": proposal_ref,
            "committed_pressure": pressure_state,
            "pressure_votes": pressure_votes_state,
            "uncovered_required_count": uncovered_required_count,
            "generation_boundary_id": boundary_id,
            "decision_boundary_id": boundary_id,
            **update,
        })

    def stop_before_candidate(
        stage: str,
        result_row: dict[str, Any],
    ) -> dict[str, Any]:
        result_key = "full_edge_result" if stage == "full_edge" else "entry_edge_result"
        required = [
            unit.id for unit in units
            if unit.must_preserve and not bool(coverage.get(unit.id))
        ]
        common = {
            "committed_pressure": pressure_state,
            "pressure_votes": pressure_votes_state,
            "uncovered_required_count": len(required),
            "generation_boundary_id": boundary_id,
            "decision_boundary_id": boundary_id,
            "generation_rejection_class": "STOP_BEFORE_CANDIDATE",
            "proposal_ref": proposal_ref,
            result_key: result_row,
        }
        if not required:
            return checkpoint({
                "status": "generated",
                "phase": "generation",
                "stop_result": {
                    "action": "STOP",
                    "reason": "accepted boundary already arrived; proposed candidate discarded",
                },
                **common,
            })
        ledger = _validated_move_coverage(
            moves,
            state.get("accepted_move_coverage"),
            set(coverage),
        )
        if (
            not moves
            or ledger is None
            or not is_natural_arrival(moves[-1])
            or int(state.get("rollback_count", 0)) >= config.max_rollbacks
        ):
            return checkpoint({
                "status": "machine_failure",
                "phase": "generation",
                "failure_class": "POLICY_CONTRADICTION",
                "generation_rejection_class": "UNSAFE_ARRIVAL_ROLLBACK",
                "uncovered_required_count": len(required),
                **{key: value for key, value in common.items() if key != "generation_rejection_class"},
            })
        retained_ledger = ledger[:-1]
        retained_units = {
            unit_id
            for row in retained_ledger
            for unit_id in row["covered_unit_ids"]
        }
        retained_coverage = {
            unit_id: unit_id in retained_units
            for unit_id in coverage
        }
        next_boundary_id = generation_boundary_id(
            moves[:-1], retained_coverage,
            graph_version=str(state.get("graph_version") or ""),
            program_version=str(state.get("program_version") or ""),
        )
        return checkpoint({
            "status": "continue_generation",
            "phase": "generation",
            "accepted_moves": moves[:-1],
            "accepted_move_coverage": retained_ledger,
            "coverage_reconciliation_required": False,
            "atom_coverage": retained_coverage,
            "accepted_prefix_hash": sha256(" ".join(moves[:-1]).encode("utf-8")).hexdigest(),
            "retry_count": 0,
            "rollback_count": int(state.get("rollback_count", 0)) + 1,
            "generation_boundary_id": next_boundary_id,
            "decision_boundary_id": boundary_id,
            "branch_memory": [{
                "kind": "rollback_before_stop",
                "removed_sha256": sha256(moves[-1].encode("utf-8")).hexdigest(),
                "unresolved_required": required,
            }],
            **{key: value for key, value in common.items() if key not in {"generation_boundary_id", "decision_boundary_id"}},
        })

    if candidate == "<STOP>":
        return retry(
            "writer_stop",
            "writer proposed a stop while committed pressure remained open",
            branch_memory=[{"kind": "premature_writer_stop", "pressure": pressure_state}],
        )
    spans = candidate_semantic_spans(candidate)
    if len(spans) != 1:
        return retry(
            "atomicity",
            f"proposal contains {len(spans)} semantic advances",
            branch_memory=[{"kind": "atomicity_fail", "candidate": candidate, "spans": spans}],
        )

    if moves:
        deterministic = judge_full_edge(moves, candidate, pressure)
        deterministic_row = {**deterministic.__dict__, "boundary_id": boundary_id}
        _emit(services, "guard.result", {
            "node": "generation",
            "gate": "deterministic_edge",
            "verdict": deterministic.verdict,
            "reason": deterministic.reason,
            "proposal_ref": proposal_ref,
        })
        if deterministic.verdict != "PASS":
            if deterministic.verdict == "STOP_BEFORE_CANDIDATE":
                return stop_before_candidate("deterministic_edge", deterministic_row)
            return retry(
                "deterministic_edge",
                deterministic.reason or deterministic.verdict,
                entry_edge_result=deterministic_row,
                generation_rejection_class=str(deterministic.verdict),
                branch_memory=[{"kind": "edge_fail", "candidate": candidate, "verdict": deterministic.verdict}],
            )
        edge_input = {"accepted_moves": moves, "pressure": pressure_state, "candidate": candidate}
        entry_direction_block, _ = _owner_direction_block(state, "entry_edge")
        entry = services.codex.call(ModelCall(
            _read_prompt(project_root, "entry_edge.md") + "\n\n"
            + json.dumps(edge_input, ensure_ascii=False, indent=2)
            + entry_direction_block,
            EDGE_SCHEMA, "entry_edge"), services.runner, store).parsed
        entry = {**entry, "boundary_id": boundary_id}
        _emit(services, "guard.result", {
            "node": "generation",
            "gate": "entry_edge",
            "verdict": str(entry.get("verdict") or ""),
            "reason": str(entry.get("reason") or ""),
            "proposal_ref": proposal_ref,
        })
        if entry["verdict"] != "PASS":
            if entry["verdict"] == "STOP_BEFORE_CANDIDATE":
                return stop_before_candidate("entry_edge", entry)
            return retry(
                "entry_edge",
                str(entry.get("reason") or entry["verdict"]),
                entry_edge_result=entry,
                generation_rejection_class=str(entry["verdict"]),
                branch_memory=[{"kind": "entry_edge_fail", "candidate": candidate, "result": entry}],
            )
        full_direction_block, _ = _owner_direction_block(state, "full_edge")
        full = services.codex.call(ModelCall(
            _read_prompt(project_root, "full_edge.md") + "\n\n"
            + json.dumps(edge_input, ensure_ascii=False, indent=2)
            + full_direction_block,
            EDGE_SCHEMA, "full_edge"), services.runner, store).parsed
        full = {**full, "boundary_id": boundary_id}
        _emit(services, "guard.result", {
            "node": "generation",
            "gate": "full_edge",
            "verdict": str(full.get("verdict") or ""),
            "reason": str(full.get("reason") or ""),
            "proposal_ref": proposal_ref,
        })
        if full["verdict"] != "PASS":
            if full["verdict"] == "STOP_BEFORE_CANDIDATE":
                return stop_before_candidate("full_edge", full)
            return retry(
                "full_edge",
                str(full.get("reason") or full["verdict"]),
                full_edge_result=full,
                generation_rejection_class=str(full["verdict"]),
                branch_memory=[{"kind": "full_edge_fail", "candidate": candidate, "result": full}],
            )
    else:
        entry = full = {"verdict": "PASS", "confidence": 1.0, "failure_type": "none", "reason": "opening", "challenge": "", "boundary_id": boundary_id}

    source = _artifact_text(store, state["source_ref"])
    if TaskMode(str(state.get("task_mode") or "P2S")) is TaskMode.P2S:
        local_fidelity = relation_guard(source, candidate)
        _emit(services, "guard.result", {
            "node": "generation",
            "gate": "local_relation",
            "verdict": local_fidelity.verdict,
            "reason": local_fidelity.reason,
            "proposal_ref": proposal_ref,
        })
        if local_fidelity.verdict != "PASS":
            return retry(
                "local_relation",
                local_fidelity.reason or local_fidelity.verdict,
                relation_result=local_fidelity.__dict__,
                branch_memory=[{"kind": "relation_fail", "candidate": candidate}],
            )
    fidelity_input = {
        "task_mode": state.get("task_mode"), "source_provenance": state.get("source_provenance"),
        "source": source, "authority_units": [u.model_dump(mode="json") for u in units],
        "accepted_moves": moves, "candidate": candidate,
    }
    fidelity_direction_block, _ = _owner_direction_block(state, "fidelity_guard")
    fidelity = services.codex.call(ModelCall(
        _read_prompt(project_root, "semantic_guard.md") + "\n\n"
        + _read_prompt(project_root, "relation_guard.md") + "\n\n"
        + json.dumps(fidelity_input, ensure_ascii=False, indent=2)
        + fidelity_direction_block,
        FIDELITY_SCHEMA, "fidelity_guard"), services.runner, store).parsed
    _emit(services, "guard.result", {
        "node": "generation",
        "gate": "model_fidelity",
        "verdict": str(fidelity.get("verdict") or ""),
        "reason": str(fidelity.get("reason") or ""),
        "proposal_ref": proposal_ref,
    })
    if fidelity["verdict"] != "PASS":
        return retry(
            "model_fidelity",
            str(fidelity.get("reason") or fidelity["verdict"]),
            semantic_result=fidelity,
            branch_memory=[{"kind": "fidelity_fail", "candidate": candidate, "result": fidelity}],
        )
    candidate_coverage = dict(coverage)
    for unit_id in fidelity.get("covered_unit_ids") or []:
        if unit_id in candidate_coverage:
            candidate_coverage[unit_id] = True
    uncovered_after_candidate = [
        unit.id for unit in units
        if unit.must_preserve and not bool(candidate_coverage.get(unit.id))
    ]
    if is_natural_arrival(candidate) and uncovered_after_candidate:
        return retry(
            "premature_arrival",
            "candidate arrives before required authority units are covered",
            generation_rejection_class="PREMATURE_ARRIVAL",
            uncovered_required_count=len(uncovered_after_candidate),
            branch_memory=[{
                "kind": "premature_arrival",
                "candidate_sha256": sha256(candidate.encode("utf-8")).hexdigest(),
                "unresolved_required": uncovered_after_candidate,
            }],
        )
    coverage = candidate_coverage
    existing_ledger = _validated_move_coverage(
        moves,
        state.get("accepted_move_coverage"),
        set(coverage),
    )
    coverage_row = {
        "move_sha256": sha256(candidate.encode("utf-8")).hexdigest(),
        "covered_unit_ids": sorted({
            unit_id
            for unit_id in fidelity.get("covered_unit_ids") or []
            if unit_id in coverage
        }),
    }
    ledger = [*existing_ledger, coverage_row] if existing_ledger is not None else []
    next_boundary_id = generation_boundary_id(
        moves + [candidate], coverage,
        graph_version=str(state.get("graph_version") or ""),
        program_version=str(state.get("program_version") or ""),
    )
    return checkpoint({
        "status": "continue_generation", "phase": "generation",
        "accepted_moves": moves + [candidate], "move_index": len(moves) + 1,
        "retry_count": 0, "committed_pressure": pressure_state, "candidate_spans": spans,
        "pressure_votes": pressure_votes_state,
        "uncovered_required_count": sum(
            1 for unit in units
            if unit.must_preserve and not bool(coverage.get(unit.id))
        ),
        "entry_edge_result": entry, "full_edge_result": full, "semantic_result": fidelity,
        "atom_coverage": coverage,
        "accepted_move_coverage": ledger,
        "coverage_reconciliation_required": existing_ledger is None,
        "accepted_prefix_hash": sha256(" ".join(moves + [candidate]).encode("utf-8")).hexdigest(),
        "generation_boundary_id": next_boundary_id,
        "decision_boundary_id": boundary_id,
        "proposal_ref": proposal_ref,
    })


def _cold_node(state: dict[str, Any], services: RuntimeServices, project_root: Path) -> dict[str, Any]:
    original_text = " ".join(state.get("accepted_moves") or []).strip()
    text = original_text
    if not text:
        return {
            "phase": "cold_audit", "status": "machine_failure",
            "accepted_moves": [],
            "final_local_gates": {"hard_pass": False, "reason": "empty candidate"},
        }

    store=services.artifact_store
    source=_artifact_text(store,state["source_ref"]) if state.get("source_ref") else ""
    units=_load_units(state,store)
    refs: list[str] = []
    revision_refs: list[str] = []
    revision_failures: list[dict[str, Any]] = []
    final: ColdAuditResult | None = None

    def audit_once(candidate_text:str,pass_no:int)->ColdAuditResult:
        direction_block, _ = _owner_direction_block(state, "cold_audit")
        prompt=(
            _read_prompt(project_root,"cold_audit.md")
            +f"\n\nCOLD AUDIT PASS {pass_no}\n\nCANDIDATE:\n{candidate_text}"
            +direction_block
        )
        row=services.codex.call(
            ModelCall(prompt,COLD_SCHEMA,"cold_audit"),services.runner,store
        ).parsed
        defects=tuple(AuditDefect(d["code"],d["detail"],d["severity"]) for d in row["defects"])
        result=ColdAuditResult(
            defects,bool(row["semantic_sanity"]),bool(row["curious_reader_chain"]),
            bool(row["stopping_point_ok"]),bool(row["fidelity_ok"]),
        )
        refs.append(_put_json(store,row,"cold-audit",pass_no=pass_no,text_sha256=sha256(candidate_text.encode()).hexdigest()))
        _emit(services, "guard.result", {
            "node": "cold_audit",
            "gate": f"cold_audit_{pass_no}",
            "verdict": "PASS" if result.pass_ else "FAIL",
            "reason": "; ".join(defect.detail for defect in defects),
            "proposal_ref": str(state.get("proposal_ref") or ""),
        })
        return result

    def revise(candidate_text:str,audit:ColdAuditResult,pass_no:int)->str:
        defect_payload=[{"code":d.code,"detail":d.detail,"severity":d.severity} for d in audit.defects]
        direction_block, _ = _owner_direction_block(state, "cold_revision")
        prompt=(
            _read_prompt(project_root,"cold_revision.md")
            +"\n\nRevise the completed candidate only where these explicit defects require it. "
             "Return only the complete revised candidate, with no analysis."
            +"\n\nDEFECTS:\n"+json.dumps(defect_payload,ensure_ascii=False,indent=2)
            +"\n\nCANDIDATE:\n"+candidate_text
            +direction_block
        )
        model_result=services.claude.call(
            ModelCall(prompt,None,"cold_revision"),services.runner,store
        )
        revised=str(model_result.parsed if isinstance(model_result.parsed,str) else model_result.text).strip().strip("`").strip()
        if not revised or revised == candidate_text:
            revision_failures.append({"pass":pass_no,"reason":"revision-empty-or-unchanged"})
            return candidate_text

        fidelity_input={
            "task_mode":state.get("task_mode"),
            "source_provenance":state.get("source_provenance"),
            "source":source,
            "authority_units":[u.model_dump(mode="json") for u in units],
            "previous_candidate":candidate_text,
            "candidate":revised,
            "instruction":"Cold revision may fix only listed defects; preserve all authority and meaning obligations.",
        }
        fidelity_direction_block, _ = _owner_direction_block(state, "fidelity_guard")
        fidelity=services.codex.call(
            ModelCall(
                _read_prompt(project_root,"semantic_guard.md")+"\n\n"+_read_prompt(project_root,"relation_guard.md")
                +"\n\n"+json.dumps(fidelity_input,ensure_ascii=False,indent=2)
                +fidelity_direction_block,
                FIDELITY_SCHEMA,"cold_revision_fidelity",
            ),services.runner,store
        ).parsed
        fidelity_ref=_put_json(store,fidelity,"cold-revision-fidelity",pass_no=pass_no)
        _emit(services, "guard.result", {
            "node": "cold_audit",
            "gate": f"cold_revision_fidelity_{pass_no}",
            "verdict": str(fidelity.get("verdict") or ""),
            "reason": str(fidelity.get("reason") or ""),
            "proposal_ref": str(state.get("proposal_ref") or ""),
        })
        if fidelity["verdict"] != "PASS":
            revision_failures.append({"pass":pass_no,"reason":"fidelity-fail","fidelity_ref":fidelity_ref})
            return candidate_text
        revision_refs.append(store.put_text(
            revised,"md",{"kind":"cold-revision","pass_no":pass_no,"parent_sha256":sha256(candidate_text.encode()).hexdigest(),"fidelity_ref":fidelity_ref}
        ).sha256)
        return revised

    # Audit twice by default. A defect causes the smallest bounded revision before the next audit.
    # A third audit is used only when audit 2 still finds a legitimate defect.
    pass_no=1
    while pass_no <= 3:
        final=audit_once(text,pass_no)
        if final.pass_:
            if pass_no == 1:
                # A second cold read is the normal standard; do not paraphrase between no-defect passes.
                pass_no += 1
                continue
            break
        if pass_no >= 3:
            break
        text=revise(text,final,pass_no)
        pass_no += 1

    assert final is not None
    regression_ok=bool((state.get("final_local_gates") or {}).get("regressions_hard_pass"))
    hard=bool(regression_ok and final.pass_)
    accepted_moves=candidate_semantic_spans(text)
    candidate_text_ref=store.put_text(
        text,"md",{"kind":"cold-audited-candidate","text_sha256":sha256(text.encode()).hexdigest()}
    ).sha256
    revision_changed = text != original_text
    return {
        "phase":"cold_audit",
        "status":"local_gates_passed" if hard else "machine_failure",
        "accepted_moves":accepted_moves,
        "accepted_move_coverage": (
            [] if revision_changed else list(state.get("accepted_move_coverage") or [])
        ),
        "coverage_reconciliation_required": bool(
            revision_changed or state.get("coverage_reconciliation_required")
        ),
        "accepted_prefix_hash": sha256(text.encode("utf-8")).hexdigest(),
        "candidate_text_ref":candidate_text_ref,
        "candidate_spans":accepted_moves,
        "final_local_gates":{
            **dict(state.get("final_local_gates") or {}),
            "hard_pass":hard,
            "semantic_sanity":final.semantic_sanity,
            "curious_reader_chain":final.curious_reader_chain,
            "stopping_point_ok":final.stopping_point_ok,
            "fidelity_ok":final.fidelity_ok,
            "cold_audit_refs":refs,
            "cold_revision_refs":revision_refs,
            "cold_revision_failures":revision_failures,
        },
    }


def _freeze_node(state: dict[str, Any], services: RuntimeServices) -> dict[str, Any]:
    text_ref=str(state.get("candidate_text_ref") or "")
    artifact=services.artifact_store.find(text_ref) if text_ref else None
    text=(artifact.path.read_text(encoding="utf-8") if artifact is not None else " ".join(state.get("accepted_moves") or [])).strip()
    hard = bool((state.get("final_local_gates") or {}).get("hard_pass"))
    frozen_text_ref=text_ref or services.artifact_store.put_text(text, "md", {"kind": "frozen-editorial-winner"}).sha256
    record = CandidateRecord(
        id="candidate-" + sha256(text.encode()).hexdigest()[:12], text=text, editorial_score=1.0,
        hard_pass=hard, frozen=True, accepted_moves=tuple(state.get("accepted_moves") or []),
        text_artifact_ref=frozen_text_ref,
        role="CONSERVATIVE" if str(state.get("task_mode")) in {"P1", "P2", "P2S"} else "DEVELOPMENTAL",
        material_route="live-thought-flow",
    )
    ref = _put_json(services.artifact_store, record.__dict__, "candidate-record", frozen=True)
    return {"phase": "freeze", "candidate_ref": ref, "status": "candidate_frozen"}


def _prepare_detector_variant(
    state: dict[str, Any], services: RuntimeServices, project_root: Path,
    parent: CandidateRecord, attempt: int,
) -> str:
    source=_artifact_text(services.artifact_store,state["source_ref"]) if state.get("source_ref") else ""
    revision_direction_block, _ = _owner_direction_block(state, "cold_revision")
    prompt=_read_prompt(project_root,"cold_revision.md")+"""

Create exactly one bounded meaning-preserving realization variant of the frozen editorial winner.
Do not add/remove claims, evidence, uncertainty, actors, causality, source roles, or authorial stance.
Do not add a summary, bridge, or new idea. Prefer the smallest natural realization/boundary change.
Return only the variant text.

FROZEN EDITORIAL WINNER:
"""+parent.text+revision_direction_block
    result=services.claude.call(ModelCall(prompt,None,"detector_variant"),services.runner,services.artifact_store)
    text=str(result.parsed if isinstance(result.parsed,str) else result.text).strip().strip("`").strip()
    if not text or text==parent.text or len(candidate_semantic_spans(text)) != len(candidate_semantic_spans(parent.text)):
        return ""
    fidelity_direction_block, _ = _owner_direction_block(state, "detector_variant_fidelity")
    fidelity=services.codex.call(ModelCall(
        "Judge strict meaning equivalence between the frozen editorial winner and detector variant. "
        "The variant fails if any claim, certainty, actor, cause, attribution, evidence/source role, or authorial position changes.\n\n"
        +json.dumps({"source":source,"parent":parent.text,"variant":text},ensure_ascii=False,indent=2)
        +fidelity_direction_block,
        FIDELITY_SCHEMA,"detector_variant_fidelity"),services.runner,services.artifact_store).parsed
    _emit(services, "guard.result", {
        "node": "detector",
        "gate": "detector_variant_fidelity",
        "verdict": str(fidelity.get("verdict") or ""),
        "reason": str(fidelity.get("reason") or ""),
        "proposal_ref": "",
    })
    if fidelity["verdict"] != "PASS":
        return ""
    audit_direction_block, _ = _owner_direction_block(state, "detector_variant_audit")
    audit=services.codex.call(ModelCall(
        _read_prompt(project_root,"cold_audit.md")+"\n\nCANDIDATE VARIANT:\n"+text
        +audit_direction_block,
        COLD_SCHEMA,"detector_variant_audit"),services.runner,services.artifact_store).parsed
    audit_pass = not audit.get("defects") and all(bool(audit.get(key)) for key in (
        "semantic_sanity", "curious_reader_chain", "stopping_point_ok", "fidelity_ok",
    ))
    _emit(services, "guard.result", {
        "node": "detector",
        "gate": "detector_variant_audit",
        "verdict": "PASS" if audit_pass else "FAIL",
        "reason": "; ".join(str(row.get("detail") or "") for row in audit.get("defects") or []),
        "proposal_ref": "",
    })
    if not audit_pass:
        return ""
    variant=CandidateRecord(
        id=f"{parent.id}-variant-{attempt:02d}-{sha256(text.encode()).hexdigest()[:8]}",
        text=text,editorial_score=max(0.0,parent.editorial_score-0.01),hard_pass=True,
        lineage_id=parent.lineage_id,parent_id=parent.id,meaning_equivalent=True,frozen=True,
        accepted_moves=tuple(candidate_semantic_spans(text)),role=parent.role,material_route=parent.material_route,
        audit_refs=parent.audit_refs,
        text_artifact_ref=services.artifact_store.put_text(text,"md",{"kind":"detector-variant","parent_id":parent.id}).sha256,
    )
    return _put_json(services.artifact_store,variant.__dict__,"candidate-record",frozen=True,detector_variant=True)


def _detector_node(
    state: dict[str, Any], services: RuntimeServices, project_root: Path, config: RuntimeConfig,
) -> dict[str, Any]:
    def detector_event(
        stage: str,
        *,
        task_id: str = "",
        candidate_ref: str = "",
        version: str = "",
        result: str = "",
        reason: str = "",
    ) -> None:
        _emit(services, "detector.state", {
            "stage": stage,
            "task_id": task_id,
            "candidate_ref": candidate_ref,
            "version": version,
            "result": result,
            "reason": reason,
        })

    if not bool((state.get("final_local_gates") or {}).get("hard_pass")):
        detector_event("skipped", reason="local hard gates did not pass")
        return {"phase":"detector","status":"detector_skipped","pangram_result_ref":""}
    detector_event("access_check")
    pangram = services.ensure_pangram()
    if pangram is None:
        detector_event("access_check", result="credential_required", reason="PANGRAM_API_KEY is unavailable")
        return {"phase":"detector","status":"credential_required","interrupt_payload":{"kind":"CREDENTIAL","credential":"PANGRAM_API_KEY"}}

    def credential_retry(exc: Exception) -> dict[str, Any] | None:
        if not isinstance(exc, httpx.HTTPStatusError):
            return None
        response=getattr(exc,"response",None)
        request=getattr(exc,"request",None)
        status_code=int(getattr(response,"status_code",0) or 0)
        url=getattr(request,"url",None)
        host=str(getattr(url,"host","") or "").lower()
        path=str(getattr(url,"path","") or "")
        method=str(getattr(request,"method","") or "").upper()
        if "pangram" not in host:
            return None
        if status_code == 402:
            detector_event("account_stop", result="PANGRAM_CREDITS", reason="payment required")
            return {
                "phase":"detector","status":"bounded_detector_account_stop",
                "detector_account_action":"PANGRAM_CREDITS",
                "pangram_task_id":"","pangram_request_identity":"",
                "pangram_candidate_ref":"","pangram_submitted_at":0.0,
            }
        if status_code == 403 and method == "GET" and path.startswith("/task/"):
            # Authentication succeeded, but the current key does not own a checkpointed
            # task (for example after a credential refresh).  Clear only that pending task
            # and resubmit the same candidate under the current key on the next detector step.
            detector_event("retry", result="task_ownership_changed", reason="checkpointed task is not owned by current key")
            return {
                "phase":"detector","status":"detector_retry",
                "pangram_task_id":"","pangram_request_identity":"",
                "pangram_candidate_ref":"","pangram_submitted_at":0.0,
            }
        if status_code != 401:
            return None
        os.environ.pop("PANGRAM_API_KEY",None)
        services.pangram=None
        detector_event("retry", result="credential_refresh_required", reason="Pangram rejected the credential")
        return {
            "phase":"detector","status":"detector_retry",
            "credential_refresh_required":"PANGRAM_API_KEY",
            "pangram_task_id":"","pangram_request_identity":"",
            "pangram_candidate_ref":"","pangram_submitted_at":0.0,
        }

    recommended_ref=str(state.get("recommended_candidate_ref") or state.get("candidate_ref") or "")
    parent=CandidateRecord(**_artifact_json(services.artifact_store,recommended_ref))
    pending_ref=str(state.get("pending_detector_variant_ref") or "")
    measured_ref=pending_ref or recommended_ref
    measured=CandidateRecord(**_artifact_json(services.artifact_store,measured_ref))

    result = None
    result_ref = ""
    async_client = all(hasattr(pangram, name) for name in ("submit", "poll", "request_identity"))
    if async_client:
        identity=str(pangram.request_identity(measured.text_sha256))
        task_id=str(state.get("pangram_task_id") or "")
        pending_identity=str(state.get("pangram_request_identity") or "")
        pending_candidate_ref=str(state.get("pangram_candidate_ref") or "")
        submitted_at=float(state.get("pangram_submitted_at") or 0.0)
        if task_id and (pending_identity != identity or pending_candidate_ref != measured_ref):
            # A detector-variant change invalidates only the previous pending identity; never poll
            # a task for one candidate as though it measured another.
            task_id=""
            submitted_at=0.0
        if not task_id:
            ensure=getattr(pangram,"ensure_access",None)
            if callable(ensure):
                try:
                    ensure()
                except Exception as exc:
                    retry=credential_retry(exc)
                    if retry is not None:
                        return retry
                    raise
            try:
                task=pangram.submit(measured.text,measured.text_sha256)
            except Exception as exc:
                retry=credential_retry(exc)
                if retry is not None:
                    return retry
                raise
            detector_event(
                "submitted",
                task_id=task.task_id,
                candidate_ref=measured_ref,
                result="checkpointed",
            )
            return {
                "phase":"detector","status":"detector_poll_pending",
                "recommended_candidate_ref":recommended_ref,
                "pending_detector_variant_ref":pending_ref,
                "pangram_task_id":task.task_id,
                "pangram_request_identity":task.request_identity,
                "pangram_candidate_ref":measured_ref,
                "pangram_submitted_at":time.time(),
            }
        if submitted_at and time.time()-submitted_at > config.pangram_timeout_seconds:
            detector_event("timeout", task_id=task_id, candidate_ref=measured_ref, result="machine_failure")
            return {
                "phase":"detector","status":"machine_failure","failure_class":"PANGRAM_ONLY",
                "failure_origin_node":"detector","pangram_task_id":task_id,
                "pangram_request_identity":pending_identity,"pangram_candidate_ref":pending_candidate_ref,
                "pangram_submitted_at":submitted_at,
            }
        try:
            detector_event("poll", task_id=task_id, candidate_ref=measured_ref)
            result=pangram.poll(task_id)
        except Exception as exc:
            retry=credential_retry(exc)
            if retry is not None:
                return retry
            raise
        raw=result.raw
        result_ref=_put_json(services.artifact_store,raw,"pangram-result",candidate_id=measured.id,task_id=task_id)
        if result.stage not in {"STAGE_SUCCESS","STAGE_FAILED"}:
            detector_event(
                "poll",
                task_id=task_id,
                candidate_ref=measured_ref,
                version=result.version,
                result=result.stage,
            )
            return {
                "phase":"detector","status":"detector_poll_pending","pangram_result_ref":result_ref,
                "recommended_candidate_ref":recommended_ref,"pending_detector_variant_ref":pending_ref,
                "pangram_task_id":task_id,"pangram_request_identity":pending_identity,
                "pangram_candidate_ref":pending_candidate_ref,"pangram_submitted_at":submitted_at,
            }
        if result.stage == "STAGE_FAILED":
            detector_event(
                "result",
                task_id=task_id,
                candidate_ref=measured_ref,
                version=result.version,
                result="STAGE_FAILED",
            )
            return {
                "phase":"detector","status":"machine_failure","failure_class":"PANGRAM_ONLY",
                "failure_origin_node":"detector","pangram_result_ref":result_ref,
                "pangram_task_id":"","pangram_request_identity":"","pangram_candidate_ref":"","pangram_submitted_at":0.0,
            }
        if result.version != "4.0":
            detector_event(
                "version",
                task_id=task_id,
                candidate_ref=measured_ref,
                version=result.version,
                result="contract_stop",
                reason="expected Pangram 4.0",
            )
            return {
                "phase":"detector","status":"bounded_detector_contract_stop",
                "detector_required_version":"4.0",
                "detector_returned_version":result.version,
                "pangram_result_ref":result_ref,
                "pangram_task_id":"","pangram_request_identity":"","pangram_candidate_ref":"","pangram_submitted_at":0.0,
            }
        outcome_status="HUMAN" if result.is_human else "NON_HUMAN"
        detector_event(
            "result",
            task_id=task_id,
            candidate_ref=measured_ref,
            version=result.version,
            result=outcome_status,
        )
    else:
        try:
            outcome=detector_node(measured,pangram,parent=parent if measured_ref!=recommended_ref else None)
        except Exception as exc:
            retry=credential_retry(exc)
            if retry is not None:
                return retry
            raise
        result=outcome.result
        outcome_status=outcome.status
        raw=result.raw if result is not None else {"status":outcome.status}
        result_ref=_put_json(services.artifact_store,raw,"pangram-result",candidate_id=measured.id)
        detector_event(
            "result",
            candidate_ref=measured_ref,
            version=str(getattr(result, "version", "") or ""),
            result=outcome_status,
        )

    cleared_pending={
        "pangram_task_id":"","pangram_request_identity":"","pangram_candidate_ref":"","pangram_submitted_at":0.0,
    }
    if outcome_status=="HUMAN":
        return {
            "phase":"detector","status":"owner_review_ready","pangram_result_ref":result_ref,
            "recommended_candidate_ref":recommended_ref,
            "pangram_human_variant_ref":measured_ref if measured_ref!=recommended_ref else "",
            "pending_detector_variant_ref":"",
            "final_local_gates":{**dict(state.get("final_local_gates") or {}),"pangram_human":True},
            **cleared_pending,
        }

    attempt=int(state.get("detector_variant_attempt",0))
    if attempt >= min(5,max(0,config.writer_attempts+1)):
        detector_event("retry_limit", candidate_ref=measured_ref, result="NON_HUMAN")
        return {
            "phase":"detector","status":"detector_nonhuman","pangram_result_ref":result_ref,
            "recommended_candidate_ref":recommended_ref,"pending_detector_variant_ref":"",
            "final_local_gates":{**dict(state.get("final_local_gates") or {}),"pangram_human":False},
            **cleared_pending,
        }
    variant_ref=_prepare_detector_variant(state,services,project_root,parent,attempt+1)
    if not variant_ref:
        detector_event("variant", candidate_ref=measured_ref, result="unavailable")
        return {
            "phase":"detector","status":"detector_nonhuman","pangram_result_ref":result_ref,
            "recommended_candidate_ref":recommended_ref,"pending_detector_variant_ref":"",
            "final_local_gates":{**dict(state.get("final_local_gates") or {}),"pangram_human":False},
            **cleared_pending,
        }
    detector_event("retry", candidate_ref=variant_ref, result="variant_ready")
    return {
        "phase":"detector","status":"detector_retry","pangram_result_ref":result_ref,
        "recommended_candidate_ref":recommended_ref,"pending_detector_variant_ref":variant_ref,
        "detector_variant_attempt":attempt+1,
        "final_local_gates":{**dict(state.get("final_local_gates") or {}),"pangram_human":False},
        **cleared_pending,
    }


def _owner_learning_node(state: dict[str, Any], services: RuntimeServices) -> dict[str, Any]:
    response = dict(state.get("owner_response") or {})
    if not response:
        return {"status": state.get("status", "owner_review_deferred")}
    interrupt_kind = str(state.get("active_interrupt_kind") or "FINAL_REVIEW")
    return capture_owner_response(state, response, services.learning_store, interrupt_kind=interrupt_kind)


def _pause_journal(services: RuntimeServices) -> EventJournal:
    if services.journal is None:
        services.journal = EventJournal(services.artifact_store.root.parent / "events.jsonl")
        services.work_feed.journal = services.journal
    return services.journal


def _checkpointed_pause_update(
    *,
    name: str,
    state: dict[str, Any],
    services: RuntimeServices,
    pause_mode: str,
    resume_node: str,
    operation: str,
    completed_update: dict[str, Any] | None = None,
) -> dict[str, Any]:
    completed = dict(completed_update or {})
    merged = {**state, **completed}
    pre_pause_status = str(merged.get("status") or "")
    pause_fields = {
        "phase": name,
        "status": "supervisor_pause_requested",
        "active_interrupt_kind": "SUPERVISOR",
        "supervisor_resume_node": resume_node,
        "supervisor_pause_mode": pause_mode,
        "supervisor_pre_pause_status": pre_pause_status,
        "supervisor_interrupted_node": name,
        "supervisor_interrupted_operation": operation,
        "supervisor_validation_error": "",
    }
    snapshot = build_supervisor_snapshot(
        {**merged, **pause_fields},
        journal=_pause_journal(services),
        store=services.artifact_store,
    )
    snapshot_ref = persist_supervisor_snapshot(snapshot, services.artifact_store)
    sessions = SupervisorSessionStore(services.artifact_store.root.parent / "supervisor")
    thread_id = str(merged.get("thread_id") or merged.get("source_hash") or "thread")
    try:
        session_ref = sessions.create(thread_id, f"pause-{snapshot_ref[:16]}")
    except ValueError:
        safe_thread = sha256(thread_id.encode("utf-8")).hexdigest()
        session_ref = sessions.create(safe_thread, f"pause-{snapshot_ref[:16]}")
    pause_fields.update({
        "supervisor_snapshot_ref": snapshot_ref,
        "supervisor_session_ref": session_ref,
    })
    services.work_feed.emit("supervisor.paused", {
        "thread_id": str(merged.get("thread_id") or ""),
        "node": name,
        "operation": operation,
        "pause_mode": pause_mode,
        "resume_node": resume_node,
        "snapshot_ref": snapshot_ref,
    })
    services.pause_controller.acknowledge()
    return {**completed, **pause_fields}


def _emit_checkpointed_prose_events(
    name: str,
    state: dict[str, Any],
    update: dict[str, Any],
    services: RuntimeServices,
) -> None:
    if "accepted_moves" not in update:
        return
    before = [str(move) for move in state.get("accepted_moves") or []]
    after = [str(move) for move in update.get("accepted_moves") or []]
    if before == after:
        return
    if name == "generation" and len(after) > len(before) and after[:len(before)] == before:
        ledger = list(update.get("accepted_move_coverage") or [])
        for index in range(len(before), len(after)):
            row = ledger[index] if index < len(ledger) and isinstance(ledger[index], dict) else {}
            _emit(services, "move.accepted", {
                "node": name,
                "move_index": index + 1,
                "proposal_ref": str(update.get("proposal_ref") or ""),
                "text": after[index],
                "covered_unit_ids": list(row.get("covered_unit_ids") or []),
            })
    text = " ".join(after)
    _emit(services, "passage.current", {
        "node": name,
        "accepted_moves": after,
        "text": text,
        "text_sha256": sha256(text.encode("utf-8")).hexdigest(),
    })


def _normalize_machine_failure(
    *,
    name: str,
    state: dict[str, Any],
    services: RuntimeServices,
    update: dict[str, Any] | None = None,
    exc: BaseException | None = None,
) -> dict[str, Any]:
    update = dict(update or {})
    merged = {**state, **update}
    existing_ref = str(update.get("failure_record_ref") or "")
    declared_class = str(update.get("failure_class") or "")
    existing_evidence = False
    if existing_ref:
        found = services.artifact_store.find(existing_ref)
        if found is not None:
            try:
                existing_evidence = (
                    json.loads(found.path.read_text(encoding="utf-8")).get("format")
                    == "authorial-flow-repair-evidence-v1"
                )
            except (OSError, ValueError, AttributeError):
                existing_evidence = False
    if existing_evidence:
        return {
            **update,
            "phase": str(update.get("phase") or name),
            "status": "machine_failure",
            "failure_class": declared_class or str(state.get("failure_class") or "DETERMINISTIC_RUNTIME"),
            "failure_origin_node": str(update.get("failure_origin_node") or name),
            "last_error_ref": existing_ref,
            "failure_evidence_ref": existing_ref,
        }

    attempts: list[str] = []
    for attempt in getattr(exc, "attempts", ()) or ():
        for ref in (getattr(attempt, "stdout_ref", ""), getattr(attempt, "stderr_ref", "")):
            if ref:
                attempts.append(ref)
    failure_code = str(
        update.get("failure_code")
        or declared_class
        or (str(exc) if exc is not None else "returned machine failure")
    )
    record = FailureRecord(
        originating_node=name,
        failure_code=failure_code,
        exception_type=type(exc).__name__ if exc is not None else "ReturnedMachineFailure",
        exception_message=(str(exc) or type(exc).__name__) if exc is not None else failure_code,
        provider_attempt_refs=tuple(attempts),
        checkpoint_id=str(merged.get("checkpoint_id") or ""),
        source_hash=str(merged.get("source_hash") or ""),
        program_hash=str(merged.get("program_version") or ""),
        local_gate_state=dict(merged.get("final_local_gates") or {}),
        authorial_information_missing=bool(
            update.get("authorial_information_missing")
            or getattr(exc, "authorial_information_missing", False)
        ),
    )
    failure_class = declared_class or classify_failure(record).value
    legacy_ref = _put_json(
        services.artifact_store,
        record.model_dump(mode="json"),
        "failure-record",
        node=name,
    )
    from .repair.evidence import build_failure_evidence
    secret_values = [
        os.environ.get("PANGRAM_API_KEY", ""),
        os.environ.get("BRAVE_SEARCH_API_KEY", ""),
        os.environ.get("OPENAI_API_KEY", ""),
        os.environ.get("ANTHROPIC_API_KEY", ""),
    ]
    event_context = services.journal.latest() if services.journal is not None else {}
    evidence_exc = exc or RuntimeError(failure_code)
    bundle = build_failure_evidence(
        record=record,
        failure_class=failure_class,
        state=merged,
        exc=evidence_exc,
        store=services.artifact_store,
        program_version=str(merged.get("program_version") or ""),
        event_context=event_context or {},
        secret_values=secret_values,
        failure_record_ref=legacy_ref,
    )
    ref = _put_json(
        services.artifact_store,
        bundle.model_dump(mode="json"),
        "repair-evidence",
        node=name,
        failure_record_ref=legacy_ref,
    )
    if services.journal is not None:
        services.journal.append("machine-failure", {
            "node": name,
            "failure_class": failure_class,
            "failure_record_ref": ref,
            "legacy_failure_record_ref": legacy_ref,
        })
    return {
        **update,
        "phase": str(update.get("phase") or name),
        "status": "machine_failure",
        "failure_class": failure_class,
        "failure_origin_node": name,
        "failure_record_ref": ref,
        "failure_evidence_ref": ref,
        "last_error_ref": ref,
        "authorial_information_missing": record.authorial_information_missing,
    }


def _guarded_node(name: str, fn, services: RuntimeServices, natural_next=None):
    def wrapped(state: dict[str, Any]) -> dict[str, Any]:
        services.work_feed.emit("flow.phase", {
            "thread_id": str(state.get("thread_id") or ""),
            "node": name,
            "phase": str(state.get("phase") or name),
            "job": str(state.get("section_job") or ""),
        })
        observation = services.pause_controller.observe()
        if observation.requested:
            operation = observation.operation.operation if observation.operation else ""
            return _checkpointed_pause_update(
                name=name,
                state=state,
                services=services,
                pause_mode="CANCELLED",
                resume_node=name,
                operation=operation,
            )
        try:
            update = dict(fn(state) or {})
        except OwnerPauseRequested as exc:
            return _checkpointed_pause_update(
                name=name,
                state=state,
                services=services,
                pause_mode="CANCELLED",
                resume_node=name,
                operation=exc.operation.operation,
            )
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            if name == "generation":
                trace = build_decision_trace(state)
                _emit(services, "decision.trace", trace)
            return _normalize_machine_failure(
                name=name,
                state=state,
                services=services,
                exc=exc,
            )
        if name == "generation":
            trace = build_decision_trace({**state, **update})
            update["decision_trace"] = trace
            _emit(services, "decision.trace", trace)
        if str(update.get("status") or "") == "machine_failure":
            update = _normalize_machine_failure(
                name=name,
                state=state,
                services=services,
                update=update,
            )
        _emit_checkpointed_prose_events(name, state, update, services)
        if services.pause_controller.requested():
            merged = {**state, **update}
            observation = services.pause_controller.observe()
            operation = observation.operation.operation if observation.operation else ""
            return _checkpointed_pause_update(
                name=name,
                state=state,
                services=services,
                pause_mode="ATOMIC_COMPLETE",
                resume_node=natural_next(merged) if natural_next is not None else name,
                operation=operation,
                completed_update=update,
            )
        return update
    return wrapped


def _production_repair_cycle(
    config: RuntimeConfig, project_root: Path, services: RuntimeServices
) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Create the bounded autonomous code-repair cycle for graph machine failures."""
    from .repair.executor import RepairExecutor
    from .repair.planner import RepairPlanner
    from .repair.protection import ProtectedSnapshot
    from .repair.reviewer import RepairReviewer
    from .repair.schemas import RepairOutcome
    from .repair.verify import (
        RepairVerifier, repair_plan_signature, validate_repair_plan_commands,
        verify_with_one_fix,
    )
    from .repair.worktree import WorktreeManager

    project_root = Path(project_root).resolve()

    def progress(phase: str, state: dict[str, Any], **payload: Any) -> None:
        event={
            "phase": phase,
            "repair_attempt":int(state.get("repair_attempt",0))+1,
            "failure_class":str(state.get("failure_class") or ""),
            "repair_commit": str(payload.get("repair_commit") or payload.get("candidate_commit") or ""),
            "pass": bool(payload.get("pass_")) if "pass_" in payload else False,
            "reason": str(payload.get("reason") or ""),
            "outcome": str(payload.get("outcome") or ""),
            "plan_signature": str(payload.get("plan_signature") or ""),
        }
        _emit(services, "repair.state", event)

    def cycle(state: dict[str, Any]) -> dict[str, Any]:
        attempt = int(state.get("repair_attempt", 0))
        evidence_ref = str(state.get("failure_record_ref") or state.get("last_error_ref") or "")
        program_version = str(state.get("program_version") or "")
        history = [
            dict(row) for row in list(state.get("repair_history") or [])[-10:]
            if isinstance(row, dict)
        ]

        def finish(
            outcome: RepairOutcome,
            reason: str,
            *,
            signature: str = "",
            pass_: bool = False,
            exhausted: bool = False,
            error_ref: str = "",
            **payload: Any,
        ) -> dict[str, Any]:
            entry = {
                "attempt": attempt + 1,
                "signature": signature,
                "outcome": outcome.value,
                "reason": str(reason or "")[:2000],
                "evidence_ref": evidence_ref,
                "program_version": program_version,
            }
            progress(
                "outcome", state, outcome=outcome.value, reason=reason,
                plan_signature=signature, pass_=pass_,
                repair_commit=payload.get("repair_commit", ""),
            )
            return {
                "pass": pass_,
                "outcome": outcome.value,
                "reason": reason,
                "plan_signature": signature,
                "history_entry": entry,
                "exhausted": exhausted,
                "error_ref": error_ref,
                **payload,
            }

        if attempt >= config.repair_rounds:
            return finish(
                RepairOutcome.NON_APPLICABLE_STOP,
                "REPAIR_BUDGET_EXHAUSTED",
                exhausted=True,
                error_ref=evidence_ref,
            )

        if evidence_ref:
            try:
                failure_context = _artifact_text(services.artifact_store, evidence_ref)
            except Exception:
                failure_context = ""
        else:
            failure_context = ""
        if not failure_context:
            failure_context = json.dumps({
                "failure_class": state.get("failure_class", ""),
                "failure_origin_node": state.get("failure_origin_node", ""),
                "failure_record_ref": evidence_ref,
                "task_mode": state.get("task_mode", ""),
                "source_provenance": state.get("source_provenance", ""),
                "thread_id": state.get("thread_id", ""),
                "source_hash": state.get("source_hash", ""),
            }, ensure_ascii=False, sort_keys=True, indent=2)
        if history:
            failure_context += "\n\nREPAIR ATTEMPT HISTORY (a new plan must differ causally):\n" + json.dumps(
                history, ensure_ascii=False, sort_keys=True, indent=2,
            )

        progress("diagnose",state,evidence_ref=evidence_ref)
        planner = RepairPlanner(codex=services.codex, runner=services.runner, store=services.artifact_store)
        plan = planner.plan(failure_context)
        plan_ref = _put_json(services.artifact_store, plan.model_dump(mode="json"), "repair-plan", repair_attempt=attempt+1)
        signature = repair_plan_signature(
            plan,
            evidence_ref=evidence_ref,
            program_version=program_version,
        )
        if any(str(row.get("signature") or "") == signature for row in history):
            return finish(
                RepairOutcome.NON_APPLICABLE_STOP,
                "DUPLICATE_PLAN_UNCHANGED_CONTEXT",
                signature=signature,
                exhausted=True,
                error_ref=plan_ref,
                plan_ref=plan_ref,
            )
        if not plan.repairable:
            return finish(
                RepairOutcome.NON_APPLICABLE_STOP,
                "PLANNER_MARKED_NON_REPAIRABLE",
                signature=signature,
                exhausted=True,
                error_ref=plan_ref,
                plan_ref=plan_ref,
            )
        if plan.needs_owner_judgment:
            if bool(state.get("authorial_information_missing")):
                return finish(
                    RepairOutcome.STAGED_FOR_OWNER,
                    "AUTHORIAL_INFORMATION_REQUIRED",
                    signature=signature,
                    error_ref=plan_ref,
                    owner_judgment_required=True,
                    owner_question=plan.owner_question or "Which meaning is actually yours?",
                )
            rejected_ref = _put_json(
                services.artifact_store, plan.model_dump(mode="json"), "rejected-repair-plan",
                reason="machine planner requested owner input without authorial-information flag",
            )
            return finish(
                RepairOutcome.REJECTED_WITH_REASON,
                "UNJUSTIFIED_OWNER_ESCALATION",
                signature=signature,
                error_ref=rejected_ref,
                plan_ref=plan_ref,
            )
        command_error = validate_repair_plan_commands(plan)
        if command_error:
            return finish(
                RepairOutcome.REJECTED_WITH_REASON,
                command_error,
                signature=signature,
                error_ref=plan_ref,
                plan_ref=plan_ref,
            )

        progress("plan-review",state,plan_ref=plan_ref)
        reviewer = RepairReviewer(
            claude=services.claude, codex=services.codex, runner=services.runner,
            store=services.artifact_store,
        )
        reviewed = reviewer.review_plan(plan)
        review_plan_ref = _put_json(
            services.artifact_store, reviewed.decision.model_dump(mode="json"),
            "repair-plan-review", provider=reviewed.provider,
        )
        if reviewed.decision.verdict != "APPROVE":
            return finish(
                RepairOutcome.REJECTED_WITH_REASON,
                "PLAN_REVIEW_REJECTED",
                signature=signature,
                error_ref=review_plan_ref,
                plan_ref=plan_ref,
                review_ref=review_plan_ref,
            )

        worktrees = WorktreeManager(project_root, config.state_dir / "repair-worktrees")
        repair_id = f"repair-{attempt + 1:03d}-{sha256(failure_context.encode()).hexdigest()[:8]}"
        ref = worktrees.create(repair_id)
        try:
            snapshot = ProtectedSnapshot.capture(ref.path, ["project/", "policy/", ".state/learning/"])
            executor = RepairExecutor(
                [m.strip() or None for m in os.environ.get(
                    "AUTHORIAL_CODEX_MODELS", "gpt-5.6-sol,"
                ).split(",")],
                timeout_seconds=config.model_timeout_seconds,
            )
            implementation = executor.apply(
                ref, plan, services.runner, services.artifact_store,
                evidence_bundle_text=failure_context,
            )
            if not implementation.success:
                return finish(
                    RepairOutcome.REJECTED_WITH_REASON,
                    "IMPLEMENTATION_REJECTED",
                    signature=signature,
                    error_ref=(
                        implementation.stderr_ref
                        or implementation.stdout_ref
                        or implementation.transcript_ref
                        or plan_ref
                    ),
                    plan_ref=plan_ref,
                    review_ref=review_plan_ref,
                )
            progress("codex-red",state,red_ref=implementation.red_ref)
            progress("patch",state,green_ref=implementation.green_ref,candidate_commit=implementation.commit_sha)

            source_text = _artifact_text(services.artifact_store, state["source_ref"]) if state.get("source_ref") else ""
            acceptance_commands=[]
            for raw in (state.get("repair_acceptance_commands") or []):
                if isinstance(raw,(list,tuple)) and raw and all(isinstance(token,str) and token for token in raw):
                    acceptance_commands.append(list(raw))
            verifier = RepairVerifier(
                reviewer=reviewer, source_texts=[source_text], protected_snapshot=snapshot,
                additional_commands=acceptance_commands,
            )
            final_commit = implementation.commit_sha
            transcript_refs = [ref for ref in [implementation.transcript_ref or implementation.stdout_ref or implementation.stderr_ref] if ref]

            def one_fix(worktree, failed_verification):
                nonlocal final_commit
                if config.implementation_fix_attempts < 1:
                    return ""
                progress("correction-1",state,failed_review=failed_verification.review_reason)
                corrected = executor.correct(
                    worktree, plan, failed_verification, services.runner, services.artifact_store,
                    previous_transcript_refs=transcript_refs,
                )
                if not corrected.success or not corrected.commit_sha:
                    return ""
                final_commit = corrected.commit_sha
                if corrected.transcript_ref:
                    transcript_refs.append(corrected.transcript_ref)
                return corrected.commit_sha

            progress("verify-targeted",state,declared_tests=list(plan.tests))
            verification = (
                verify_with_one_fix(verifier, ref, plan, one_fix)
                if config.implementation_fix_attempts >= 1
                else verifier.verify(ref, plan)
            )
            progress("verify-full",state,pass_=verification.pass_,fix_attempts=verification.fix_attempts)
            test_ref = _put_json(services.artifact_store, {
                "pass": verification.pass_,
                "fix_attempts": verification.fix_attempts,
                "review_provider": verification.review_provider,
                "review_reason": verification.review_reason,
                "commands": [
                    {"argv": list(c.argv), "returncode": c.returncode, "stdout": c.stdout[-6000:], "stderr": c.stderr[-6000:]}
                    for c in verification.commands
                ],
                "red_ref": implementation.red_ref,
                "green_ref": implementation.green_ref,
                "transcript_refs": transcript_refs,
            }, "repair-verification", repair_attempt=attempt+1)
            if not verification.pass_:
                return finish(
                    RepairOutcome.REJECTED_WITH_REASON,
                    "VERIFICATION_REJECTED",
                    signature=signature,
                    error_ref=test_ref,
                    plan_ref=plan_ref,
                    review_ref=review_plan_ref,
                    test_ref=test_ref,
                )

            progress("promote",state,repair_commit=final_commit,test_ref=test_ref)
            promoted = worktrees.promote(ref, final_commit)
            return finish(
                RepairOutcome.APPLIED_VERIFIED,
                "PROMOTED_AFTER_FULL_VERIFICATION",
                signature=signature,
                pass_=True,
                program_version=promoted,
                restart_required=True,
                repair_commit=final_commit,
                plan_ref=plan_ref,
                test_ref=test_ref,
                review_ref=review_plan_ref,
                failure_evidence_ref=evidence_ref,
            )
        finally:
            worktrees.discard(ref)

    return cycle

def build_runtime_dependencies(
    config: RuntimeConfig, *, project_root: Path, services: RuntimeServices | None = None,
) -> GraphDependencies:
    services = services or RuntimeServices.from_config(config)
    project_root = Path(project_root).resolve()
    return GraphDependencies(
        regressions=_guarded_node(
            "regressions", lambda state: _run_regressions(state, services), services,
            natural_next=route_after_regressions,
        ),
        representation=_guarded_node(
            "representation", lambda state: _representation_node(state, services, project_root), services,
            natural_next=route_after_representation,
        ),
        generation=_guarded_node(
            "generation", lambda state: _generation_node(state, services, project_root, config), services,
            natural_next=route_generation,
        ),
        cold_audit=_guarded_node(
            "cold_audit", lambda state: _cold_node(state, services, project_root), services,
            natural_next=route_after_cold_audit,
        ),
        freeze=_guarded_node(
            "freeze", lambda state: _freeze_node(state, services), services,
            natural_next=route_after_freeze,
        ),
        detector=_guarded_node(
            "detector", lambda state: _detector_node(state, services, project_root, config), services,
            natural_next=route_after_detector,
        ),
        owner_learning=_guarded_node(
            "owner_learning", lambda state: _owner_learning_node(state, services), services,
            natural_next=route_after_owner_learning,
        ),
        repair=_guarded_node(
            "repair",
            lambda state: repair_node(
                state, services.repair_cycle or _production_repair_cycle(config, project_root, services)
            ),
            services,
            natural_next=route_after_repair,
        ),
        supervisor=lambda state: supervisor_pause_node(
            state,
            artifact_store=services.artifact_store,
            learning_store=services.learning_store,
            journal=services.journal,
            work_feed=services.work_feed,
            reconcile_coverage=lambda legacy_state: _reconcile_move_coverage(
                legacy_state,
                services,
                project_root,
            ),
        ),
    )
