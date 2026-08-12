from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
import json
import time
from typing import Any

from .events import EventJournal


EVENT_FIELDS: dict[str, frozenset[str]] = {
    "flow.phase": frozenset({"thread_id", "node", "phase", "job"}),
    "model.start": frozenset({"node", "provider", "model", "role", "pid"}),
    "model.heartbeat": frozenset({
        "node", "provider", "model", "role", "pid", "elapsed_seconds",
    }),
    "proposal.complete": frozenset({
        "node", "proposal_ref", "proposal_sha256", "text",
    }),
    "guard.result": frozenset({
        "node", "gate", "verdict", "reason", "proposal_ref",
    }),
    "generation.retry": frozenset({
        "node", "stage", "reason", "retry_count", "proposal_ref",
    }),
    "decision.trace": frozenset({
        "boundary_id", "decision_boundary_id", "accepted_move_count",
        "uncovered_required_count", "pressure_votes", "committed_pressure",
        "edge", "candidate_sha256", "rejection_class", "budgets",
    }),
    "move.accepted": frozenset({
        "node", "move_index", "proposal_ref", "text", "covered_unit_ids",
    }),
    "passage.current": frozenset({
        "node", "accepted_moves", "text", "text_sha256",
    }),
    "detector.state": frozenset({
        "stage", "task_id", "candidate_ref", "version", "result", "reason",
    }),
    "repair.state": frozenset({
        "phase", "repair_attempt", "failure_class", "repair_commit", "pass", "reason",
        "outcome", "plan_signature",
    }),
    "supervisor.paused": frozenset({
        "thread_id", "node", "operation", "pause_mode", "resume_node", "snapshot_ref",
    }),
    "supervisor.action": frozenset({
        "thread_id", "action_kind", "scope", "restart_depth", "resume_node", "reason",
    }),
}


def redact_secret_values(value: Any, secrets: tuple[str, ...]) -> Any:
    if isinstance(value, str):
        for secret in secrets:
            value = value.replace(secret, "[REDACTED]")
        return value
    if isinstance(value, dict):
        return {key: redact_secret_values(item, secrets) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_secret_values(item, secrets) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_secret_values(item, secrets) for item in value)
    return value


def render_work_event(event: Mapping[str, Any]) -> str:
    kind = str(event.get("kind") or "")
    if kind == "proposal.complete":
        return f"proposal complete | {event.get('node', '')}\n{event.get('text', '')}"
    if kind == "guard.result":
        return (
            f"guard {event.get('gate', '')} | {event.get('verdict', '')} | "
            f"{event.get('reason', '')}"
        )
    if kind == "generation.retry":
        return (
            f"generation retry {event.get('retry_count', '')} | "
            f"{event.get('stage', '')} | {event.get('reason', '')}"
        )
    if kind == "decision.trace":
        pressure = event.get("committed_pressure") or {}
        edge = event.get("edge") or {}
        return (
            f"decision {event.get('rejection_class', '') or edge.get('verdict', '')} | "
            f"pressure={pressure.get('state', '')} | "
            f"uncovered_required={event.get('uncovered_required_count', 0)} | "
            f"boundary={str(event.get('decision_boundary_id') or '')[:12]}"
        )
    if kind == "move.accepted":
        return f"move accepted {event.get('move_index', '')}\n{event.get('text', '')}"
    if kind == "passage.current":
        return f"current passage\n{event.get('text', '')}"
    if kind == "model.start":
        return (
            f"model start | {event.get('provider', '')}/{event.get('model', '')} | "
            f"{event.get('role', '')} | pid={event.get('pid', '')}"
        )
    if kind == "model.heartbeat":
        elapsed = int(float(event.get("elapsed_seconds") or 0))
        return (
            f"model call alive | {event.get('provider', '')}/{event.get('model', '')} | "
            f"{event.get('role', '')} | pid={event.get('pid', '')} | "
            f"elapsed={elapsed // 60:02d}:{elapsed % 60:02d}"
        )
    if kind == "flow.phase":
        return f"flow {event.get('phase', '')} | {event.get('node', '')}"
    if kind == "detector.state":
        return (
            f"detector {event.get('stage', '')} | {event.get('result', '')} | "
            f"{event.get('reason', '')}"
        )
    if kind == "repair.state":
        return (
            f"repair {event.get('phase', '')} | {event.get('outcome', '') or event.get('failure_class', '')} | "
            f"{event.get('reason', '')}"
        )
    if kind == "supervisor.paused":
        return (
            f"supervisor paused | {event.get('pause_mode', '')} | "
            f"resume={event.get('resume_node', '')}"
        )
    if kind == "supervisor.action":
        return (
            f"supervisor action | {event.get('action_kind', '')} | "
            f"scope={event.get('scope', '')} | {event.get('reason', '')}"
        )
    return json.dumps(dict(event), ensure_ascii=False, sort_keys=True)


class WorkFeed:
    def __init__(
        self,
        *,
        journal: EventJournal | None,
        renderer: Callable[[str], None],
        secret_values: Callable[[], Iterable[str]] | None = None,
        clock: Callable[[], float] = time.monotonic,
        silent_seconds: float = 10,
    ) -> None:
        if silent_seconds < 0:
            raise ValueError("silent_seconds must be >= 0")
        self.journal = journal
        self.renderer = renderer
        self.secret_values = secret_values or (lambda: ())
        self.clock = clock
        self.silent_seconds = silent_seconds
        self.last_substantive_at = clock()

    def _secrets(self) -> tuple[str, ...]:
        values = {str(value) for value in self.secret_values() if str(value)}
        return tuple(sorted(values, key=len, reverse=True))

    def sanitize(self, value: Any) -> Any:
        return redact_secret_values(value, self._secrets())

    def emit(self, kind: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        fields = EVENT_FIELDS.get(kind)
        if fields is None:
            raise ValueError(f"unknown work event: {kind}")
        safe = {
            key: self.sanitize(payload[key])
            for key in fields
            if key in payload
        }
        persisted = {"schema_version": 1, **safe}
        sequence = self.journal.append(kind, persisted) if self.journal is not None else 0
        event = {"sequence": sequence, "kind": kind, **persisted}
        self.renderer(render_work_event(event))
        if kind != "model.heartbeat":
            self.last_substantive_at = self.clock()
        return event

    def heartbeat(self, payload: Mapping[str, Any]) -> dict[str, Any] | None:
        if self.clock() - self.last_substantive_at < self.silent_seconds:
            return None
        return self.emit("model.heartbeat", payload)
