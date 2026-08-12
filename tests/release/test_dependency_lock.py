from __future__ import annotations

import json
from pathlib import Path

import pytest

from authorial_flow.dependency_lock import build_hashed_lock_from_pip_report


def test_pip_report_becomes_exact_hash_pinned_lock(tmp_path):
    report=tmp_path/'report.json'
    report.write_text(json.dumps({
        'install':[
            {
                'metadata':{'name':'Example-Pkg','version':'1.2.3'},
                'download_info':{'archive_info':{'hashes':{'sha256':'a'*64}}},
            },
            {
                'metadata':{'name':'other_pkg','version':'4.5.6'},
                'download_info':{'archive_info':{'hashes':{'sha256':'b'*64}}},
            },
        ]
    }))
    out=tmp_path/'resolved.lock'
    source=tmp_path/'requirements.lock'; source.write_text('example-pkg==1.2.3\n')
    meta=tmp_path/'resolved.json'
    build_hashed_lock_from_pip_report(report,out,source_requirements=source,metadata_path=meta)
    text=out.read_text()
    assert 'example-pkg==1.2.3 --hash=sha256:' + 'a'*64 in text
    assert 'other-pkg==4.5.6 --hash=sha256:' + 'b'*64 in text
    metadata=json.loads(meta.read_text())
    assert metadata['source_requirements_sha256']
    assert metadata['package_count']==2


def test_pip_report_without_sha256_fails_closed(tmp_path):
    report=tmp_path/'report.json'
    report.write_text(json.dumps({'install':[{
        'metadata':{'name':'pkg','version':'1.0'},
        'download_info':{'archive_info':{'hashes':{}}},
    }]}))
    source=tmp_path/'requirements.lock'; source.write_text('pkg==1.0\n')
    with pytest.raises(ValueError,match='sha256'):
        build_hashed_lock_from_pip_report(report,tmp_path/'resolved.lock',source_requirements=source)


def test_installer_resolves_before_install_and_installs_under_require_hashes():
    root=Path(__file__).resolve().parents[2]
    text=(root/'INSTALL-AND-RUN.sh').read_text()
    assert 'pip install --dry-run --ignore-installed --report' in text
    assert 'scripts/resolve_dependency_lock.py' in text
    assert 'pip install --require-hashes --requirement "$RESOLVED_LOCK"' in text
    assert 'pip install --requirement requirements.lock' not in text


def test_resolved_lock_is_reused_only_for_same_source_and_lock_hash(tmp_path):
    from authorial_flow.dependency_lock import lock_is_current
    report=tmp_path/'report.json'
    report.write_text(json.dumps({'install':[{
        'metadata':{'name':'pkg','version':'1.0'},
        'download_info':{'archive_info':{'hashes':{'sha256':'c'*64}}},
    }]}))
    source=tmp_path/'requirements.lock'; source.write_text('pkg==1.0\n')
    lock=tmp_path/'resolved.lock'; meta=tmp_path/'resolved.json'
    build_hashed_lock_from_pip_report(report,lock,source_requirements=source,metadata_path=meta)
    assert lock_is_current(source,meta,lock) is True
    source.write_text('pkg==1.1\n')
    assert lock_is_current(source,meta,lock) is False
