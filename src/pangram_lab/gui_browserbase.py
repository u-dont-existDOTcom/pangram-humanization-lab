from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


RUNNER_VERSION = "pangram-gui-browserbase-v1"
MODEL_ID = "pangram-4"
BROWSERBASE_API_ROOT = "https://api.browserbase.com/v1"
PANGRAM_LOGIN_URL = "https://www.pangram.com/login"
DEFAULT_PANGRAM_GUI_URL = "https://www.pangram.com/"

_SEGMENT_LABELS = (
    "Fully AI Generated",
    "Moderately AI Assisted",
    "Lightly AI Assisted",
    "Human Written",
)
_SUMMARY_FIELDS = {
    "AI Generated": "fraction_ai",
    "Moderately AI Assisted": "fraction_moderately_ai_assisted",
    "Lightly AI Assisted": "fraction_lightly_ai_assisted",
    "Human Written": "fraction_human",
}
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_SEGMENT_HEADER_RE = re.compile(
    r"(?P<label>Fully\s+AI\s+Generated|Moderately\s+AI\s+Assisted|Lightly\s+AI\s+Assisted|Human\s+Written)"
    r"\s*(?:[|•·—–-]\s*)?"
    r"(?P<words>\d[\d,]*)\s+Words?"
    r"(?:\s*(?:[|•·—–-]\s*)?(?P<confidence>High|Medium|Low)\s+Confidence)?",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class BrowserbaseConfig:
    api_key: str
    context_id: str | None
    project_id: str | None
    pangram_url: str = DEFAULT_PANGRAM_GUI_URL

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        *,
        require_context: bool,
        require_project_if_context_missing: bool = False,
    ) -> "BrowserbaseConfig":
        values: Mapping[str, str] = os.environ if env is None else env
        api_key = values.get("BROWSERBASE_API_KEY", "").strip()
        context_id = values.get("BROWSERBASE_CONTEXT_ID", "").strip() or None
        project_id = values.get("BROWSERBASE_PROJECT_ID", "").strip() or None
        pangram_url = values.get("PANGRAM_GUI_URL", DEFAULT_PANGRAM_GUI_URL).strip() or DEFAULT_PANGRAM_GUI_URL

        if not api_key:
            raise RuntimeError("BROWSERBASE_API_KEY is required")
        if require_context and not context_id:
            raise RuntimeError("BROWSERBASE_CONTEXT_ID is required for unattended GUI runs")
        if require_project_if_context_missing and not context_id and not project_id:
            raise RuntimeError("BROWSERBASE_PROJECT_ID is required to create a Browserbase Context")
        return cls(
            api_key=api_key,
            context_id=context_id,
            project_id=project_id,
            pangram_url=pangram_url,
        )


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def measurement_dir(root: Path, input_sha256: str) -> Path:
    if not _HEX64_RE.fullmatch(input_sha256):
        raise ValueError("input_sha256 must be 64 lowercase hexadecimal characters")
    return root / MODEL_ID / input_sha256


