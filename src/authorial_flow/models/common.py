from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
from enum import StrEnum
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_request_id(provider: str, role: str, prompt: str, schema: dict | None, model: str = "") -> str:
    payload = canonical_json({
        "provider": provider,
        "role": role,
        "model": model,
        "prompt": prompt,
        "schema": schema or {},
    })
    return sha256(payload.encode("utf-8")).hexdigest()


def extract_json_object(text: str) -> dict:
    decoder = json.JSONDecoder()
    matches: list[dict] = []
    i = 0
    while i < len(text):
        j = text.find("{", i)
        if j < 0:
            break
        try:
            value, end = decoder.raw_decode(text[j:])
        except json.JSONDecodeError:
            i = j + 1
            continue
        if isinstance(value, dict):
            matches.append(value)
        i = j + max(1, end)
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one JSON object; found {len(matches)}")
    return matches[0]


def validate_json_schema(value: Any, schema: dict | None) -> None:
    """Small fail-closed validator for the JSON-schema features used by this project.

    Full Pydantic models validate at higher-level call sites. This catches the common schema
    contract before a result enters graph state without adding another runtime dependency.
    """
    if not schema:
        return
    typ = schema.get("type")
    if typ == "object":
        if not isinstance(value, dict):
            raise ValueError("schema requires object")
        for key in schema.get("required", []):
            if key not in value:
                raise ValueError(f"missing required field: {key}")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = set(value) - set(props)
            if extra:
                raise ValueError(f"unexpected fields: {sorted(extra)}")
        for key, child in props.items():
            if key in value:
                validate_json_schema(value[key], child)
    elif typ == "array":
        if not isinstance(value, list):
            raise ValueError("schema requires array")
        item_schema = schema.get("items")
        if item_schema:
            for item in value:
                validate_json_schema(item, item_schema)
    elif typ == "string" and not isinstance(value, str):
        raise ValueError("schema requires string")
    elif typ == "integer" and (not isinstance(value, int) or isinstance(value, bool)):
        raise ValueError("schema requires integer")
    elif typ == "number" and (not isinstance(value, (int, float)) or isinstance(value, bool)):
        raise ValueError("schema requires number")
    elif typ == "boolean" and not isinstance(value, bool):
        raise ValueError("schema requires boolean")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"value {value!r} not in enum")


class FailureKind(StrEnum):
    AUTH = "AUTH"
    UNSUPPORTED_MODEL = "UNSUPPORTED_MODEL"
    INVALID_SCHEMA = "INVALID_SCHEMA"
    STRUCTURED_CONTRACT = "STRUCTURED_CONTRACT"
    TRANSIENT = "TRANSIENT"
    UNKNOWN = "UNKNOWN"


def validate_schema_contract(schema: dict | None) -> None:
    """Validate the local subset before paying for a provider attempt."""
    if schema is None:
        return
    if not isinstance(schema, dict):
        raise ValueError("schema must be an object")

    def walk(node: Any, path: str) -> None:
        if not isinstance(node, dict):
            raise ValueError(f"{path} must be an object")
        typ = node.get("type")
        if typ is not None and typ not in {"object", "array", "string", "integer", "number", "boolean", "null"}:
            raise ValueError(f"{path}.type is unsupported")
        if typ == "object":
            props = node.get("properties", {})
            required = node.get("required", [])
            if not isinstance(props, dict) or not isinstance(required, list):
                raise ValueError(f"{path} object contract is malformed")
            if any(not isinstance(item, str) for item in required):
                raise ValueError(f"{path}.required must contain strings")
            for key, child in props.items():
                walk(child, f"{path}.properties.{key}")
        if typ == "array" and "items" in node:
            walk(node["items"], f"{path}.items")
        if "enum" in node and (not isinstance(node["enum"], list) or not node["enum"]):
            raise ValueError(f"{path}.enum must be a non-empty list")
        for combiner in ("anyOf", "oneOf", "allOf"):
            if combiner in node:
                values = node[combiner]
                if not isinstance(values, list) or not values:
                    raise ValueError(f"{path}.{combiner} must be a non-empty list")
                for index, child in enumerate(values):
                    walk(child, f"{path}.{combiner}[{index}]")
        definitions = node.get("$defs", {})
        if definitions:
            if not isinstance(definitions, dict):
                raise ValueError(f"{path}.$defs must be an object")
            for key, child in definitions.items():
                walk(child, f"{path}.$defs.{key}")
        if "$ref" in node and not isinstance(node["$ref"], str):
            raise ValueError(f"{path}.$ref must be a string")

    walk(schema, "root")


