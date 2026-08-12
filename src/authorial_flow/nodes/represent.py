from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from ..authority import Authority, AuthorityUnit


class RepresentationResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    section_job: str
    units: tuple[AuthorityUnit, ...]
    exact_identity_strings: tuple[str, ...] = ()

    @property
    def unresolved_required_ids(self) -> tuple[str, ...]:
        return tuple(u.id for u in self.units if u.must_preserve and u.disposition == "unresolved")


def represent_source(
    source: str,
    *,
    default_authority: Authority = Authority.AI_PROVISIONAL,
    locked_spans: tuple[str, ...] = (),
    section_job: str = "develop the thought from its live pressure",
) -> RepresentationResult:
    """Deterministic fallback representation used by tests and bootstrap.

    Model-backed representation may replace this fallback at runtime. The key contract is that
    inherited prose is decomposed into authority units; source order and bridges are not promoted
    merely because they were present in an AI draft.
    """
    paragraphs = [p.strip() for p in source.split("\n\n") if p.strip()]
    if not paragraphs and source.strip():
        paragraphs = [source.strip()]
    units: list[AuthorityUnit] = []
    for i, text in enumerate(paragraphs, 1):
        exact = text in locked_spans
        authority = Authority.OWNER_LOCKED if exact else default_authority
        units.append(AuthorityUnit(
            id=f"u{i:03d}", text=text, authority=authority, exact_lock=exact,
            reason="explicit locked span" if exact else "inherited source representation",
        ))
    return RepresentationResult(
        section_job=section_job,
        units=tuple(units),
        exact_identity_strings=tuple(locked_spans),
    )
