from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import os
from typing import Any, Callable, Iterator

from .config import RuntimeConfig
from .state import AuthorialState
from .nodes.owner_interrupt import owner_review_node, owner_ambiguity_node, owner_research_adoption_node
from .nodes.repair import repair_restart_boundary_node
from .routing import (route_generation, route_after_regressions, route_after_representation,
                      route_after_cold_audit, route_after_detector, route_after_owner_learning,
                      route_after_freeze, route_after_repair, route_after_repair_restart,
                      route_after_supervisor)

NodeFn=Callable[[AuthorialState],dict[str,Any]]


def _noop(_state: AuthorialState) -> dict[str,Any]:
    return {}


@dataclass(frozen=True)
class GraphDependencies:
    regressions: NodeFn=_noop
    representation: NodeFn=_noop
    generation: NodeFn=_noop
    cold_audit: NodeFn=_noop
    freeze: NodeFn=_noop
    detector: NodeFn=_noop
    owner_learning: NodeFn=_noop
    repair: NodeFn=_noop
    supervisor: NodeFn=_noop


def finalize_node(state: AuthorialState) -> dict[str,Any]:
    # Owner-review node already determines accepted/deferred/feedback status.
    return {"phase":"finalized","status":state.get("status","completed")}


def build_graph(dependencies: GraphDependencies, *, checkpointer: Any=None):
    try:
        from langgraph.graph import StateGraph, START, END
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "LangGraph is not installed. Run INSTALL-AND-RUN.sh or install requirements.lock."
        ) from exc

    builder=StateGraph(AuthorialState)
    builder.add_node("regressions",dependencies.regressions)
    builder.add_node("representation",dependencies.representation)
    builder.add_node("generation",dependencies.generation)
    builder.add_node("cold_audit",dependencies.cold_audit)
    builder.add_node("freeze",dependencies.freeze)
    builder.add_node("detector",dependencies.detector)
    builder.add_node("owner_review",owner_review_node)
    builder.add_node("owner_ambiguity",owner_ambiguity_node)
    builder.add_node("research_adoption",owner_research_adoption_node)
    builder.add_node("owner_learning",dependencies.owner_learning)
    builder.add_node("repair",dependencies.repair)
    builder.add_node("repair_restart",repair_restart_boundary_node)
    builder.add_node("supervisor_pause",dependencies.supervisor)
    builder.add_node("finalize",finalize_node)

    builder.add_edge(START,"regressions")
    builder.add_conditional_edges("regressions",route_after_regressions,{"representation":"representation","repair":"repair","supervisor_pause":"supervisor_pause"})
    builder.add_conditional_edges(
        "representation",route_after_representation,
        {"generation":"generation","repair":"repair","owner_ambiguity":"owner_ambiguity","research_adoption":"research_adoption","supervisor_pause":"supervisor_pause"},
    )
    builder.add_edge("owner_ambiguity","owner_learning")
    builder.add_edge("research_adoption","owner_learning")
    builder.add_conditional_edges(
        "generation",
        route_generation,
        {"generation":"generation","cold_audit":"cold_audit","repair":"repair","supervisor_pause":"supervisor_pause"},
    )
    builder.add_conditional_edges("cold_audit",route_after_cold_audit,{"freeze":"freeze","repair":"repair","supervisor_pause":"supervisor_pause"})
    builder.add_conditional_edges("freeze",route_after_freeze,{"detector":"detector","supervisor_pause":"supervisor_pause"})
    builder.add_conditional_edges("detector",route_after_detector,{"detector":"detector","owner_review":"owner_review","repair":"repair","finalize":"finalize","supervisor_pause":"supervisor_pause"})
    builder.add_edge("owner_review","owner_learning")
    builder.add_conditional_edges("owner_learning",route_after_owner_learning,{"regressions":"regressions","representation":"representation","finalize":"finalize","supervisor_pause":"supervisor_pause"})
    builder.add_conditional_edges("repair",route_after_repair,{"regressions":"regressions","repair":"repair","repair_restart":"repair_restart","owner_ambiguity":"owner_ambiguity","finalize":"finalize","supervisor_pause":"supervisor_pause"})
    builder.add_conditional_edges("repair_restart",route_after_repair_restart,{"regressions":"regressions","representation":"representation","generation":"generation","cold_audit":"cold_audit","freeze":"freeze","detector":"detector","owner_learning":"owner_learning"})
    supervisor_targets = (
        "regressions", "representation", "generation", "cold_audit", "freeze",
        "detector", "owner_review", "owner_ambiguity", "research_adoption",
        "owner_learning", "repair", "repair_restart", "finalize", "supervisor_pause",
    )
    builder.add_conditional_edges(
        "supervisor_pause",
        route_after_supervisor,
        {name: name for name in supervisor_targets},
    )
    builder.add_edge("finalize",END)
    return builder.compile(checkpointer=checkpointer)


@contextmanager
def open_graph(config: RuntimeConfig, dependencies: GraphDependencies) -> Iterator[Any]:
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "langgraph-checkpoint-sqlite is not installed. Run INSTALL-AND-RUN.sh or install requirements.lock."
        ) from exc

    os.environ.setdefault("LANGGRAPH_STRICT_MSGPACK","true")
    config.state_dir.mkdir(parents=True,exist_ok=True)
    # Keep saver open for the complete graph lifetime; thread_id is supplied per invoke call.
    with SqliteSaver.from_conn_string(str(config.checkpoint_db)) as checkpointer:
        setup=getattr(checkpointer,"setup",None)
        if callable(setup):
            setup()
        yield build_graph(dependencies,checkpointer=checkpointer)