def completed_result_exists(root: Path, input_sha256: str) -> bool:
    receipt = measurement_dir(root, input_sha256) / "result.json"
    if not receipt.is_file():
        return False
    try:
        value = json.loads(receipt.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    return (
        isinstance(value, dict)
        and value.get("status") == "complete"
        and value.get("runner_version") == RUNNER_VERSION
    )


def build_context_payload(project_id: str) -> dict[str, str]:
    project_id = project_id.strip()
    if not project_id:
        raise ValueError("project_id is required")
    return {"projectId": project_id}


def build_session_payload(
    context_id: str,
    *,
    persist: bool,
    keep_alive: bool,
    timeout: int,
    user_metadata: dict[str, str],
) -> dict[str, object]:
    if not context_id.strip():
        raise ValueError("context_id is required")
    if timeout < 60 or timeout > 21600:
        raise ValueError("timeout must be between 60 and 21600 seconds")
    return {
        "browserSettings": {
            "context": {
                "id": context_id,
                "persist": bool(persist),
            }
        },
        "keepAlive": bool(keep_alive),
        "timeout": timeout,
        "userMetadata": dict(user_metadata),
    }


class BrowserbaseRestClient:
    def __init__(self, api_key: str, *, api_root: str = BROWSERBASE_API_ROOT) -> None:
        api_key = api_key.strip()
        if not api_key:
            raise ValueError("Browserbase API key is required")
        self._api_key = api_key
        self._api_root = api_root.rstrip("/")

    def _request(self, method: str, path: str, payload: dict[str, object] | None = None) -> dict[str, Any]:
        url = f"{self._api_root}/{path.lstrip('/')}"
        data = None
        headers = {"X-BB-API-Key": self._api_key}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Browserbase HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Browserbase transport error: {exc.reason}") from exc
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("Browserbase returned invalid JSON") from exc
        if not isinstance(decoded, dict):
            raise RuntimeError("Browserbase returned an unexpected non-object response")
        return decoded

    def create_context(self, project_id: str) -> dict[str, Any]:
        return self._request("POST", "contexts", build_context_payload(project_id))

    def create_session(
        self,
        context_id: str,
        *,
        persist: bool,
        keep_alive: bool,
        timeout: int,
        user_metadata: dict[str, str],
    ) -> dict[str, Any]:
        payload = build_session_payload(
            context_id,
            persist=persist,
            keep_alive=keep_alive,
            timeout=timeout,
            user_metadata=user_metadata,
        )
        return self._request("POST", "sessions", payload)

    def debug_urls(self, session_id: str) -> dict[str, Any]:
        session_id = session_id.strip()
        if not session_id:
            raise ValueError("session_id is required")
        return self._request("GET", f"sessions/{session_id}/debug")


def _canonical_label(raw: str) -> str:
    compact = " ".join(raw.split()).lower()
    for label in _SEGMENT_LABELS:
        if compact == label.lower():
            return label
    raise ValueError(f"unknown Pangram segment label: {raw!r}")


def _summary_fraction(summary_text: str, label: str) -> float | None:
    escaped = re.escape(label)
    patterns = (
        rf"(?P<percent>\d+(?:\.\d+)?)\s*%\s*(?:of\s+the\s+document\s*)?{escaped}",
        rf"{escaped}\s*(?:[:|•·—–-]\s*)?(?P<percent>\d+(?:\.\d+)?)\s*%",
    )
    for pattern in patterns:
        match = re.search(pattern, summary_text, flags=re.IGNORECASE)
        if match:
            return float(match.group("percent")) / 100.0
    return None


def _clean_segment_text(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"^[\s|•·—–-]+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_report_text(body: str) -> dict[str, Any]:
    """Parse Pangram GUI report text without inventing fields the GUI did not expose."""
    marker = re.search(r"\bAnalyzed\s+Text\b", body, flags=re.IGNORECASE)
    if marker:
        summary_text = body[: marker.start()]
        segment_text = body[marker.end() :]
    else:
        summary_text = body
        segment_text = body

    summary: dict[str, float | None] = {
        "fraction_ai": None,
        "fraction_moderately_ai_assisted": None,
        "fraction_lightly_ai_assisted": None,
        "fraction_human": None,
    }
    for label, field in _SUMMARY_FIELDS.items():
        summary[field] = _summary_fraction(summary_text, label)

    matches = list(_SEGMENT_HEADER_RE.finditer(segment_text))
    segments: list[dict[str, object]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(segment_text)
        segment_body = _clean_segment_text(segment_text[match.end() : end])
        confidence = match.group("confidence")
        segments.append(
            {
                "label": _canonical_label(match.group("label")),
                "word_count": int(match.group("words").replace(",", "")),
                "confidence": confidence.title() if confidence else None,
                "text": segment_body,
            }
        )

    return {"summary": summary, "segments": segments}


def _load_playwright() -> Any:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - exercised only in live browser runs
        raise RuntimeError(
            "Playwright is not installed. Install the optional browser dependencies with "
            "python -m pip install -e '.[browser]'."
        ) from exc
    return sync_playwright


def _first_visible(page: Any, selectors: tuple[str, ...]) -> Any:
    for selector in selectors:
        locator = page.locator(selector)
        count = locator.count()
        for index in range(count):
            candidate = locator.nth(index)
            try:
                if candidate.is_visible():
                    return candidate
            except Exception:
                continue
    return None


def detector_input(page: Any) -> Any:
    locator = _first_visible(
        page,
        (
            "textarea",
            '[contenteditable="true"]',
            '[role="textbox"]',
        ),
    )
    if locator is None:
        raise RuntimeError("Pangram detector text input was not found; login may have expired or the UI changed")
    return locator


def detection_button(page: Any) -> Any:
    name_pattern = re.compile(r"^(?:check(?:\s+for)?\s+ai|scan(?:\s+for)?\s+ai|detect(?:\s+ai)?|analyze)$", re.IGNORECASE)
    locator = page.get_by_role("button", name=name_pattern)
    for index in range(locator.count()):
        candidate = locator.nth(index)
        try:
            if candidate.is_visible() and candidate.is_enabled():
                return candidate
        except Exception:
            continue
    raise RuntimeError("Pangram detection action was not found; refusing to click an unbounded fallback")


def wait_for_report(page: Any, *, timeout_ms: int = 180_000) -> None:
    markers = ("Authorship Breakdown", "Analyzed Text")
    last_error: Exception | None = None
    slice_ms = max(5_000, timeout_ms // len(markers))
    for marker in markers:
        try:
            page.get_by_text(marker, exact=False).first.wait_for(state="visible", timeout=slice_ms)
            return
        except Exception as exc:  # Playwright timeout type is optional at import time
            last_error = exc
    raise RuntimeError("Pangram report did not become visible before timeout") from last_error


def _connect_session(connect_url: str) -> tuple[Any, Any, Any]:
    sync_playwright = _load_playwright()
    playwright = sync_playwright().start()
    try:
        browser = playwright.chromium.connect_over_cdp(connect_url)
    except Exception:
        playwright.stop()
        raise
    contexts = browser.contexts
    if not contexts:
        browser.close()
        playwright.stop()
        raise RuntimeError("Browserbase session exposed no default browser context")
    context = contexts[0]
    pages = context.pages
    page = pages[0] if pages else context.new_page()
    return playwright, browser, page


def bootstrap_login(config: BrowserbaseConfig, *, input_fn: Any = input, print_fn: Any = print) -> dict[str, object]:
    client = BrowserbaseRestClient(config.api_key)
    context_id = config.context_id
    if context_id is None:
        if config.project_id is None:
            raise RuntimeError("BROWSERBASE_PROJECT_ID is required to create a Browserbase Context")
        context = client.create_context(config.project_id)
        context_id = str(context.get("id", "")).strip()
        if not context_id:
            raise RuntimeError("Browserbase did not return a Context ID")

    session = client.create_session(
        context_id,
        persist=True,
        keep_alive=True,
        timeout=1800,
        user_metadata={"task": "pangram-gui-bootstrap"},
    )
    session_id = str(session.get("id", "")).strip()
    connect_url = str(session.get("connectUrl", "")).strip()
    if not session_id or not connect_url:
        raise RuntimeError("Browserbase session response is missing id/connectUrl")
    debug = client.debug_urls(session_id)
    debugger_url = str(debug.get("debuggerUrl", "")).strip()

    playwright, browser, page = _connect_session(connect_url)
    try:
        page.goto(PANGRAM_LOGIN_URL, wait_until="domcontentloaded")
        print_fn(f"Browserbase Context ID: {context_id}")
        print_fn(f"Live debugger URL: {debugger_url}")
        input_fn("Open the debugger URL, finish Pangram login, then press Enter here to verify: ")
        page.goto(config.pangram_url, wait_until="domcontentloaded")
        detector_input(page)
    finally:
        browser.close()
        playwright.stop()

    return {
        "context_id": context_id,
        "session_id": session_id,
        "debugger_url": debugger_url,
        "verified": True,
    }
