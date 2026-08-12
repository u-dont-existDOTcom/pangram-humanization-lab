from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuditDefect:
    code: str
    detail: str
    severity: str = "important"


@dataclass(frozen=True)
class ColdAuditResult:
    defects: tuple[AuditDefect, ...] = ()
    semantic_sanity: bool = True
    curious_reader_chain: bool = True
    stopping_point_ok: bool = True
    fidelity_ok: bool = True

    @property
    def pass_(self) -> bool:
        return bool(
            not self.defects and self.semantic_sanity and self.curious_reader_chain
            and self.stopping_point_ok and self.fidelity_ok
        )


def cold_audit_from_defects(defects: list[AuditDefect] | tuple[AuditDefect, ...]) -> ColdAuditResult:
    """Deterministic container for model-produced cold-audit defects.

    The audit reports defects; revision is a separate operation so a no-defect pass cannot
    trigger novelty paraphrasing.
    """
    return ColdAuditResult(tuple(defects))
