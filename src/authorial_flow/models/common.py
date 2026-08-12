from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
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
