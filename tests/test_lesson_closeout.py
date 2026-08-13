import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from pangram_lab.lesson_closeout import audit_ref, validate_ledger


def run(cwd, *args):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=True)


def init_repo(tmp_path):
    run(tmp_path, 'git', 'init', '-q')
    run(tmp_path, 'git', 'config', 'user.email', 'test@example.com')
    run(tmp_path, 'git', 'config', 'user.name', 'Test')
    (tmp_path / 'state').mkdir()
    (tmp_path / 'tools').mkdir()
    config = {
        'schema_version': 1,
        'enforcement_started_at_utc': '2000-01-01T00:00:00Z',
        'tracked_globs': ['state/*INCIDENT*.md', 'state/*CASE-STUDY*.md', 'notes/**/*.md', 'state/experiments/**/*.json'],
        'lesson_index': 'state/LESSON-INDEX.md',
        'lesson_summary_globs': ['state/WORKING-LESSONS*.md'],
    }
    (tmp_path / 'state/lesson-closeout-config.json').write_text(json.dumps(config), encoding='utf-8')
    (tmp_path / 'state/LESSON-LEDGER.json').write_text(json.dumps({'schema_version': 1, 'entries': []}), encoding='utf-8')
    (tmp_path / 'state/LESSON-INDEX.md').write_text('# Index\n', encoding='utf-8')
    (tmp_path / 'state/WORKING-LESSONS.md').write_text('# Lessons\n', encoding='utf-8')
    run(tmp_path, 'git', 'add', '.')
    run(tmp_path, 'git', 'commit', '-qm', 'init')
    return config


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_audit_flags_current_tracked_artifact_without_disposition(tmp_path):
    init_repo(tmp_path)
    incident = tmp_path / 'state/ROMANCE-TEST-INCIDENT-2026-08-13.md'
    incident.write_text('finding', encoding='utf-8')
    run(tmp_path, 'git', 'add', '.')
    run(tmp_path, 'git', 'commit', '-qm', 'add incident')

    report = audit_ref(tmp_path, 'HEAD')
    assert report['ok'] is False
    assert report['orphans'][0]['path'] == 'state/ROMANCE-TEST-INCIDENT-2026-08-13.md'


def test_audit_accepts_disposition_for_exact_artifact_hash(tmp_path):
    init_repo(tmp_path)
    incident = tmp_path / 'state/ROMANCE-TEST-INCIDENT-2026-08-13.md'
    incident.write_text('finding', encoding='utf-8')
    ledger = {
        'schema_version': 1,
        'entries': [{
            'id': 'L1',
            'source_path': 'state/ROMANCE-TEST-INCIDENT-2026-08-13.md',
            'source_sha256': sha256(incident),
            'finding': 'A local detector interaction was observed.',
            'disposition': 'provisional',
            'reason': 'Needs cross-case replication.',
            'promoted_to': [],
        }],
    }
    (tmp_path / 'state/LESSON-LEDGER.json').write_text(json.dumps(ledger), encoding='utf-8')
    run(tmp_path, 'git', 'add', '.')
    run(tmp_path, 'git', 'commit', '-qm', 'add incident with closeout')

    report = audit_ref(tmp_path, 'HEAD')
    assert report['ok'] is True
    assert report['orphans'] == []


def test_audit_rejects_stale_disposition_after_artifact_changes(tmp_path):
    init_repo(tmp_path)
    incident = tmp_path / 'state/ROMANCE-TEST-INCIDENT-2026-08-13.md'
    incident.write_text('v1', encoding='utf-8')
    ledger = {'schema_version': 1, 'entries': [{
        'id': 'L1', 'source_path': incident.relative_to(tmp_path).as_posix(),
        'source_sha256': sha256(incident), 'finding': 'finding', 'disposition': 'article-specific',
        'reason': 'Only applies to this section.', 'promoted_to': []}]}
    (tmp_path / 'state/LESSON-LEDGER.json').write_text(json.dumps(ledger), encoding='utf-8')
    run(tmp_path, 'git', 'add', '.')
    run(tmp_path, 'git', 'commit', '-qm', 'v1')
    incident.write_text('v2', encoding='utf-8')
    run(tmp_path, 'git', 'add', '.')
    run(tmp_path, 'git', 'commit', '-qm', 'v2 without closeout')

    report = audit_ref(tmp_path, 'HEAD')
    assert report['ok'] is False
    assert report['orphans'][0]['reason'] == 'current artifact hash has no disposition'


def test_promoted_finding_requires_index_and_summary_targets():
    bad = {'schema_version': 1, 'entries': [{
        'id': 'L1', 'source_path': 'state/X-INCIDENT.md', 'source_sha256': 'a' * 64,
        'finding': 'durable rule', 'disposition': 'promoted', 'reason': '',
        'promoted_to': ['state/LESSON-INDEX.md']}]}
    errors = validate_ledger(bad, {
        'lesson_index': 'state/LESSON-INDEX.md',
        'lesson_summary_globs': ['state/WORKING-LESSONS*.md'],
    })
    assert any('lesson summary' in e for e in errors)


