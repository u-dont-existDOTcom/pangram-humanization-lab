from __future__ import annotations
from typing import Any
from ..source_provenance import ProvenanceResult, classify_provenance


def classify_source_node(state:dict[str,Any])->dict[str,Any]:
    result=classify_provenance(str(state.get('source_text') or ''),metadata=state.get('source_metadata') or {})
    return {'source_provenance':result.provenance.value,'source_provenance_reason':result.reason,
            'source_provenance_evidence':list(result.evidence_spans)}
