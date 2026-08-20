from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from pangram_lab import gui_local  # noqa: E402


_LOCAL_PLAYWRIGHT_TEST_FILES = {
    "test_gui_local.py",
    "test_gui_local_factory_contract.py",
    "test_gui_local_live_safety.py",
}


@pytest.fixture(autouse=True)
def isolate_local_playwright_tests_from_ambient_tmp_git_root(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep local-Playwright unit tests independent of machine-level /tmp Git state.

    Pytest creates ``tmp_path`` below the OS temporary directory. On Joel's
    Zorin machine, ``/tmp`` itself can resolve as a Git worktree, which is real
    ambient machine state but not part of these unit-test fixtures. Tests that
    create a repository *inside* their own ``tmp_path`` must still see and
    exercise the production guard.

    This fixture is deliberately test-only. Production profile validation is
    not weakened: the live runner still refuses any real enclosing Git root.
    """
    filename = Path(str(request.fspath)).name
    if filename not in _LOCAL_PLAYWRIGHT_TEST_FILES:
        return

    ambient_tmp_root = Path(tempfile.gettempdir()).expanduser().resolve(strict=False)
    original = gui_local.containing_git_root

    def isolated_probe(path: Path, *, home: Path | None = None) -> Path | None:
        result = original(path, home=home)
        if result is not None and result.expanduser().resolve(strict=False) == ambient_tmp_root:
            return None
        return result

    monkeypatch.setattr(gui_local, "containing_git_root", isolated_probe)
    monkeypatch.setattr(gui_local._legacy, "containing_git_root", isolated_probe)
