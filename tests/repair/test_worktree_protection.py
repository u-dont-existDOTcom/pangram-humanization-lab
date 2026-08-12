import subprocess
from pathlib import Path
import pytest

from authorial_flow.repair.worktree import WorktreeManager
from authorial_flow.repair.protection import ProtectedSnapshot, validate_candidate_diff


@pytest.fixture
def tmp_git_repo(tmp_path:Path)->Path:
    repo=tmp_path/'repo'; repo.mkdir()
    subprocess.run(['git','init','-q'],cwd=repo,check=True)
    subprocess.run(['git','config','user.email','test@example.invalid'],cwd=repo,check=True)
    subprocess.run(['git','config','user.name','Test'],cwd=repo,check=True)
    (repo/'project').mkdir(); (repo/'project'/'INPUT.md').write_text('source text '+('A'*80))
    (repo/'project'/'HUMAN-FLOW-GOLD.json').write_text('{}')
    (repo/'code.py').write_text('x=1\n')
    subprocess.run(['git','add','.'],cwd=repo,check=True)
    subprocess.run(['git','commit','-qm','base'],cwd=repo,check=True)
    return repo


def test_repair_uses_separate_worktree(tmp_git_repo:Path):
    mgr=WorktreeManager(tmp_git_repo,tmp_git_repo/'.state'/'worktrees')
    ref=mgr.create('r001')
    assert ref.path != tmp_git_repo
    assert (ref.path/'.git').exists()
    mgr.discard(ref)
    assert not ref.path.exists()


def test_protected_mutation_is_hard_failure(tmp_git_repo:Path):
    snap=ProtectedSnapshot.capture(tmp_git_repo,['project/INPUT.md','project/HUMAN-FLOW-GOLD.json'])
    (tmp_git_repo/'project'/'INPUT.md').write_text('changed')
    report=snap.validate(tmp_git_repo)
    assert report.pass_ is False
    assert 'project/INPUT.md' in report.mutated


def test_source_hardcoding_added_to_production_is_rejected(tmp_git_repo:Path):
    base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=tmp_git_repo,text=True).strip()
    source=(tmp_git_repo/'project'/'INPUT.md').read_text()
    (tmp_git_repo/'code.py').write_text('x=1\nPROMPT='+repr(source)+'\n')
    report=validate_candidate_diff(tmp_git_repo,base,source_texts=[source])
    assert report.pass_ is False
    assert report.source_hardcoding_hits


def test_common_short_text_is_not_source_hardcoding(tmp_git_repo:Path):
    base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=tmp_git_repo,text=True).strip()
    (tmp_git_repo/'code.py').write_text('x=1\nmessage="choices happen"\n')
    report=validate_candidate_diff(tmp_git_repo,base,source_texts=['choices happen'])
    assert report.source_hardcoding_hits == ()


def test_protected_directory_snapshot_detects_existing_and_new_files(tmp_git_repo:Path):
    (tmp_git_repo/'policy').mkdir()
    (tmp_git_repo/'policy'/'RULES.md').write_text('locked')
    subprocess.run(['git','add','policy/RULES.md'],cwd=tmp_git_repo,check=True)
    subprocess.run(['git','commit','-qm','policy'],cwd=tmp_git_repo,check=True)
    snap=ProtectedSnapshot.capture(tmp_git_repo,['project/','policy/'])
    (tmp_git_repo/'policy'/'RULES.md').write_text('changed')
    (tmp_git_repo/'policy'/'NEW.md').write_text('new protected file')
    report=snap.validate(tmp_git_repo)
    assert report.pass_ is False
    assert 'policy/RULES.md' in report.mutated
    assert 'policy/NEW.md' in report.mutated


def test_source_hardcoding_added_to_regression_test_is_rejected(tmp_git_repo:Path):
    base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=tmp_git_repo,text=True).strip()
    source=(tmp_git_repo/'project'/'INPUT.md').read_text()
    (tmp_git_repo/'tests').mkdir()
    (tmp_git_repo/'tests'/'test_current_article.py').write_text('ARTICLE='+repr(source)+'\n')
    subprocess.run(['git','add','tests/test_current_article.py'],cwd=tmp_git_repo,check=True)
    subprocess.run(['git','commit','-qm','candidate'],cwd=tmp_git_repo,check=True)
    report=validate_candidate_diff(tmp_git_repo,base,source_texts=[source])
    assert report.pass_ is False
    assert report.source_hardcoding_hits
