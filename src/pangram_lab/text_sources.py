from __future__ import annotations

import base64
import hashlib
import json
import re
import urllib.request
from copy import deepcopy
from typing import Any, Callable

_GITHUB_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_GIT_BLOB_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_TEXT_BYTES = 2_000_000


class TextSourceError(ValueError):
    pass


def validate_text_source(source: object) -> dict[str, str]:
    if not isinstance(source, dict):
        raise TextSourceError("text_source must be an object")
    expected_keys = {"kind", "repository", "blob_sha", "text_sha256"}
    if set(source) != expected_keys:
        raise TextSourceError(
            f"text_source keys must equal {sorted(expected_keys)}"
        )
    kind = source.get("kind")
    repository = source.get("repository")
    blob_sha = source.get("blob_sha")
    text_sha256 = source.get("text_sha256")
    if kind != "github_blob":
        raise TextSourceError("text_source kind must equal github_blob")
    if not isinstance(repository, str) or not _GITHUB_REPOSITORY_RE.fullmatch(repository):
        raise TextSourceError("text_source repository must be owner/name")
    if not isinstance(blob_sha, str) or not _GIT_BLOB_RE.fullmatch(blob_sha):
        raise TextSourceError("text_source blob_sha must be 40 lowercase hexadecimal characters")
    if not isinstance(text_sha256, str) or not _SHA256_RE.fullmatch(text_sha256):
        raise TextSourceError("text_source text_sha256 must be 64 lowercase hexadecimal characters")
    return {
        "kind": kind,
        "repository": repository,
        "blob_sha": blob_sha,
        "text_sha256": text_sha256,
    }


def fetch_github_blob_text(source: dict[str, str]) -> str:
    source = validate_text_source(source)
    repository = source["repository"]
    blob_sha = source["blob_sha"]
    url = f"https://api.github.com/repos/{repository}/git/blobs/{blob_sha}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "pangram-humanization-lab-fixed-batch",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read(MAX_TEXT_BYTES * 2)
    except Exception as exc:  # pragma: no cover - network-specific error classes vary
        raise TextSourceError(f"cannot fetch immutable GitHub blob {repository}@{blob_sha}: {exc}") from exc
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TextSourceError("GitHub blob response is not valid UTF-8 JSON") from exc
    if not isinstance(payload, dict) or payload.get("sha") != blob_sha or payload.get("encoding") != "base64":
        raise TextSourceError("GitHub blob response identity/encoding mismatch")
    encoded = payload.get("content")
    if not isinstance(encoded, str):
        raise TextSourceError("GitHub blob response has no base64 content")
    try:
        content = base64.b64decode(encoded.replace("\n", ""), validate=True)
    except Exception as exc:
        raise TextSourceError("GitHub blob response contains invalid base64") from exc
    if len(content) > MAX_TEXT_BYTES:
        raise TextSourceError(f"resolved text exceeds {MAX_TEXT_BYTES} byte limit")
    actual_sha = hashlib.sha256(content).hexdigest()
    if actual_sha != source["text_sha256"]:
        raise TextSourceError(
            f"resolved text SHA-256 mismatch: expected {source['text_sha256']}, got {actual_sha}"
        )
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TextSourceError("resolved GitHub blob is not UTF-8 text") from exc
    if not text:
        raise TextSourceError("resolved GitHub blob text is empty")
    return text


def resolve_text_sources(
    spec: dict[str, Any],
    *,
    fetcher: Callable[[dict[str, str]], str] = fetch_github_blob_text,
) -> dict[str, Any]:
    resolved = deepcopy(spec)
    for variant in resolved.get("variants", []):
        if not isinstance(variant, dict) or "text_source" not in variant:
            continue
        source = validate_text_source(variant["text_source"])
        text = fetcher(source)
        if not isinstance(text, str) or not text:
            raise TextSourceError("text source fetcher returned empty/non-string text")
        actual_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if actual_sha != source["text_sha256"]:
            raise TextSourceError(
                f"resolved text SHA-256 mismatch: expected {source['text_sha256']}, got {actual_sha}"
            )
        variant["text"] = text
    return resolved
