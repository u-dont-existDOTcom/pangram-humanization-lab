from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .source_provenance import SourceProvenance


class TaskMode(StrEnum):
    P0='P0'; P1='P1'; P2='P2'; P2S='P2S'; P3='P3'; P4='P4'


@dataclass(frozen=True)
class ModeDecision:
    mode: TaskMode
    reason: str
    substantive_permission: bool
    research_permission: bool
    requires_owner_authority: bool=False


def _decision(mode:TaskMode,reason:str,requires_owner_authority:bool=False)->ModeDecision:
    substantive=mode in {TaskMode.P3,TaskMode.P4}
    research=mode in {TaskMode.P0,TaskMode.P3,TaskMode.P4}
    return ModeDecision(mode,reason,substantive,research,requires_owner_authority)


def choose_mode(requested_operation:str, provenance:SourceProvenance, *, semantic_sanity:bool=True,
                locked_conflict:bool=False)->ModeDecision:
    token=requested_operation.strip().upper()
    if token in {m.value for m in TaskMode}:
        mode=TaskMode(token)
        if locked_conflict and mode in {TaskMode.P3,TaskMode.P4}:
            return _decision(mode,'explicit mode conflicts with higher-priority owner lock',True)
        return _decision(mode,f'explicit {mode.value} request')

    if requested_operation.strip().lower() != 'humanize':
        # Least invasive useful default for unspecified editorial requests.
        return _decision(TaskMode.P2,'unspecified edit defaults to line edit')

    if provenance is SourceProvenance.OWNER_FINAL:
        return _decision(TaskMode.P2S if not semantic_sanity else TaskMode.P2,
                         'owner-final material remains non-substantive by default')
    if provenance is SourceProvenance.SOURCE_POOL:
        return _decision(TaskMode.P4,'source-pool material requires fresh construction')
    if provenance in {SourceProvenance.AI_FROM_OWNER_INPUTS,SourceProvenance.MIXED}:
        if not semantic_sanity or provenance is SourceProvenance.MIXED:
            return _decision(TaskMode.P3,'AI/mixed inherited thought requires developmental repair')
        return _decision(TaskMode.P2S,'AI realization appears semantically sound; reconstruct realization only')
    if provenance is SourceProvenance.RESEARCH_PROVISIONAL:
        return _decision(TaskMode.P3,'research-provisional material requires developmental authority separation')
    return _decision(TaskMode.P2,'natural owner draft defaults to smallest effective edit')