def test_nonpromoted_finding_requires_reason():
    bad = {'schema_version': 1, 'entries': [{
        'id': 'L1', 'source_path': 'state/X-INCIDENT.md', 'source_sha256': 'a' * 64,
        'finding': 'local observation', 'disposition': 'provisional', 'reason': '', 'promoted_to': []}]}
    errors = validate_ledger(bad, {'lesson_index': 'state/LESSON-INDEX.md', 'lesson_summary_globs': ['state/WORKING-LESSONS*.md']})
    assert any('reason' in e for e in errors)


def test_artifact_before_enforcement_cutoff_is_grandfathered(tmp_path):
    config = init_repo(tmp_path)
    incident = tmp_path / 'state/OLD-INCIDENT.md'
    incident.write_text('old', encoding='utf-8')
    run(tmp_path, 'git', 'add', '.')
    run(tmp_path, 'git', 'commit', '-qm', 'old incident')
    # Move enforcement far into the future after the artifact commit.
    config['enforcement_started_at_utc'] = '2999-01-01T00:00:00Z'
    (tmp_path / 'state/lesson-closeout-config.json').write_text(json.dumps(config), encoding='utf-8')
    run(tmp_path, 'git', 'add', '.')
    run(tmp_path, 'git', 'commit', '-qm', 'enable gate later')

    report = audit_ref(tmp_path, 'HEAD')
    assert report['ok'] is True
    assert report['grandfathered'][0]['path'] == 'state/OLD-INCIDENT.md'

from pangram_lab.lesson_closeout import check_range


def test_promoted_change_requires_index_and_summary_to_change_in_same_range(tmp_path):
    init_repo(tmp_path)
    base = run(tmp_path, 'git', 'rev-parse', 'HEAD').stdout.strip()
    incident = tmp_path / 'state/NEW-INCIDENT.md'
    incident.write_text('important', encoding='utf-8')
    ledger = {'schema_version': 1, 'entries': [{
        'id': 'L1', 'source_path': 'state/NEW-INCIDENT.md', 'source_sha256': sha256(incident),
        'finding': 'Promote this.', 'disposition': 'promoted', 'reason': '',
        'promoted_to': ['state/LESSON-INDEX.md', 'state/WORKING-LESSONS.md']}]}
    (tmp_path / 'state/LESSON-LEDGER.json').write_text(json.dumps(ledger), encoding='utf-8')
    run(tmp_path, 'git', 'add', '.')
    run(tmp_path, 'git', 'commit', '-qm', 'promote without touching summary')
    head = run(tmp_path, 'git', 'rev-parse', 'HEAD').stdout.strip()

    report = check_range(tmp_path, base, head)
    assert report['ok'] is False
    assert any('promoted target was not changed' in e for e in report['errors'])


def test_promoted_change_passes_when_index_and_summary_change_in_same_range(tmp_path):
    init_repo(tmp_path)
    base = run(tmp_path, 'git', 'rev-parse', 'HEAD').stdout.strip()
    incident = tmp_path / 'state/NEW-INCIDENT.md'
    incident.write_text('important', encoding='utf-8')
    ledger = {'schema_version': 1, 'entries': [{
        'id': 'L1', 'source_path': 'state/NEW-INCIDENT.md', 'source_sha256': sha256(incident),
        'finding': 'Promote this.', 'disposition': 'promoted', 'reason': '',
        'promoted_to': ['state/LESSON-INDEX.md', 'state/WORKING-LESSONS.md']}]}
    (tmp_path / 'state/LESSON-LEDGER.json').write_text(json.dumps(ledger), encoding='utf-8')
    (tmp_path / 'state/LESSON-INDEX.md').write_text('# Index\n- Promote this.\n', encoding='utf-8')
    (tmp_path / 'state/WORKING-LESSONS.md').write_text('# Lessons\n- Promote this.\n', encoding='utf-8')
    run(tmp_path, 'git', 'add', '.')
    run(tmp_path, 'git', 'commit', '-qm', 'promote with summary')
    head = run(tmp_path, 'git', 'rev-parse', 'HEAD').stdout.strip()

    report = check_range(tmp_path, base, head)
    assert report['ok'] is True

from pangram_lab.lesson_closeout import record_finding


def test_record_can_disposition_artifact_from_another_ref(tmp_path):
    init_repo(tmp_path)
    run(tmp_path, 'git', 'checkout', '-qb', 'experiment')
    incident = tmp_path / 'state/BRANCH-INCIDENT.md'
    incident.write_text('branch evidence', encoding='utf-8')
    run(tmp_path, 'git', 'add', '.')
    run(tmp_path, 'git', 'commit', '-qm', 'branch evidence')
    run(tmp_path, 'git', 'checkout', '-q', 'master')

    entry = record_finding(
        tmp_path,
        'state/BRANCH-INCIDENT.md',
        'Branch-only finding reviewed.',
        'provisional',
        'Needs replication.',
        [],
        source_ref='experiment',
    )
    assert entry['source_ref'] == 'experiment'
    assert entry['source_sha256'] == hashlib.sha256(b'branch evidence').hexdigest()
