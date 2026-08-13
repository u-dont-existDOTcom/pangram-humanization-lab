from pathlib import Path


def test_project_instructions_under_limit():
    text = Path("PASTE_INTO_PROJECT_INSTRUCTIONS.txt").read_text()
    assert 0 < len(text) < 8000


def test_project_instructions_do_not_inline_master():
    text = Path("PASTE_INTO_PROJECT_INSTRUCTIONS.txt").read_text()
    assert "# INSTRUCTIONS FOR WRITING/EDITING JOEL'S ARTICLES" not in text


def test_graph_version_is_explicit():
    from authorial_flow.version import GRAPH_VERSION
    assert GRAPH_VERSION == "1.3.0-dev1"


def test_diagnostics_release_members_are_present():
    required = [
        Path("src/authorial_flow/diagnostics.py"),
        Path("tests/unit/test_diagnostics.py"),
        Path("tests/integration/test_diagnostics_git.py"),
        Path("tests/integration/test_diagnostics_end_to_end.py"),
        Path("docs/superpowers/specs/2026-08-12-automatic-diagnostics-publication-design.md"),
    ]
    assert all(path.is_file() for path in required)
