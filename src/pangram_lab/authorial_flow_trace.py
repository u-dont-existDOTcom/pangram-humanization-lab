from __future__ import annotations

import collections
import json
import re
from pathlib import Path


SCHEMA_VERSION = "authorial-flow-rsg-ls/v1"
ALLOWED_FUNCTIONS = {
    "CONCRETIZE",
    "COMPLICATE",
    "TEST",
    "QUALIFY",
    "COUNTEREXAMPLE",
    "REFRAME",
    "ANALOGIZE",
    "RECALL",
    "SELF_IMPLICATE",
    "APPLY",
    "RESOLVE",
    "REOPEN",
    "OTHER",
    "UNKNOWN",
}
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _require_hex64(value: object, field: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not _HEX64.fullmatch(value):
        raise ValueError(f"{field} must be a lowercase 64-character SHA-256 hex string")
    return value


def _label(value: object, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be null or a non-empty string")
    return value.strip()


def validate_trace(trace: dict) -> dict:
    if not isinstance(trace, dict):
        raise ValueError("trace must be a JSON object")
    if trace.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION!r}")
    if trace.get("condition") != "RSG-LS":
        raise ValueError("condition must be 'RSG-LS'")
    experiment_id = trace.get("experiment_id")
    if not isinstance(experiment_id, str) or not experiment_id.strip():
        raise ValueError("experiment_id must be a non-empty string")
    _require_hex64(trace.get("source_packet_sha256"), "source_packet_sha256")

    model = trace.get("model")
    if not isinstance(model, dict):
        raise ValueError("model must be an object")
    for key in ("provider", "name"):
        if not isinstance(model.get(key), str) or not model[key].strip():
            raise ValueError(f"model.{key} must be a non-empty string")
    version = model.get("version")
    if version is not None and (not isinstance(version, str) or not version.strip()):
        raise ValueError("model.version must be null or a non-empty string")

    steps = trace.get("steps")
    if not isinstance(steps, list):
        raise ValueError("steps must be an array")

    revealed: list[str] = []
    selected_positions: dict[str, int] = {}
    stopped = False
    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            raise ValueError(f"steps[{index - 1}] must be an object")
        if step.get("step") != index:
            raise ValueError(f"steps[{index - 1}].step must equal {index}")
        if stopped:
            raise ValueError("no steps may follow a STOP action")

        action = step.get("controller_action")
        if action not in {"REVEAL", "STOP"}:
            raise ValueError(f"step {index}: controller_action must be REVEAL or STOP")
        after = step.get("revealed_source_ids_after")
        if not isinstance(after, list) or any(not isinstance(x, str) or not x for x in after):
            raise ValueError(f"step {index}: revealed_source_ids_after must be an array of non-empty strings")
        if len(after) != len(set(after)):
            raise ValueError(f"step {index}: revealed_source_ids_after contains duplicates")
        _require_hex64(
            step.get("accepted_prose_sha256_after"),
            f"step {index}: accepted_prose_sha256_after",
        )

        if action == "STOP":
            if after != revealed:
                raise ValueError(f"step {index}: STOP may not change revealed_source_ids_after")
            for field in ("selected_source_id", "selected_source_position", "selection_function"):
                if step.get(field) is not None:
                    raise ValueError(f"step {index}: {field} must be null on STOP")
            if step.get("writer_action") is not None:
                raise ValueError(f"step {index}: writer_action must be null on STOP")
            if step.get("candidate_delta_sha256") is not None:
                raise ValueError(f"step {index}: candidate_delta_sha256 must be null on STOP")
            stopped = True
        else:
            source_id = step.get("selected_source_id")
            if not isinstance(source_id, str) or not source_id:
                raise ValueError(f"step {index}: selected_source_id must be a non-empty string on REVEAL")
            if source_id in revealed:
                raise ValueError(f"step {index}: selected_source_id was already revealed")
            expected_after = [*revealed, source_id]
            if after != expected_after:
                raise ValueError(
                    f"step {index}: revealed_source_ids_after must append exactly selected_source_id"
                )
            position = step.get("selected_source_position")
            if not isinstance(position, int) or isinstance(position, bool) or position < 1:
                raise ValueError(f"step {index}: selected_source_position must be a positive integer")
            if position in selected_positions.values():
                raise ValueError(f"step {index}: selected_source_position was already revealed")
            selected_positions[source_id] = position
            function = step.get("selection_function")
            if function not in ALLOWED_FUNCTIONS:
                raise ValueError(
                    f"step {index}: selection_function must be one of {sorted(ALLOWED_FUNCTIONS)}"
                )
            writer_action = step.get("writer_action")
            if writer_action not in {"MORE", "WRITE"}:
                raise ValueError(f"step {index}: writer_action must be MORE or WRITE on REVEAL")
            candidate_sha = step.get("candidate_delta_sha256")
            if writer_action == "MORE":
                if candidate_sha is not None:
                    raise ValueError(f"step {index}: MORE requires candidate_delta_sha256=null")
            else:
                _require_hex64(candidate_sha, f"step {index}: candidate_delta_sha256")
            revealed = expected_after

        immediate = step.get("manual_immediate_discharge")
        if immediate not in {None, True, False}:
            raise ValueError(f"step {index}: manual_immediate_discharge must be true, false, or null")
        for field in ("discourse_relation", "fidelity_label", "flow_label"):
            _label(step.get(field), f"step {index}: {field}")

    return trace


def _count_labels(steps: list[dict], field: str) -> dict[str, int]:
    counts = collections.Counter(
        str(step[field]) for step in steps if step.get(field) is not None
    )
    return dict(sorted(counts.items()))


def summarize_trace(trace: dict) -> dict:
    validate_trace(trace)
    steps = trace["steps"]
    reveal_steps = [step for step in steps if step["controller_action"] == "REVEAL"]
    writer_steps = [step for step in reveal_steps if step.get("writer_action") in {"MORE", "WRITE"}]
    write_steps = [step for step in writer_steps if step["writer_action"] == "WRITE"]
    more_steps = [step for step in writer_steps if step["writer_action"] == "MORE"]
    stop_steps = [step for step in steps if step["controller_action"] == "STOP"]

    depths = [len(step["revealed_source_ids_after"]) for step in write_steps]
    positions = [int(step["selected_source_position"]) for step in reveal_steps]
    pair_count = max(0, len(positions) - 1)
    monotonic_pairs = sum(b > a for a, b in zip(positions, positions[1:]))
    exact_next_pairs = sum(b == a + 1 for a, b in zip(positions, positions[1:]))

    immediate_counts = {
        "true": sum(step.get("manual_immediate_discharge") is True for step in steps),
        "false": sum(step.get("manual_immediate_discharge") is False for step in steps),
        "unreviewed": sum(step.get("manual_immediate_discharge") is None for step in steps),
    }

    return {
        "schema_version": trace["schema_version"],
        "experiment_id": trace["experiment_id"],
        "condition": trace["condition"],
        "source_packet_sha256": trace["source_packet_sha256"],
        "model": trace["model"],
        "step_count": len(steps),
        "reveal_count": len(reveal_steps),
        "stop_count": len(stop_steps),
        "write_count": len(write_steps),
        "more_count": len(more_steps),
        "more_rate": round(len(more_steps) / len(writer_steps), 6) if writer_steps else None,
        "accumulation_depth_at_write": {
            "values": depths,
            "min": min(depths) if depths else None,
            "max": max(depths) if depths else None,
            "mean": round(sum(depths) / len(depths), 6) if depths else None,
        },
        "source_position_sequence": positions,
        "source_order": {
            "reveal_pair_count": pair_count,
            "monotonic_increasing_pair_count": monotonic_pairs,
            "monotonic_increasing_pair_fraction": round(monotonic_pairs / pair_count, 6)
            if pair_count
            else None,
            "exact_next_position_pair_count": exact_next_pairs,
            "exact_next_position_pair_fraction": round(exact_next_pairs / pair_count, 6)
            if pair_count
            else None,
        },
        "selection_function_counts": _count_labels(reveal_steps, "selection_function"),
        "manual_immediate_discharge_counts": immediate_counts,
        "discourse_relation_counts": _count_labels(steps, "discourse_relation"),
        "fidelity_label_counts": _count_labels(steps, "fidelity_label"),
        "flow_label_counts": _count_labels(steps, "flow_label"),
    }


def summarize_file(trace_path: Path, output_path: Path | None = None) -> dict:
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    summary = summarize_trace(trace)
    encoded = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    if output_path is None:
        print(encoded, end="")
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(encoded, encoding="utf-8")
    return summary


def add_cli_parsers(subparsers) -> None:
    parser = subparsers.add_parser(
        "authorial-flow-trace",
        help="validate and summarize a metadata-only RSG-LS authorial-flow trace",
    )
    parser.add_argument("trace")
    parser.add_argument("--output")


def run_cli(args) -> int:
    summarize_file(
        Path(args.trace).expanduser(),
        Path(args.output).expanduser() if args.output else None,
    )
    return 0
