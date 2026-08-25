from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlsplit


RUNNER_VERSION = "pangram-gui-browserbase-v1"
MODEL_ID = "pangram-4"
BROWSERBASE_API_ROOT = "https://api.browserbase.com/v1"
PANGRAM_LOGIN_URL = "https://www.pangram.com/login"
DEFAULT_PANGRAM_GUI_URL = "https://www.pangram.com/dashboard"

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
    pangram_url: str = DEFAULT_PANGRAM_GUI_URL

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        *,
        require_context: bool,
        context_id_path: Path | None = None,
    ) -> "BrowserbaseConfig":
        values: Mapping[str, str] = os.environ if env is None else env
        api_key = values.get("BROWSERBASE_API_KEY", "").strip()
        context_id = values.get("BROWSERBASE_CONTEXT_ID", "").strip() or None
        if context_id is None and context_id_path is not None:
            context_id = load_context_id(context_id_path)
        pangram_url = values.get("PANGRAM_GUI_URL", DEFAULT_PANGRAM_GUI_URL).strip() or DEFAULT_PANGRAM_GUI_URL

        if not api_key:
            raise RuntimeError("BROWSERBASE_API_KEY is required")
        if require_context and not context_id:
            raise RuntimeError("BROWSERBASE_CONTEXT_ID is required for unattended GUI runs")
        return cls(
            api_key=api_key,
            context_id=context_id,
            pangram_url=pangram_url,
        )


def load_context_id(path: Path) -> str | None:
    try:
        context_id = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(f"cannot read saved Browserbase Context ID from {path}: {exc}") from exc
    return context_id or None


def save_context_id(path: Path, context_id: str) -> None:
    context_id = context_id.strip()
    if not context_id:
        raise ValueError("Browserbase Context ID is required")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.parent.chmod(0o700)
    path.write_text(context_id + "\n", encoding="utf-8")
    path.chmod(0o600)


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


