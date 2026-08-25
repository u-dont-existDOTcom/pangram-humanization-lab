from __future__ import annotations

from datetime import datetime
from typing import Any

from pangram_lab.history_api_record import ExactHistoryRecord, match_exact_history_record
from pangram_lab.history_list_recovery import (
    HistoryListCandidate,
    extract_history_list_candidates,
    rank_by_target_time,
)


HISTORY_LIST_URL = "https://web.pangram.com/api/history-list/"
MAX_TARGET_DISTANCE_SECONDS = 15 * 60


def history_record_url(candidate: HistoryListCandidate) -> str:
    return f"https://web.pangram.com/api/history/{candidate.uuid}/"


def safe_response_json(response: Any) -> tuple[Any | None, str]:
    try:
        status = int(getattr(response, "status", 0) or 0)
        if status != 200:
            return None, f"http_status:{status}"
        headers = getattr(response, "headers", {}) or {}
        if "json" not in str(headers.get("content-type", "")).casefold():
            return None, "non_json_response"
        return response.json(), "ok"
    except Exception as exc:
        return None, f"response_error:{type(exc).__name__}"


def context_get_json(context: Any, url: str) -> tuple[Any | None, str]:
    request = getattr(context, "request", None)
    getter = getattr(request, "get", None)
    if not callable(getter):
        return None, "context_request_unavailable"
    try:
        response = getter(url, timeout=15_000)
    except Exception as exc:
        return None, f"request_failed:{type(exc).__name__}"
    return safe_response_json(response)


def candidate_window(
    history_list_payload: Any,
    *,
    target_time: datetime | None,
    limit: int = 20,
) -> tuple[HistoryListCandidate, ...]:
    if limit < 1:
        raise ValueError("limit must be positive")
    candidates = extract_history_list_candidates(history_list_payload)
    if target_time is None:
        return candidates[:limit]
    ranked = rank_by_target_time(candidates, target_time)
    return tuple(
        candidate
        for candidate in ranked[:limit]
        if candidate.distance_seconds(target_time) <= MAX_TARGET_DISTANCE_SECONDS
    )


def find_exact_history_record(
    context: Any,
    history_list_payload: Any,
    exact_text: str,
    *,
    target_time: datetime | None,
    limit: int = 20,
) -> tuple[ExactHistoryRecord | None, dict[str, object]]:
    candidates = candidate_window(
        history_list_payload,
        target_time=target_time,
        limit=limit,
    )
    inspected = 0
    statuses: dict[str, int] = {}
    for candidate in candidates:
        payload, status = context_get_json(context, history_record_url(candidate))
        statuses[status] = statuses.get(status, 0) + 1
        if payload is None:
            continue
        inspected += 1
        match = match_exact_history_record(
            history_record_url(candidate),
            payload,
            exact_text,
        )
        if match is None:
            continue
        proof: dict[str, object] = {
            "history_candidate_count": len(candidates),
            "history_records_inspected": inspected,
            "read_status_counts": statuses,
            "target_time_binding_used": target_time is not None,
        }
        if target_time is not None:
            proof.update(
                {
                    "created_at_utc": candidate.created_at_utc.isoformat().replace(
                        "+00:00", "Z"
                    ),
                    "seconds_from_recovery_target": round(
                        candidate.distance_seconds(target_time), 3
                    ),
                    "timestamp_key": candidate.timestamp_key,
                    "record_field_path": list(candidate.field_path),
                }
            )
        return match, proof
    return None, {
        "history_candidate_count": len(candidates),
        "history_records_inspected": inspected,
        "read_status_counts": statuses,
        "target_time_binding_used": target_time is not None,
    }
