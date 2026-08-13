from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from typing import Any, Mapping, Sequence
from dataclasses import dataclass

from .config import RuntimeConfig
from .decision_trace import build_decision_trace
from .failures import FailureClass
from .repair.schemas import RepairOutcome
from .version import GRAPH_VERSION


DIAGNOSTIC_FORMAT = "authorial-flow-diagnostic-v1"
DIAGNOSTICS_BRANCH = "diagnostics/authorial-flow-graph-v1"
DIAGNOSTICS_REPOSITORY = "u-dont-existDOTcom/pangram-humanization-lab"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MODEL_RE = re.compile(r"^(?:claude|gpt)[A-Za-z0-9._-]{1,63}$")
_SAFE_BRANCH_RE = re.compile(
    r"^(?:install|local)/authorial-flow-graph-v1-[A-Za-z0-9._-]{1,48}$"
)
_PHASES = {
    "installer-preflight",
    "installer-live-smoke",
    "runtime-run",
    "runtime-resume",
    "runtime-answer",
    "manual-status",
    "cli-interrupted",
}
_OUTCOMES = {
    "pass",
    "failed",
    "credential_required",
    "account_action_required",
    "bounded_machine_stop",
    "accepted",
    "supervisor_paused",
    "repair_promoted_restart_required",
    "interrupted",
    "snapshot",
    "machine_failure",
    "ok",
    "owner_input_required",
}
_ORIGIN_NODES = {
    "provider-smoke",
    "regressions",
    "representation",
    "semantic_sanity",
    "research",
    "generation",
    "cold_audit",
    "freeze",
    "detector",
    "owner_learning",
    "repair",
}
_PROVIDERS = {"claude", "codex", "pangram", "research", "heartbeat"}
_PROVIDER_STATUSES = {
    "pass",
    "fail",
    "skipped",
    "credential_required",
    "account_action_required",
}
_FAILURE_KINDS = {
    "",
    "AUTHENTICATION",
    "UNSUPPORTED_MODEL",
    "INVALID_SCHEMA",
    "UNSUPPORTED_SCHEMA",
    "STRUCTURED_OUTPUT_CONTRACT",
    "TRANSIENT",
    "TIMEOUT",
    "UNKNOWN",
}
_EXCLUDED_CATEGORIES = (
    "source_or_article_text",
    "accepted_candidate_or_rejected_prose",
    "prompts_or_transcripts",
    "stdout_or_stderr_bodies",
    "exception_messages",
    "credentials_or_environment_values",
    "full_local_paths",
    "evidence_zip_bytes",
)


@dataclass(frozen=True)
class DiagnosticsRemote:
    name: str
    url: str


@dataclass(frozen=True)
class PublicationResult:
    status: str
    run_id: str
    branch: str
    queued_count: int
    commit_sha: str = ""
    failure_kind: str = ""
    attempts: int = 0


def format_publication_status(result: PublicationResult) -> str:
    return (
        f"diagnostics_status={result.status} branch={result.branch} "
        f"run_id={result.run_id} commit={result.commit_sha} queued={result.queued_count} "
        f"failure={result.failure_kind} attempts={result.attempts}"
    )


def _sha_text(value: Any) -> str:
    return sha256(str(value or "").encode("utf-8")).hexdigest()


def _sha_token(value: Any) -> str:
    token = str(value or "").strip().lower()
    return token if _SHA256_RE.fullmatch(token) else ""


def _file_sha(path: Path) -> str:
    digest = sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return ""
    return digest.hexdigest()


def _count(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _enum(
    value: Any,
    allowed: set[str],
    field: str,
    unclassified: dict[str, str],
    *,
    upper: bool = False,
) -> str:
    token = str(value or "").strip()
    if not token:
        return ""
    candidate = token.upper() if upper else token.lower()
    if candidate in allowed:
        return candidate
    unclassified[field] = _sha_text(token)
    return "UNCLASSIFIED"


def _program_version(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
            timeout=5,
        )
        token = result.stdout.strip().lower()
        if re.fullmatch(r"[0-9a-f]{40,64}", token):
            return token
    except (OSError, subprocess.SubprocessError):
        pass
    return GRAPH_VERSION


def _source_branch(root: Path, unclassified: dict[str, str]) -> str:
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
            timeout=5,
        )
        branch = result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""
    if not branch:
        return ""
    if _SAFE_BRANCH_RE.fullmatch(branch):
        return branch
    unclassified["source_branch"] = _sha_text(branch)
    return "UNCLASSIFIED"


