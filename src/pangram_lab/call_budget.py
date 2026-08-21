from __future__ import annotations

import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SECTION_CALL_CAP = 6
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
    def __init__(self, root: Path | str, audit_id: str, cap: int = SECTION_CALL_CAP):
        if cap > SECTION_CALL_CAP:
            raise ValueError(f"cap cannot exceed {SECTION_CALL_CAP}")
        if not audit_id or not str(audit_id).strip():
            raise ValueError("audit_id must be non-empty")
        self.root = Path(root)
        self.audit_id = str(audit_id)
        self.cap = int(cap)
        self.path = self.root / "state" / "pangram-call-ledgers" / f"{self._safe(self.audit_id)}.json"
        self.state = self._load()

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
        return {
            "format": "pangram-call-ledger-v1",
            "audit_id": self.audit_id,
            "section_call_cap": self.cap,
            "sections": {},
        }

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

    def _summary_from_section(self, section: dict[str, Any]) -> dict[str, Any]:
        scope = section.get("budget_scope", "section")
        return {k: v for k, v in section.items() if k != "events"} | {
            "hard_cap_applies": scope == "section",
            "cap": self.cap if scope == "section" else None,
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