def capability_signature(provider: str, model: str, schema: dict | None) -> str:
    payload = canonical_json({
        "provider": str(provider),
        "model": str(model),
        "structured": schema is not None,
        "schema_sha256": sha256(canonical_json(schema or {}).encode("utf-8")).hexdigest(),
    })
    return sha256(payload.encode("utf-8")).hexdigest()


def unique_model_profiles(models: list[Any]) -> list[Any]:
    unique: list[Any] = []
    seen: set[str] = set()
    for model in models:
        key = "<CLI_DEFAULT>" if model is None else str(model)
        if key in seen:
            continue
        seen.add(key)
        unique.append(model)
    return unique


def classify_attempt_failure(*, returncode: int, stdout: str, stderr: str, error: str) -> FailureKind:
    text = " ".join((str(stdout or ""), str(stderr or ""), str(error or ""))).lower()
    if re.search(r"\b(401|403)\b|unauthori[sz]ed|authentication|invalid api key|login required|not logged in", text):
        return FailureKind.AUTH
    if "model does not exist" in text or "model not found" in text or "unsupported model" in text:
        return FailureKind.UNSUPPORTED_MODEL
    if "invalid json schema" in text or "schema is invalid" in text or "unsupported schema" in text:
        return FailureKind.INVALID_SCHEMA
    if any(token in text for token in (
        "parse/schema", "structured output", "missing structured output",
        "expected exactly one json", "missing required field", "schema requires",
    )):
        return FailureKind.STRUCTURED_CONTRACT
    transient_tokens = (
        "timed out", "timeout", "rate limit", "429", "overloaded", "capacity",
        "temporarily unavailable", "service unavailable", "internal server error",
        "bad gateway", "connection reset", "connection refused", "connection error",
        "stream disconnected", "error sending request", "network is unreachable",
        "name or service not known", "temporary failure in name resolution",
        "dns error", "tls handshake",
    )
    if any(token in text for token in transient_tokens) or re.search(r"\b(500|502|503|504)\b", text):
        return FailureKind.TRANSIENT
    return FailureKind.UNKNOWN


def stops_provider_fallback(kind: FailureKind) -> bool:
    return kind in {FailureKind.AUTH, FailureKind.INVALID_SCHEMA}


@dataclass(frozen=True)
class ModelCall:
    prompt: str
    schema: dict | None
    role: str
    request_id: str | None = None


@dataclass(frozen=True)
class ModelAttempt:
    model: str
    returncode: int
    stdout_ref: str = ""
    stderr_ref: str = ""
    error: str = ""
    failure_kind: str = ""
    capability_signature: str = ""


@dataclass(frozen=True)
class ModelResult:
    provider: str
    role: str
    request_id: str
    model: str
    cli_version: str
    parsed: Any
    text: str
    stdout_ref: str
    stderr_ref: str
    attempts: tuple[ModelAttempt, ...] = field(default_factory=tuple)


class ProviderFailure(RuntimeError):
    def __init__(self, provider: str, role: str, request_id: str, attempts: list[ModelAttempt], *, schema: dict | None = None):
        self.provider = provider
        self.role = role
        self.request_id = request_id
        self.attempts = tuple(attempts)
        self.schema = dict(schema or {})
        super().__init__(f"{provider} provider failed for role={role} after {len(attempts)} attempt(s); request_id={request_id[:12]}")
