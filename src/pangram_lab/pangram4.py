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

    def probe_auth(self) -> None:
        """Verify the current async external API without creating a billable task."""
        url=f"{self.base_url}/task/00000000-0000-0000-0000-000000000000"
        try:
            response=self.transport.request("GET",url,headers=self._headers(False),body=None)
        except (OSError, urllib.error.URLError, TimeoutError) as exc:
            raise PangramError(f"Pangram auth probe network failure: {exc}") from exc
        status=int(response.get("status",0))
        if status in {200,403,404}:
            print(f"[pangram] auth probe reached task API (HTTP {status}); no billable task created",flush=True)
            return
        if status == 401:
            raise PangramError("Pangram API key rejected (HTTP 401)")
        if status == 402:
            raise PangramError("Pangram account has insufficient credits (HTTP 402)")
        raise PangramError(f"Unexpected Pangram auth-probe HTTP {status}: {response.get('json',{})}")

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

    def _cross_key_guard(self, text: str, cache: PangramCache, measurement_key: str) -> dict | None:
        """Reuse or block same-content work recorded under another key.

        Measurement keys describe experimental identity; they are not permission to
        buy the same model/version/text bytes again. Intentional detector-research
        repeats bypass this guard only via allow_paid_repeat=True on detect_cached.
        """
        equivalents = [
            rec for rec in cache.records_for_text(self.model, self.expected_version, text)
            if rec.get("measurement_key") != measurement_key
        ]
        successes = [rec for rec in equivalents if rec.get("status") == "success" and isinstance(rec.get("result"), dict)]
        if successes:
            # Prefer a non-alias record when both the original and prior aliases exist.
            successes.sort(key=lambda rec: (str(rec.get("source") or "").startswith("cross-key-cache:"), str(rec.get("created_utc") or ""), str(rec.get("measurement_key") or "")))
            source = successes[0]
            source_key = str(source.get("measurement_key") or "")
            result = source["result"]
            cache.save_success(
                self.model,
                self.expected_version,
                text,
                measurement_key,
                str(source.get("task_id") or ""),
                result,
                source=f"cross-key-cache:{source_key}",
                submitted_model=str(source.get("submitted_model") or ""),
            )
            self.sync(f"pangram cross-key cache alias {measurement_key}")
            print(
                f"[pangram] CROSS-KEY CACHE HIT {measurement_key} ← {source_key} "
                f"{source['text_sha256'][:12]}; NO new POST",
                flush=True,
            )
            return result

        pending = [rec for rec in equivalents if rec.get("status") == "pending" and rec.get("task_id")]
        if pending:
            source = pending[0]
            raise PangramError(
                f"Equivalent Pangram text is already pending under measurement key {source.get('measurement_key')!r} "
                f"with task_id {source.get('task_id')!r}. Resume that existing key/task; refusing a new paid POST "
                f"for {measurement_key!r}."
            )

        ambiguous = [rec for rec in equivalents if rec.get("status") == "submit_ambiguous"]
        if ambiguous:
            source = ambiguous[0]
            raise PangramError(
                f"Equivalent Pangram text has an ambiguous prior submit under measurement key "
                f"{source.get('measurement_key')!r}. Resolve/recover that record before any repeat; refusing a new "
                f"paid POST for {measurement_key!r}."
            )

        explicit_wrong = [
            rec for rec in equivalents
            if rec.get("status") == "terminal_wrong_version" and str(rec.get("submitted_model") or "") == self.model
        ]
        if explicit_wrong:
            source = explicit_wrong[0]
            actual = str((source.get("result") or {}).get("version") or "")
            raise PangramError(
                f"Equivalent Pangram text already has an explicit {self.model!r} terminal version mismatch under "
                f"measurement key {source.get('measurement_key')!r}: expected {self.expected_version!r}, got "
                f"{actual!r}; refusing another paid POST under {measurement_key!r}."
            )
        return None

    def detect_cached(
        self,
        text: str,
        cache: PangramCache,
        measurement_key: str = "base",
        *,
        allow_paid_repeat: bool = False,
    ) -> dict:
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

        if not rec and not allow_paid_repeat:
            cross_key = self._cross_key_guard(text, cache, measurement_key)
            if cross_key is not None:
                return cross_key
        elif rec and rec.get("status") == "failed" and not allow_paid_repeat:
            cross_key = self._cross_key_guard(text, cache, measurement_key)
            if cross_key is not None:
                return cross_key

        submitted_model = ""
        if rec and rec.get("status") == "pending" and rec.get("task_id"):
            task_id = str(rec["task_id"])
            submitted_model = str(rec.get("submitted_model") or "")
            print(f"[pangram] RESUME pending task {task_id} for {measurement_key}; NO new POST", flush=True)
        else:
            if allow_paid_repeat:
                print(f"[pangram] EXPLICIT RESEARCH REPEAT authorized for {measurement_key}", flush=True)
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
