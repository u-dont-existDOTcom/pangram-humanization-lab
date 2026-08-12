from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

import httpx


@dataclass(frozen=True)
class PangramTask:
    task_id: str
    request_identity: str
    candidate_hash: str
    model: str


@dataclass(frozen=True)
class PangramResult:
    stage: str
    version: str
    prediction_short: str
    fraction_ai: float
    fraction_ai_assisted: float
    windows: tuple[dict[str, Any], ...]
    raw: dict[str, Any]
    is_human: bool


class PangramClient:
    def __init__(self, api_key: str, client: httpx.Client, model: str = "pangram-4") -> None:
        self.api_key = api_key
        self.client = client
        self.model = model

    @property
    def headers(self) -> dict[str, str]:
        return {"x-api-key": self.api_key}

    def request_identity(self, candidate_hash: str) -> str:
        return sha256(f"{self.model}\0{candidate_hash}".encode()).hexdigest()

    def ensure_access(self) -> None:
        """Verify async API authentication without creating a billable task.

        Pangram's current async API does not document a /models endpoint.  Probe a
        syntactically valid impossible task id instead: 401 means the key is rejected;
        403/404 mean authentication succeeded but the task is unavailable/not owned.
        The detector contract itself is verified from the returned result version after
        a real candidate is submitted.
        """
        probe_id = "00000000-0000-0000-0000-000000000000"
        response = self.client.get(f"/task/{probe_id}", headers=self.headers)
        if response.status_code in {200, 403, 404}:
            return
        response.raise_for_status()

    def submit(self, text: str, candidate_hash: str) -> PangramTask:
        identity = self.request_identity(candidate_hash)
        response = self.client.post(
            "/task",
            headers=self.headers,
            json={"text": text, "public_dashboard_link": False},
        )
        response.raise_for_status()
        task_id = str(response.json()["task_id"])
        return PangramTask(task_id, identity, candidate_hash, self.model)

    @staticmethod
    def parse_result(payload: dict[str, Any]) -> PangramResult:
        windows = tuple(payload.get("windows") or [])
        bad_window = any(
            str(w.get("prediction_short") or w.get("prediction") or "").lower()
            in {"ai", "ai-assisted", "ai assisted"}
            for w in windows if isinstance(w, dict)
        )
        stage = str(payload.get("stage") or "")
        version = str(payload.get("version") or "")
        prediction = str(payload.get("prediction_short") or "")
        fraction_ai = float(payload.get("fraction_ai") or 0)
        fraction_assisted = float(payload.get("fraction_ai_assisted") or 0)
        is_human = bool(
            stage == "STAGE_SUCCESS"
            and version == "4.0"
            and prediction.lower() == "human"
            and fraction_ai == 0
            and fraction_assisted == 0
            and not bad_window
        )
        return PangramResult(
            stage, version, prediction, fraction_ai, fraction_assisted,
            windows, payload, is_human,
        )

    def poll(self, task_id: str) -> PangramResult:
        response = self.client.get(f"/task/{task_id}", headers=self.headers)
        response.raise_for_status()
        return self.parse_result(response.json())

    def evaluate(self, text: str, candidate_hash: str, pending: dict[str, str] | None = None) -> PangramResult:
        identity = self.request_identity(candidate_hash)
        task_id = (pending or {}).get(identity)
        if task_id is None:
            task_id = self.submit(text, candidate_hash).task_id
        return self.poll(task_id)
