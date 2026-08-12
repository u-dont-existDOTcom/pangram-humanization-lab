from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationScore:
    hard_pass: bool
    target_metrics: dict[str,float]
    fidelity_regressions: tuple[str,...]=()
    owner_regressions: tuple[str,...]=()

    @property
    def promotion_eligible(self)->bool:
        return bool(self.hard_pass and not self.fidelity_regressions and not self.owner_regressions)
