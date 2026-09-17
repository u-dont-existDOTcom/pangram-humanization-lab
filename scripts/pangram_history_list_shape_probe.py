#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pangram_lab import gui_local as local
from pangram_lab.history_list_recovery import extract_history_list_candidates


HISTORY_LIST_URL = "https://web.pangram.com/api/history-list/"
PAGINATION_KEYS = {
    "next",
    "previous",
    "count",
    "page",
    "page_size",
    "pages",
    "total_pages",
    "has_more",
    "cursor",
    "next_cursor",
    "offset",
    "limit",
}


def safe_shape(value: Any, *, depth: int = 0) -> Any:
    if depth > 4:
        return "DEPTH_LIMIT"
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            folded = str(key).replace("-", "_").casefold()
            if folded in PAGINATION_KEYS and isinstance(child, (str, int, float, bool, type(None))):
                result[str(key)] = child
            elif isinstance(child, (dict, list, tuple)):
                result[str(key)] = safe_shape(child, depth=depth + 1)
            else:
                result[str(key)] = type(child).__name__
        return result
    if isinstance(value, (list, tuple)):
        return {
            "type": type(value).__name__,
            "length": len(value),
            "first_item_shape": safe_shape(value[0], depth=depth + 1) if value else None,
        }
    return type(value).__name__


def context_get_json(context: Any, url: str) -> tuple[Any | None, str]:
    try:
        response = context.request.get(url, timeout=15_000)
        status = int(response.status)
        if status != 200:
            return None, f"http_status:{status}"
        if "json" not in str((response.headers or {}).get("content-type", "")).casefold():
            return None, "non_json_response"
        return response.json(), "ok"
    except Exception as exc:
        return None, f"request_failed:{type(exc).__name__}"


def main() -> int:
    config = local.LocalPlaywrightConfig.from_env()
    playwright = context = page = None
    try:
        playwright, context, page = local._launch_persistent_context(config)
        page.goto(config.pangram_url, wait_until="domcontentloaded")
        local.wait_for_authenticated_detector_input(page)
        payload, status = context_get_json(context, HISTORY_LIST_URL)
        candidates = extract_history_list_candidates(payload)
        print(
            json.dumps(
                {
                    "status": status,
                    "candidate_count": len(candidates),
                    "payload_shape": safe_shape(payload),
                    "detector_submission_attempted": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if payload is not None else 2
    finally:
        if playwright is not None and context is not None:
            local._close_local_session(playwright, context)


if __name__ == "__main__":
    raise SystemExit(main())
