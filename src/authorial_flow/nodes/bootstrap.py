from __future__ import annotations

from ..project import ProjectInputs, compute_thread_id
from ..policy import PolicySnapshot
from ..version import GRAPH_VERSION


def bootstrap_state(project_dir, policy_dir, learning_version: str = "learning-v1") -> dict:
    project = ProjectInputs.load(project_dir)
    policy = PolicySnapshot.load(policy_dir)
    thread_id = compute_thread_id(project, policy, GRAPH_VERSION, learning_version)
    return {
        "project_id": project.manifest_hash[:16],
        "thread_id": thread_id,
        "source_hash": project.hashes["INPUT.md"],
        "protected_input_hashes": dict(project.hashes),
        "graph_version": GRAPH_VERSION,
        "regression_version": learning_version,
        "phase": "bootstrap",
        "status": "running",
    }
