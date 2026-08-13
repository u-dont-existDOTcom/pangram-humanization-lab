from __future__ import annotations

from typing import Any


class CallStats:
    def __init__(self, ledger: Any):
        self.ledger = ledger
        self.first_success: dict[tuple[str, str, str], dict[str, Any]] = {}

    def note(self, section_id: str, model: str, version: str, measurement_key: str, detector: dict[str, Any]) -> None:
        key = (section_id, model, version)
        if detector.get("prediction_short") != "Human" or key in self.first_success:
            return
        section = self.ledger.section_summary(section_id, model, version)
        self.first_success[key] = {
            "paid_calls_to_human": section["paid_api_calls"],
            "estimated_credits_to_human": section["estimated_credits"],
            "first_human_measurement_key": measurement_key,
        }

    def summary(self) -> dict[str, Any]:
        out = self.ledger.audit_summary()
        for section in out.get("sections", []):
            key = (section["section_id"], section["model"], section["version"])
            section.update(self.first_success.get(key, {
                "paid_calls_to_human": None,
                "estimated_credits_to_human": None,
                "first_human_measurement_key": None,
            }))
        return out
