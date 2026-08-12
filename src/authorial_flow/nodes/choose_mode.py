from __future__ import annotations
from typing import Any
from ..modes import choose_mode
from ..source_provenance import SourceProvenance


def choose_mode_node(state:dict[str,Any])->dict[str,Any]:
    decision=choose_mode(
        str(state.get('requested_operation') or 'humanize'),
        SourceProvenance(str(state['source_provenance'])),
        semantic_sanity=bool(state.get('semantic_sanity',True)),
        locked_conflict=bool(state.get('locked_conflict',False)),
    )
    return {'task_mode':decision.mode.value,'mode_reason':decision.reason,
            'substantive_permission':decision.substantive_permission,
            'research_permission':decision.research_permission,
            'requires_owner_authority':decision.requires_owner_authority}
