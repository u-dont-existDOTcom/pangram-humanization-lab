from __future__ import annotations

import base64
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from pangram_lab import gui_browserbase as gui_core


LOCAL_RUNNER_VERSION = "pangram-gui-local-playwright-v1"
TRANSPORT_ID = "local_playwright"
DEFAULT_PROFILE_DIR = Path.home() / ".config" / "pangram-local-browser"

_BROWSER_PATH_CANDIDATES = (
    Path("/opt/brave.com/brave/brave"),
    Path("/usr/bin/brave-browser"),
    Path("/usr/bin/brave"),
    Path("/usr/bin/chromium"),
    Path("/usr/bin/chromium-browser"),
    Path("/usr/bin/google-chrome-stable"),
    Path("/usr/bin/google-chrome"),
)
_BROWSER_COMMAND_CANDIDATES = (
    "brave-browser",
    "brave",
    "chromium",
    "chromium-browser",
    "google-chrome-stable",
    "google-chrome",
)

EvidenceCallback = Callable[[Path, Mapping[str, object]], None]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _resolved(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _is_same_or_within(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def ordinary_browser_profile_roots(home: Path | None = None) -> tuple[Path, ...]:
    root = _resolved(Path.home() if home is None else home)
    config = root / ".config"
    return tuple(
        _resolved(path)
        for path in (
            config / "BraveSoftware" / "Brave-Browser",
            config / "chromium",
            config / "google-chrome",
            config / "google-chrome-beta",
            config / "microsoft-edge",
            config / "vivaldi",
        )
    )


def containing_git_root(path: Path) -> Path | None:
    current = _resolved(path)
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def validate_profile_dir(
    profile_dir: Path,
    *,
    allow_ordinary_profile: bool = False,
    allow_in_git_repo: bool = False,
    home: Path | None = None,
) -> Path:
    resolved = _resolved(profile_dir)
    resolved_home = _resolved(Path.home() if home is None else home)
    dangerous_broad_paths = {
        Path("/"),
        resolved_home,
        resolved_home / ".config",
    }
    if resolved in dangerous_broad_paths:
        raise RuntimeError(
            f"refusing unsafe Pangram profile directory {resolved}; use a dedicated directory"
        )

    if not allow_ordinary_profile:
        for ordinary_root in ordinary_browser_profile_roots(resolved_home):
            if _is_same_or_within(resolved, ordinary_root):
                raise RuntimeError(
                    "refusing to use an ordinary browser profile for Pangram automation: "
                    f"{resolved}. Use the dedicated default "
                    f"{resolved_home / '.config' / 'pangram-local-browser'} instead."
                )

    if not allow_in_git_repo:
        git_root = containing_git_root(resolved)
        if git_root is not None:
            raise RuntimeError(
                "refusing to place a persistent Pangram browser profile inside a Git repository: "
                f"profile={resolved} repo={git_root}"
            )

    if resolved.exists() and not resolved.is_dir():
        raise RuntimeError(f"Pangram profile path exists but is not a directory: {resolved}")
    return resolved


def ensure_profile_dir(profile_dir: Path) -> Path:
    profile_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        profile_dir.chmod(0o700)
    except OSError:
        pass
    return profile_dir


def discover_browser_executable(
    explicit: Path | str | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> Path | None:
    values: Mapping[str, str] = os.environ if env is None else env
    configured = explicit or values.get("PANGRAM_LOCAL_BROWSER", "").strip() or None
    if configured is not None:
        candidate = _resolved(Path(configured))
        if not candidate.is_file() or not os.access(candidate, os.X_OK):
            raise RuntimeError(f"configured Pangram browser executable is not runnable: {candidate}")
        return candidate

    for candidate in _BROWSER_PATH_CANDIDATES:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return _resolved(candidate)
    for command in _BROWSER_COMMAND_CANDIDATES:
        located = shutil.which(command)
        if located:
            return _resolved(Path(located))
    return None


@dataclass(frozen=True)
class LocalPlaywrightConfig:
    profile_dir: Path = DEFAULT_PROFILE_DIR
    browser_executable: Path | None = None
    pangram_url: str = gui_core.DEFAULT_PANGRAM_GUI_URL
    headed: bool = True
    allow_ordinary_profile: bool = False
    allow_profile_in_git_repo: bool = False

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        *,
        profile_dir: Path | None = None,
        browser_executable: Path | None = None,
        headed: bool = True,
        allow_ordinary_profile: bool = False,
        allow_profile_in_git_repo: bool = False,
    ) -> "LocalPlaywrightConfig":
        values: Mapping[str, str] = os.environ if env is None else env
        selected_profile = profile_dir or Path(
            values.get("PANGRAM_LOCAL_PROFILE", "").strip() or DEFAULT_PROFILE_DIR
        )
        selected_profile = validate_profile_dir(
            selected_profile,
            allow_ordinary_profile=allow_ordinary_profile,
            allow_in_git_repo=allow_profile_in_git_repo,
        )
        selected_browser = discover_browser_executable(browser_executable, env=values)
        pangram_url = (
            values.get("PANGRAM_GUI_URL", gui_core.DEFAULT_PANGRAM_GUI_URL).strip()
            or gui_core.DEFAULT_PANGRAM_GUI_URL
        )
        return cls(
            profile_dir=selected_profile,
            browser_executable=selected_browser,
            pangram_url=pangram_url,
            headed=bool(headed),
            allow_ordinary_profile=bool(allow_ordinary_profile),
            allow_profile_in_git_repo=bool(allow_profile_in_git_repo),
        )


def _launch_persistent_context(config: LocalPlaywrightConfig) -> tuple[Any, Any, Any]:
    profile_dir = validate_profile_dir(
        config.profile_dir,
        allow_ordinary_profile=config.allow_ordinary_profile,
        allow_in_git_repo=config.allow_profile_in_git_repo,
    )
    ensure_profile_dir(profile_dir)
    sync_playwright = gui_core._load_playwright()
    playwright = sync_playwright().start()
    launch_options: dict[str, object] = {
        "user_data_dir": str(profile_dir),
        "headless": not config.headed,
    }
    if config.browser_executable is not None:
        launch_options["executable_path"] = str(config.browser_executable)
    if config.headed:
        launch_options["no_viewport"] = True
        launch_options["args"] = ["--start-maximized"]
    try:
        context = playwright.chromium.launch_persistent_context(**launch_options)
    except Exception:
        playwright.stop()
        raise
    pages = context.pages
    page = pages[0] if pages else context.new_page()
    return playwright, context, page


def _close_local_session(playwright: Any, context: Any) -> None:
    try:
        context.close()
    finally:
        playwright.stop()


def _browser_label(config: LocalPlaywrightConfig) -> str:
    if config.browser_executable is None:
        return "playwright-managed-chromium"
    return str(config.browser_executable)


def _profile_label(path: Path) -> str:
    resolved = _resolved(path)
    home = _resolved(Path.home())
    try:
        return "~/" + str(resolved.relative_to(home))
    except ValueError:
        return str(resolved)


def _playwright_version() -> str | None:
    try:
        return importlib.metadata.version("playwright")
    except importlib.metadata.PackageNotFoundError:
        return None


def _transport_fields(config: LocalPlaywrightConfig) -> dict[str, object]:
    return {
        "transport": TRANSPORT_ID,
        "transport_runner_version": LOCAL_RUNNER_VERSION,
        "runner_version": gui_core.RUNNER_VERSION,
        "profile_kind": "dedicated_persistent_automation_profile",
        "local_profile_path": _profile_label(config.profile_dir),
        "browser_executable": _browser_label(config),
        "headed": config.headed,
        "playwright_version": _playwright_version(),
        "platform": platform.platform(),
    }


def _source_for_item(
    item: Mapping[str, object],
    source_metadata: Mapping[str, Mapping[str, object]] | None,
) -> Mapping[str, object] | None:
    if source_metadata is None:
        return None
    input_path = str(item["input_path"])
    return source_metadata.get(input_path) or source_metadata.get(Path(input_path).name)


def _receipt_input_path(
    item: Mapping[str, object],
    source: Mapping[str, object] | None,
) -> str:
    if source is not None and source.get("source_path"):
        return str(source["source_path"])
    return str(item["input_path"])


def extract_report_metadata(body: str, parsed: Mapping[str, object]) -> dict[str, object]:
    version_match = re.search(r"\bPangram\s+(?P<version>\d+(?:\.\d+)*)\b", body, re.IGNORECASE)
    if parsed.get("report_layout"):
        layout = parsed.get("report_layout")
    elif parsed.get("segments"):
        layout = "segmented_report"
    else:
        layout = None
    return {
        "detector_version": version_match.group("version") if version_match else None,
        "report_layout": layout,
    }


def build_complete_receipt(
    config: LocalPlaywrightConfig,
    *,
    item: Mapping[str, object],
    report_url: str,
    pdf_provenance: str,
    parsed: dict[str, object],
    body: str,
    pdf_path: Path,
    source: Mapping[str, object] | None = None,
    evidence_source: str = "new_detector_submission",
    detector_submission_attempted: bool = True,
) -> dict[str, object]:
    receipt: dict[str, object] = {
        "schema_version": 1,
        "status": "complete",
        **_transport_fields(config),
        "model": gui_core.MODEL_ID,
        "captured_at_utc": utc_now_iso(),
        "input_path": _receipt_input_path(item, source),
        "input_sha256": str(item["input_sha256"]),
        "word_count": int(item["word_count"]),
        "report_url": report_url,
        "report_body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "report_pdf_sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
        "pdf_provenance": pdf_provenance,
        "evidence_source": evidence_source,
        "detector_submission_attempted": detector_submission_attempted,
        **extract_report_metadata(body, parsed),
        "parsed": parsed,
    }
    if source is not None:
        receipt["source"] = dict(source)
    return receipt


def build_failure_receipt(
    config: LocalPlaywrightConfig,
    *,
    item: Mapping[str, object],
    stage: str,
    detector_submission_attempted: bool,
    error: Exception,
    source: Mapping[str, object] | None = None,
    evidence_source: str = "new_detector_submission",
) -> dict[str, object]:
    receipt: dict[str, object] = {
        "schema_version": 1,
        "status": "failed",
        **_transport_fields(config),
        "model": gui_core.MODEL_ID,
        "captured_at_utc": utc_now_iso(),
        "input_path": _receipt_input_path(item, source),
        "input_sha256": str(item["input_sha256"]),
        "word_count": int(item["word_count"]),
        "stage": stage,
        "detector_submission_attempted": detector_submission_attempted,
        "evidence_source": evidence_source,
        "error_type": type(error).__name__,
        "error": str(error),
    }
    if source is not None:
        receipt["source"] = dict(source)
    return receipt


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _remove_stale_failures(directory: Path, paths: Mapping[str, Path]) -> None:
    for stale in (
        paths["failure"],
        paths["failure_screenshot"],
        directory / "reservation.json",
        directory / "recovery-failure.json",
        directory / "recovery-failure.png",
    ):
        try:
            stale.unlink()
        except FileNotFoundError:
            pass


def capture_report_pdf(page: Any, path: Path) -> str:
    try:
        return gui_core.capture_report_pdf(page, path)
    except Exception as playwright_pdf_error:
        path.parent.mkdir(parents=True, exist_ok=True)
        cdp_session = None
        try:
            cdp_session = page.context.new_cdp_session(page)
            result = cdp_session.send(
                "Page.printToPDF",
                {
                    "printBackground": True,
                    "paperWidth": 8.27,
                    "paperHeight": 11.69,
                    "marginTop": 0.4,
                    "marginBottom": 0.4,
                    "marginLeft": 0.4,
                    "marginRight": 0.4,
                },
            )
            encoded = str(result.get("data", ""))
            if not encoded:
                raise RuntimeError("CDP Page.printToPDF returned no data")
            path.write_bytes(base64.b64decode(encoded, validate=True))
            return "local_cdp_print_fallback"
        except Exception as cdp_error:
            raise RuntimeError(
                "Pangram report PDF capture failed through both Playwright and local CDP: "
                f"playwright={playwright_pdf_error}; cdp={cdp_error}"
            ) from cdp_error
        finally:
            if cdp_session is not None:
                try:
                    cdp_session.detach()
                except Exception:
                    pass


def _prepare_inputs(
    input_paths: Iterable[Path],
    *,
    output_root: Path,
    force: bool,
    expected_sha256: Mapping[str, str] | None,
) -> list[dict[str, object]]:
    prepared = [
        gui_core.prepare_measurement(path, output_root=output_root, force=force)
        for path in input_paths
    ]
    if expected_sha256 is not None:
        for item in prepared:
            input_path = Path(str(item["input_path"]))
            expected = expected_sha256.get(str(input_path)) or expected_sha256.get(input_path.name)
            if expected is None:
                raise RuntimeError(f"no expected SHA-256 gate was supplied for {input_path}")
            actual = str(item["input_sha256"])
            if actual != expected:
                raise RuntimeError(
                    f"refusing Pangram submission because exact SHA-256 changed for {input_path}: "
                    f"expected={expected} actual={actual}"
                )
    return prepared


def bootstrap_login(
    config: LocalPlaywrightConfig,
    *,
    input_fn: Any = input,
    print_fn: Any = print,
) -> dict[str, object]:
    playwright, context, page = _launch_persistent_context(config)
    try:
        page.goto(gui_core.PANGRAM_LOGIN_URL, wait_until="domcontentloaded")
        print_fn(f"Dedicated Pangram profile: {_profile_label(config.profile_dir)}")
        print_fn(f"Browser: {_browser_label(config)}")
        input_fn(
            "Finish Pangram login in the visible dedicated browser. Wait until the detector dashboard "
            "appears, then press Enter here to verify and close it: "
        )
        selected = gui_core.select_authenticated_dashboard_page(page, config.pangram_url)
        gui_core.authenticated_detector_input(selected)
    finally:
        _close_local_session(playwright, context)
    return {
        **_transport_fields(config),
        "verified": True,
        "submitted": False,
    }


def verify_login_persistence(
    config: LocalPlaywrightConfig,
    *,
    print_fn: Any = print,
) -> dict[str, object]:
    playwright, context, page = _launch_persistent_context(config)
    try:
        page.goto(config.pangram_url, wait_until="domcontentloaded")
        field = gui_core.authenticated_detector_input(page)
        editable = bool(field.is_editable()) if hasattr(field, "is_editable") else None
        print_fn("Authenticated Pangram detector verified without filling or submitting text.")
    finally:
        _close_local_session(playwright, context)
    return {
        **_transport_fields(config),
        "verified": True,
        "detector_input_editable": editable,
        "submitted": False,
    }


def launch_smoke_test(
    config: LocalPlaywrightConfig,
    *,
    input_fn: Any = input,
) -> dict[str, object]:
    playwright, context, page = _launch_persistent_context(config)
    try:
        page.goto(
            "data:text/html,<title>Pangram local browser smoke</title>"
            "<h1>Pangram local Playwright smoke</h1>",
            wait_until="domcontentloaded",
        )
        if config.headed:
            input_fn(
                "Confirm the dedicated Pangram browser window is visible, then press Enter to close it: "
            )
    finally:
        _close_local_session(playwright, context)
    return {
        **_transport_fields(config),
        "launch_succeeded": True,
        "closed_cleanly": True,
    }


def _persist_evidence(
    callback: EvidenceCallback | None,
    directory: Path,
    receipt: Mapping[str, object],
) -> None:
    if callback is not None:
        callback(directory, receipt)


def run_inputs(
    config: LocalPlaywrightConfig,
    input_paths: Iterable[Path],
    *,
    output_root: Path = Path("state/gui-runs"),
    force: bool = False,
    report_timeout_ms: int = 180_000,
    expected_sha256: Mapping[str, str] | None = None,
    source_metadata: Mapping[str, Mapping[str, object]] | None = None,
    evidence_callback: EvidenceCallback | None = None,
    print_fn: Any = print,
) -> list[dict[str, object]]:
    prepared = _prepare_inputs(
        input_paths,
        output_root=output_root,
        force=force,
        expected_sha256=expected_sha256,
    )
    blocked = [item for item in prepared if item["blocked_by_ambiguous_submission"]]
    if blocked:
        identities = ", ".join(str(item["input_sha256"]) for item in blocked)
        raise RuntimeError(
            "refusing to repeat Pangram GUI input after an ambiguous prior submission: "
            f"{identities}. Inspect the saved failure/History evidence; use --force only after "
            "confirming a repeat detector call is intended."
        )

    pending = [item for item in prepared if not item["skip"]]
    results: list[dict[str, object]] = [
        {
            "status": "cached",
            "transport": TRANSPORT_ID,
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

    playwright, context, page = _launch_persistent_context(config)
    try:
        for item in pending:
            directory = Path(str(item["directory"]))
            paths = gui_core.artifact_paths(directory)
            directory.mkdir(parents=True, exist_ok=True)
            source = _source_for_item(item, source_metadata)
            stage = "navigate"
            detector_submission_attempted = False
            try:
                page.goto(config.pangram_url, wait_until="domcontentloaded")
                stage = "verify_authentication"
                field = gui_core.authenticated_detector_input(page)
                stage = "fill_input"
                field.fill(str(item["text"]))
                stage = "submit"
                detector_submission_attempted = True
                gui_core.detection_button(page).click()
                print_fn(
                    f"[pangram-local] submitted sha={item['input_sha256']}; waiting for report"
                )
                stage = "wait_report"
                gui_core.wait_for_report(page, timeout_ms=report_timeout_ms)
                stage = "capture_body"
                body = gui_core.clean_report_body_artifact(page.locator("body").inner_text())
                paths["body"].write_text(body, encoding="utf-8")
                parsed = gui_core.parse_report_for_exact_input(
                    body,
                    str(item["text"]),
                    expected_word_count=int(item["word_count"]),
                )
                segments = list(parsed["segments"])
                if not segments:
                    raise RuntimeError(
                        "Pangram report became visible but no analyzed segments could be parsed"
                    )
                parsed_word_count = sum(int(segment["word_count"]) for segment in segments)
                if parsed_word_count != int(item["word_count"]):
                    raise RuntimeError(
                        "Pangram report word count does not match exact input: "
                        f"report={parsed_word_count} input={item['word_count']}"
                    )
                stage = "capture_pdf"
                pdf_provenance = capture_report_pdf(page, paths["pdf"])
                receipt = build_complete_receipt(
                    config,
                    item=item,
                    report_url=page.url,
                    pdf_provenance=pdf_provenance,
                    parsed=parsed,
                    body=body,
                    pdf_path=paths["pdf"],
                    source=source,
                )
                _write_json(paths["result"], receipt)
                _remove_stale_failures(directory, paths)
                stage = "persist_evidence"
                _persist_evidence(evidence_callback, directory, receipt)
                results.append(receipt)
                print_fn(
                    f"[pangram-local] complete sha={item['input_sha256']} "
                    f"words={item['word_count']} pdf={pdf_provenance}"
                )
            except Exception as exc:
                if stage == "persist_evidence":
                    raise
                failure = build_failure_receipt(
                    config,
                    item=item,
                    stage=stage,
                    detector_submission_attempted=detector_submission_attempted,
                    error=exc,
                    source=source,
                )
                _write_json(paths["failure"], failure)
                try:
                    page.screenshot(path=str(paths["failure_screenshot"]), full_page=True)
                except Exception:
                    pass
                try:
                    _persist_evidence(evidence_callback, directory, failure)
                except Exception as durability_error:
                    raise RuntimeError(
                        "Pangram run failed and the saved failure evidence could not be pushed durably: "
                        f"run_error={exc}; durability_error={durability_error}"
                    ) from durability_error
                raise
    finally:
        _close_local_session(playwright, context)
    return results


def recover_existing_report(
    config: LocalPlaywrightConfig,
    input_path: Path,
    *,
    output_root: Path = Path("state/gui-runs"),
    expected_sha256: str | None = None,
    source_metadata: Mapping[str, object] | None = None,
    evidence_callback: EvidenceCallback | None = None,
    input_fn: Any = input,
    print_fn: Any = print,
) -> dict[str, object]:
    expected = None if expected_sha256 is None else {str(input_path): expected_sha256}
    item = _prepare_inputs(
        [input_path],
        output_root=output_root,
        force=True,
        expected_sha256=expected,
    )[0]
    directory = Path(str(item["directory"]))
    paths = gui_core.artifact_paths(directory)
    exact_text = str(item["text"])
    word_count = int(item["word_count"])

    playwright, context, page = _launch_persistent_context(config)
    stage = "navigate"
    try:
        page.goto(config.pangram_url, wait_until="domcontentloaded")
        stage = "verify_authentication"
        gui_core.authenticated_detector_input(page)
        stage = "select_existing_report"
        input_fn(
            "Select the existing matching Pangram History report in the visible browser, then press "
            f"Enter. Do not submit text. SHA: {item['input_sha256']} "
        )
        report_page, body = gui_core.select_existing_report_page(page, exact_text)
        body = gui_core.clean_report_body_artifact(body)
        directory.mkdir(parents=True, exist_ok=True)
        paths["body"].write_text(body, encoding="utf-8")
        stage = "parse_existing_report"
        parsed = gui_core.parse_report_for_exact_input(
            body,
            exact_text,
            expected_word_count=word_count,
        )
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
            config,
            item=item,
            report_url=report_page.url,
            pdf_provenance=pdf_provenance,
            parsed=parsed,
            body=body,
            pdf_path=paths["pdf"],
            source=source_metadata,
            evidence_source="recovered_existing_report",
            detector_submission_attempted=False,
        )
        _write_json(paths["result"], receipt)
        _remove_stale_failures(directory, paths)
        stage = "persist_evidence"
        _persist_evidence(evidence_callback, directory, receipt)
        print_fn(
            f"[pangram-local] recovered sha={item['input_sha256']} "
            f"words={word_count} pdf={pdf_provenance}"
        )
        return receipt
    except Exception as exc:
        if stage == "persist_evidence":
            raise
        directory.mkdir(parents=True, exist_ok=True)
        failure = build_failure_receipt(
            config,
            item=item,
            stage=stage,
            detector_submission_attempted=False,
            error=exc,
            source=source_metadata,
            evidence_source="existing_report_recovery",
        )
        _write_json(directory / "recovery-failure.json", failure)
        try:
            page.screenshot(path=str(directory / "recovery-failure.png"), full_page=True)
        except Exception:
            pass
        try:
            _persist_evidence(evidence_callback, directory, failure)
        except Exception as durability_error:
            raise RuntimeError(
                "Pangram History recovery failed and the saved failure evidence could not be pushed "
                f"durably: recovery_error={exc}; durability_error={durability_error}"
            ) from durability_error
        raise
    finally:
        _close_local_session(playwright, context)


def input_status(
    input_paths: Iterable[Path],
    *,
    output_root: Path = Path("state/gui-runs"),
    expected_sha256: Mapping[str, str] | None = None,
) -> list[dict[str, object]]:
    prepared = _prepare_inputs(
        input_paths,
        output_root=output_root,
        force=False,
        expected_sha256=expected_sha256,
    )
    return [
        {
            "input_path": item["input_path"],
            "input_sha256": item["input_sha256"],
            "word_count": item["word_count"],
            "result_cached": bool(item["skip"]),
            "ambiguous_submission_block": bool(item["blocked_by_ambiguous_submission"]),
            "directory": item["directory"],
        }
        for item in prepared
    ]


def environment_status(config: LocalPlaywrightConfig) -> dict[str, object]:
    return {
        **_transport_fields(config),
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "virtualenv_active": sys.prefix != getattr(sys, "base_prefix", sys.prefix),
        "playwright_available": _playwright_version() is not None,
        "display": os.environ.get("DISPLAY"),
        "wayland_display": os.environ.get("WAYLAND_DISPLAY"),
        "xdg_session_type": os.environ.get("XDG_SESSION_TYPE"),
        "profile_exists": config.profile_dir.is_dir(),
        "profile_safe": True,
    }
