import subprocess
from pathlib import Path
from pangram_lab.git_sync import GitSync


def run(*args,cwd):
    return subprocess.run(args,cwd=cwd,text=True,capture_output=True,check=True)


def test_local_commit_sync_commits_durable_state(tmp_path):
    run('git','init','-b','main',cwd=tmp_path)
    run('git','config','user.email','test@example.com',cwd=tmp_path); run('git','config','user.name','Test',cwd=tmp_path)
    (tmp_path/'a.txt').write_text('a')
    gs=GitSync(tmp_path, require_remote=False)
    gs.sync('initial')
    assert run('git','log','--oneline','-1',cwd=tmp_path).stdout.strip()
