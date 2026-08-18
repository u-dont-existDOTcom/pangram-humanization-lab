import json
from pathlib import Path

from pangram_lab import authorial_flow_rsg as rsg


class FakeRunner:
    model = "fake-model"

    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    def available(self):
        return True

    def run_json(self, role, prompt, schema_path, out_path, log_path):
        self.calls.append({"role": role, "prompt": prompt, "schema": schema_path.name})
        obj = self.outputs.pop(0)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(obj), encoding="utf-8")
        log_path.write_text(f"fake role={role}\n", encoding="utf-8")
        return obj


def repo_root():
    return Path(__file__).resolve().parents[1]


def write_packet(tmp_path, *, source_items, initial_revealed, initial_prose="Existing thought.", max_steps=6):
    packet = {
        "schema_version": rsg.INPUT_SCHEMA_VERSION,
        "experiment_id": "rsg-test",
        "source_items": source_items,
        "initial_revealed_source_ids": initial_revealed,
        "initial_prose": initial_prose,
        "constraints": ["Do not change certainty."],
        "max_steps": max_steps,
    }
    path = tmp_path / "packet.json"
    path.write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def test_writer_never_receives_unrevealed_source_or_source_positions(tmp_path):
    packet = write_packet(
        tmp_path,
        source_items=[
            {"id": "s1", "position": 1, "text": "initial visible fact"},
            {"id": "s2", "position": 2, "text": "UNREVEALED SECRET FACT"},
            {"id": "s3", "position": 3, "text": "newly selected fact"},
        ],
        initial_revealed=["s1"],
    )
    runner = FakeRunner(
        [
            {"action": "REVEAL", "source_id": "s3", "selection_function": "TEST"},
            {"action": "MORE", "prose": ""},
            {"action": "STOP", "source_id": None, "selection_function": None},
        ]
    )
    work = tmp_path / "work"
    result = rsg.run_rsg_ls(packet, repo_root=repo_root(), runner=runner, work_dir=work)

    assert result["terminal_state"] == "coverage_flow_conflict"
    writer_prompt = next(call["prompt"] for call in runner.calls if call["role"] == "flow-writer")
    assert "initial visible fact" in writer_prompt
    assert "newly selected fact" in writer_prompt
    assert "UNREVEALED SECRET FACT" not in writer_prompt
    assert "source_position=" not in writer_prompt

    controller_prompt = runner.calls[0]["prompt"]
    assert "UNREVEALED SECRET FACT" in controller_prompt
    summary = result["metrics"]
    assert summary["initial_revealed_count"] == 1
    assert summary["reveal_count"] == 1
    assert summary["more_count"] == 1
    assert summary["stop_count"] == 1


def test_accepted_candidate_is_hashed_out_of_metadata_and_terminal_run_resumes(tmp_path):
    packet = write_packet(
        tmp_path,
        source_items=[
            {"id": "s1", "position": 1, "text": "visible seed"},
            {"id": "s2", "position": 2, "text": "final licensed fact"},
        ],
        initial_revealed=["s1"],
    )
    runner = FakeRunner(
        [
            {"action": "REVEAL", "source_id": "s2", "selection_function": "CONCRETIZE"},
            {"action": "WRITE", "prose": "A genuinely new sentence."},
            {"label": "PASS", "issue": ""},
            {"label": "NATURAL_STOP", "issue": "", "discourse_relation": "EXPANSION"},
        ]
    )
    work = tmp_path / "work"
    result = rsg.run_rsg_ls(packet, repo_root=repo_root(), runner=runner, work_dir=work)

    assert result["terminal_state"] == "complete"
    metadata = (work / "metadata-trace.json").read_text(encoding="utf-8")
    assert "A genuinely new sentence." not in metadata
    assert "final licensed fact" not in metadata
    assert json.loads(metadata)["steps"][0]["candidate_delta_sha256"]
    assert json.loads(metadata)["steps"][0]["flow_label"] == "NATURAL_STOP"

    resumed = FakeRunner([])
    again = rsg.run_rsg_ls(packet, repo_root=repo_root(), runner=resumed, work_dir=work)
    assert again["resumed_terminal"] is True
    assert resumed.calls == []


def test_fidelity_failure_stops_without_accepting_candidate(tmp_path):
    packet = write_packet(
        tmp_path,
        source_items=[
            {"id": "s1", "position": 1, "text": "visible seed"},
            {"id": "s2", "position": 2, "text": "licensed fact"},
        ],
        initial_revealed=["s1"],
    )
    runner = FakeRunner(
        [
            {"action": "REVEAL", "source_id": "s2", "selection_function": "COMPLICATE"},
            {"action": "WRITE", "prose": "Unsupported leap."},
            {"label": "FAIL", "issue": "Changes certainty."},
            {"label": "PASS", "issue": "", "discourse_relation": "EXPANSION"},
        ]
    )
    work = tmp_path / "work"
    result = rsg.run_rsg_ls(packet, repo_root=repo_root(), runner=runner, work_dir=work)

    assert result["terminal_state"] == "candidate_rejected"
    state = json.loads((work / "raw-state.json").read_text(encoding="utf-8"))
    assert state["accepted_prose"] == "Existing thought."
    assert state["steps"][0]["fidelity_label"] == "FAIL"
