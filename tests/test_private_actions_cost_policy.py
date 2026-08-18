from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
HEAVY_MARKER = "# actions-cost-class: manual-heavy-research"

REQUIRED_MANUAL_HEAVY_WORKFLOWS = {
    "idiolect-luar-matched-pilot.yml",
    "idiolect-content-light-matched-control.yml",
    "idiolect-luar-content-controls.yml",
    "idiolect-snapshot-repro-audit.yml",
    "idiolect-transformation-sensitivity.yml",
    "idiolect-dharma-author-census.yml",
    "idiolect-dharma-profile-census.yml",
    "idiolect-dharma-control-profile-extract.yml",
    "idiolect-ordinary-control-census.yml",
}

NETWORK_RESEARCH_WORKFLOWS = {
    "idiolect-dharma-author-census.yml",
    "idiolect-dharma-profile-census.yml",
    "idiolect-dharma-control-profile-extract.yml",
    "idiolect-ordinary-control-census.yml",
}


def _top_level_on_block(text: str) -> str:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line == "on:":
            start = index
            break
    assert start is not None, "workflow is missing top-level on: block"

    block = []
    for line in lines[start + 1 :]:
        if line and not line.startswith((" ", "\t")):
            break
        block.append(line)
    return "\n".join(block)


def _assert_manual_only(name: str, text: str) -> None:
    triggers = _top_level_on_block(text)
    assert "workflow_dispatch:" in triggers, name
    assert "pull_request" not in triggers, name
    assert "push:" not in triggers, name
    assert "schedule:" not in triggers, name


def test_marked_heavy_research_workflows_are_manual_only():
    marked = []
    for path in sorted(WORKFLOWS.glob("*.y*ml")):
        text = path.read_text(encoding="utf-8")
        if HEAVY_MARKER not in text:
            continue
        marked.append(path.name)
        _assert_manual_only(path.name, text)

    assert set(marked) >= REQUIRED_MANUAL_HEAVY_WORKFLOWS


def test_known_live_network_research_workflows_are_marked_and_manual_only():
    for name in sorted(NETWORK_RESEARCH_WORKFLOWS):
        text = (WORKFLOWS / name).read_text(encoding="utf-8")
        assert HEAVY_MARKER in text, name
        _assert_manual_only(name, text)
        assert "group: idiolect-source-network-${{ github.ref }}" in text, name
        assert "cancel-in-progress: false" in text, name


def test_ordinary_validation_does_not_duplicate_on_main_push():
    for name in ("lesson-integrity.yml", "repository-workflow-policy.yml"):
        text = (WORKFLOWS / name).read_text(encoding="utf-8")
        triggers = _top_level_on_block(text)
        assert "pull_request:" in triggers, name
        assert "push:" not in triggers, name


def test_superseded_pull_request_validation_is_cancelled():
    lesson = (WORKFLOWS / "lesson-integrity.yml").read_text(encoding="utf-8")
    assert "cancel-in-progress: ${{ github.event_name == 'pull_request' }}" in lesson

    policy = (WORKFLOWS / "repository-workflow-policy.yml").read_text(encoding="utf-8")
    assert "cancel-in-progress: true" in policy


def test_closeout_mutation_is_path_scoped_and_not_cancellable():
    text = (WORKFLOWS / "lesson-closeout-requests.yml").read_text(encoding="utf-8")
    triggers = _top_level_on_block(text)
    assert "pull_request:" in triggers
    assert "state/lesson-closeout-requests/**" in triggers
    assert "push:" not in triggers
    assert "schedule:" not in triggers
    assert "cancel-in-progress: false" in text
