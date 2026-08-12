from __future__ import annotations

from typing import Protocol, Any
from pydantic import BaseModel, ConfigDict


class SearchHit(BaseModel):
    model_config=ConfigDict(frozen=True, extra='forbid')
    title: str
    url: str
    snippet: str=''
    primary_hint: bool=False


class ResearchQuestion(BaseModel):
    model_config=ConfigDict(frozen=True, extra='forbid')
    uncertainty: str
    material_consequence: str
    query: str=''


class RetrievedSource(BaseModel):
    model_config=ConfigDict(frozen=True, extra='forbid')
    url: str
    final_url: str
    mime_type: str
    body: str
    body_sha256: str
    retrieved_at: float
    access_level: Any
    headers: dict[str,str]
    access_limitation: str=''


class ResearchProvider(Protocol):
    def search(self,query:str,limit:int)->list[SearchHit]: ...


class Fetcher(Protocol):
    def fetch(self,url:str)->RetrievedSource: ...
