from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from .pangram4 import PangramClient


class ExactTextRepeatBlocked(RuntimeError):
    def __init__(self, section_id: str, text_sha256: str, prior_measurement_key: str):
        self.section_id = section_id
        self.text_sha256 = text_sha256
        self.prior_measurement_key = prior_measurement_key
        super().__init__(
            "exact Pangram text already has a paid/reserved measurement in this audit section: "
            f"section={section_id} sha256={text_sha256} prior={prior_measurement_key}"
        )


@dataclass
class TrackedPangramClient(PangramClient):
    call_ledger: Any | None = None
    _call_context: tuple[str, str, str, str, bool] | None = field(default=None, init=False, repr=False)

    def detect_cached(
        self,
        text: str,
        cache: Any,
        measurement_key: str = "base",
        *,
        section_id: str | None = None,
        budget_scope: str = "section",
        allow_exact_repeat: bool = False,
    ) -> dict:
        if self.call_ledger is not None and not section_id:
            raise ValueError("section_id is required when call accounting is enabled")
        if budget_scope not in {"section", "aggregate"}:
            raise ValueError("budget_scope must be 'section' or 'aggregate'")
        if not isinstance(allow_exact_repeat, bool):
            raise ValueError("allow_exact_repeat must be boolean")
        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if self.call_ledger is not None:
            rec = cache.lookup(self.model, self.expected_version, text, measurement_key)
            if rec and rec.get("status") == "success" and isinstance(rec.get("result"), dict):
                self.call_ledger.record_cache_hit(
                    section_id,
                    self.model,
                    self.expected_version,
                    measurement_key,
                    sha,
                    budget_scope=budget_scope,
                )
            elif rec and rec.get("status") == "pending" and rec.get("task_id"):
                self.call_ledger.record_pending_resume(
                    section_id,
                    self.model,
                    self.expected_version,
                    measurement_key,
                    sha,
                    budget_scope=budget_scope,
                )
        previous = self._call_context
        self._call_context = (section_id or "", measurement_key, sha, budget_scope, allow_exact_repeat)
        try:
            return super().detect_cached(text, cache, measurement_key=measurement_key)
        finally:
            self._call_context = previous

    def _prior_exact_reservation(self, section_id: str, sha: str) -> dict[str, Any] | None:
        if self.call_ledger is None:
            return None
        key = self.call_ledger._key(section_id, self.model, self.expected_version)
        section = self.call_ledger.state.get("sections", {}).get(key, {})
        for event in reversed(section.get("events", [])):
            if event.get("text_sha256") != sha:
                continue
            if event.get("type") in {"paid_post_reserved", "external_paid_measurement_imported"}:
                if event.get("count_effect") == "not_counted_no_task_created_no_owner_account_usage":
                    continue
                return event
        return None

    def submit_once(self, text: str) -> str:
        if self.call_ledger is not None:
            if self._call_context is None:
                raise RuntimeError("detector submission attempted without a section call context")
            section_id, measurement_key, sha, budget_scope, allow_exact_repeat = self._call_context
            if not allow_exact_repeat:
                prior = self._prior_exact_reservation(section_id, sha)
                if prior is not None and prior.get("measurement_key") != measurement_key:
                    raise ExactTextRepeatBlocked(
                        section_id,
                        sha,
                        str(prior.get("measurement_key", "")),
                    )
            self.call_ledger.reserve_paid_call(
                section_id=section_id,
                model=self.model,
                version=self.expected_version,
                measurement_key=measurement_key,
                text_sha256=sha,
                word_count=len(text.split()),
                budget_scope=budget_scope,
            )
            self.sync(f"pangram call reservation {measurement_key}")
        return super().submit_once(text)
