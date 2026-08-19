import json

import pytest

from pangram_lab import authorial_flow_trace as aft


H0 = "0" * 64
H1 = "1" * 64
H2 = "2" * 64
H3 = "3" * 64


def valid_trace():
    return {
        "schema_version": aft.SCHEMA_VERSION,
        "experiment_id": "feasibility-001",
        "condition": "RSG-LS",
        "source_packet_sha256": H0,
        "initial_prose_sha256": H0,
        "initial_revealed_source_ids": [],
        "initial_revealed_source_positions": {},
        "model": {"provider": "test", "name": "writer", "version": None},
        "steps": [
            {
                "step": 1,
                "controller_action": "REVEAL",
                "selected_source_id": "s1",
                "selected_source_position": 1,
                "selection_function": "COMPLICATE",
                "revealed_source_ids_after": ["s1"],
                "writer_action": "MORE",
                "candidate_delta_sha256": None,
                "accepted_prose_sha256_after": H1,
                "manual_immediate_discharge": None,
                "discourse_relation": None,
                "fidelity_label": None,
                "flow_label": None,
            },
            {
                "step": 2,
                "controller_action": "REVEAL",
                "selected_source_id": "s3",
                "selected_source_position": 3,
                "selection_function": "TEST",
                "revealed_source_ids_after": ["s1", "s3"],
                "writer_action": "WRITE",
                "candidate_delta_sha256": H2,
                "accepted_prose_sha256_after": H2,
                "manual_immediate_discharge": False,
                "discourse_relation": "COMPARISON.CONTRAST",
                "fidelity_label": "PASS",
                "flow_label": "PASS",
            },
            {
                "step": 3,
                "controller_action": "REVEAL",
                "selected_source_id": "s2",
                "selected_source_position": 2,
                "selection_function": "CONCRETIZE",
                "revealed_source_ids_after": ["s1", "s3", "s2"],
                "writer_action": "WRITE",
                "candidate_delta_sha256": H3,
                "accepted_prose_sha256_after": H3,
                "manual_immediate_discharge": True,
                "discourse_relation": "EXPANSION.LEVEL-OF-DETAIL",
                "fidelity_label": "PASS",
                "flow_label": "PASS",
            },
            {
                "step": 4,
                "controller_action": "STOP",
                "selected_source_id": None,
                "selected_source_position": None,
                "selection_function": None,
                "revealed_source_ids_after": ["s1", "s3", "s2"],
                "writer_action": None,
                "candidate_delta_sha256": None,
                "accepted_prose_sha256_after": H3,
                "manual_immediate_discharge": None,
                "discourse_relation": None,
                "fidelity_label": None,
                "flow_label": "NATURAL_STOP",
            },
        ],
    }


def test_summary_keeps_axes_separate_and_measures_source_reordering():
    summary = aft.summarize_trace(valid_trace())
    assert summary["initial_revealed_count"] == 0
    assert summary["reveal_count"] == 3
    assert summary["write_count"] == 2
    assert summary["more_count"] == 1
    assert summary["more_rate"] == pytest.approx(1 / 3)
    assert summary["accumulation_depth_at_write"] == {
        "values": [2, 3],
        "min": 2,
        "max": 3,
        "mean": 2.5,
    }
    assert summary["source_position_sequence"] == [1, 3, 2]
    assert summary["source_order"]["reveal_pair_count"] == 2
    assert summary["source_order"]["monotonic_increasing_pair_count"] == 1
    assert summary["source_order"]["exact_next_position_pair_count"] == 0
    assert summary["manual_immediate_discharge_counts"] == {
        "true": 1,
        "false": 1,
        "unreviewed": 0,
    }
    assert summary["selection_function_counts"] == {
        "COMPLICATE": 1,
        "CONCRETIZE": 1,
        "TEST": 1,
    }
    assert summary["fidelity_label_counts"] == {"PASS": 2}
    assert summary["flow_label_counts"] == {"NATURAL_STOP": 1, "PASS": 2}


def test_trace_can_resume_from_an_existing_recurrent_checkpoint():
    trace = valid_trace()
    trace["initial_revealed_source_ids"] = ["seed-a", "seed-b", "seed-c"]
    trace["initial_revealed_source_positions"] = {
        "seed-a": 7,
        "seed-b": 8,
        "seed-c": 9,
    }
    for step in trace["steps"]:
        step["revealed_source_ids_after"] = [
            "seed-a",
            "seed-b",
            "seed-c",
            *step["revealed_source_ids_after"],
        ]
    summary = aft.summarize_trace(trace)
    assert summary["initial_revealed_count"] == 3
    assert summary["accumulation_depth_at_write"]["values"] == [5, 6]


def test_initial_reveal_positions_must_match_checkpoint_ids():
    trace = valid_trace()
    trace["initial_revealed_source_ids"] = ["seed-a"]
    trace["initial_revealed_source_positions"] = {}
    with pytest.raises(ValueError, match="keys must exactly match"):
        aft.validate_trace(trace)


def test_more_cannot_smuggle_a_candidate_hash():
    trace = valid_trace()
    trace["steps"][0]["candidate_delta_sha256"] = H2
    with pytest.raises(ValueError, match="MORE requires"):
        aft.validate_trace(trace)


def test_reveal_history_must_be_cumulative_and_exact():
    trace = valid_trace()
    trace["steps"][1]["revealed_source_ids_after"] = ["s3"]
    with pytest.raises(ValueError, match="append exactly"):
        aft.validate_trace(trace)


def test_stop_is_terminal():
    trace = valid_trace()
    extra = dict(trace["steps"][0])
    extra["step"] = 5
    extra["selected_source_id"] = "s4"
    extra["selected_source_position"] = 4
    extra["revealed_source_ids_after"] = ["s1", "s3", "s2", "s4"]
    trace["steps"].append(extra)
    with pytest.raises(ValueError, match="no steps may follow"):
        aft.validate_trace(trace)


def test_cli_summary_contains_no_unknown_raw_text(tmp_path):
    trace = valid_trace()
    trace["private_local_note"] = "raw source prose must not be copied into summary"
    trace_path = tmp_path / "trace.json"
    out_path = tmp_path / "summary.json"
    trace_path.write_text(json.dumps(trace), encoding="utf-8")

    aft.summarize_file(trace_path, out_path)
    encoded = out_path.read_text(encoding="utf-8")
    assert "raw source prose" not in encoded
    assert json.loads(encoded)["experiment_id"] == "feasibility-001"