from __future__ import annotations

from hashlib import sha256
import json
from typing import Mapping, Sequence


BOUNDARY_FORMAT = "authorial-flow-generation-boundary-v1"


def generation_boundary_id(
    accepted_moves: Sequence[str],
    atom_coverage: Mapping[str, bool],
    *,
    graph_version: str,
    program_version: str,
) -> str:
    """Identify the exact accepted boundary controlled by pressure/edge decisions."""
    passage = " ".join(str(move) for move in accepted_moves)
    coverage_json = json.dumps(
        {str(key): bool(value) for key, value in atom_coverage.items()},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    payload = {
        "format": BOUNDARY_FORMAT,
        "accepted_passage_sha256": sha256(passage.encode("utf-8")).hexdigest(),
        "accepted_move_count": len(accepted_moves),
        "coverage_sha256": sha256(coverage_json.encode("utf-8")).hexdigest(),
        "graph_version": str(graph_version or ""),
        "program_version": str(program_version or ""),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()

