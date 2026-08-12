from __future__ import annotations

from enum import StrEnum
from pydantic import BaseModel, ConfigDict


class Authority(StrEnum):
    OWNER_LOCKED = "OWNER_LOCKED"
    OWNER_GROUNDED = "OWNER_GROUNDED"
    AI_PROVISIONAL = "AI_PROVISIONAL"
    RESEARCH_PROVISIONAL = "RESEARCH_PROVISIONAL"
    OPEN_AUTHORIAL = "OPEN_AUTHORIAL"


class AuthorityUnit(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    text: str
    authority: Authority
    exact_lock: bool = False
    disposition: str = "unresolved"
    reason: str = ""

    @property
    def must_preserve(self) -> bool:
        return self.authority in {Authority.OWNER_LOCKED, Authority.OWNER_GROUNDED}
