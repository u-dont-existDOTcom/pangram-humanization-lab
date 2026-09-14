from __future__ import annotations

import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SECTION_CALL_REVIEW_THRESHOLD = 6
# Compatibility alias for older imports/tests. Six is the default ceiling until
# an explicitly reasoned owner-authorized extension raises it for the same audit.
SECTION_CALL_CAP = SECTION_CALL_REVIEW_THRESHOLD
CREDIT_WORDS = 1000
CREDIT_COST_USD = 0.05
VALID_BUDGET_SCOPES = {"section", "aggregate"}


class SectionCallCapReached(RuntimeError):
    def __init__(self, audit_id: str, section_id: str, cap: int = SECTION_CALL_CAP):
        self.audit_id = audit_id
        self.section_id = section_id
        self.cap = cap
        super().__init__(f"Pangram call cap reached for audit={audit_id} section={section_id}: {cap}")


class PangramCallLedger:
    def __init__(
        self,
        root: Path | str,
        audit_id: str,
        cap: int = SECTION_CALL_REVIEW_THRESHOLD,
        override_reason: str | None = None,
    ):
        if isinstance(cap, bool) or not isinstance(cap, int) or cap < 1:
            raise ValueError("cap must be a positive integer")
        if not audit_id or not str(audit_id).strip():
            raise ValueError("audit_id must be non-empty")
        self.root = Path(root)
        self.audit_id = str(audit_id)
        self.requested_cap = int(cap)
        self.override_reason = str(override_reason).strip() if override_reason is not None else None
        self.path = self.root / "state" / "pangram-call-ledgers" / f"{self._safe(self.audit_id)}.json"
        self._ledger_existed = self.path.exists()
        self.state = self._load()
        self.cap = self._reconcile_cap()

    @staticmethod
    def _safe(value: str) -> str:
        out = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")
        return out or "unnamed"

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _key(section_id: str, model: str, version: str) -> str:
        return f"{section_id}\x1f{model}\x1f{version}"

    @staticmethod
    def _validate_budget_scope(budget_scope: str) -> str:
        scope = str(budget_scope or "section")
        if scope not in VALID_BUDGET_SCOPES:
            raise ValueError(f"budget_scope must be one of {sorted(VALID_BUDGET_SCOPES)}")
        return scope

    def _load(self) -> dict[str, Any]:
        if self.path.exists():
            obj = json.loads(self.path.read_text(encoding="utf-8"))
            if obj.get("audit_id") != self.audit_id:
                raise ValueError("call ledger audit_id mismatch")
            return obj
        initial_cap = min(self.requested_cap, SECTION_CALL_REVIEW_THRESHOLD)
        return {
            "format": "pangram-call-ledger-v1",
            "audit_id": self.audit_id,
            "section_call_review_threshold": SECTION_CALL_REVIEW_THRESHOLD,
            "section_call_cap": initial_cap,
            "sections": {},
        }

    def _reconcile_cap(self) -> int:
        raw_stored = self.state.get("section_call_cap", SECTION_CALL_REVIEW_THRESHOLD)
        if isinstance(raw_stored, bool):
            raise ValueError("stored section_call_cap must be a positive integer")
        try:
            stored = int(raw_stored)
        except (TypeError, ValueError) as exc:
            raise ValueError("stored section_call_cap must be a positive integer") from exc
        if stored < 1:
            raise ValueError("stored section_call_cap must be a positive integer")

        self.state.setdefault("section_call_review_threshold", SECTION_CALL_REVIEW_THRESHOLD)
        requested = self.requested_cap

        # An audit ledger is monotonic. Once an owner-authorized ceiling has been
        # raised, reopening the same audit with default arguments must not silently
        # shrink or reset its accounting boundary.
        if self._ledger_existed and requested < stored:
            return stored

        if requested > stored:
            if requested > SECTION_CALL_REVIEW_THRESHOLD and not self.override_reason:
                raise ValueError(
                    "cap above the six-call review threshold requires a non-empty owner override reason"
                )
            previous = stored
            self.state["section_call_cap"] = requested
            if requested > SECTION_CALL_REVIEW_THRESHOLD:
                self.state.setdefault("cap_overrides", []).append(
                    {
                        "from_cap": previous,
                        "to_cap": requested,
                        "reason": self.override_reason,
                        "recorded_at_utc": self._now(),
                    }
                )
            self._persist()
            return requested

        # New ledgers requested above six start at six in _load so that the
        # extension is always recorded through the branch above. Equal values are
        # otherwise already durable.
        if (
            not self._ledger_existed
            and requested > SECTION_CALL_REVIEW_THRESHOLD
            and stored == SECTION_CALL_REVIEW_THRESHOLD
        ):
            if not self.override_reason:
                raise ValueError(
                    "cap above the six-call review threshold requires a non-empty owner override reason"
                )
            self.state["section_call_cap"] = requested
            self.state.setdefault("cap_overrides", []).append(
                {
                    "from_cap": stored,
                    "to_cap": requested,
                    "reason": self.override_reason,
                    "recorded_at_utc": self._now(),
                }
            )
            self._persist()
            return requested

        return stored

    def _persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self.state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, self.path)

    def _section(
        self,
        section_id: str,
        model: str,
        version: str,
        *,
        budget_scope: str | None = None,
    ) -> dict[str, Any]:
        scope = self._validate_budget_scope(budget_scope or "section")
        key = self._key(section_id, model, version)
        sections = self.state.setdefault("sections", {})
        if key not in sections:
            sections[key] = {
                "section_id": section_id,
                "model": model,
                "version": version,
                "budget_scope": scope,
                "paid_api_calls": 0,
                "cache_hits": 0,
                "pending_resumes": 0,
                "estimated_credits": 0,
                "estimated_cost_usd": 0.0,
                "events": [],
            }
        else:
            section = sections[key]
            existing_scope = section.get("budget_scope")
            if existing_scope is None:
                # Historical ledgers predate budget_scope and were all section-capped.
                section["budget_scope"] = "section"
                existing_scope = "section"
            if budget_scope is not None and existing_scope != scope:
                raise ValueError(
                    f"budget_scope mismatch for section={section_id}: existing={existing_scope} requested={scope}"
                )
        return sections[key]

    def reserve_paid_call(
        self,
        *,
        section_id: str,
        model: str,
        version: str,
        measurement_key: str,
        text_sha256: str,
        word_count: int,
        budget_scope: str = "section",
    ) -> dict[str, Any]:
        scope = self._validate_budget_scope(budget_scope)
        section = self._section(section_id, model, version, budget_scope=scope)
        if scope == "section" and int(section["paid_api_calls"]) >= self.cap:
            raise SectionCallCapReached(self.audit_id, section_id, self.cap)
        words = max(0, int(word_count))
        credits = max(1, math.ceil(words / CREDIT_WORDS))
        section["paid_api_calls"] += 1
        section["estimated_credits"] += credits
        section["estimated_cost_usd"] = round(section["estimated_credits"] * CREDIT_COST_USD, 10)
        section["events"].append(
            {
                "type": "paid_post_reserved",
                "measurement_key": measurement_key,
                "text_sha256": text_sha256,
                "word_count": words,
                "estimated_credits": credits,
                "budget_scope": scope,
                "recorded_at_utc": self._now(),
            }
        )
        self._persist()
        return self.section_summary(section_id, model, version, budget_scope=scope)

    def record_cache_hit(
        self,
        section_id: str,
        model: str,
        version: str,
        measurement_key: str,
        text_sha256: str,
        *,
        budget_scope: str = "section",
    ) -> None:
        section = self._section(section_id, model, version, budget_scope=budget_scope)
        section["cache_hits"] += 1
        section["events"].append(
            {
                "type": "cache_hit",
                "measurement_key": measurement_key,
                "text_sha256": text_sha256,
                "budget_scope": budget_scope,
                "recorded_at_utc": self._now(),
            }
        )
        self._persist()

    def record_pending_resume(
        self,
        section_id: str,
        model: str,
        version: str,
        measurement_key: str,
        text_sha256: str,
        *,
        budget_scope: str = "section",
    ) -> None:
        section = self._section(section_id, model, version, budget_scope=budget_scope)
        section["pending_resumes"] += 1
        section["events"].append(
            {
                "type": "pending_resume",
                "measurement_key": measurement_key,
                "text_sha256": text_sha256,
                "budget_scope": budget_scope,
                "recorded_at_utc": self._now(),
            }
        )
        self._persist()

    def _latest_override_reason(self) -> str | None:
        overrides = self.state.get("cap_overrides", [])
        if not isinstance(overrides, list) or not overrides:
            return None
        reason = overrides[-1].get("reason") if isinstance(overrides[-1], dict) else None
        return str(reason) if reason else None

    def _summary_from_section(self, section: dict[str, Any]) -> dict[str, Any]:
        scope = section.get("budget_scope", "section")
        return {k: v for k, v in section.items() if k != "events"} | {
            "hard_cap_applies": scope == "section",
            "cap": self.cap if scope == "section" else None,
            "review_threshold": SECTION_CALL_REVIEW_THRESHOLD if scope == "section" else None,
            "owner_override_active": scope == "section" and self.cap > SECTION_CALL_REVIEW_THRESHOLD,
            "owner_override_reason": self._latest_override_reason() if scope == "section" else None,
        }

    def section_summary(
        self,
        section_id: str,
        model: str,
        version: str,
        *,
        budget_scope: str | None = None,
    ) -> dict[str, Any]:
        section = self._section(section_id, model, version, budget_scope=budget_scope)
        return self._summary_from_section(section)

    def audit_summary(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "section_call_review_threshold": SECTION_CALL_REVIEW_THRESHOLD,
            "section_call_cap": self.cap,
            "sections": [
                self._summary_from_section(section)
                for section in self.state.get("sections", {}).values()
            ],
        }

    def write_handoff(
        self,
        section_id: str,
        model: str,
        version: str,
        completed_results: list[dict[str, Any]],
    ) -> Path:
        section = self._section(section_id, model, version)
        if section.get("budget_scope", "section") != "section":
            raise ValueError("section-call handoff is only valid for section-scoped boundaries")
        path = (
            self.root
            / "state"
            / "handoffs"
            / "pangram"
            / f"{self._safe(self.audit_id)}-{self._safe(section_id)}.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "format": "pangram-section-handoff-v1",
            "reason": "section_call_cap_reached",
            "audit_id": self.audit_id,
            "section_id": section_id,
            "section": self.section_summary(section_id, model, version, budget_scope="section"),
            "completed_results": completed_results,
            "recorded_at_utc": self._now(),
        }
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, path)
        return path
