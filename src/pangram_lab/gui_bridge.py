from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import quote

from pangram_lab import gui_local
from pangram_lab.call_budget import (
    PangramCallLedger,
    SECTION_CALL_CAP,
    SectionCallCapReached,
)
from pangram_lab.git_sync import GitSync, GitSyncError
from pangram_lab.local_cli import GitEvidenceDurability


SCHEMA_VERSION = 1
SERVICE_VERSION = "pangram-gui-bridge-v1"
QUEUE_REPOSITORY = "u-dont-existDOTcom/pangram-humanization-lab"
QUEUE_BRANCH = "automation/pangram-gui-bridge-queue"
RESULT_BRANCH = "agent/pangram-local-playwright-gpt-20260818"
BRIDGE_ROOT = Path("state/pangram-gui-bridge")
REQUEST_ROOT = BRIDGE_ROOT / "requests"
RESULT_ROOT = BRIDGE_ROOT / "results"
SEEN_ROOT = BRIDGE_ROOT / "seen"
WORK_ROOT = BRIDGE_ROOT / "work"
CONFLICT_ROOT = BRIDGE_ROOT / "conflicts"
PAID_RESERVATION_ROOT = BRIDGE_ROOT / "paid-reservations"
CURSOR_PATH = BRIDGE_ROOT / "queue-cursor.json"
MAX_REQUEST_BYTES = 32 * 1024
PANGRAM_MODEL = "pangram-4"
PANGRAM_VERSION = "4.0"
EXTRACTION_PROFILE = "joel_articles_markdown_from_unique_introduction_v1"

_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")
_SAFE_SOURCE_PATH = re.compile(r"^[A-Za-z0-9._/-]+\.md$")
_SAFE_REF = re.compile(r"^refs/heads/[A-Za-z0-9][A-Za-z0-9._/-]{0,220}$")
_UUID_IN_TEXT = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_HEADING = re.compile(r"^#{1,6}\s+")
_LIST_MARKER = re.compile(r"^\s*(?:[-+*]|\d+\.)\s+")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_PLACEHOLDER = re.compile(r"^\*\*\[EXISTING [^\]]+\]\*\*$")
_THEMATIC_BREAK = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")

_TRUSTED_SOURCES: dict[str, tuple[str, ...]] = {
    "u-dont-existDOTcom/joel-articles": ("articles/",),
}
_TRUSTED_ORIGIN_URLS = {
    "git@github.com:u-dont-existDOTcom/pangram-humanization-lab.git",
    "https://github.com/u-dont-existDOTcom/pangram-humanization-lab.git",
}


class BridgeError(RuntimeError):
    code = "bridge_error"


class RequestValidationError(BridgeError):
    code = "invalid_request"


class QueueTopologyError(BridgeError):
    code = "queue_topology_blocked"


class BridgeBlocked(BridgeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        ambiguous: bool = False,
        details: Mapping[str, object] | None = None,
    ):
        self.code = code
        self.ambiguous = ambiguous
        self.details = dict(details or {})
        super().__init__(message)


@dataclass(frozen=True)
class SourceSpec:
    repository: str
    ref: str
    commit: str
    path: str
    file_sha256: str
    text_sha256: str
    text_word_count: int


@dataclass(frozen=True)
class BridgeRequest:
    request_id: str
    operation: str
    source: SourceSpec | None
    extraction_profile: str | None
    audit_id: str | None
    section_id: str | None
    call_cap: int | None


@dataclass(frozen=True)
class MaterializedInput:
    path: Path
    text: str
    text_sha256: str
    word_count: int
    source_file_sha256: str
    extraction_counts: dict[str, int]


@dataclass(frozen=True)
class QueueBatch:
    previous_commit: str
    head_commit: str
    request_paths: tuple[str, ...]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _atomic_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise RequestValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise RequestValidationError(f"non-finite JSON number is not allowed: {value}")


def _reject_controls(value: object) -> None:
    if isinstance(value, str):
        if _CONTROL.search(value):
            raise RequestValidationError("JSON strings may not contain control characters")
        return
    if isinstance(value, dict):
        for key, child in value.items():
            _reject_controls(key)
            _reject_controls(child)
        return
    if isinstance(value, list):
        for child in value:
            _reject_controls(child)


def _exact_keys(
    value: Mapping[str, object],
    *,
    required: set[str],
    allowed: set[str],
    label: str,
) -> None:
    keys = set(value)
    missing = sorted(required - keys)
    unknown = sorted(keys - allowed)
    if missing:
        raise RequestValidationError(f"{label} is missing required field(s): {', '.join(missing)}")
    if unknown:
        raise RequestValidationError(f"{label} contains unsupported field(s): {', '.join(unknown)}")


def _valid_uuid4(value: object) -> str:
    if not isinstance(value, str):
        raise RequestValidationError("request_id must be a lowercase UUIDv4 string")
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise RequestValidationError("request_id must be a lowercase UUIDv4 string") from exc
    if parsed.version != 4 or str(parsed) != value:
        raise RequestValidationError("request_id must be a lowercase UUIDv4 string")
    return value


def _safe_id(value: object, label: str) -> str:
    if not isinstance(value, str) or not _SAFE_ID.fullmatch(value):
        raise RequestValidationError(
            f"{label} must match {_SAFE_ID.pattern} and be at most 96 characters"
        )
    return value


def _source_spec(value: object) -> SourceSpec:
    if not isinstance(value, dict):
        raise RequestValidationError("source must be a JSON object")
    required = {
        "repository",
        "ref",
        "commit",
        "path",
        "file_sha256",
        "text_sha256",
        "text_word_count",
    }
    _exact_keys(value, required=required, allowed=required, label="source")

    repository = value["repository"]
    if repository not in _TRUSTED_SOURCES:
        raise RequestValidationError("source.repository is not in the fixed trusted registry")
    ref = value["ref"]
    if (
        not isinstance(ref, str)
        or not _SAFE_REF.fullmatch(ref)
        or ".." in ref
        or "@{" in ref
        or "\\" in ref
    ):
        raise RequestValidationError("source.ref is not a safe fully qualified heads ref")
    commit = value["commit"]
    if not isinstance(commit, str) or not _HEX40.fullmatch(commit):
        raise RequestValidationError("source.commit must be a lowercase 40-character Git SHA")
    path = value["path"]
    if not isinstance(path, str) or not _SAFE_SOURCE_PATH.fullmatch(path):
        raise RequestValidationError("source.path must be an allowlisted Markdown repository path")
    pure = PurePosixPath(path)
    if pure.is_absolute() or any(part in ("", ".", "..", ".git") for part in pure.parts):
        raise RequestValidationError("source.path is not normalized or traverses a protected path")
    if not any(path.startswith(prefix) for prefix in _TRUSTED_SOURCES[str(repository)]):
        raise RequestValidationError("source.path is outside the repository's trusted prefixes")
    file_sha256 = value["file_sha256"]
    text_sha256 = value["text_sha256"]
    if not isinstance(file_sha256, str) or not _HEX64.fullmatch(file_sha256):
        raise RequestValidationError("source.file_sha256 must be lowercase SHA-256")
    if not isinstance(text_sha256, str) or not _HEX64.fullmatch(text_sha256):
        raise RequestValidationError("source.text_sha256 must be lowercase SHA-256")
    word_count = value["text_word_count"]
    if isinstance(word_count, bool) or not isinstance(word_count, int) or not 1 <= word_count <= 250_000:
        raise RequestValidationError("source.text_word_count must be an integer from 1 to 250000")
    return SourceSpec(
        repository=str(repository),
        ref=ref,
        commit=commit,
        path=path,
        file_sha256=file_sha256,
        text_sha256=text_sha256,
        text_word_count=word_count,
    )


