from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import stat
import zipfile
from pathlib import Path

import pytest

from authorial_flow.release import ReleaseError, build_release, verify_release
from authorial_flow.version import GRAPH_VERSION


REPO = Path(__file__).resolve().parents[2]


def _mode(info: zipfile.ZipInfo) -> int:
    return (info.external_attr >> 16) & 0o777


def test_release_documents_interactive_same_terminal_supervisor():
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    checklist = (REPO / "docs" / "release-checklist.md").read_text(encoding="utf-8")
    matrix = (REPO / "docs" / "acceptance-matrix.md").read_text(encoding="utf-8")
    for token in [
        "Ctrl+C", "same terminal", "leave paused", "same thread",
        "discard", "Pangram task ID", "confirmed action",
    ]:
        assert token.lower() in readme.lower()
    assert "supervisor question" in matrix.lower()
    assert "target Zorin" in checklist


def test_release_contains_required_assets_and_excludes_runtime_state(tmp_path):
    out = tmp_path / "release.zip"
    manifest = build_release(REPO, out)

    with zipfile.ZipFile(out) as z:
        names = set(z.namelist())
        prefix = manifest.archive_root + "/"
        for required in [
            "INSTALL-AND-RUN.sh",
            "RUN.sh",
            "requirements.lock",
            "PASTE_INTO_PROJECT_INSTRUCTIONS.txt",
            "MANIFEST.json",
            "SHA256SUMS.txt",
        ]:
            assert prefix + required in names
        assert not any("/.state/" in n or "/.venv/" in n or "/.git/" in n for n in names)
        assert not any(Path(n).name.startswith(("RESULT-", "UPLOAD-")) for n in names)
        assert _mode(z.getinfo(prefix + "INSTALL-AND-RUN.sh")) & stat.S_IXUSR
        assert _mode(z.getinfo(prefix + "RUN.sh")) & stat.S_IXUSR

    report = verify_release(out)
    assert report.pass_
    assert report.project_instructions_chars < 8000


def test_release_manifest_and_checksums_match_exact_members(tmp_path):
    out = tmp_path / "release.zip"
    manifest = build_release(REPO, out)
    with zipfile.ZipFile(out) as z:
        prefix = manifest.archive_root + "/"
        payload = json.loads(z.read(prefix + "MANIFEST.json"))
        sums = z.read(prefix + "SHA256SUMS.txt").decode().splitlines()
        by_path = {row["path"]: row for row in payload["members"]}
        for line in sums:
            digest, rel = line.split("  ", 1)
            assert hashlib.sha256(z.read(prefix + rel)).hexdigest() == digest
            assert by_path[rel]["sha256"] == digest
        assert payload["source_commit_sha"] == manifest.source_commit_sha
        assert payload["graph_version"]
        assert payload["policy_version"]


