from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable

from .cache import PangramCache


class PangramError(RuntimeError):
    pass


class UrllibTransport:
    def request(self, method, url, headers=None, body=None, timeout=60):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                return {"status": resp.status, "json": json.loads(raw) if raw else {}}
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                body_obj = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                body_obj = {"raw": raw}
            return {"status": exc.code, "json": body_obj}


@dataclass
class PangramClient:
    api_key: str
    model: str = "pangram-4"
    expected_version: str = "4.0"
    base_url: str = "https://text.external-api.pangram.com"
    transport: object | None = None
    sleep: Callable[[float], None] = time.sleep
    sync: Callable[[str], None] = lambda _reason: None
    poll_interval: float = 2.0
    poll_timeout: float = 300.0
    get_retries: int = 5

    def __post_init__(self):
        if not self.api_key:
            raise PangramError("PANGRAM_API_KEY is empty")
        if self.transport is None:
            self.transport = UrllibTransport()

    def _headers(self, json_body=False):
        out = {"x-api-key": self.api_key, "Accept": "application/json"}
        if json_body:
            out["Content-Type"] = "application/json"
        return out

    def _request_once(self, method: str, url: str, body=None) -> dict:
        try:
            response = self.transport.request(method, url, headers=self._headers(body is not None), body=body)
        except (OSError, urllib.error.URLError, TimeoutError) as exc:
            raise PangramError(f"Pangram {method} network failure: {exc}") from exc
        status = int(response.get("status", 0))
        if status != 200:
            raise PangramError(f"Pangram HTTP {status}: {response.get('json', {})}")
        obj = response.get("json", {})
        if not isinstance(obj, dict):
            raise PangramError("Pangram returned non-object JSON")
        return obj

    def probe_connectivity(self) -> None:
        """Check async task-API reachability without creating a billable task.

        An invented task id cannot prove that the supplied API key is accepted for
        task submission. Pangram can return 404 here even when a subsequent POST
        rejects the same key with HTTP 401.
        """
        url=f"{self.base_url}/task/00000000-0000-0000-0000-000000000000"
        try:
            response=self.transport.request("GET",url,headers=self._headers(False),body=None)
        except (OSError, urllib.error.URLError, TimeoutError) as exc:
            raise PangramError(f"Pangram connectivity probe network failure: {exc}") from exc
        status=int(response.get("status",0))
        if status in {200,403,404}:
            print(
                f"[pangram] connectivity probe reached task API (HTTP {status}); "
                "authentication not established; no billable task created",
                flush=True,
            )
            return
        if status == 401:
            raise PangramError("Pangram API key rejected by connectivity probe (HTTP 401)")
        if status == 402:
            raise PangramError("Pangram account has insufficient credits (HTTP 402)")
        raise PangramError(f"Unexpected Pangram connectivity-probe HTTP {status}: {response.get('json',{})}")

    def probe_auth(self) -> None:
        """Backward-compatible alias for the non-billable connectivity probe."""
        self.probe_connectivity()

    def _get_with_retry(self, url: str) -> dict:
        delay = 1.0
        last = None
        for attempt in range(self.get_retries + 1):
            try:
                return self._request_once("GET", url)
            except PangramError as exc:
                last = exc
                msg = str(exc)
                retryable = "network failure" in msg or any(f"HTTP {code}" in msg for code in (429,500,502,503,504))
                if not retryable or attempt >= self.get_retries:
                    raise
                print(f"[pangram] transient GET failure; retrying in {delay:g}s: {exc}", flush=True)
                self.sleep(delay); delay=min(8.0,delay*2)
        raise PangramError(str(last))

    def submit_once(self, text: str) -> str:
        # POST is deliberately not automatically retried. If transport fails after
        # Pangram accepts a request but before task_id returns, another POST can cost
        # money twice and cannot be deduplicated locally.
        obj = self._request_once("POST", f"{self.base_url}/task", {"text": text, "public_dashboard_link": False, "model": self.model})
        task_id = str(obj.get("task_id") or "")
        if not task_id:
            raise PangramError(f"Pangram submit response missing task_id: {obj}")
        return task_id

    def poll(self, task_id: str) -> dict:
        deadline = time.monotonic() + self.poll_timeout
        last_stage = None
        while True:
            obj = self._get_with_retry(f"{self.base_url}/task/{task_id}")
            stage = str(obj.get("stage") or "")
            if stage != last_stage:
                print(f"[pangram] task {task_id}: {stage or 'pending'}", flush=True)
                last_stage = stage
            if stage == "STAGE_SUCCESS":
                return obj
            if stage == "STAGE_FAILED":
                raise PangramError(f"Pangram task {task_id} terminal failure: {obj}")
            if time.monotonic() >= deadline:
                raise PangramError(f"Pangram task {task_id} did not finish within {self.poll_timeout:g}s; task_id is checkpointed and will be resumed")
            self.sleep(self.poll_interval)

    def detect_cached(self, text: str, cache: PangramCache, measurement_key: str = "base") -> dict:
        rec = cache.lookup(self.model, self.expected_version, text, measurement_key)
        if rec and rec.get("status") == "success" and isinstance(rec.get("result"), dict):
            print(f"[pangram] CACHE HIT {measurement_key} {rec['text_sha256'][:12]} → {rec['result'].get('headline') or rec['result'].get('prediction_short')}", flush=True)
            return rec["result"]
        if rec and rec.get("status") == "submit_ambiguous":
            raise PangramError(
                f"Previous Pangram submit for {measurement_key} ended ambiguously before a task_id was received. "
                "The harness will not POST it again automatically because that could duplicate a paid call. "
                f"Inspect/resolve cache record {cache.path_for(self.model, self.expected_version, text, measurement_key)}."
            )
        if rec and rec.get("status") == "terminal_wrong_version":
            submitted_model = str(rec.get("submitted_model") or "")
            actual = str((rec.get("result") or {}).get("version") or "")
            if submitted_model == self.model:
                raise PangramError(
                    f"Pangram terminal version mismatch after explicit model {self.model!r}: "
                    f"expected {self.expected_version!r}, got {actual!r}; refusing another paid POST"
                )
            print(
                f"[pangram] MIGRATE prior terminal task {rec.get('task_id')} returned {actual or 'unknown version'} "
                f"without an explicit model selector; preserved result and will submit one corrected {self.model} task",
                flush=True,
            )
            rec = None

        submitted_model = ""
        if rec and rec.get("status") == "pending" and rec.get("task_id"):
            task_id = str(rec["task_id"])
            submitted_model = str(rec.get("submitted_model") or "")
            print(f"[pangram] RESUME pending task {task_id} for {measurement_key}; NO new POST", flush=True)
        else:
            print(f"[pangram] SUBMIT new task for {measurement_key}; no cached equivalent exists", flush=True)
            try:
                task_id = self.submit_once(text)
            except Exception as exc:
                msg = str(exc)
                lowered = msg.lower()
                ambiguous = ("network failure" in lowered or any(f"HTTP {code}" in msg for code in (429,500,502,503,504)))
                if ambiguous:
                    cache.save_submit_ambiguous(self.model, self.expected_version, text, measurement_key, error=msg)
                    self.sync(f"pangram ambiguous submit {measurement_key}")
                else:
                    cache.save_failure(self.model, self.expected_version, text, measurement_key, error=msg)
                    self.sync(f"pangram submit failure {measurement_key}")
                raise
            submitted_model = self.model
            cache.save_pending(self.model, self.expected_version, text, measurement_key, task_id, submitted_model=self.model)
            self.sync(f"pangram task checkpoint {measurement_key}")
            print(f"[pangram] CHECKPOINTED task_id={task_id} model={self.model} before polling", flush=True)

        try:
            result = self.poll(task_id)
        except Exception as exc:
            if "terminal failure" in str(exc):
                cache.save_failure(self.model, self.expected_version, text, measurement_key, task_id=task_id, error=str(exc))
            self.sync(f"pangram poll state {measurement_key}")
            raise

        actual_version = str(result.get("version") or "")
        if self.expected_version and actual_version != self.expected_version:
            cache.save_wrong_version(
                self.model, self.expected_version, text, measurement_key, task_id, result,
                submitted_model=submitted_model,
            )
            self.sync(f"pangram wrong-version result {measurement_key}")
            if submitted_model == self.model:
                raise PangramError(
                    f"Pangram terminal version mismatch after explicit model {self.model!r}: "
                    f"expected {self.expected_version!r}, got {actual_version!r}; refusing another paid POST"
                )
            print(
                f"[pangram] PRESERVED paid task {task_id} as terminal version {actual_version!r}; "
                f"v2.0 had omitted the model selector. Submitting one corrected {self.model} task now.",
                flush=True,
            )
            try:
                task_id = self.submit_once(text)
            except Exception as exc:
                msg = str(exc)
                lowered = msg.lower()
                ambiguous = ("network failure" in lowered or any(f"HTTP {code}" in msg for code in (429,500,502,503,504)))
                if ambiguous:
                    cache.save_submit_ambiguous(self.model, self.expected_version, text, measurement_key, error=msg)
                    self.sync(f"pangram ambiguous corrected submit {measurement_key}")
                else:
                    cache.save_failure(self.model, self.expected_version, text, measurement_key, error=msg)
                    self.sync(f"pangram corrected submit failure {measurement_key}")
                raise
            submitted_model = self.model
            cache.save_pending(self.model, self.expected_version, text, measurement_key, task_id, submitted_model=self.model)
            self.sync(f"pangram corrected task checkpoint {measurement_key}")
            print(f"[pangram] CHECKPOINTED corrected task_id={task_id} model={self.model} before polling", flush=True)
            result = self.poll(task_id)
            actual_version = str(result.get("version") or "")
            if self.expected_version and actual_version != self.expected_version:
                cache.save_wrong_version(
                    self.model, self.expected_version, text, measurement_key, task_id, result,
                    submitted_model=self.model,
                )
                self.sync(f"pangram corrected wrong-version result {measurement_key}")
                raise PangramError(
                    f"Pangram terminal version mismatch after corrected explicit model {self.model!r}: "
                    f"expected {self.expected_version!r}, got {actual_version!r}; refusing another paid POST"
                )

        cache.save_success(
            self.model, self.expected_version, text, measurement_key, task_id, result,
            submitted_model=submitted_model,
        )
        self.sync(f"pangram result {measurement_key}")
        print(f"[pangram] SAVED {measurement_key}: {result.get('headline') or result.get('prediction_short')} AI={result.get('fraction_ai')} assisted={result.get('fraction_ai_assisted')} human={result.get('fraction_human')}", flush=True)
        return result