def ambiguous_submission_exists(root: Path, input_sha256: str) -> bool:
    receipt = measurement_dir(root, input_sha256) / "failure.json"
    if not receipt.is_file():
        return False
    try:
        value = json.loads(receipt.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    return (
        isinstance(value, dict)
        and value.get("status") == "failed"
        and value.get("runner_version") == RUNNER_VERSION
        and value.get("detector_submission_attempted") is True
    )


def unresolved_paid_reservation_exists(root: Path, input_sha256: str) -> bool:
    directory = measurement_dir(root, input_sha256)
    if (directory / "result.json").is_file():
        return False
    failure = directory / "failure.json"
    if failure.is_file():
        try:
            failure_value = json.loads(failure.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            failure_value = None
        if (
            isinstance(failure_value, dict)
            and failure_value.get("status") == "failed"
            and failure_value.get("detector_submission_attempted") is False
        ):
            return False
    reservation = directory / "reservation.json"
    if not reservation.is_file():
        return False
    try:
        value = json.loads(reservation.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return True
    return isinstance(value, dict) and value.get("status") == "reserved"


def artifact_paths(directory: Path) -> dict[str, Path]:
    return {
        "result": directory / "result.json",
        "body": directory / "report-body.txt",
        "pdf": directory / "report.pdf",
        "failure": directory / "failure.json",
        "failure_screenshot": directory / "failure.png",
    }


def prepare_measurement(input_path: Path, *, output_root: Path, force: bool) -> dict[str, object]:
    try:
        text = input_path.read_bytes().decode("utf-8")
    except OSError as exc:
        raise RuntimeError(f"cannot read Pangram GUI input {input_path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"Pangram GUI input must be UTF-8: {input_path}") from exc
    digest = sha256_text(text)
    directory = measurement_dir(output_root, digest)
    return {
        "input_path": str(input_path),
        "text": text,
        "input_sha256": digest,
        "word_count": len(text.split()),
        "directory": str(directory),
        "skip": completed_result_exists(output_root, digest) and not force,
        "blocked_by_ambiguous_submission": (
            ambiguous_submission_exists(output_root, digest)
            or unresolved_paid_reservation_exists(output_root, digest)
        )
        and not force,
    }


def build_complete_receipt(
    *,
    input_path: str,
    input_sha256: str,
    word_count: int,
    session_id: str,
    debugger_url: str,
    report_url: str,
    pdf_provenance: str,
    parsed: dict[str, object],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "complete",
        "runner_version": RUNNER_VERSION,
        "model": MODEL_ID,
        "input_path": input_path,
        "input_sha256": input_sha256,
        "word_count": word_count,
        "browserbase_session_id": session_id,
        "browserbase_debugger_url": debugger_url,
        "browserbase_recording_url": f"https://browserbase.com/sessions/{session_id}",
        "report_url": report_url,
        "pdf_provenance": pdf_provenance,
        "parsed": parsed,
    }


def build_context_payload() -> dict[str, object]:
    return {}


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

    def create_context(self) -> dict[str, Any]:
        return self._request("POST", "contexts", build_context_payload())

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


def select_live_view_url(debug_response: Mapping[str, Any]) -> str:
    """Return Browserbase's human-control Live View, preferring fullscreen."""
    for field in ("debuggerFullscreenUrl", "debuggerUrl"):
        url = str(debug_response.get(field, "")).strip()
        if url:
            return url
    raise RuntimeError("Browserbase debug response is missing a Live View URL")


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


def clean_report_body_artifact(body: str) -> str:
    """Remove non-visible end-of-line whitespace while preserving text and line structure."""
    terminal_newline = body.endswith(("\n", "\r"))
    cleaned = "\n".join(line.rstrip() for line in body.splitlines())
    return cleaned + ("\n" if terminal_newline else "")


def parse_report_for_exact_input(
    body: str,
    exact_text: str,
    *,
    expected_word_count: int,
) -> dict[str, Any]:
    """Parse a segmented report or Pangram's bounded short-text Overview layout."""
    parsed = parse_report_text(body)
    if parsed["segments"]:
        return parsed

    normalized_body = " ".join(body.split())
    normalized_exact = " ".join(exact_text.split())
    words_match = re.search(r"\b(?P<words>\d[\d,]*)\s+words?\s+scanned\b", normalized_body, re.IGNORECASE)
    percent_match = re.search(
        r"(?P<percent>\d+(?:\.\d+)?)\s*%\s*of\s+this\s+text\s+is\s+AI\b",
        normalized_body,
        re.IGNORECASE,
    )
    is_entirely_ai = re.search(
        r"\bWe\s+believe\s+that\s+this\s+entire\s+text\s+is\s+AI\b",
        normalized_body,
        re.IGNORECASE,
    )
    if not (
        normalized_exact
        and normalized_exact.casefold() in normalized_body.casefold()
        and re.search(r"\bAI\s+Generated\b", normalized_body, re.IGNORECASE)
        and words_match
        and int(words_match.group("words").replace(",", "")) == expected_word_count
        and percent_match
        and float(percent_match.group("percent")) == 100.0
        and is_entirely_ai
    ):
        return parsed

    return {
        "summary": {
            "fraction_ai": 1.0,
            "fraction_moderately_ai_assisted": 0.0,
            "fraction_lightly_ai_assisted": 0.0,
            "fraction_human": 0.0,
        },
        "segments": [
            {
                "label": "Fully AI Generated",
                "word_count": expected_word_count,
                "confidence": None,
                "text": exact_text,
            }
        ],
        "report_layout": "short_text_overview",
        "confidence_note": "Confidence limited — short text",
    }


def report_body_matches_input(body: str, exact_text: str, *, anchor_words: int = 12) -> bool:
    """Bind a rendered History report to exact input using stable leading/trailing anchors."""
    if anchor_words < 1:
        raise ValueError("anchor_words must be positive")
    words = " ".join(exact_text.split()).casefold().split()
    if not words:
        return False
    width = min(anchor_words, len(words))
    normalized_body = " ".join(body.split()).casefold()
    leading = " ".join(words[:width])
    trailing = " ".join(words[-width:])
    if leading in normalized_body and trailing in normalized_body:
        return True

    parsed = parse_report_text(body)
    reconstructed = " ".join(
        str(segment.get("text", "")) for segment in parsed["segments"]
    )
    normalized_reconstructed = " ".join(reconstructed.split()).casefold()
    normalized_exact = " ".join(words)
    return normalized_exact in normalized_reconstructed


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


def authenticated_detector_input(page: Any) -> Any:
    """Return the detector input only from Pangram's authenticated dashboard."""
    path = urlsplit(str(getattr(page, "url", ""))).path.lower()
    if re.search(r"/(?:login|signup)(?:/|$)", path):
        raise RuntimeError("authenticated Pangram dashboard is required; login did not persist")

    try:
        body = " ".join(page.locator("body").inner_text().casefold().split())
    except Exception:
        body = ""
    account_wall_markers = (
        "log in to your account",
        "create your account to get started",
        "sign up to gain access to the pangram dashboard",
        "already have an account? sign in",
        "don't have an account? sign up",
    )
    if any(marker in body for marker in account_wall_markers):
        raise RuntimeError("authenticated Pangram dashboard is required; account wall is visible")

    return detector_input(page)


def select_authenticated_dashboard_page(page: Any, dashboard_url: str) -> Any:
    """Prefer an authenticated dashboard tab opened during interactive login."""
    target_path = urlsplit(dashboard_url).path.rstrip("/").lower()
    context = getattr(page, "context", None)
    open_pages = tuple(getattr(context, "pages", ()))
    for candidate in reversed(open_pages):
        candidate_path = urlsplit(str(getattr(candidate, "url", ""))).path.rstrip("/").lower()
        if candidate_path == target_path or candidate_path.startswith(target_path + "/"):
            try:
                authenticated_detector_input(candidate)
            except RuntimeError:
                continue
            return candidate

    page.goto(dashboard_url, wait_until="domcontentloaded")
    authenticated_detector_input(page)
    return page


def select_existing_report_page(page: Any, exact_text: str) -> tuple[Any, str]:
    """Select an already-open Pangram report matching the exact input anchors."""
    context = getattr(page, "context", None)
    open_pages = tuple(getattr(context, "pages", ())) or (page,)
    for candidate in reversed(open_pages):
        try:
            body = candidate.locator("body").inner_text()
        except Exception:
            continue
        if report_body_matches_input(body, exact_text):
            return candidate, body
    raise RuntimeError("the open Pangram History report does not match the requested exact input")


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
    marker = re.compile(
        r"Authorship\s+Breakdown|Analyzed\s+Text|of\s+this\s+text\s+is\s+(?:AI|human)",
        re.IGNORECASE,
    )
    try:
        page.get_by_text(marker, exact=False).first.wait_for(state="visible", timeout=timeout_ms)
    except Exception as exc:
        raise RuntimeError("Pangram report did not become visible before timeout") from exc


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
        context = client.create_context()
        context_id = str(context.get("id", "")).strip()
        if not context_id:
            raise RuntimeError("Browserbase did not return a Context ID")

    session = client.create_session(
        context_id,
        persist=True,
        # The Playwright CDP connection remains open while the user logs in.
        # Disabling Browserbase keep-alive makes browser.close() end the session,
        # which is the boundary at which Context changes are persisted.
        keep_alive=False,
        timeout=1800,
        user_metadata={"task": "pangram-gui-bootstrap"},
    )
    session_id = str(session.get("id", "")).strip()
    connect_url = str(session.get("connectUrl", "")).strip()
    if not session_id or not connect_url:
        raise RuntimeError("Browserbase session response is missing id/connectUrl")
    debug = client.debug_urls(session_id)
    debugger_url = select_live_view_url(debug)

    playwright, browser, page = _connect_session(connect_url)
    try:
        page.goto(PANGRAM_LOGIN_URL, wait_until="domcontentloaded")
        print_fn(f"Browserbase Context ID: {context_id}")
        print_fn(f"Live debugger URL: {debugger_url}")
        input_fn(
            "Open the debugger URL and finish Pangram login. Wait until the page leaves /login "
            "and shows the detector dashboard, then press Enter here to verify: "
        )
        select_authenticated_dashboard_page(page, config.pangram_url)
    finally:
        browser.close()
        playwright.stop()

    return {
        "context_id": context_id,
        "session_id": session_id,
        "debugger_url": debugger_url,
        "verified": True,
    }


def verify_login_persistence(
    config: BrowserbaseConfig,
    *,
    print_fn: Any = print,
) -> dict[str, object]:
    """Verify a saved Context in a fresh session without submitting detector text."""
    if config.context_id is None:
        raise RuntimeError("BROWSERBASE_CONTEXT_ID is required to verify persisted login")

    client = BrowserbaseRestClient(config.api_key)
    session = client.create_session(
        config.context_id,
        persist=True,
        keep_alive=False,
        timeout=300,
        user_metadata={"task": "pangram-gui-verify"},
    )
    session_id = str(session.get("id", "")).strip()
    connect_url = str(session.get("connectUrl", "")).strip()
    if not session_id or not connect_url:
        raise RuntimeError("Browserbase session response is missing id/connectUrl")
    debug = client.debug_urls(session_id)
    debugger_url = select_live_view_url(debug)
    print_fn(f"Browserbase verification session: {session_id}")
    print_fn(f"Live debugger: {debugger_url}")

    playwright, browser, page = _connect_session(connect_url)
    try:
        page.goto(config.pangram_url, wait_until="domcontentloaded")
        authenticated_detector_input(page)
    finally:
        browser.close()
        playwright.stop()

    return {
        "context_id": config.context_id,
        "session_id": session_id,
        "debugger_url": debugger_url,
        "verified": True,
        "submitted": False,
    }


def recover_existing_report(
    config: BrowserbaseConfig,
    input_path: Path,
    *,
    output_root: Path = Path("state/gui-runs"),
    input_fn: Any = input,
    print_fn: Any = print,
) -> dict[str, object]:
    """Capture an existing Pangram History report without making a detector submission."""
    if config.context_id is None:
        raise RuntimeError("BROWSERBASE_CONTEXT_ID is required to recover a Pangram report")
    item = prepare_measurement(input_path, output_root=output_root, force=True)
    input_sha256 = str(item["input_sha256"])
    exact_text = str(item["text"])
    word_count = int(item["word_count"])
    directory = Path(str(item["directory"]))
    paths = artifact_paths(directory)

    client = BrowserbaseRestClient(config.api_key)
    session = client.create_session(
        config.context_id,
        persist=True,
        keep_alive=False,
        timeout=1800,
        user_metadata={"task": "pangram-gui-recover", "inputSha256": input_sha256},
    )
    session_id = str(session.get("id", "")).strip()
    connect_url = str(session.get("connectUrl", "")).strip()
    if not session_id or not connect_url:
        raise RuntimeError("Browserbase session response is missing id/connectUrl")
    debug = client.debug_urls(session_id)
    debugger_url = select_live_view_url(debug)
    print_fn(f"Browserbase recovery session: {session_id}")
    print_fn(f"Live debugger: {debugger_url}")

    playwright, browser, page = _connect_session(connect_url)
    stage = "navigate"
    try:
        page.goto(config.pangram_url, wait_until="domcontentloaded")
        stage = "verify_authentication"
        authenticated_detector_input(page)
        stage = "select_existing_report"
        input_fn(
            "Open the Live debugger, select the existing Pangram History report for "
            f"SHA {input_sha256}, and press Enter here. Do not submit text: "
        )
        report_page, body = select_existing_report_page(page, exact_text)
        body = clean_report_body_artifact(body)
        directory.mkdir(parents=True, exist_ok=True)
        paths["body"].write_text(body, encoding="utf-8")
        stage = "parse_existing_report"
        parsed = parse_report_for_exact_input(body, exact_text, expected_word_count=word_count)
        segments = list(parsed["segments"])
        if not segments:
            raise RuntimeError("the existing Pangram report contained no parseable analyzed segments")
        parsed_word_count = sum(int(segment["word_count"]) for segment in segments)
        if parsed_word_count != word_count:
            raise RuntimeError(
                "the existing Pangram report word count does not match the requested input: "
                f"report={parsed_word_count} input={word_count}"
            )

        stage = "capture_existing_report"
        pdf_provenance = capture_report_pdf(report_page, paths["pdf"])
        receipt = build_complete_receipt(
            input_path=str(item["input_path"]),
            input_sha256=input_sha256,
            word_count=word_count,
            session_id=session_id,
            debugger_url=debugger_url,
            report_url=report_page.url,
            pdf_provenance=pdf_provenance,
            parsed=parsed,
        )
        receipt["evidence_source"] = "recovered_existing_report"
        receipt["detector_submission_attempted"] = False
        _write_json(paths["result"], receipt)
        for stale in (
            paths["failure"],
            paths["failure_screenshot"],
            directory / "recovery-failure.json",
            directory / "recovery-failure.png",
        ):
            if stale.exists():
                stale.unlink()
        print_fn(
            f"[pangram-gui] recovered sha={input_sha256} words={word_count} "
            f"pdf={pdf_provenance}"
        )
        return receipt
    except Exception as exc:
        directory.mkdir(parents=True, exist_ok=True)
        recovery_failure = _failure_receipt(
            input_path=str(item["input_path"]),
            input_sha256=input_sha256,
            word_count=word_count,
            session_id=session_id,
            debugger_url=debugger_url,
            stage=stage,
            detector_submission_attempted=False,
            error=exc,
        )
        recovery_failure["evidence_source"] = "existing_report_recovery"
        _write_json(directory / "recovery-failure.json", recovery_failure)
        try:
            page.screenshot(path=str(directory / "recovery-failure.png"), full_page=True)
        except Exception:
            pass
        raise
    finally:
        browser.close()
        playwright.stop()


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _native_pdf_control(page: Any) -> Any:
    pattern = re.compile(
        r"(?:download|export).*(?:pdf|report)|(?:pdf|report).*(?:download|export)",
        re.IGNORECASE,
    )
    for role in ("button", "link"):
        locator = page.get_by_role(role, name=pattern)
        for index in range(locator.count()):
            candidate = locator.nth(index)
            try:
                if candidate.is_visible() and candidate.is_enabled():
                    return candidate
            except Exception:
                continue
    return None


def capture_report_pdf(page: Any, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    control = _native_pdf_control(page)
    if control is not None:
        try:
            with page.expect_download(timeout=12_000) as download_info:
                control.click()
            download = download_info.value
            download.save_as(str(path))
            return "native_pangram_download"
        except Exception:
            pass
    page.pdf(path=str(path), format="A4", print_background=True)
    return "playwright_print_fallback"


def _failure_receipt(
    *,
    input_path: str,
    input_sha256: str,
    word_count: int,
    session_id: str,
    debugger_url: str,
    stage: str,
    detector_submission_attempted: bool,
    error: Exception,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "failed",
        "runner_version": RUNNER_VERSION,
        "model": MODEL_ID,
        "input_path": input_path,
        "input_sha256": input_sha256,
        "word_count": word_count,
        "browserbase_session_id": session_id,
        "browserbase_debugger_url": debugger_url,
        "browserbase_recording_url": f"https://browserbase.com/sessions/{session_id}",
        "stage": stage,
        "detector_submission_attempted": detector_submission_attempted,
        "error_type": type(error).__name__,
        "error": str(error),
    }


def run_inputs(
    config: BrowserbaseConfig,
    input_paths: Iterable[Path],
    *,
    output_root: Path = Path("state/gui-runs"),
    force: bool = False,
    report_timeout_ms: int = 180_000,
    print_fn: Any = print,
) -> list[dict[str, object]]:
    if config.context_id is None:
        raise RuntimeError("BROWSERBASE_CONTEXT_ID is required for unattended GUI runs")
    prepared = [prepare_measurement(path, output_root=output_root, force=force) for path in input_paths]
    blocked = [item for item in prepared if item["blocked_by_ambiguous_submission"]]
    if blocked:
        identities = ", ".join(str(item["input_sha256"]) for item in blocked)
        raise RuntimeError(
            "refusing to repeat Pangram GUI input after an ambiguous prior submission: "
            f"{identities}. Inspect the saved failure/session evidence; use --force only after "
            "confirming a repeat detector call is intended."
        )
    pending = [item for item in prepared if not item["skip"]]
    results: list[dict[str, object]] = [
        {
            "status": "cached",
            "input_path": item["input_path"],
            "input_sha256": item["input_sha256"],
            "word_count": item["word_count"],
            "directory": item["directory"],
        }
        for item in prepared
        if item["skip"]
    ]
    if not pending:
        return results

    client = BrowserbaseRestClient(config.api_key)
    session = client.create_session(
        config.context_id,
        persist=True,
        keep_alive=False,
        timeout=3600,
        user_metadata={"task": "pangram-gui", "inputCount": str(len(pending))},
    )
    session_id = str(session.get("id", "")).strip()
    connect_url = str(session.get("connectUrl", "")).strip()
    if not session_id or not connect_url:
        raise RuntimeError("Browserbase session response is missing id/connectUrl")
    debug = client.debug_urls(session_id)
    debugger_url = select_live_view_url(debug)
    print_fn(f"Browserbase session: {session_id}")
    print_fn(f"Live debugger: {debugger_url}")

    playwright, browser, page = _connect_session(connect_url)
    try:
        for item in pending:
            directory = Path(str(item["directory"]))
            paths = artifact_paths(directory)
            directory.mkdir(parents=True, exist_ok=True)
            stage = "navigate"
            detector_submission_attempted = False
            try:
                page.goto(config.pangram_url, wait_until="domcontentloaded")
                stage = "verify_authentication"
                field = authenticated_detector_input(page)
                stage = "fill_input"
                field.fill(str(item["text"]))

                stage = "submit"
                detector_submission_attempted = True
                detection_button(page).click()
                print_fn(
                    f"[pangram-gui] submitted sha={item['input_sha256']}; waiting for report"
                )
                stage = "wait_report"
                wait_for_report(page, timeout_ms=report_timeout_ms)

                stage = "capture_body"
                body = clean_report_body_artifact(page.locator("body").inner_text())
                paths["body"].write_text(body, encoding="utf-8")
                parsed = parse_report_for_exact_input(
                    body,
                    str(item["text"]),
                    expected_word_count=int(item["word_count"]),
                )
                if not parsed["segments"]:
                    raise RuntimeError("Pangram report became visible but no analyzed segments could be parsed")

                stage = "capture_pdf"
                pdf_provenance = capture_report_pdf(page, paths["pdf"])
                receipt = build_complete_receipt(
                    input_path=str(item["input_path"]),
                    input_sha256=str(item["input_sha256"]),
                    word_count=int(item["word_count"]),
                    session_id=session_id,
                    debugger_url=debugger_url,
                    report_url=page.url,
                    pdf_provenance=pdf_provenance,
                    parsed=parsed,
                )
                _write_json(paths["result"], receipt)
                for stale in (
                    paths["failure"],
                    paths["failure_screenshot"],
                    directory / "recovery-failure.json",
                    directory / "recovery-failure.png",
                ):
                    if stale.exists():
                        stale.unlink()
                results.append(receipt)
                print_fn(
                    f"[pangram-gui] complete sha={item['input_sha256']} words={item['word_count']} "
                    f"pdf={pdf_provenance}"
                )
            except Exception as exc:
                failure = _failure_receipt(
                    input_path=str(item["input_path"]),
                    input_sha256=str(item["input_sha256"]),
                    word_count=int(item["word_count"]),
                    session_id=session_id,
                    debugger_url=debugger_url,
                    stage=stage,
                    detector_submission_attempted=detector_submission_attempted,
                    error=exc,
                )
                _write_json(paths["failure"], failure)
                try:
                    page.screenshot(path=str(paths["failure_screenshot"]), full_page=True)
                except Exception:
                    pass
                raise
    finally:
        browser.close()
        playwright.stop()

    return results