def _thread_summary(config: RuntimeConfig) -> dict[str, str]:
    path = config.state_dir / "current-thread.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        payload = {}
    if not isinstance(payload, Mapping):
        payload = {}
    return {
        "thread_id": _sha_token(payload.get("thread_id")),
        "source_sha256": _sha_token(payload.get("source_sha256")),
    }


def _event_count(config: RuntimeConfig) -> int:
    try:
        return sum(1 for row in config.event_path.read_text(encoding="utf-8").splitlines() if row.strip())
    except OSError:
        return 0


def _command_kind(command: Sequence[str] | None) -> str:
    argv = [str(item) for item in (command or ())]
    joined = " ".join(Path(item).name for item in argv[:4]).lower()
    if "live_smoke.py" in joined:
        return "live_smoke"
    if "pytest" in joined:
        return "pytest"
    return "other" if argv else ""


def _provider_summary(
    report_path: Path | None,
    unclassified: dict[str, str],
) -> dict[str, dict[str, Any]]:
    if report_path is None:
        return {}
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(report, Mapping):
        return {}
    output: dict[str, dict[str, Any]] = {}
    raw_results = report.get("results")
    raw_results = raw_results if isinstance(raw_results, Mapping) else {}
    for raw_name, raw in raw_results.items():
        name = str(raw_name or "").lower()
        if name not in _PROVIDERS or not isinstance(raw, Mapping):
            continue
        provider = str(raw.get("provider") or name).lower()
        if provider not in _PROVIDERS:
            provider = ""
        raw_model = str(raw.get("resolved_model") or raw.get("model") or "")
        model = raw_model if _MODEL_RE.fullmatch(raw_model) else ""
        if raw_model and not model:
            unclassified[f"providers.{name}.model"] = _sha_text(raw_model)
        status = str(raw.get("status") or "").lower()
        if status not in _PROVIDER_STATUSES:
            if status:
                unclassified[f"providers.{name}.status"] = _sha_text(status)
            status = "UNCLASSIFIED" if status else ""
        failure_kind = str(raw.get("failure_kind") or "").upper()
        if failure_kind not in _FAILURE_KINDS:
            if failure_kind:
                unclassified[f"providers.{name}.failure_kind"] = _sha_text(failure_kind)
            failure_kind = "UNCLASSIFIED" if failure_kind else ""
        output[name] = {
            "provider": provider,
            "model": model,
            "status": status,
            "failure_kind": failure_kind,
            "capability_signature": _sha_token(raw.get("capability_signature")),
            "attempt_count": _count(raw.get("attempt_count")),
        }
    credential = str(report.get("credential_required") or "")
    if credential and "pangram" not in output:
        output["pangram"] = {
            "provider": "pangram",
            "model": "",
            "status": "credential_required",
            "failure_kind": "AUTHENTICATION",
            "capability_signature": "",
            "attempt_count": 1,
        }
    account_action = str(report.get("account_action_required") or "")
    if account_action and "pangram" not in output:
        output["pangram"] = {
            "provider": "pangram",
            "model": "",
            "status": "account_action_required",
            "failure_kind": "",
            "capability_signature": "",
            "attempt_count": 1,
        }
    return output


