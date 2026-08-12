from pathlib import Path


def test_project_instructions_under_limit():
    text = Path("PASTE_INTO_PROJECT_INSTRUCTIONS.txt").read_text()
    assert 0 < len(text) < 8000


def test_project_instructions_do_not_inline_master():
    text = Path("PASTE_INTO_PROJECT_INSTRUCTIONS.txt").read_text()
    assert "# INSTRUCTIONS FOR WRITING/EDITING JOEL'S ARTICLES" not in text


def test_graph_version_is_explicit():
    from authorial_flow.version import GRAPH_VERSION
    assert GRAPH_VERSION == "1.2.0-dev1"