def parse_request(raw: bytes, *, expected_request_id: str | None = None) -> BridgeRequest:
    if not raw or len(raw) > MAX_REQUEST_BYTES:
        raise RequestValidationError(
            f"request must contain 1..{MAX_REQUEST_BYTES} UTF-8 bytes"
        )
    if raw.startswith(b"\xef\xbb\xbf"):
        raise RequestValidationError("UTF-8 BOM is not allowed")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RequestValidationError("request must be valid UTF-8") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except RequestValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise RequestValidationError(f"request is not valid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise RequestValidationError("request must be a JSON object")
    _reject_controls(value)

    common = {"schema_version", "request_id", "operation"}
    operation = value.get("operation")
    if operation == "verify":
        _exact_keys(value, required=common, allowed=common, label="verify request")
    elif operation in {"recover", "localize"}:
        fields = common | {"source", "extraction_profile", "audit_id", "section_id"}
        _exact_keys(value, required=fields, allowed=fields, label=f"{operation} request")
    elif operation == "measure":
        fields = common | {
            "source",
            "extraction_profile",
            "audit_id",
            "section_id",
            "call_cap",
        }
        _exact_keys(value, required=fields, allowed=fields, label="measure request")
    else:
        raise RequestValidationError("operation must be verify, recover, localize, or measure")

    if value.get("schema_version") != SCHEMA_VERSION:
        raise RequestValidationError(f"schema_version must be {SCHEMA_VERSION}")
    request_id = _valid_uuid4(value.get("request_id"))
    if expected_request_id is not None and request_id != expected_request_id:
        raise RequestValidationError("request_id must match the immutable request filename")
    if operation == "verify":
        return BridgeRequest(request_id, "verify", None, None, None, None, None)

    source = _source_spec(value.get("source"))
    extraction_profile = value.get("extraction_profile")
    if extraction_profile != EXTRACTION_PROFILE:
        raise RequestValidationError(
            f"extraction_profile must be the fixed named profile {EXTRACTION_PROFILE}"
        )
    audit_id = _safe_id(value.get("audit_id"), "audit_id")
    section_id = _safe_id(value.get("section_id"), "section_id")
    call_cap: int | None = None
    if operation == "measure":
        supplied = value.get("call_cap")
        if (
            isinstance(supplied, bool)
            or not isinstance(supplied, int)
            or not 1 <= supplied <= SECTION_CALL_CAP
        ):
            raise RequestValidationError(
                f"call_cap must be an integer from 1 to {SECTION_CALL_CAP}"
            )
        call_cap = supplied
    return BridgeRequest(
        request_id,
        str(operation),
        source,
        str(extraction_profile),
        audit_id,
        section_id,
        call_cap,
    )


def extract_reader_visible(source: str, profile: str) -> tuple[str, dict[str, int]]:
    if profile != EXTRACTION_PROFILE:
        raise RequestValidationError(f"unknown trusted extraction profile: {profile}")
    lines = source.splitlines()
    if lines.count("# Introduction") != 1:
        raise BridgeBlocked(
            "extraction_boundary_mismatch",
            "source must contain exactly one # Introduction boundary",
        )
    start = lines.index("# Introduction")
    visible: list[str] = []
    placeholders = 0
    links = 0
    thematic_breaks = 0
    headings = 0
    lists = 0
    for original in lines[start:]:
        if _PLACEHOLDER.fullmatch(original):
            placeholders += 1
            continue
        if _THEMATIC_BREAK.fullmatch(original):
            thematic_breaks += 1
            continue
        if _HEADING.match(original):
            headings += 1
        line = _HEADING.sub("", original)
        if _LIST_MARKER.match(line):
            lists += 1
        line = _LIST_MARKER.sub("", line)
        while True:
            match = _LINK.search(line)
            if match is None:
                break
            links += 1
            line = line[: match.start()] + match.group(1) + line[match.end() :]
        line = line.replace("**", "").replace("`", "")
        if re.search(r"https?://|\[[^\]]+\]\(|^#{1,6}\s+|^\s*(?:[-+*]|\d+\.)\s+", line):
            raise BridgeBlocked(
                "extraction_markdown_remaining",
                "trusted extraction profile left unsupported Markdown syntax",
            )
        if not line:
            if visible and visible[-1] != "":
                visible.append("")
            continue
        visible.append(line)
    while visible and visible[-1] == "":
        visible.pop()
    text = "\n".join(visible) + "\n"
    return text, {
        "excluded_native_editor_placeholders": placeholders,
        "excluded_link_destinations": links,
        "excluded_non_prose_thematic_breaks": thematic_breaks,
        "retained_heading_text_lines": headings,
        "retained_list_text_lines": lists,
    }


class GitHubSourceClient:
    def __init__(self, executable: str = "gh") -> None:
        self.executable = executable

    def _run(self, args: list[str], *, text: bool) -> subprocess.CompletedProcess[Any]:
        completed = subprocess.run(
            [self.executable, "api", *args],
            capture_output=True,
            text=text,
            check=False,
        )
        if completed.returncode:
            detail = completed.stderr.strip() if text else completed.stderr.decode(
                "utf-8", errors="replace"
            ).strip()
            raise BridgeBlocked("source_fetch_failed", _safe_message(detail or "GitHub read failed"))
        return completed

    def verify_commit_on_ref(self, source: SourceSpec) -> None:
        endpoint = f"repos/{source.repository}/commits/{quote(source.ref, safe='')}"
        resolved = self._run([endpoint, "--jq", ".sha"], text=True).stdout.strip()
        if not _HEX40.fullmatch(resolved):
            raise BridgeBlocked("source_ref_unresolved", "trusted source ref did not resolve to a commit")
        if resolved == source.commit:
            return
        comparison = self._run(
            [
                f"repos/{source.repository}/compare/{source.commit}...{resolved}",
                "--jq",
                ".status",
            ],
            text=True,
        ).stdout.strip()
        if comparison not in {"ahead", "identical"}:
            raise BridgeBlocked(
                "source_commit_not_on_ref",
                "expected source commit is not an ancestor of the trusted source ref",
            )

    def verify_regular_blob(self, source: SourceSpec) -> None:
        tree_sha = self._run(
            [
                f"repos/{source.repository}/git/commits/{source.commit}",
                "--jq",
                ".tree.sha",
            ],
            text=True,
        ).stdout.strip()
        if not _HEX40.fullmatch(tree_sha):
            raise BridgeBlocked("source_tree_unresolved", "source commit tree did not resolve")
        parts = PurePosixPath(source.path).parts
        for index, part in enumerate(parts):
            row = self._run(
                [
                    f"repos/{source.repository}/git/trees/{tree_sha}",
                    "--jq",
                    f'.tree[] | select(.path == {json.dumps(part)}) | '
                    "[.mode, .type, .sha] | @tsv",
                ],
                text=True,
            ).stdout.strip()
            fields = row.split("\t") if row else []
            if len(fields) != 3 or not _HEX40.fullmatch(fields[2]):
                raise BridgeBlocked("source_tree_entry_missing", "source path tree entry is missing")
            mode, entry_type, entry_sha = fields
            final = index == len(parts) - 1
            if final:
                if entry_type != "blob" or mode not in {"100644", "100755"}:
                    raise BridgeBlocked(
                        "source_not_regular_blob",
                        "source path must resolve to a regular Git blob, not a symlink or submodule",
                    )
            elif entry_type != "tree" or mode != "040000":
                raise BridgeBlocked(
                    "source_parent_not_tree",
                    "source path parent must resolve to a regular Git tree",
                )
            tree_sha = entry_sha

    def fetch_blob(self, source: SourceSpec) -> bytes:
        self.verify_commit_on_ref(source)
        self.verify_regular_blob(source)
        endpoint = (
            f"repos/{source.repository}/contents/{source.path}?ref={source.commit}"
        )
        return bytes(
            self._run(
                ["-H", "Accept: application/vnd.github.raw", endpoint],
                text=False,
            ).stdout
        )


def materialize_source(
    request: BridgeRequest,
    *,
    source_client: GitHubSourceClient,
    cache_root: Path | None = None,
) -> MaterializedInput:
    if request.source is None or request.extraction_profile is None:
        raise AssertionError("source materialization requires a source-bearing request")
    source = request.source
    raw = source_client.fetch_blob(source)
    raw_sha = _sha256_bytes(raw)
    if raw_sha != source.file_sha256:
        raise BridgeBlocked(
            "source_file_sha_mismatch",
            f"source file SHA-256 changed: expected={source.file_sha256} actual={raw_sha}",
        )
    try:
        markdown = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BridgeBlocked("source_not_utf8", "trusted source file is not UTF-8") from exc
    text, counts = extract_reader_visible(markdown, request.extraction_profile)
    text_sha = _sha256_bytes(text.encode("utf-8"))
    words = len(text.split())
    if text_sha != source.text_sha256:
        raise BridgeBlocked(
            "extracted_text_sha_mismatch",
            f"reader-visible SHA-256 changed: expected={source.text_sha256} actual={text_sha}",
        )
    if words != source.text_word_count:
        raise BridgeBlocked(
            "extracted_word_count_mismatch",
            f"reader-visible word count changed: expected={source.text_word_count} actual={words}",
        )
    base = cache_root or Path.home() / ".cache" / "pangram-local" / "bridge-inputs"
    directory = base / source.file_sha256 / source.text_sha256
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = directory / "reader-visible.txt"
    path.write_bytes(text.encode("utf-8"))
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return MaterializedInput(path, text, text_sha, words, raw_sha, counts)


def _safe_float(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BridgeBlocked("cache_invalid", "cached score contains a non-numeric fraction")
    parsed = float(value)
    if not math.isfinite(parsed) or not 0.0 <= parsed <= 1.0:
        raise BridgeBlocked("cache_invalid", "cached score fraction is outside [0,1]")
    return parsed


def validate_completed_cache(
    repo_root: Path,
    request: BridgeRequest,
    materialized: MaterializedInput,
) -> dict[str, object] | None:
    if request.source is None:
        raise AssertionError("cache validation requires a source request")
    directory = repo_root / "state" / "gui-runs" / PANGRAM_MODEL / materialized.text_sha256
    result_path = directory / "result.json"
    if not result_path.is_file():
        return None
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BridgeBlocked("cache_invalid", "cached result.json is unreadable") from exc
    if not isinstance(result, dict) or result.get("status") != "complete":
        raise BridgeBlocked("cache_invalid", "cached result is not complete")
    if result.get("transport") != "local_playwright" or result.get("model") != PANGRAM_MODEL:
        raise BridgeBlocked("cache_invalid", "cached result is not the local Pangram-4 GUI transport")
    if result.get("input_sha256") != materialized.text_sha256:
        raise BridgeBlocked("cache_invalid", "cached input SHA-256 does not match the request")
    if result.get("word_count") != materialized.word_count:
        raise BridgeBlocked("cache_invalid", "cached word count does not match the request")
    source = result.get("source")
    if not isinstance(source, dict):
        raise BridgeBlocked("cache_invalid", "cached result lacks source provenance")
    expected_source = request.source
    source_pairs = {
        "repository": expected_source.repository,
        "source_commit": expected_source.commit,
        "source_path": expected_source.path,
        "source_file_sha256": expected_source.file_sha256,
    }
    for key, expected in source_pairs.items():
        if source.get(key) != expected:
            raise BridgeBlocked("cache_invalid", f"cached source provenance mismatch: {key}")
    parsed = result.get("parsed")
    if not isinstance(parsed, dict):
        raise BridgeBlocked("cache_invalid", "cached result lacks parsed detector evidence")
    if parsed.get("detector_stage") != "STAGE_SUCCESS" or parsed.get("detector_version") != PANGRAM_VERSION:
        raise BridgeBlocked("cache_invalid", "cached result is not Pangram 4.0 STAGE_SUCCESS")
    if parsed.get("summary_source") != "stored_history_structured_result":
        raise BridgeBlocked("cache_invalid", "cached score is not from the stored History result")
    if parsed.get("structured_result_field_path") != ["response", "overall"]:
        raise BridgeBlocked("cache_invalid", "cached score is not response.overall")
    summary = parsed.get("summary")
    if not isinstance(summary, dict):
        raise BridgeBlocked("cache_invalid", "cached result lacks a detector summary")
    ai = _safe_float(summary.get("fraction_ai"))
    assisted = _safe_float(summary.get("fraction_ai_assisted"))
    human = _safe_float(summary.get("fraction_human"))
    if abs((ai + assisted + human) - 1.0) > 0.02:
        raise BridgeBlocked("cache_invalid", "cached detector fractions do not sum to one")
    identity = result.get("history_api_exact_identity")
    if not isinstance(identity, dict):
        raise BridgeBlocked("cache_invalid", "cached result lacks exact History identity")
    for key in ("authorized_text_sha256", "stored_text_sha256", "exact_text_sha256"):
        if identity.get(key) != materialized.text_sha256:
            raise BridgeBlocked("cache_invalid", f"cached History identity mismatch: {key}")
    if identity.get("transport_match_mode") != "exact_utf8":
        raise BridgeBlocked("cache_invalid", "cached History binding is not exact UTF-8")

    artifacts: dict[str, dict[str, object]] = {}
    for name, filename, hash_key in (
        ("result", "result.json", None),
        ("report_body", "report-body.txt", "report_body_sha256"),
        ("report_pdf", "report.pdf", "report_pdf_sha256"),
    ):
        path = directory / filename
        if not path.is_file():
            raise BridgeBlocked("cache_invalid", f"cached artifact is missing: {filename}")
        digest = _sha256_bytes(path.read_bytes())
        if hash_key is not None and result.get(hash_key) != digest:
            raise BridgeBlocked("cache_invalid", f"cached artifact hash mismatch: {filename}")
        artifacts[name] = {
            "path": path.relative_to(repo_root).as_posix(),
            "sha256": digest,
        }
    return {
        "receipt": result,
        "score": {
            "fraction_ai": ai,
            "fraction_ai_assisted": assisted,
            "fraction_human": human,
            "stage": "STAGE_SUCCESS",
            "version": PANGRAM_VERSION,
            "headline": parsed.get("headline"),
            "prediction_short": parsed.get("prediction_short"),
            "source": "response.overall",
        },
        "artifacts": artifacts,
        "measurement_directory": directory,
    }


def _ambiguous_state(
    repo_root: Path,
    request: BridgeRequest,
    text_sha256: str,
) -> dict[str, object] | None:
    directory = repo_root / "state" / "gui-runs" / PANGRAM_MODEL / text_sha256
    reservation = directory / "reservation.json"
    failure = directory / "failure.json"
    bridge_reservation = repo_root / PAID_RESERVATION_ROOT / f"{text_sha256}.json"
    attempted = False
    stage = None
    target_time: str | None = None
    target_source: str | None = None
    ledger_reservations: list[Path] = []

    def timestamp_from(path: Path, *keys: str) -> str | None:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise BridgeBlocked(
                "reservation_evidence_invalid",
                "reservation evidence is unreadable; refusing a possible repeat",
                ambiguous=True,
            ) from exc
        for key in keys:
            value = payload.get(key)
            if not isinstance(value, str):
                continue
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                continue
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        return None

    if bridge_reservation.is_file():
        target_time = timestamp_from(bridge_reservation, "reserved_at_utc")
        target_source = "bridge_paid_reservation"
    if reservation.is_file() and target_time is None:
        target_time = timestamp_from(reservation, "reserved_at_utc")
        target_source = "gui_paid_reservation"
    if failure.is_file():
        try:
            payload = json.loads(failure.read_text(encoding="utf-8"))
            attempted = payload.get("detector_submission_attempted") is True
            stage = payload.get("stage")
        except (OSError, UnicodeError, json.JSONDecodeError):
            attempted = True
    ledger_root = repo_root / "state" / "pangram-call-ledgers"
    if ledger_root.is_dir():
        ledger_times: list[str] = []
        for ledger_path in sorted(ledger_root.glob("*.json")):
            try:
                ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
                sections = ledger.get("sections", {})
                if not isinstance(sections, dict):
                    raise AttributeError("invalid sections")
                matched_file = False
                for section in sections.values():
                    if not isinstance(section, dict):
                        raise AttributeError("invalid section")
                    events = section.get("events", [])
                    if not isinstance(events, list):
                        raise AttributeError("invalid events")
                    for event in events:
                        if not isinstance(event, dict):
                            raise AttributeError("invalid event")
                        if not (
                            event.get("type") == "paid_post_reserved"
                            and event.get("measurement_key") == f"gui:{text_sha256}"
                        ):
                            continue
                        if event.get("text_sha256") != text_sha256:
                            raise AttributeError("paid reservation text identity mismatch")
                        matched_file = True
                        recorded = event.get("recorded_at_utc")
                        if isinstance(recorded, str):
                            try:
                                parsed = datetime.fromisoformat(
                                    recorded.replace("Z", "+00:00")
                                )
                            except ValueError:
                                continue
                            if parsed.tzinfo is None:
                                parsed = parsed.replace(tzinfo=timezone.utc)
                            ledger_times.append(
                                parsed.astimezone(timezone.utc)
                                .isoformat()
                                .replace("+00:00", "Z")
                            )
                if matched_file:
                    ledger_reservations.append(ledger_path)
            except (OSError, UnicodeError, json.JSONDecodeError, AttributeError):
                raise BridgeBlocked(
                    "call_ledger_invalid",
                    "paid-call ledger is unreadable; refusing a possible repeat",
                    ambiguous=True,
                )
        if target_time is None and ledger_reservations:
            distinct_times = sorted(set(ledger_times))
            if len(distinct_times) == 1:
                target_time = distinct_times[0]
                target_source = "paid_call_ledger"
            elif len(distinct_times) > 1:
                target_source = "multiple_paid_call_ledger_events"
    if attempted and target_time is None:
        target_time = timestamp_from(failure, "captured_at_utc")
        target_source = "ambiguous_failure"
    if (
        bridge_reservation.is_file()
        or reservation.is_file()
        or attempted
        or ledger_reservations
    ):
        return {
            "state": "action_may_have_happened",
            "recover_before_repeat_required": True,
            "bridge_reservation_path": bridge_reservation.relative_to(repo_root).as_posix()
            if bridge_reservation.is_file()
            else None,
            "reservation_path": reservation.relative_to(repo_root).as_posix()
            if reservation.is_file()
            else None,
            "failure_path": failure.relative_to(repo_root).as_posix()
            if failure.is_file()
            else None,
            "call_ledger_paths": [
                path.relative_to(repo_root).as_posix() for path in ledger_reservations
            ],
            "recovery_target_time_utc": target_time,
            "recovery_target_source": target_source,
            "last_failure_stage": stage,
        }
    return None


def _localization_artifact(
    repo_root: Path,
    cache: Mapping[str, object],
    materialized: MaterializedInput,
) -> dict[str, object]:
    receipt = cache["receipt"]
    assert isinstance(receipt, dict)
    parsed = receipt.get("parsed")
    segments = parsed.get("segments", []) if isinstance(parsed, dict) else []
    safe_windows: list[dict[str, object]] = []
    if isinstance(segments, list):
        for segment in segments:
            if not isinstance(segment, dict):
                continue
            row: dict[str, object] = {}
            for key in ("label", "classification", "word_count", "start", "end", "text"):
                value = segment.get(key)
                if isinstance(value, (str, int, float)) and not isinstance(value, bool):
                    if key != "text" or str(value) in materialized.text:
                        row[key] = value
            if row:
                safe_windows.append(row)
    directory = cache["measurement_directory"]
    assert isinstance(directory, Path)
    path = directory / "localization.json"
    payload: dict[str, object] = {
        "schema_version": 1,
        "input_sha256": materialized.text_sha256,
        "score": dict(cache["score"]),
        "evidence": {
            "report_body": dict(cache["artifacts"]["report_body"]),
            "report_pdf": dict(cache["artifacts"]["report_pdf"]),
        },
        "window_status": "segments_available" if safe_windows else "report_pdf_only",
        "windows": safe_windows,
        "privacy": "No History UUID, private URL, cookie, storage value, or browser-profile data.",
    }
    _atomic_json(path, payload)
    return {
        "path": path.relative_to(repo_root).as_posix(),
        "sha256": _sha256_bytes(path.read_bytes()),
        "window_status": payload["window_status"],
        "window_count": len(safe_windows),
    }


def _reserve_bridge_paid_intent(
    repo_root: Path,
    request: BridgeRequest,
    materialized: MaterializedInput,
) -> Path:
    path = repo_root / PAID_RESERVATION_ROOT / f"{materialized.text_sha256}.json"
    if path.exists():
        state = _ambiguous_state(repo_root, request, materialized.text_sha256) or {}
        raise BridgeBlocked(
            "existing_bridge_paid_reservation",
            "a durable bridge paid reservation already exists; recover before repeat",
            ambiguous=True,
            details={"ambiguity": state},
        )
    _atomic_json(
        path,
        {
            "schema_version": 1,
            "service_version": SERVICE_VERSION,
            "request_id": request.request_id,
            "audit_id": request.audit_id,
            "section_id": request.section_id,
            "model": PANGRAM_MODEL,
            "version": PANGRAM_VERSION,
            "measurement_key": f"gui:{materialized.text_sha256}",
            "text_sha256": materialized.text_sha256,
            "text_word_count": materialized.word_count,
            "reserved_at_utc": _utc_now(),
            "state": "recover_before_repeat_if_result_missing",
        },
    )
    GitSync(repo_root, require_remote=True).sync_paths(
        [path], f"bridge paid intent {materialized.text_sha256[:16]}"
    )
    return path


def _safe_message(message: object) -> str:
    text = _UUID_IN_TEXT.sub("<uuid>", str(message))
    text = re.sub(r"([?&](?:token|key|auth|session)=[^\s&]+)", "?<redacted>", text, flags=re.I)
    return text[:1200]


def _declared_input(request: BridgeRequest | None) -> dict[str, object] | None:
    if request is None or request.source is None:
        return None
    return {
        "repository": request.source.repository,
        "ref": request.source.ref,
        "commit": request.source.commit,
        "path": request.source.path,
        "source_file_sha256": request.source.file_sha256,
        "text_sha256": request.source.text_sha256,
        "text_word_count": request.source.text_word_count,
        "extraction_profile": request.extraction_profile,
    }


class BridgeExecutor:
    def __init__(
        self,
        repo_root: Path,
        *,
        source_client: GitHubSourceClient | None = None,
        cache_root: Path | None = None,
        recover_runner: Callable[[BridgeRequest, MaterializedInput], None] | None = None,
        verify_runner: Callable[[], Mapping[str, object]] | None = None,
        measure_runner: Callable[[BridgeRequest, MaterializedInput], None] | None = None,
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.source_client = source_client or GitHubSourceClient()
        self.cache_root = cache_root
        self.recover_runner = recover_runner or self._recover
        self.verify_runner = verify_runner or self._verify
        self.measure_runner = measure_runner or self._measure

    def _verify(self) -> Mapping[str, object]:
        return gui_local.verify_login_persistence(gui_local.LocalPlaywrightConfig.from_env())

    def _source_metadata(
        self, request: BridgeRequest, materialized: MaterializedInput
    ) -> dict[str, object]:
        assert request.source is not None
        return {
            "repository": request.source.repository,
            "source_branch": request.source.ref,
            "source_commit": request.source.commit,
            "source_path": request.source.path,
            "source_file_sha256": request.source.file_sha256,
            "materialization": request.extraction_profile,
            "audit_id": request.audit_id,
            "section_id": request.section_id,
            **materialized.extraction_counts,
        }

    def _recover(self, request: BridgeRequest, materialized: MaterializedInput) -> None:
        assert request.source is not None
        ambiguity = _ambiguous_state(self.repo_root, request, materialized.text_sha256)
        command = [
            sys.executable,
            str(self.repo_root / "scripts" / "pangram_local_recover_exact_history.py"),
            "--input",
            str(materialized.path),
            "--expect-sha",
            materialized.text_sha256,
            "--source-repository",
            request.source.repository,
            "--source-branch",
            request.source.ref,
            "--source-commit",
            request.source.commit,
            "--source-path",
            request.source.path,
            "--source-file-sha256",
            request.source.file_sha256,
        ]
        if ambiguity is not None:
            target_time = ambiguity.get("recovery_target_time_utc")
            if not isinstance(target_time, str):
                raise BridgeBlocked(
                    "recovery_target_ambiguous",
                    "paid ambiguity has no unique trustworthy reservation timestamp",
                    ambiguous=True,
                    details={"ambiguity": ambiguity},
                )
            command.extend(
                [
                    "--target-time-utc",
                    target_time,
                    "--require-unique-target-match",
                ]
            )
        completed = subprocess.run(
            command,
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise BridgeBlocked(
                "exact_history_recovery_failed",
                _safe_message(detail or "exact History recovery did not produce a result"),
                ambiguous=True,
                details={"ambiguity": ambiguity} if ambiguity is not None else None,
            )

    def _ledger(self, request: BridgeRequest) -> PangramCallLedger:
        assert request.audit_id is not None
        ledger_path = (
            self.repo_root
            / "state"
            / "pangram-call-ledgers"
            / f"{PangramCallLedger._safe(request.audit_id)}.json"
        )
        cap = request.call_cap
        if cap is None and ledger_path.is_file():
            try:
                stored = json.loads(ledger_path.read_text(encoding="utf-8"))
                cap = int(stored["section_call_cap"])
            except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                raise BridgeBlocked("call_ledger_invalid", "existing audit ledger is unreadable") from exc
        cap = cap or SECTION_CALL_CAP
        ledger = PangramCallLedger(self.repo_root, request.audit_id, cap=cap)
        stored_cap = int(ledger.state.get("section_call_cap", cap))
        if request.call_cap is not None and stored_cap != cap:
            raise BridgeBlocked(
                "call_cap_mismatch",
                f"existing audit ledger cap={stored_cap} does not match request cap={cap}",
            )
        return ledger

    def _record_cache_hit(self, request: BridgeRequest, materialized: MaterializedInput) -> None:
        if request.audit_id is None or request.section_id is None:
            return
        ledger_path = (
            self.repo_root
            / "state"
            / "pangram-call-ledgers"
            / f"{PangramCallLedger._safe(request.audit_id)}.json"
        )
        if not ledger_path.is_file():
            return
        ledger = self._ledger(request)
        ledger.record_cache_hit(
            request.section_id,
            PANGRAM_MODEL,
            PANGRAM_VERSION,
            f"gui:{materialized.text_sha256}",
            materialized.text_sha256,
            event_key=f"bridge-request:{request.request_id}",
        )
        GitSync(self.repo_root, require_remote=True).sync_paths(
            [ledger.path], f"bridge cache hit {materialized.text_sha256[:16]}"
        )

    def _measure(self, request: BridgeRequest, materialized: MaterializedInput) -> None:
        assert request.source is not None and request.section_id is not None
        ledger = self._ledger(request)
        reservation = ledger.reserve_paid_call(
            section_id=request.section_id,
            model=PANGRAM_MODEL,
            version=PANGRAM_VERSION,
            measurement_key=f"gui:{materialized.text_sha256}",
            text_sha256=materialized.text_sha256,
            word_count=materialized.word_count,
        )
        if reservation.get("reservation_created") is not True:
            ambiguity = _ambiguous_state(self.repo_root, request, materialized.text_sha256) or {}
            raise BridgeBlocked(
                "paid_call_already_reserved",
                "the exact measurement key was already reserved; recover before repeat",
                ambiguous=True,
                details={"ambiguity": ambiguity},
            )
        GitSync(self.repo_root, require_remote=True).sync_paths(
            [ledger.path],
            f"bridge reserve paid call {request.audit_id} {request.section_id} "
            f"{materialized.text_sha256[:16]}",
        )
        _reserve_bridge_paid_intent(self.repo_root, request, materialized)
        output = self.repo_root / "state" / "gui-runs"
        durability = GitEvidenceDurability(self.repo_root, output)
        gui_local.run_inputs(
            gui_local.LocalPlaywrightConfig.from_env(),
            [materialized.path],
            output_root=output,
            expected_sha256={str(materialized.path): materialized.text_sha256},
            source_metadata={
                str(materialized.path): self._source_metadata(request, materialized)
            },
            evidence_callback=durability,
        )

    def execute(self, request: BridgeRequest) -> dict[str, object]:
        if request.operation == "verify":
            verification = dict(self.verify_runner())
            if verification.get("verified") is not True or verification.get("submitted") is not False:
                raise BridgeBlocked("verify_failed", "read-only Pangram authentication did not verify")
            return {
                "status": "complete",
                "outcome": "verified",
                "request_submission_attempted": False,
                "verification": verification,
                "ambiguity": None,
                "blocked": None,
            }

        materialized = materialize_source(
            request,
            source_client=self.source_client,
            cache_root=self.cache_root,
        )
        cache = validate_completed_cache(self.repo_root, request, materialized)
        if cache is not None:
            prior_ambiguity = _ambiguous_state(
                self.repo_root, request, materialized.text_sha256
            )
            self._record_cache_hit(request, materialized)
            localization = _localization_artifact(self.repo_root, cache, materialized)
            GitSync(self.repo_root, require_remote=True).sync_paths(
                [self.repo_root / localization["path"]],
                f"bridge localization cache {materialized.text_sha256[:16]}",
            )
            return self._completed_result(
                request,
                materialized,
                cache,
                outcome="localized" if request.operation == "localize" else "cache_hit",
                localization=localization,
                request_submission_attempted=False,
                prior_ambiguity=prior_ambiguity,
            )

        ambiguity = _ambiguous_state(self.repo_root, request, materialized.text_sha256)
        if ambiguity is not None or request.operation in {"recover", "localize"}:
            try:
                self.recover_runner(request, materialized)
            except BridgeBlocked as exc:
                if ambiguity is not None and not exc.ambiguous:
                    raise BridgeBlocked(
                        exc.code,
                        str(exc),
                        ambiguous=True,
                        details={"ambiguity": ambiguity},
                    ) from exc
                raise
            cache = validate_completed_cache(self.repo_root, request, materialized)
            if cache is None:
                raise BridgeBlocked(
                    "exact_history_recovery_empty",
                    "read-only recovery completed without an exact cached result",
                    ambiguous=ambiguity is not None,
                    details={"ambiguity": ambiguity} if ambiguity is not None else None,
                )
            localization = _localization_artifact(self.repo_root, cache, materialized)
            GitSync(self.repo_root, require_remote=True).sync_paths(
                [self.repo_root / localization["path"]],
                f"bridge localization recovered {materialized.text_sha256[:16]}",
            )
            return self._completed_result(
                request,
                materialized,
                cache,
                outcome="localized" if request.operation == "localize" else "recovered",
                localization=localization,
                request_submission_attempted=False,
                prior_ambiguity=ambiguity,
            )

        if request.operation != "measure":
            raise BridgeBlocked("no_cached_result", "requested operation requires an existing result")
        try:
            self.measure_runner(request, materialized)
            cache = validate_completed_cache(self.repo_root, request, materialized)
            if cache is None:
                raise BridgeBlocked(
                    "measurement_missing_exact_result",
                    "GUI measurement returned without an exact stored-History result",
                    ambiguous=True,
                )
            localization = _localization_artifact(self.repo_root, cache, materialized)
            GitSync(self.repo_root, require_remote=True).sync_paths(
                [self.repo_root / localization["path"]],
                f"bridge localization measured {materialized.text_sha256[:16]}",
            )
        except SectionCallCapReached as exc:
            raise BridgeBlocked("section_call_cap_reached", str(exc)) from exc
        except Exception as exc:
            ambiguity = _ambiguous_state(self.repo_root, request, materialized.text_sha256)
            if ambiguity is not None:
                raise BridgeBlocked(
                    "measurement_ambiguous_recovery_required",
                    _safe_message(exc),
                    ambiguous=True,
                    details={"ambiguity": ambiguity},
                ) from exc
            raise
        return self._completed_result(
            request,
            materialized,
            cache,
            outcome="measured",
            localization=localization,
            request_submission_attempted=True,
            prior_ambiguity=None,
        )

    def _completed_result(
        self,
        request: BridgeRequest,
        materialized: MaterializedInput,
        cache: Mapping[str, object],
        *,
        outcome: str,
        localization: Mapping[str, object],
        request_submission_attempted: bool,
        prior_ambiguity: Mapping[str, object] | None,
    ) -> dict[str, object]:
        assert request.source is not None
        receipt = cache["receipt"]
        assert isinstance(receipt, dict)
        artifacts = dict(cache["artifacts"])
        artifacts["localization"] = dict(localization)
        return {
            "status": "complete",
            "outcome": outcome,
            "request_submission_attempted": request_submission_attempted,
            "historical_artifact_submission_attempted": True,
            "historical_submission_state": "attempted",
            "input": {
                "repository": request.source.repository,
                "ref": request.source.ref,
                "commit": request.source.commit,
                "path": request.source.path,
                "source_file_sha256": materialized.source_file_sha256,
                "text_sha256": materialized.text_sha256,
                "text_word_count": materialized.word_count,
                "extraction_profile": request.extraction_profile,
                "extraction_counts": materialized.extraction_counts,
            },
            "score": dict(cache["score"]),
            "exact_history_binding": {
                "bound": True,
                "transport_match_mode": "exact_utf8",
                "api_path": "/api/history/<uuid>/",
                "private_record_identifier_stored": False,
            },
            "artifacts": artifacts,
            "recovery": {
                "prior_ambiguity": dict(prior_ambiguity),
                "resolved_by_exact_history_binding": True,
            }
            if prior_ambiguity is not None
            else None,
            "ambiguity": None,
            "blocked": None,
        }


def _run_git(repo_root: Path, args: Iterable[str], *, check: bool = True) -> str:
    command = ["git", *args]
    completed = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise QueueTopologyError(f"Git queue operation failed: {_safe_message(detail)}")
    return completed.stdout


class QueueReader:
    def __init__(
        self,
        repo_root: Path,
        *,
        queue_branch: str = QUEUE_BRANCH,
        request_root: Path = REQUEST_ROOT,
        cursor_path: Path = CURSOR_PATH,
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.queue_branch = queue_branch
        self.request_root = request_root
        self.cursor_path = self.repo_root / cursor_path
        self.remote_ref = f"refs/remotes/origin/{queue_branch}"

    def _fetch(self) -> str:
        _run_git(
            self.repo_root,
            [
                "fetch",
                "--no-tags",
                "origin",
                f"refs/heads/{self.queue_branch}:{self.remote_ref}",
            ],
        )
        head = _run_git(self.repo_root, ["rev-parse", self.remote_ref]).strip()
        if not _HEX40.fullmatch(head):
            raise QueueTopologyError("queue branch did not resolve to a commit")
        return head

    def _cursor(self, head: str) -> str:
        if self.cursor_path.is_file():
            try:
                value = json.loads(self.cursor_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise QueueTopologyError("queue cursor is unreadable") from exc
            if value.get("queue_branch") != self.queue_branch:
                raise QueueTopologyError("queue cursor branch mismatch")
            commit = value.get("last_processed_commit")
            if not isinstance(commit, str) or not _HEX40.fullmatch(commit):
                raise QueueTopologyError("queue cursor commit is invalid")
            return commit
        local_head = _run_git(self.repo_root, ["rev-parse", "HEAD"]).strip()
        base = _run_git(self.repo_root, ["merge-base", local_head, head]).strip()
        if not _HEX40.fullmatch(base):
            raise QueueTopologyError("request and result branches have no trusted merge base")
        return base

    def poll(self) -> QueueBatch:
        head = self._fetch()
        previous = self._cursor(head)
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", previous, head],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if ancestor.returncode != 0:
            raise QueueTopologyError(
                "queue history was rewritten or diverged; refusing untrusted request topology"
            )
        if previous == head:
            return QueueBatch(previous, head, ())
        commits = tuple(
            value
            for value in _run_git(
                self.repo_root,
                ["rev-list", "--reverse", "--topo-order", f"{previous}..{head}"],
            ).splitlines()
            if value
        )
        paths: list[str] = []
        seen_paths: set[str] = set()
        expected_prefix = self.request_root.as_posix() + "/"
        for commit in commits:
            parents = _run_git(
                self.repo_root, ["rev-list", "--parents", "-n", "1", commit]
            ).split()
            if len(parents) != 2:
                raise QueueTopologyError("queue commits must be linear and may not be merges")
            raw = subprocess.run(
                [
                    "git",
                    "diff-tree",
                    "--no-commit-id",
                    "--name-status",
                    "-r",
                    "-z",
                    parents[1],
                    commit,
                ],
                cwd=self.repo_root,
                capture_output=True,
                check=False,
            )
            if raw.returncode:
                raise QueueTopologyError("cannot inspect append-only queue commit")
            fields = raw.stdout.split(b"\0")
            if fields and fields[-1] == b"":
                fields.pop()
            if not fields or len(fields) % 2:
                raise QueueTopologyError("queue commit has no valid request addition")
            for index in range(0, len(fields), 2):
                status = fields[index].decode("ascii", errors="replace")
                path = fields[index + 1].decode("utf-8", errors="strict")
                if status != "A":
                    raise QueueTopologyError(
                        f"queue is append-only; refusing status={status} path={path}"
                    )
                if path in seen_paths:
                    raise QueueTopologyError(f"queue request path was added more than once: {path}")
                if not path.startswith(expected_prefix):
                    raise QueueTopologyError(f"queue commit changed a non-request path: {path}")
                name = PurePosixPath(path).name
                request_id = name.removesuffix(".json") if name.endswith(".json") else ""
                if not name.endswith(".json"):
                    raise QueueTopologyError(f"queue request path must end in .json: {path}")
                try:
                    _valid_uuid4(request_id)
                except RequestValidationError as exc:
                    raise QueueTopologyError(f"queue filename is not a UUIDv4: {path}") from exc
                if PurePosixPath(path).parent.as_posix() != self.request_root.as_posix():
                    raise QueueTopologyError(f"queue requests may not use nested directories: {path}")
                entry = _run_git(self.repo_root, ["ls-tree", commit, "--", path])
                if not entry.startswith("100644 blob "):
                    raise QueueTopologyError(
                        f"queue request must be a non-executable regular blob: {path}"
                    )
                seen_paths.add(path)
                paths.append(path)
        return QueueBatch(previous, head, tuple(sorted(paths)))

    def read(self, head_commit: str, path: str) -> bytes:
        try:
            size = int(
                _run_git(self.repo_root, ["cat-file", "-s", f"{head_commit}:{path}"])
            )
        except ValueError as exc:
            raise QueueTopologyError("queue request blob size is invalid") from exc
        if size < 1 or size > MAX_REQUEST_BYTES:
            raise QueueTopologyError(
                f"queue request must contain 1..{MAX_REQUEST_BYTES} bytes: {path}"
            )
        completed = subprocess.run(
            ["git", "show", f"{head_commit}:{path}"],
            cwd=self.repo_root,
            capture_output=True,
            check=False,
        )
        if completed.returncode:
            raise QueueTopologyError(f"cannot read immutable queue request: {path}")
        return bytes(completed.stdout)

    def write_cursor(self, head_commit: str) -> Path:
        _atomic_json(
            self.cursor_path,
            {
                "schema_version": 1,
                "queue_repository": QUEUE_REPOSITORY,
                "queue_branch": self.queue_branch,
                "last_processed_commit": head_commit,
                "updated_at_utc": _utc_now(),
            },
        )
        return self.cursor_path


class BridgeWorker:
    def __init__(
        self,
        repo_root: Path,
        executor: BridgeExecutor,
        *,
        git_sync: GitSync | None = None,
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.executor = executor
        self.git = git_sync or GitSync(self.repo_root, require_remote=True)

    def _relative(self, root: Path, request_id: str) -> Path:
        return self.repo_root / root / f"{request_id}.json"

    def process(self, queue_path: str, queue_commit: str, raw: bytes) -> dict[str, object]:
        request_id = PurePosixPath(queue_path).name.removesuffix(".json")
        request_sha = _sha256_bytes(raw)
        result_path = self._relative(RESULT_ROOT, request_id)
        seen_path = self._relative(SEEN_ROOT, request_id)
        work_path = self._relative(WORK_ROOT, request_id)

        if result_path.is_file():
            existing = json.loads(result_path.read_text(encoding="utf-8"))
            same_request = existing.get("request_sha256") == request_sha
            if same_request:
                if existing.get("status") not in {"ambiguous", "failed"}:
                    durable_paths = [
                        path for path in (seen_path, work_path, result_path) if path.is_file()
                    ]
                    self.git.sync_paths(
                        durable_paths, f"bridge confirm result {request_id}"
                    )
                    return existing
            else:
                conflict = (
                    self.repo_root / CONFLICT_ROOT / f"{request_id}-{request_sha[:16]}.json"
                )
                payload = {
                    "schema_version": 1,
                    "service_version": SERVICE_VERSION,
                    "request_id": request_id,
                    "request_sha256": request_sha,
                    "status": "blocked",
                    "outcome": "duplicate_conflict",
                    "request_submission_attempted": False,
                    "ambiguity": None,
                    "blocked": {
                        "code": "duplicate_request_id_conflict",
                        "safe_message": "request_id was already used for different immutable bytes",
                    },
                    "queue": {"path": queue_path, "commit": queue_commit},
                    "processed_at_utc": _utc_now(),
                }
                _atomic_json(conflict, payload)
                self.git.sync_paths([conflict], f"bridge duplicate conflict {request_id}")
                return payload

        if seen_path.is_file():
            seen = json.loads(seen_path.read_text(encoding="utf-8"))
            if seen.get("request_sha256") != request_sha:
                raise BridgeBlocked(
                    "duplicate_request_id_conflict",
                    "request_id was durably claimed for different immutable bytes",
                )
        else:
            _atomic_json(
                seen_path,
                {
                    "schema_version": 1,
                    "request_id": request_id,
                    "request_sha256": request_sha,
                    "queue_path": queue_path,
                    "queue_commit": queue_commit,
                    "first_seen_at_utc": _utc_now(),
                },
            )
        _atomic_json(
            work_path,
            {
                "schema_version": 1,
                "request_id": request_id,
                "request_sha256": request_sha,
                "status": "processing",
                "queue_path": queue_path,
                "queue_commit": queue_commit,
                "updated_at_utc": _utc_now(),
            },
        )
        self.git.sync_paths([seen_path, work_path], f"bridge claim request {request_id}")

        request: BridgeRequest | None = None
        try:
            request = parse_request(raw, expected_request_id=request_id)
            operation_result = self.executor.execute(request)
            payload: dict[str, object] = {
                "schema_version": 1,
                "service_version": SERVICE_VERSION,
                "request_id": request_id,
                "request_sha256": request_sha,
                "operation": request.operation,
                **operation_result,
            }
        except RequestValidationError as exc:
            payload = {
                "schema_version": 1,
                "service_version": SERVICE_VERSION,
                "request_id": request_id,
                "request_sha256": request_sha,
                "operation": None,
                "status": "invalid",
                "outcome": "rejected",
                "request_submission_attempted": False,
                "ambiguity": None,
                "blocked": {"code": exc.code, "safe_message": _safe_message(exc)},
            }
        except BridgeBlocked as exc:
            ambiguity = exc.details.get("ambiguity")
            if not isinstance(ambiguity, dict):
                ambiguity = (
                    _ambiguous_state(
                        self.repo_root,
                        request,
                        request.source.text_sha256,
                    )
                    if exc.ambiguous and request is not None and request.source is not None
                    else None
                )
            payload = {
                "schema_version": 1,
                "service_version": SERVICE_VERSION,
                "request_id": request_id,
                "request_sha256": request_sha,
                "operation": request.operation if request is not None else None,
                "status": "ambiguous" if exc.ambiguous else "blocked",
                "outcome": "blocked",
                "request_submission_attempted": None if exc.ambiguous else False,
                "input": _declared_input(request),
                "ambiguity": ambiguity
                if ambiguity is not None
                else {
                    "state": "action_may_have_happened",
                    "recover_before_repeat_required": True,
                }
                if exc.ambiguous
                else None,
                "blocked": {"code": exc.code, "safe_message": _safe_message(exc)},
            }
        except Exception as exc:
            ambiguity = (
                _ambiguous_state(
                    self.repo_root,
                    request,
                    request.source.text_sha256,
                )
                if request is not None and request.source is not None
                else None
            )
            payload = {
                "schema_version": 1,
                "service_version": SERVICE_VERSION,
                "request_id": request_id,
                "request_sha256": request_sha,
                "operation": request.operation if request is not None else None,
                "status": "ambiguous" if ambiguity is not None else "failed",
                "outcome": "blocked" if ambiguity is not None else "failed",
                "request_submission_attempted": None if ambiguity is not None else False,
                "input": _declared_input(request),
                "ambiguity": ambiguity,
                "blocked": {
                    "code": "unexpected_bridge_failure",
                    "safe_message": _safe_message(f"{type(exc).__name__}: {exc}"),
                },
            }
        payload["queue"] = {"path": queue_path, "commit": queue_commit}
        payload["processed_at_utc"] = _utc_now()
        _atomic_json(result_path, payload)
        _atomic_json(
            work_path,
            {
                "schema_version": 1,
                "request_id": request_id,
                "request_sha256": request_sha,
                "status": "published",
                "result_path": result_path.relative_to(self.repo_root).as_posix(),
                "updated_at_utc": _utc_now(),
            },
        )
        self.git.sync_paths(
            [seen_path, work_path, result_path], f"bridge publish result {request_id}"
        )
        return payload


class _BridgeLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.handle: Any | None = None

    def __enter__(self) -> "_BridgeLock":
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.handle = self.path.open("a+")
        try:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            self.handle.close()
            raise BridgeBlocked("bridge_already_running", "another bridge process holds the lock") from exc
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.handle is not None:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
            self.handle.close()


class BridgeDaemon:
    def __init__(
        self,
        repo_root: Path,
        *,
        queue: QueueReader | None = None,
        worker: BridgeWorker | None = None,
        result_branch: str = RESULT_BRANCH,
        require_trusted_origin: bool = True,
        lock_path: Path | None = None,
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.git = GitSync(self.repo_root, require_remote=True)
        executor = BridgeExecutor(self.repo_root)
        self.queue = queue or QueueReader(self.repo_root)
        self.worker = worker or BridgeWorker(self.repo_root, executor, git_sync=self.git)
        self.result_branch = result_branch
        self.require_trusted_origin = require_trusted_origin
        self.lock_path = lock_path or Path.home() / ".cache" / "pangram-local" / "gui-bridge.lock"

    def _preflight(self) -> None:
        branch = self.git.current_branch()
        if branch != self.result_branch:
            raise BridgeBlocked(
                "result_branch_mismatch",
                f"bridge must run on fixed result branch {self.result_branch}; found {branch}",
            )
        if self.require_trusted_origin:
            origin = _run_git(self.repo_root, ["remote", "get-url", "origin"]).strip()
            if origin not in _TRUSTED_ORIGIN_URLS:
                raise BridgeBlocked("untrusted_origin", "origin is not the fixed trusted tooling repository")
        self.git.ensure_remote_durable("bridge result preflight")

    def once(self) -> dict[str, object]:
        with _BridgeLock(self.lock_path):
            self._preflight()
            batch = self.queue.poll()
            results: list[dict[str, object]] = []
            for path in batch.request_paths:
                raw = self.queue.read(batch.head_commit, path)
                results.append(self.worker.process(path, batch.head_commit, raw))
            retryable = any(
                result.get("status") in {"ambiguous", "failed"} for result in results
            )
            cursor_advanced = False
            if not retryable and (
                batch.previous_commit != batch.head_commit
                or not self.queue.cursor_path.is_file()
            ):
                cursor = self.queue.write_cursor(batch.head_commit)
                self.git.sync_paths(
                    [cursor], f"bridge queue cursor {batch.head_commit[:12]}"
                )
                cursor_advanced = True
            return {
                "queue_head": batch.head_commit,
                "processed": len(results),
                "results": results,
                "cursor_advanced": cursor_advanced,
                "retryable_block": retryable,
            }


def _repository_root() -> Path:
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode:
        raise BridgeError("pangram-gui-bridge must run inside the tooling repository")
    return Path(completed.stdout.strip()).resolve()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pangram-gui-bridge",
        description="Fixed-schema GitHub mailbox to local headed Pangram GUI bridge.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("once", help="Poll and process the append-only request queue once.")
    daemon = sub.add_parser("daemon", help="Run persistently in the graphical user session.")
    daemon.add_argument("--poll-seconds", type=int, default=20)
    validate = sub.add_parser("validate", help="Validate one local request file without executing it.")
    validate.add_argument("path", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "validate":
        raw = args.path.read_bytes()
        request = parse_request(raw, expected_request_id=args.path.stem)
        print(
            json.dumps(
                {
                    "valid": True,
                    "request_id": request.request_id,
                    "operation": request.operation,
                    "request_sha256": _sha256_bytes(raw),
                },
                sort_keys=True,
            ),
            flush=True,
        )
        return 0

    daemon = BridgeDaemon(_repository_root())
    if args.command == "once":
        print(json.dumps(daemon.once(), ensure_ascii=False, sort_keys=True), flush=True)
        return 0

    if args.poll_seconds < 5 or args.poll_seconds > 3600:
        raise BridgeError("--poll-seconds must be between 5 and 3600")
    while True:
        try:
            outcome = daemon.once()
            if outcome["processed"]:
                print(json.dumps(outcome, ensure_ascii=False, sort_keys=True), flush=True)
        except (BridgeError, GitSyncError) as exc:
            print(
                json.dumps(
                    {
                        "status": "blocked",
                        "code": getattr(exc, "code", "git_sync_blocked"),
                        "safe_message": _safe_message(exc),
                        "at_utc": _utc_now(),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
