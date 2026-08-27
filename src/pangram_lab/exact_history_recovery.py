from __future__ import annotations

import time
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
    require_unique_match: bool = False,
    not_before_tolerance_seconds: float = 5.0,
) -> tuple[ExactHistoryRecord | None, dict[str, object]]:
    if require_unique_match:
        if target_time is None:
            raise ValueError("unique exact History recovery requires a target time")
        candidates = tuple(
            candidate
            for candidate in rank_by_target_time(
                extract_history_list_candidates(history_list_payload), target_time
            )
            if candidate.distance_seconds(target_time) <= MAX_TARGET_DISTANCE_SECONDS
            and candidate.created_at_utc.timestamp()
            >= target_time.timestamp() - not_before_tolerance_seconds
        )
        if len(candidates) > limit:
            return None, {
                "history_candidate_count": len(candidates),
                "history_records_inspected": 0,
                "read_status_counts": {},
                "target_time_binding_used": True,
                "candidate_window_truncated": True,
                "exact_match_count": 0,
            }
    else:
        candidates = candidate_window(
            history_list_payload,
            target_time=target_time,
            limit=limit,
        )
    inspected = 0
    statuses: dict[str, int] = {}
    exact_matches: list[tuple[ExactHistoryRecord, HistoryListCandidate]] = []
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
        exact_matches.append((match, candidate))
        if require_unique_match:
            continue
        return _matched_proof(
            match,
            candidate,
            candidates=candidates,
            inspected=inspected,
            statuses=statuses,
            target_time=target_time,
            exact_match_count=1,
        )
    incomplete_reads = require_unique_match and inspected != len(candidates)
    if incomplete_reads:
        return None, {
            "history_candidate_count": len(candidates),
            "history_records_inspected": inspected,
            "read_status_counts": statuses,
            "target_time_binding_used": target_time is not None,
            "incomplete_candidate_reads": True,
            "exact_match_count": len(exact_matches),
        }
    if len(exact_matches) == 1:
        match, candidate = exact_matches[0]
        return _matched_proof(
            match,
            candidate,
            candidates=candidates,
            inspected=inspected,
            statuses=statuses,
            target_time=target_time,
            exact_match_count=1,
        )
    if len(exact_matches) > 1:
        return None, {
            "history_candidate_count": len(candidates),
            "history_records_inspected": inspected,
            "read_status_counts": statuses,
            "target_time_binding_used": target_time is not None,
            "exact_match_count": len(exact_matches),
            "ambiguous_exact_matches": True,
        }
    return None, {
        "history_candidate_count": len(candidates),
        "history_records_inspected": inspected,
        "read_status_counts": statuses,
        "target_time_binding_used": target_time is not None,
        "exact_match_count": 0,
    }


def _matched_proof(
    match: ExactHistoryRecord,
    candidate: HistoryListCandidate,
    *,
    candidates: tuple[HistoryListCandidate, ...],
    inspected: int,
    statuses: dict[str, int],
    target_time: datetime | None,
    exact_match_count: int,
) -> tuple[ExactHistoryRecord, dict[str, object]]:
    proof: dict[str, object] = {
        "history_candidate_count": len(candidates),
        "history_records_inspected": inspected,
        "read_status_counts": statuses,
        "target_time_binding_used": target_time is not None,
        "exact_match_count": exact_match_count,
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


def wait_for_exact_history_record(
    context: Any,
    exact_text: str,
    *,
    target_time: datetime,
    timeout_ms: int = 30_000,
    poll_ms: int = 500,
) -> tuple[ExactHistoryRecord | None, dict[str, object]]:
    if timeout_ms < 1 or poll_ms < 1:
        raise ValueError("timeout_ms and poll_ms must be positive")
    deadline = time.monotonic() + timeout_ms / 1000.0
    attempts = 0
    last_proof: dict[str, object] = {
        "history_candidate_count": 0,
        "history_records_inspected": 0,
        "read_status_counts": {},
        "target_time_binding_used": True,
    }
    history_status_counts: dict[str, int] = {}
    while True:
        attempts += 1
        history_list, status = context_get_json(context, HISTORY_LIST_URL)
        history_status_counts[status] = history_status_counts.get(status, 0) + 1
        if history_list is not None:
            record, last_proof = find_exact_history_record(
                context,
                history_list,
                exact_text,
                target_time=target_time,
            )
            if record is not None:
                return record, {
                    **last_proof,
                    "history_list_attempts": attempts,
                    "history_list_status_counts": history_status_counts,
                }
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None, {
                **last_proof,
                "history_list_attempts": attempts,
                "history_list_status_counts": history_status_counts,
            }
        time.sleep(min(poll_ms / 1000.0, remaining))