def build_diagnostic_record(
    config: RuntimeConfig,
    *,
    phase: str,
    outcome: str,
    result: Mapping[str, Any] | None = None,
    report_path: Path | None = None,
    command: Sequence[str] | None = None,
    returncode: int | None = None,
    now: float | None = None,
) -> dict[str, Any]:
    state = dict(result or {})
    unclassified: dict[str, str] = {}
    safe_phase = _enum(phase, _PHASES, "phase", unclassified)
    safe_outcome = _enum(outcome, _OUTCOMES, "outcome", unclassified)
    failure_class = _enum(
        state.get("failure_class"),
        {item.value for item in FailureClass},
        "failure_class",
        unclassified,
        upper=True,
    )
    origin_node = _enum(
        state.get("failure_origin_node"),
        _ORIGIN_NODES,
        "failure_origin_node",
        unclassified,
    )
    repair_outcome = _enum(
        state.get("repair_outcome"),
        {item.value for item in RepairOutcome},
        "repair_outcome",
        unclassified,
        upper=True,
    )
    timestamp = float(time.time() if now is None else now)
    package_path = Path(str(state.get("evidence_package_path") or ""))
    base: dict[str, Any] = {
        "format": DIAGNOSTIC_FORMAT,
        "created_utc": timestamp,
        "phase": safe_phase,
        "outcome": safe_outcome,
        "command_kind": _command_kind(command),
        "returncode": int(returncode) if returncode is not None else 0,
        "graph_version": GRAPH_VERSION,
        "program_version": _program_version(config.root),
        "source_branch": _source_branch(config.root, unclassified),
        "thread": _thread_summary(config),
        "failure": {
            "class": failure_class,
            "origin_node": origin_node,
            "repair_outcome": repair_outcome,
        },
        "counts": {
            "accepted_moves": len(state.get("accepted_moves") or []),
            "retry_count": _count(state.get("retry_count")),
            "rollback_count": _count(state.get("rollback_count")),
            "uncovered_required_count": _count(state.get("uncovered_required_count")),
            "event_count": _event_count(config),
        },
        "decision_trace": build_decision_trace(state),
        "providers": _provider_summary(report_path, unclassified),
        "artifacts": {
            "failure_evidence_sha256": _sha_token(
                state.get("failure_evidence_ref")
                or state.get("failure_record_ref")
                or state.get("last_error_ref")
            ),
            "local_package_sha256": _file_sha(package_path) if str(package_path) else "",
        },
        "privacy": {
            "schema_version": 1,
            "excluded_categories": list(_EXCLUDED_CATEGORIES),
        },
    }
    if unclassified:
        base["unclassified_sha256"] = dict(sorted(unclassified.items()))
    canonical = json.dumps(base, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {**base, "run_id": sha256(canonical.encode("utf-8")).hexdigest()}


def _outbox(config: RuntimeConfig) -> Path:
    return config.state_dir / "diagnostics" / "outbox"


def _exact_keys(value: Any, keys: set[str]) -> bool:
    return isinstance(value, Mapping) and set(value) == keys


def _valid_count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _valid_confidence(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0.0 <= float(value) <= 1.0


def _valid_decision_trace(value: Any) -> bool:
    keys = {
        "schema_version", "boundary_id", "decision_boundary_id", "accepted_move_count",
        "uncovered_required_count", "pressure_votes", "committed_pressure", "edge",
        "candidate_sha256", "rejection_class", "budgets",
    }
    if not _exact_keys(value, keys) or value.get("schema_version") != 1:
        return False
    for key in ("boundary_id", "decision_boundary_id", "candidate_sha256"):
        if value.get(key) and not _sha_token(value.get(key)):
            return False
    for key in ("accepted_move_count", "uncovered_required_count"):
        if not _valid_count(value.get(key)):
            return False
    rejection = str(value.get("rejection_class") or "")
    if rejection and not re.fullmatch(r"[A-Z0-9_.:-]{1,64}", rejection):
        return False
    votes = value.get("pressure_votes")
    if not isinstance(votes, list) or len(votes) > 4:
        return False
    for vote in votes:
        if not _exact_keys(vote, {"state", "confidence", "provider", "boundary_id"}):
            return False
        if vote.get("state") not in {"", "OPEN", "NATURAL_STOP", "AMBIGUOUS"}:
            return False
        if vote.get("provider") not in {"", "codex", "claude", "controller"}:
            return False
        if not _valid_confidence(vote.get("confidence")):
            return False
        if vote.get("boundary_id") and not _sha_token(vote.get("boundary_id")):
            return False
    pressure = value.get("committed_pressure")
    if not _exact_keys(pressure, {"state", "confidence", "boundary_id"}):
        return False
    if pressure.get("state") not in {"", "OPEN", "NATURAL_STOP", "AMBIGUOUS"}:
        return False
    if not _valid_confidence(pressure.get("confidence")):
        return False
    if pressure.get("boundary_id") and not _sha_token(pressure.get("boundary_id")):
        return False
    edge = value.get("edge")
    if not isinstance(edge, Mapping):
        return False
    if edge:
        if not _exact_keys(edge, {"verdict", "confidence", "boundary_id"}):
            return False
        if edge.get("verdict") not in {"", "PASS", "FAIL", "STOP_BEFORE_CANDIDATE"}:
            return False
        if not _valid_confidence(edge.get("confidence")):
            return False
        if edge.get("boundary_id") and not _sha_token(edge.get("boundary_id")):
            return False
    budgets = value.get("budgets")
    if not _exact_keys(budgets, {"retry_count", "rollback_count", "active_budget", "budget_limit"}):
        return False
    if not _valid_count(budgets.get("retry_count")) or not _valid_count(budgets.get("rollback_count")) or not _valid_count(budgets.get("budget_limit")):
        return False
    active_budget = str(budgets.get("active_budget") or "")
    return not active_budget or bool(re.fullmatch(r"[A-Z0-9_.:-]{1,64}", active_budget))


def _valid_diagnostic_record(record: Mapping[str, Any]) -> bool:
    required = {
        "format", "created_utc", "phase", "outcome", "command_kind", "returncode",
        "graph_version", "program_version", "source_branch", "thread", "failure", "counts",
        "decision_trace", "providers", "artifacts", "privacy", "run_id",
    }
    optional = {"unclassified_sha256"}
    if set(record) - required - optional or not required.issubset(record):
        return False
    if record.get("format") != DIAGNOSTIC_FORMAT:
        return False
    created = record.get("created_utc")
    if not isinstance(created, (int, float)) or isinstance(created, bool) or float(created) < 0:
        return False
    if record.get("phase") not in _PHASES | {"UNCLASSIFIED"}:
        return False
    if record.get("outcome") not in _OUTCOMES | {"UNCLASSIFIED"}:
        return False
    if record.get("command_kind") not in {"", "live_smoke", "pytest", "other"}:
        return False
    if not isinstance(record.get("returncode"), int) or isinstance(record.get("returncode"), bool):
        return False
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+-dev[0-9]+", str(record.get("graph_version") or "")):
        return False
    program = str(record.get("program_version") or "")
    if not (re.fullmatch(r"[0-9a-f]{40,64}", program) or program == record.get("graph_version")):
        return False
    branch = str(record.get("source_branch") or "")
    if branch not in {"", "UNCLASSIFIED"} and not _SAFE_BRANCH_RE.fullmatch(branch):
        return False
    thread = record.get("thread")
    if not _exact_keys(thread, {"thread_id", "source_sha256"}):
        return False
    if any(thread.get(key) and not _sha_token(thread.get(key)) for key in ("thread_id", "source_sha256")):
        return False
    failure = record.get("failure")
    if not _exact_keys(failure, {"class", "origin_node", "repair_outcome"}):
        return False
    if failure.get("class") not in {"", "UNCLASSIFIED"} | {item.value for item in FailureClass}:
        return False
    if failure.get("origin_node") not in {"", "UNCLASSIFIED"} | _ORIGIN_NODES:
        return False
    if failure.get("repair_outcome") not in {"", "UNCLASSIFIED"} | {item.value for item in RepairOutcome}:
        return False
    counts = record.get("counts")
    count_keys = {"accepted_moves", "retry_count", "rollback_count", "uncovered_required_count", "event_count"}
    if not _exact_keys(counts, count_keys) or any(not _valid_count(counts.get(key)) for key in count_keys):
        return False
    if not _valid_decision_trace(record.get("decision_trace")):
        return False
    providers = record.get("providers")
    if not isinstance(providers, Mapping) or set(providers) - _PROVIDERS:
        return False
    provider_keys = {"provider", "model", "status", "failure_kind", "capability_signature", "attempt_count"}
    for name, provider in providers.items():
        if not _exact_keys(provider, provider_keys):
            return False
        if provider.get("provider") not in {"", name}:
            return False
        model = str(provider.get("model") or "")
        if model and not _MODEL_RE.fullmatch(model):
            return False
        if provider.get("status") not in {"", "UNCLASSIFIED"} | _PROVIDER_STATUSES:
            return False
        if provider.get("failure_kind") not in _FAILURE_KINDS | {"UNCLASSIFIED"}:
            return False
        if provider.get("capability_signature") and not _sha_token(provider.get("capability_signature")):
            return False
        if not _valid_count(provider.get("attempt_count")):
            return False
    artifacts = record.get("artifacts")
    if not _exact_keys(artifacts, {"failure_evidence_sha256", "local_package_sha256"}):
        return False
    if any(artifacts.get(key) and not _sha_token(artifacts.get(key)) for key in artifacts):
        return False
    privacy = record.get("privacy")
    if not _exact_keys(privacy, {"schema_version", "excluded_categories"}):
        return False
    if privacy.get("schema_version") != 1 or tuple(privacy.get("excluded_categories") or ()) != _EXCLUDED_CATEGORIES:
        return False
    unclassified = record.get("unclassified_sha256", {})
    if not isinstance(unclassified, Mapping) or len(unclassified) > 32:
        return False
    for key, value in unclassified.items():
        if not re.fullmatch(r"[a-z0-9_.]{1,96}", str(key)) or not _sha_token(value):
            return False
    run_id = _sha_token(record.get("run_id"))
    if not run_id:
        return False
    base = dict(record)
    base.pop("run_id", None)
    canonical = json.dumps(base, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest() == run_id


def queue_diagnostic(config: RuntimeConfig, record: Mapping[str, Any]) -> Path:
    run_id = _sha_token(record.get("run_id"))
    if not run_id or not _valid_diagnostic_record(record):
        raise ValueError("invalid diagnostic record")
    outbox = _outbox(config)
    outbox.mkdir(parents=True, exist_ok=True)
    destination = outbox / f"{run_id}.json"
    encoded = json.dumps(dict(record), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if destination.is_file():
        if destination.read_text(encoding="utf-8") != encoded:
            raise ValueError("diagnostic run ID collision")
        return destination
    temporary = outbox / f".{run_id}.{os.getpid()}.tmp"
    temporary.write_text(encoded, encoding="utf-8")
    os.chmod(temporary, 0o600)
    os.replace(temporary, destination)
    return destination


def load_queued_diagnostics(config: RuntimeConfig) -> tuple[Path, ...]:
    outbox = _outbox(config)
    if not outbox.is_dir():
        return ()
    return tuple(sorted(path for path in outbox.glob("*.json") if _SHA256_RE.fullmatch(path.stem)))


def _normalized_repository(url: str) -> str:
    value = str(url or "").strip()
    patterns = (
        r"^https?://github\.com/([^/]+/[^/]+?)(?:\.git)?/?$",
        r"^ssh://git@github\.com/([^/]+/[^/]+?)(?:\.git)?/?$",
        r"^git@github\.com:([^/]+/[^/]+?)(?:\.git)?$",
    )
    for pattern in patterns:
        match = re.fullmatch(pattern, value, flags=re.IGNORECASE)
        if match:
            return match.group(1).removesuffix(".git").lower()
    return ""


def _safe_remote_name(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", value))


def _safe_branch(value: str) -> bool:
    return bool(
        value
        and value.startswith("diagnostics/")
        and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,127}", value)
        and ".." not in value
        and not value.endswith(("/", "."))
    )


def select_diagnostics_remote(config: RuntimeConfig) -> DiagnosticsRemote | None:
    requested = str(os.environ.get("AUTHORIAL_DIAGNOSTICS_REMOTE") or "").strip()
    if requested and not _safe_remote_name(requested):
        return None
    try:
        result = subprocess.run(
            ["git", "remote"],
            cwd=config.root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    names = [line.strip() for line in result.stdout.splitlines() if _safe_remote_name(line.strip())]
    if requested:
        names = [requested] if requested in names else []
    else:
        preferred = ["authorial-release", "authorial-source", "origin"]
        names = [name for name in preferred if name in names] + [name for name in names if name not in preferred]
    canonical = DIAGNOSTICS_REPOSITORY.lower()
    for name in names:
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", name],
                cwd=config.root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        url = result.stdout.strip()
        if _normalized_repository(url) == canonical:
            return DiagnosticsRemote(name=name, url=url)
    return None


def _write_status(config: RuntimeConfig, result: PublicationResult) -> None:
    directory = config.state_dir / "diagnostics"
    directory.mkdir(parents=True, exist_ok=True)
    payload = {
        "format": "authorial-flow-diagnostics-publication-v1",
        "status": result.status,
        "run_id": result.run_id,
        "branch": result.branch,
        "queued_count": result.queued_count,
        "commit_sha": result.commit_sha,
        "failure_kind": result.failure_kind,
        "attempts": result.attempts,
    }
    destination = directory / "status.json"
    temporary = directory / f".status.{os.getpid()}.tmp"
    temporary.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.chmod(temporary, 0o600)
    os.replace(temporary, destination)


def _git_result(
    args: Sequence[str],
    *,
    cwd: Path,
    timeout_seconds: float,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    environment = {**os.environ}
    effective_ctype = (
        environment.get("LC_CTYPE")
        or environment.get("LC_ALL")
        or environment.get("LANG")
    )
    environment.pop("LC_ALL", None)
    if effective_ctype:
        environment["LC_CTYPE"] = effective_ctype
    environment.update(
        {
            "LC_MESSAGES": "C",
            "LANGUAGE": "C",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_ASKPASS": "false",
            "SSH_ASKPASS": "false",
            "GIT_CONFIG_NOSYSTEM": "1",
        }
    )
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_seconds,
    )
    if check and result.returncode:
        raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
    return result


def _classify_publication_failure(exc: BaseException, remote_url: str) -> str:
    if isinstance(exc, subprocess.TimeoutExpired):
        return "TIMEOUT"
    text = ""
    if isinstance(exc, subprocess.CalledProcessError):
        text = f"{exc.stdout or ''}\n{exc.stderr or ''}".lower()
    if not _normalized_repository(remote_url) and not Path(remote_url).exists():
        return "REMOTE_MISSING"
    if any(token in text for token in ("authentication failed", "could not read username", "permission denied", "publickey")):
        return "AUTH_REQUIRED"
    if any(token in text for token in ("could not resolve host", "network is unreachable", "failed to connect")):
        return "NETWORK_UNAVAILABLE"
    if any(token in text for token in ("non-fast-forward", "fetch first", "stale info")):
        return "NON_FAST_FORWARD"
    return "GIT_FAILURE"


def _load_queued_record(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    if not _valid_diagnostic_record(payload) or _sha_token(payload.get("run_id")) != path.stem:
        return None
    return payload


def _prepare_diagnostics_checkout(
    checkout: Path,
    *,
    remote_url: str,
    branch: str,
    timeout_seconds: float,
) -> str:
    _git_result(["init", "-q", "-b", "diagnostics-stage"], cwd=checkout, timeout_seconds=timeout_seconds)
    _git_result(["config", "user.name", "Authorial Flow Diagnostics"], cwd=checkout, timeout_seconds=timeout_seconds)
    _git_result(["config", "user.email", "diagnostics@authorial-flow.invalid"], cwd=checkout, timeout_seconds=timeout_seconds)
    fetched = _git_result(
        ["fetch", "--no-tags", "--depth=1", remote_url, f"refs/heads/{branch}:refs/diagnostics/published"],
        cwd=checkout,
        timeout_seconds=timeout_seconds,
        check=False,
    )
    if fetched.returncode == 0:
        _git_result(["checkout", "-q", "-B", "diagnostics-stage", "refs/diagnostics/published"], cwd=checkout, timeout_seconds=timeout_seconds)
        return "existing"
    remote_missing_branch = (fetched.stderr or "").lower()
    if "couldn't find remote ref" in remote_missing_branch or "could not find remote ref" in remote_missing_branch:
        return "orphan"
    raise subprocess.CalledProcessError(fetched.returncode, fetched.args, fetched.stdout, fetched.stderr)


def _install_queued_records(checkout: Path, queued: Sequence[Path]) -> tuple[list[Path], str]:
    installed: list[Path] = []
    latest: tuple[float, dict[str, Any]] | None = None
    for path in queued:
        payload = _load_queued_record(path)
        if payload is None:
            continue
        created = float(payload.get("created_utc") or 0.0)
        day = time.strftime("%Y-%m-%d", time.gmtime(created))
        destination = checkout / "runs" / day / path.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if destination.is_file() and destination.read_text(encoding="utf-8") != encoded:
            raise ValueError("published diagnostic collision")
        destination.write_text(encoded, encoding="utf-8")
        installed.append(path)
        candidate = (created, payload)
        if latest is None or candidate[0] >= latest[0]:
            latest = candidate
    if latest is None:
        return [], ""
    (checkout / "LATEST.json").write_text(
        json.dumps(latest[1], ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return installed, str(latest[1]["run_id"])


def publish_queued_diagnostics(
    config: RuntimeConfig,
    *,
    remote_url: str | None = None,
    remote_name: str | None = None,
    branch: str | None = None,
    timeout_seconds: float = 45,
) -> PublicationResult:
    configured_branch = branch or str(os.environ.get("AUTHORIAL_DIAGNOSTICS_BRANCH") or DIAGNOSTICS_BRANCH)
    if not _safe_branch(configured_branch):
        result = PublicationResult("queued", "", DIAGNOSTICS_BRANCH, len(load_queued_diagnostics(config)), failure_kind="GIT_FAILURE")
        _write_status(config, result)
        return result
    queued = load_queued_diagnostics(config)
    if not queued:
        result = PublicationResult("nothing_to_publish", "", configured_branch, 0)
        _write_status(config, result)
        return result
    selected = select_diagnostics_remote(config) if remote_url is None else None
    if remote_url is None:
        if selected is None:
            result = PublicationResult("queued", queued[-1].stem, configured_branch, len(queued), failure_kind="REMOTE_MISSING")
            _write_status(config, result)
            return result
        remote_url = selected.url
        remote_name = selected.name
    attempts = 0
    last_failure = "GIT_FAILURE"
    for attempts in range(1, 4):
        temp_root = config.state_dir / "diagnostics" / "tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        checkout = Path(tempfile.mkdtemp(prefix="publish-", dir=temp_root))
        try:
            _prepare_diagnostics_checkout(
                checkout,
                remote_url=str(remote_url),
                branch=configured_branch,
                timeout_seconds=timeout_seconds,
            )
            installed, latest_run = _install_queued_records(checkout, queued)
            if not installed:
                result = PublicationResult("nothing_to_publish", "", configured_branch, len(queued), attempts=attempts)
                _write_status(config, result)
                return result
            _git_result(["add", "LATEST.json", "runs"], cwd=checkout, timeout_seconds=timeout_seconds)
            diff = _git_result(["diff", "--cached", "--quiet"], cwd=checkout, timeout_seconds=timeout_seconds, check=False)
            if diff.returncode == 0:
                commit = _git_result(["rev-parse", "HEAD"], cwd=checkout, timeout_seconds=timeout_seconds).stdout.strip()
                for path in installed:
                    path.unlink(missing_ok=True)
                result = PublicationResult("already_published", latest_run, configured_branch, len(load_queued_diagnostics(config)), commit_sha=commit, attempts=attempts)
                _write_status(config, result)
                return result
            _git_result(["commit", "-q", "-m", f"diagnostics: {latest_run[:12]}"], cwd=checkout, timeout_seconds=timeout_seconds)
            commit = _git_result(["rev-parse", "HEAD"], cwd=checkout, timeout_seconds=timeout_seconds).stdout.strip()
            push = _git_result(
                ["push", str(remote_url), f"HEAD:refs/heads/{configured_branch}"],
                cwd=checkout,
                timeout_seconds=timeout_seconds,
                check=False,
            )
            if push.returncode:
                raise subprocess.CalledProcessError(push.returncode, push.args, push.stdout, push.stderr)
            for path in installed:
                path.unlink(missing_ok=True)
            result = PublicationResult("published", latest_run, configured_branch, len(load_queued_diagnostics(config)), commit_sha=commit, attempts=attempts)
            _write_status(config, result)
            return result
        except Exception as exc:
            last_failure = _classify_publication_failure(exc, str(remote_url))
            if last_failure != "NON_FAST_FORWARD":
                break
        finally:
            shutil.rmtree(checkout, ignore_errors=True)
    result = PublicationResult("queued", queued[-1].stem, configured_branch, len(load_queued_diagnostics(config)), failure_kind=last_failure, attempts=attempts)
    _write_status(config, result)
    return result


def publish_diagnostic(
    config: RuntimeConfig,
    record: Mapping[str, Any],
    **transport_options: Any,
) -> PublicationResult:
    queue_diagnostic(config, record)
    return publish_queued_diagnostics(config, **transport_options)


def safely_publish_diagnostic(
    config: RuntimeConfig,
    *,
    phase: str,
    outcome: str,
    result: Mapping[str, Any] | None = None,
    report_path: Path | None = None,
    command: Sequence[str] | None = None,
    returncode: int | None = None,
    **transport_options: Any,
) -> PublicationResult:
    """Build, queue, and publish one diagnostic without changing the wrapped outcome."""
    try:
        record = build_diagnostic_record(
            config,
            phase=phase,
            outcome=outcome,
            result=result,
            report_path=report_path,
            command=command,
            returncode=returncode,
        )
        return publish_diagnostic(config, record, **transport_options)
    except Exception:
        try:
            queued_count = len(load_queued_diagnostics(config))
        except Exception:
            queued_count = 0
        unavailable = PublicationResult(
            status="publication_unavailable",
            run_id="",
            branch=DIAGNOSTICS_BRANCH,
            queued_count=queued_count,
            failure_kind="LOCAL_FAILURE",
        )
        try:
            _write_status(config, unavailable)
        except Exception:
            pass
        return unavailable