def test_root_metadata_sync_is_rebuild_stable_after_metadata_only_commit(tmp_path):
    root = tmp_path / "Téléchargements" / "authorial-flow-graph-v1"
    root.mkdir(parents=True)
    for name, data in {
        "INSTALL-AND-RUN.sh": "#!/bin/sh\nexit 0\n",
        "RUN.sh": "#!/bin/sh\nexit 0\n",
        "requirements.lock": "# locked\n",
        "pyproject.toml": "[project]\nname='synthetic-release'\nversion='1'\n",
        "README.md": "# Synthetic release\n",
        "PASTE_INTO_PROJECT_INSTRUCTIONS.txt": "instructions\n",
        "source.txt": "release member\n",
        "MANIFEST.json": '{"graph_version":"stale"}\n',
        "SHA256SUMS.txt": "stale\n",
    }.items():
        (root / name).write_text(data, encoding="utf-8")
    (root / "INSTALL-AND-RUN.sh").chmod(0o755)
    (root / "RUN.sh").chmod(0o755)
    policy = root / "policy" / "test-policy"
    policy.mkdir(parents=True)
    (policy / "MASTER.md").write_text("policy\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "content release"], cwd=root, check=True)
    content_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()

    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "build_release.py"), "--repo", str(root), "--write-root-metadata"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )

    assert proc.returncode == 0, proc.stderr
    assert "root_metadata=PASS" in proc.stdout
    payload = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    assert payload["graph_version"] == GRAPH_VERSION
    assert payload["source_commit_sha"] == content_commit
    rows = {row["path"]: row for row in payload["members"]}
    assert "MANIFEST.json" not in rows
    assert "SHA256SUMS.txt" not in rows
    for rel, row in rows.items():
        source = root / rel
        assert row["size_bytes"] == len(source.read_bytes())
        assert row["sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
        assert row["executable"] == bool(source.stat().st_mode & stat.S_IXUSR)
    sums = {}
    for line in (root / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        sums[rel] = digest
    assert sums == {rel: row["sha256"] for rel, row in rows.items()}

    subprocess.run(["git", "add", "MANIFEST.json", "SHA256SUMS.txt"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "finalize release metadata"], cwd=root, check=True)
    rebuilt = tmp_path / "rebuilt.zip"
    manifest = build_release(root, rebuilt)
    assert manifest.source_commit_sha == content_commit
    with zipfile.ZipFile(rebuilt) as archive:
        prefix = manifest.archive_root + "/"
        assert archive.read(prefix + "MANIFEST.json") == (root / "MANIFEST.json").read_bytes()
        assert archive.read(prefix + "SHA256SUMS.txt") == (root / "SHA256SUMS.txt").read_bytes()


def test_release_build_is_deterministic_for_same_commit(tmp_path):
    first = tmp_path / "a.zip"
    second = tmp_path / "b.zip"
    build_release(REPO, first)
    build_release(REPO, second)
    assert first.read_bytes() == second.read_bytes()


def test_release_blocks_oversized_project_instructions(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    # Minimum tree required before the character-limit gate is checked.
    for name in ["INSTALL-AND-RUN.sh", "RUN.sh", "requirements.lock", "README.md", "pyproject.toml"]:
        p = repo / name
        p.write_text("#!/bin/sh\n" if name.endswith(".sh") else "x\n")
    (repo / "src").mkdir()
    (repo / "project").mkdir()
    (repo / "policy").mkdir()
    (repo / "PASTE_INTO_PROJECT_INSTRUCTIONS.txt").write_text("x" * 8001)
    with pytest.raises(ReleaseError, match="8,000"):
        build_release(repo, tmp_path / "bad.zip")


def test_one_command_installer_initializes_repairable_git_baseline_and_runs_provider_smoke():
    text=(REPO/'INSTALL-AND-RUN.sh').read_text()
    reconcile=(REPO/'scripts'/'reconcile_release_baseline.py').read_text()
    assert 'scripts/reconcile_release_baseline.py' in text
    assert 'git' in reconcile and 'Authorial Flow Baseline' in reconcile
    assert 'scripts/live_smoke.py' in text
    assert '--claude' in text and '--codex' in text and '--heartbeat' in text


def test_release_module_verify_cli_reports_pass(tmp_path):
    out = tmp_path / "release.zip"
    build_release(REPO, out)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO / "src")
    proc = subprocess.run(
        [sys.executable, "-m", "authorial_flow.release", "verify", str(out)],
        cwd=REPO, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    assert proc.returncode == 0, proc.stderr
    assert "verification=PASS" in proc.stdout
    assert "project_instructions_chars=" in proc.stdout


def test_installer_preflights_pangram_model_when_key_is_already_available():
    text=(REPO/'INSTALL-AND-RUN.sh').read_text()
    assert 'PANGRAM_API_KEY' in text
    assert '--pangram' in text
    assert '--pangram-submit' not in text


def test_release_archive_root_matches_owner_approved_install_contract(tmp_path):
    out = tmp_path / "release.zip"
    manifest = build_release(REPO, out)
    assert manifest.archive_root == "authorial-flow-graph-v1"
    with zipfile.ZipFile(out) as z:
        assert all(name.startswith("authorial-flow-graph-v1/") for name in z.namelist())


def test_one_command_installer_delegates_to_state_aware_run_wrapper_for_first_run_or_resume():
    installer=(REPO/'INSTALL-AND-RUN.sh').read_text()
    runner=(REPO/'RUN.sh').read_text()
    assert 'exec ./RUN.sh "$@"' in installer
    assert '.state/current-thread.json' in runner
    assert 'authorial-flow resume' in runner
    assert 'authorial-flow run' in runner



def _write_synthetic_release_manifest(root:Path, *, source_commit:str, members:list[str]):
    rows=[]
    for rel in members:
        data=(root/rel).read_bytes()
        rows.append({
            'path':rel,'size_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
            'executable':bool((root/rel).stat().st_mode & stat.S_IXUSR),
        })
    payload={
        'format':'authorial-flow-release-v1','archive_root':'authorial-flow-graph-v1',
        'source_commit_sha':source_commit,'graph_version':'test','policy_version':'test','members':rows,
    }
    (root/'MANIFEST.json').write_text(json.dumps(payload,sort_keys=True,indent=2)+'\n')
    (root/'SHA256SUMS.txt').write_text(''.join(f"{row['sha256']}  {row['path']}\n" for row in rows))


def _init_synthetic_release_repo(root:Path):
    (root/'.gitignore').write_text('.state/\n.venv/\n')
    (root/'file.txt').write_text('old\n')
    _write_synthetic_release_manifest(root,source_commit='upstream-old',members=['.gitignore','file.txt'])
    subprocess.run(['git','init','-q'],cwd=root,check=True)
    subprocess.run(['git','config','user.email','test@example.invalid'],cwd=root,check=True)
    subprocess.run(['git','config','user.name','Test'],cwd=root,check=True)
    subprocess.run(['git','add','-A'],cwd=root,check=True)
    subprocess.run(['git','commit','-qm','old release baseline'],cwd=root,check=True)


def test_release_baseline_reconciles_in_place_update_and_preserves_state(tmp_path):
    root=tmp_path/'authorial-flow-graph-v1'; root.mkdir(); _init_synthetic_release_repo(root)
    state=root/'.state'; state.mkdir(); checkpoint=state/'checkpoints.sqlite'; checkpoint.write_bytes(b'checkpoint-state')
    old_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()

    (root/'file.txt').write_text('new release\n')
    _write_synthetic_release_manifest(root,source_commit='upstream-new',members=['.gitignore','file.txt'])
    proc=subprocess.run([sys.executable,str(REPO/'scripts'/'reconcile_release_baseline.py'),'--root',str(root)],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    assert proc.returncode == 0, proc.stderr
    new_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    assert new_head != old_head
    assert subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip() == ''
    assert checkpoint.read_bytes() == b'checkpoint-state'
    meta=json.loads((state/'release-baseline.json').read_text())
    assert meta['release_source_commit'] == 'upstream-new'
    assert meta['local_baseline_commit'] == new_head


def test_release_baseline_clean_self_repair_does_not_revert_to_stale_manifest(tmp_path):
    root=tmp_path/'authorial-flow-graph-v1'; root.mkdir(); _init_synthetic_release_repo(root)
    (root/'file.txt').write_text('locally self-repaired\n')
    subprocess.run(['git','add','file.txt'],cwd=root,check=True)
    subprocess.run(['git','commit','-qm','machine repair'],cwd=root,check=True)
    repaired_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()

    proc=subprocess.run([sys.executable,str(REPO/'scripts'/'reconcile_release_baseline.py'),'--root',str(root)],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    assert proc.returncode == 0, proc.stderr
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip() == repaired_head
    assert (root/'file.txt').read_text() == 'locally self-repaired\n'


def _write_valid_legacy_evidence_zip(path:Path):
    package=(json.dumps({
        'format':'authorial-flow-evidence-v1','reason':'bounded-failure','built_utc':1.0,
    },sort_keys=True,indent=2)+'\n').encode()
    payload=b'bounded evidence\n'
    sums=(
        f"{hashlib.sha256(package).hexdigest()}  PACKAGE.json\n"
        f"{hashlib.sha256(payload).hexdigest()}  .state/events.jsonl\n"
    )
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('PACKAGE.json',package)
        z.writestr('.state/events.jsonl',payload)
        z.writestr('SHA256SUMS.txt',sums)


def test_release_baseline_migrates_valid_legacy_root_evidence_before_dirty_check(tmp_path):
    root=tmp_path/'authorial-flow-graph-v1'; root.mkdir(); _init_synthetic_release_repo(root)
    state=root/'.state'; state.mkdir(); checkpoint=state/'checkpoints.sqlite'; checkpoint.write_bytes(b'checkpoint-state')
    evidence=root/'AUTHORIAL-FLOW-EVIDENCE-bounded-failure-20260811-182825.zip'
    _write_valid_legacy_evidence_zip(evidence)

    (root/'file.txt').write_text('new release\n')
    _write_synthetic_release_manifest(root,source_commit='upstream-new',members=['.gitignore','file.txt'])
    proc=subprocess.run([sys.executable,str(REPO/'scripts'/'reconcile_release_baseline.py'),'--root',str(root)],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    assert proc.returncode == 0, proc.stderr
    migrated=state/'evidence'/evidence.name
    assert migrated.is_file()
    assert not evidence.exists()
    assert checkpoint.read_bytes() == b'checkpoint-state'
    assert subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip() == ''


def test_release_baseline_does_not_trust_filename_pattern_for_invalid_evidence_zip(tmp_path):
    root=tmp_path/'authorial-flow-graph-v1'; root.mkdir(); _init_synthetic_release_repo(root)
    fake=root/'AUTHORIAL-FLOW-EVIDENCE-bounded-failure-not-ours.zip'
    with zipfile.ZipFile(fake,'w') as z:
        z.writestr('PACKAGE.json',json.dumps({'format':'something-else'}))
    proc=subprocess.run([sys.executable,str(REPO/'scripts'/'reconcile_release_baseline.py'),'--root',str(root)],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    assert proc.returncode != 0
    assert 'non-release working-tree changes' in proc.stderr
    assert fake.is_file()


def test_release_baseline_rejects_unrelated_dirty_files(tmp_path):
    root=tmp_path/'authorial-flow-graph-v1'; root.mkdir(); _init_synthetic_release_repo(root)
    (root/'personal-notes.txt').write_text('do not absorb me into a release baseline')
    proc=subprocess.run([sys.executable,str(REPO/'scripts'/'reconcile_release_baseline.py'),'--root',str(root)],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    assert proc.returncode != 0
    assert 'non-release working-tree changes' in proc.stderr
    assert not subprocess.check_output(['git','ls-files','personal-notes.txt'],cwd=root,text=True).strip()


def test_installer_reconciles_release_git_baseline_before_runtime_start():
    text=(REPO/'INSTALL-AND-RUN.sh').read_text()
    assert 'scripts/reconcile_release_baseline.py' in text
    assert text.index('scripts/reconcile_release_baseline.py') < text.index('exec ./RUN.sh "$@"')


def test_installer_routes_preflight_pytest_through_bootstrap_self_heal_after_baseline_reconciliation():
    text=(REPO/'INSTALL-AND-RUN.sh').read_text()
    reconcile='scripts/reconcile_release_baseline.py'
    bootstrap='authorial_flow.bootstrap_repair'
    assert bootstrap in text
    assert '.venv/bin/python -m pytest -q' not in text.replace(
        '.venv/bin/python -m authorial_flow.bootstrap_repair --root . -- .venv/bin/python -m pytest -q',''
    )
    assert text.index(reconcile) < text.index(bootstrap) < text.index('scripts/live_smoke.py')


def test_installer_routes_live_smoke_through_bootstrap_self_heal_before_runtime_start():
    text=(REPO/'INSTALL-AND-RUN.sh').read_text()
    live='scripts/live_smoke.py'
    bootstrap='authorial_flow.bootstrap_repair'
    assert '--phase installer-live-smoke' in text
    assert '--failure-class PROVIDER_PLUMBING' in text
    assert '--originating-node provider-smoke' in text
    assert '--evidence-file .state/live-smoke/install-report.json' in text
    assert text.index(bootstrap, text.index('# Live capability smoke')) < text.index(live) < text.index('exec ./RUN.sh "$@"')
    live_line=[line for line in text.splitlines() if 'scripts/live_smoke.py' in line][0]
    assert 'bootstrap_repair' in live_line or live_line.rstrip().endswith('--')


def test_live_smoke_self_heal_requires_pre_promotion_live_acceptance_gate():
    text=(REPO/'INSTALL-AND-RUN.sh').read_text()
    assert '--verify-before-promotion' in text


def test_installer_securely_reprompts_once_for_rejected_pangram_key():
    text=(REPO/'INSTALL-AND-RUN.sh').read_text()
    assert 'SMOKE_RC' in text
    assert 'bootstrap_credential_required' not in text  # bootstrap reports it; shell branches on rc
    assert 'read -r -s' in text
    assert 'PANGRAM_API_KEY' in text
    assert 'Pangram API key was rejected' in text


def test_installer_handles_pangram_credit_action_and_rejected_retry_explicitly():
    text=(REPO/'INSTALL-AND-RUN.sh').read_text()
    assert 'RETRY_SMOKE_RC' in text
    assert 'replacement Pangram API key was also rejected' in text
    assert 'account needs API credits' in text
    assert 'SMOKE_RC" -eq 4' in text
