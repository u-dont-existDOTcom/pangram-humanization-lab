from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from .pangram4 import PangramClient


@dataclass
class TrackedPangramClient(PangramClient):
    call_ledger: Any | None = None
    _call_context: tuple[str, str, str, str] | None = field(default=None, init=False, repr=False)

    def detect_cached(
        self,
        text: str,
        cache: Any,
        measurement_key: str = "base",
        *,
        section_id: str | None = None,
        budget_scope: str = "section",
    ) -> dict:
        if self.call_ledger is not None and not section_id:
            raise ValueError("section_id is required when call accounting is enabled")
        if budget_scope not in {"section", "aggregate"}:
            raise ValueError("budget_scope must be 'section' or 'aggregate'")
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
        self._call_context = (section_id or "", measurement_key, sha, budget_scope)
        try:
            return super().detect_cached(text, cache, measurement_key=measurement_key)
        finally:
            self._call_context = previous

    def submit_once(self, text: str) -> str:
        if self.call_ledger is not None:
            if self._call_context is None:
                raise RuntimeError("detector submission attempted without a section call context")
            section_id, measurement_key, sha, budget_scope = self._call_context
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
