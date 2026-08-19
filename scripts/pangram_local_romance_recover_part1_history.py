#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Any

import pangram_local_romance_recover_part1 as base
from pangram_lab.browser_history_recovery import discover_pangram_history_urls

HISTORY_ROOT_URL = "https://www.pangram.com/history"


def _try_exact_history_urls(
    context: Any,
    page: Any,
    exact_text: str,
    history_urls: tuple[str, ...],
) -> tuple[Any, str, dict[str, object]] | None:
    if not history_urls:
        return None
    working = base.local_transport.normalize_context_tabs(context, keep=page)
    for candidate_url in history_urls:
        try:
            working.goto(candidate_url, wait_until="domcontentloaded")
            return base.local_transport.wait_for_exact_report_page(
                context,
                exact_text,
                expected_word_count=base.EXPECTED_WORDS,
                timeout_ms=6_000,
                poll_ms=400,
            )
        except Exception:
            continue
    return None


def _try_history_root(
    context: Any,
    page: Any,
    exact_text: str,
) -> tuple[Any, str, dict[str, object]] | None:
    working = base.local_transport.normalize_context_tabs(context, keep=page)
    try:
        working.goto(HISTORY_ROOT_URL, wait_until="domcontentloaded")
        working.wait_for_timeout(1_500)
    except Exception:
        return None

    try:
        return base.local_transport.wait_for_exact_report_page(
            context,
            exact_text,
            expected_word_count=base.EXPECTED_WORDS,
            timeout_ms=4_000,
            poll_ms=400,
        )
    except RuntimeError:
        pass

    try:
        if base._try_open_exact_preview(context, exact_text):
            return base.local_transport.wait_for_exact_report_page(
                context,
                exact_text,
                expected_word_count=base.EXPECTED_WORDS,
                timeout_ms=8_000,
                poll_ms=400,
            )
    except Exception:
        pass
    return None


def main() -> int:
    config = base.local_transport.LocalPlaywrightConfig.from_env()
    history_urls = discover_pangram_history_urls(config.profile_dir, limit=20)
    print(
        "[pangram-local-recover] dedicated-profile Pangram result URL candidates="
        f"{len(history_urls)} (URLs not printed)",
        flush=True,
    )

    original_find = base._find_or_open_report

    def enhanced_find(
        context: Any,
        page: Any,
        exact_text: str,
    ) -> tuple[Any, str, dict[str, object]]:
        recovered = _try_exact_history_urls(context, page, exact_text, history_urls)
        if recovered is not None:
            print(
                "[pangram-local-recover] recovered exact Part 1 from dedicated-profile Pangram URL history",
                flush=True,
            )
            return recovered

        recovered = _try_history_root(context, page, exact_text)
        if recovered is not None:
            print(
                "[pangram-local-recover] recovered exact Part 1 from Pangram History route",
                flush=True,
            )
            return recovered

        return original_find(context, page, exact_text)

    base._find_or_open_report = enhanced_find
    try:
        base._json(base.recover())
    except Exception as exc:
        # Preserve the exact no-repeat boundary in the terminal log.
        diagnostic = {
            "status": "not_recovered",
            "detector_submission_attempted_during_recovery": False,
            "dedicated_profile_history_candidates": len(history_urls),
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        print(json.dumps(diagnostic, ensure_ascii=False, indent=2, sort_keys=True), flush=True)
        raise
    finally:
        base._find_or_open_report = original_find
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
