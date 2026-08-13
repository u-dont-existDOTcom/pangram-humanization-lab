from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ALLOWED_DISPOSITIONS = {
    'promoted', 'provisional', 'experimental', 'article-specific', 'superseded', 'no-new-lesson'
}


def _run(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=repo, text=True, capture_output=True, check=check)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def _parse_time(value: str) -> datetime:
    value = value.replace('Z', '+00:00')
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _git_paths(repo: Path, ref: str) -> list[str]:
    cp = _run(repo, 'git', 'ls-tree', '-r', '--name-only', ref)
    return [line.strip() for line in cp.stdout.splitlines() if line.strip()]


def _git_bytes(repo: Path, ref: str, path: str) -> bytes:
    cp = subprocess.run(['git', 'show', f'{ref}:{path}'], cwd=repo, capture_output=True, check=True)
    return cp.stdout


def _git_last_modified(repo: Path, ref: str, path: str) -> datetime:
    cp = _run(repo, 'git', 'log', '-1', '--format=%cI', ref, '--', path)
    value = cp.stdout.strip()
    if not value:
        return datetime.fromtimestamp(0, timezone.utc)
    return _parse_time(value)


def _review_entries(repo: Path, ref: str) -> list[dict]:
    exists = _run(repo, 'git', 'cat-file', '-e', f'{ref}:state/LESSON-INBOX.json', check=False).returncode == 0
    if not exists:
        return []
    obj = json.loads(_git_bytes(repo, ref, 'state/LESSON-INBOX.json').decode('utf-8'))
    if obj.get('format') != 'lesson-review-v1' or not isinstance(obj.get('entries'), list):
        raise ValueError(f'invalid lesson review queue at {ref}:state/LESSON-INBOX.json')
    return [entry for entry in obj['entries'] if isinstance(entry, dict)]


def validate_ledger(ledger: dict, config: dict) -> list[str]:
    errors: list[str] = []
    entries = ledger.get('entries')
    if ledger.get('schema_version') != 1:
        errors.append('ledger schema_version must be 1')
    if not isinstance(entries, list):
        return errors + ['ledger entries must be a list']

    seen_ids: set[str] = set()
    lesson_index = config.get('lesson_index', 'state/LESSON-INDEX.md')
    summary_globs = config.get('lesson_summary_globs', ['state/WORKING-LESSONS*.md'])

    for i, entry in enumerate(entries):
        prefix = f'entry[{i}]'
        if not isinstance(entry, dict):
            errors.append(f'{prefix} must be an object')
            continue
        eid = str(entry.get('id') or '').strip()
        if not eid:
            errors.append(f'{prefix} id is required')
        elif eid in seen_ids:
            errors.append(f'{prefix} duplicate id {eid}')
        seen_ids.add(eid)
        path = str(entry.get('source_path') or '').strip()
        sha = str(entry.get('source_sha256') or '').strip().lower()
        finding = str(entry.get('finding') or '').strip()
        disposition = str(entry.get('disposition') or '').strip()
        reason = str(entry.get('reason') or '').strip()
        promoted_to = entry.get('promoted_to', [])
        if not path:
            errors.append(f'{prefix} source_path is required')
        if len(sha) != 64 or any(ch not in '0123456789abcdef' for ch in sha):
            errors.append(f'{prefix} source_sha256 must be 64 lowercase hex characters')
        if not finding:
            errors.append(f'{prefix} finding is required')
        if disposition not in ALLOWED_DISPOSITIONS:
            errors.append(f'{prefix} disposition must be one of {sorted(ALLOWED_DISPOSITIONS)}')
        if not isinstance(promoted_to, list) or not all(isinstance(x, str) and x for x in promoted_to):
            errors.append(f'{prefix} promoted_to must be a list of non-empty paths')
            promoted_to = []
        if disposition == 'promoted':
            if lesson_index not in promoted_to:
                errors.append(f'{prefix} promoted finding must target lesson index {lesson_index}')
            if not any(_matches(target, summary_globs) for target in promoted_to):
                errors.append(f'{prefix} promoted finding must target at least one lesson summary')
        elif disposition in ALLOWED_DISPOSITIONS:
            if not reason:
                errors.append(f'{prefix} non-promoted finding requires a reason')
    return errors


def audit_ref(repo: Path | str, ref: str = 'HEAD') -> dict:
    repo = Path(repo)
    config = _load_json(repo / 'state/lesson-closeout-config.json')
    ledger = _load_json(repo / 'state/LESSON-LEDGER.json')
    ledger_errors = validate_ledger(ledger, config)
    cutoff = _parse_time(config['enforcement_started_at_utc'])
    tracked_globs = config.get('tracked_globs', [])

    by_key: dict[tuple[str, str], list[dict]] = {}
    ledger_entries = [entry for entry in ledger.get('entries', []) if isinstance(entry, dict)]
    for entry in ledger_entries:
        key = (str(entry.get('source_path') or ''), str(entry.get('source_sha256') or '').lower())
        by_key.setdefault(key, []).append(entry)

    pending_review: list[dict] = []
    for queued in _review_entries(repo, ref):
        source_path = str(queued.get('source_path') or '')
        source_ref = str(queued.get('source_ref') or '')
        source_sha = str(queued.get('source_sha256') or '').lower()
        matches = [
            entry for entry in ledger_entries
            if str(entry.get('source_path') or '') == source_path
            and str(entry.get('source_sha256') or '').lower() == source_sha
            and str(entry.get('source_ref') or '') == source_ref
        ]
        if not matches:
            pending_review.append({
                'id': queued.get('id'),
                'source_path': source_path,
                'source_ref': source_ref,
                'source_sha256': source_sha,
            })

    orphans: list[dict] = []
    grandfathered: list[dict] = []
    reviewed: list[dict] = []
    for path in _git_paths(repo, ref):
        if not _matches(path, tracked_globs):
            continue
        modified = _git_last_modified(repo, ref, path)
        if modified < cutoff:
            grandfathered.append({'path': path, 'last_modified': modified.isoformat()})
            continue
        data = _git_bytes(repo, ref, path)
        sha = hashlib.sha256(data).hexdigest()
        matching = by_key.get((path, sha), [])
        if not matching:
            orphans.append({
                'path': path,
                'sha256': sha,
                'last_modified': modified.isoformat(),
                'reason': 'current artifact hash has no disposition',
            })
        else:
            reviewed.append({'path': path, 'sha256': sha, 'entries': [e.get('id') for e in matching]})

    return {
        'ok': not ledger_errors and not orphans and not pending_review,
        'ref': ref,
        'ledger_errors': ledger_errors,
        'orphans': orphans,
        'pending_review': pending_review,
        'reviewed': reviewed,
        'grandfathered': grandfathered,
    }


def check_range(repo: Path | str, base: str, head: str = "HEAD") -> dict:
    repo = Path(repo)
    config = _load_json(repo / "state/lesson-closeout-config.json")
    ledger = _load_json(repo / "state/LESSON-LEDGER.json")
    errors = validate_ledger(ledger, config)
    cp = _run(repo, "git", "diff", "--name-only", f"{base}..{head}")
    changed = {line.strip() for line in cp.stdout.splitlines() if line.strip()}
    tracked = [p for p in changed if _matches(p, config.get("tracked_globs", []))]
    by_key = {}
    for entry in ledger.get("entries", []):
        if isinstance(entry, dict):
            key = (str(entry.get("source_path") or ""), str(entry.get("source_sha256") or "").lower())
            by_key.setdefault(key, []).append(entry)

    reviewed = []
    for path in tracked:
        exists = _run(repo, "git", "cat-file", "-e", f"{head}:{path}", check=False).returncode == 0
        if not exists:
            continue
        sha = hashlib.sha256(_git_bytes(repo, head, path)).hexdigest()
        matches = by_key.get((path, sha), [])
        if not matches:
            errors.append(f"{path}: changed tracked artifact has no disposition for current hash {sha}")
            continue
        reviewed.append({"path": path, "sha256": sha, "entries": [e.get("id") for e in matches]})
        for entry in matches:
            if entry.get("disposition") == "promoted":
                for target in entry.get("promoted_to", []):
                    if target not in changed:
                        errors.append(f"{path}: promoted target was not changed in the same range: {target}")

    return {
        "ok": not errors,
        "base": base,
        "head": head,
        "changed": sorted(changed),
        "reviewed": reviewed,
        "errors": errors,
    }


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')


def record_finding(repo: Path, source: str, finding: str, disposition: str, reason: str, promoted_to: list[str], source_ref: str | None = None) -> dict:
    if source_ref:
        exists = _run(repo, 'git', 'cat-file', '-e', f'{source_ref}:{source}', check=False).returncode == 0
        if not exists:
            raise SystemExit(f'source file does not exist at {source_ref}: {source}')
        source_bytes = _git_bytes(repo, source_ref, source)
    else:
        source_path = repo / source
        if not source_path.is_file():
            raise SystemExit(f'source file does not exist: {source}')
        source_bytes = source_path.read_bytes()
    if disposition == 'experimental':
        disposition = 'provisional'
    if disposition not in ALLOWED_DISPOSITIONS:
        raise SystemExit(f'invalid disposition: {disposition}')
    sha = hashlib.sha256(source_bytes).hexdigest()
    ledger_path = repo / 'state/LESSON-LEDGER.json'
    ledger = _load_json(ledger_path)
    existing = [e for e in ledger.get('entries', []) if e.get('source_path') == source and e.get('source_sha256') == sha]
    seq = len(existing) + 1
    eid = f"L-{sha[:10]}-{seq:02d}"
    entry = {
        'id': eid,
        'source_path': source,
        'source_sha256': sha,
        'finding': finding,
        'disposition': disposition,
        'reason': reason,
        'promoted_to': promoted_to,
        'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
        'source_ref': source_ref or 'working-tree',
    }
    ledger.setdefault('entries', []).append(entry)
    errors = validate_ledger(ledger, _load_json(repo / 'state/lesson-closeout-config.json'))
    if errors:
        raise SystemExit('\n'.join(errors))
    _write_json(ledger_path, ledger)
    return entry


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description='Lesson closeout/disposition gate')
    p.add_argument('--repo', default='.', help='repository root')
    sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('audit', help='audit tracked current research artifacts')
    a.add_argument('--ref', default='HEAD')
    a.add_argument('--json-out')
    c = sub.add_parser('check', help='check changed tracked artifacts in a git range')
    c.add_argument('--base', required=True)
    c.add_argument('--head', default='HEAD')
    c.add_argument('--json-out')
    r = sub.add_parser('record', help='record a finding disposition for the current source file hash')
    r.add_argument('--source', required=True)
    r.add_argument('--finding', required=True)
    r.add_argument('--disposition', required=True, choices=sorted(ALLOWED_DISPOSITIONS))
    r.add_argument('--reason', default='')
    r.add_argument('--promoted-to', action='append', default=[])
    r.add_argument('--source-ref', help='optional git ref containing the source artifact')

    args = p.parse_args(argv)
    repo = Path(args.repo).resolve()
    if args.cmd == 'audit':
        report = audit_ref(repo, args.ref)
        text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True)
        print(text)
        if args.json_out:
            Path(args.json_out).write_text(text + '\n', encoding='utf-8')
        return 0 if report['ok'] else 1
    if args.cmd == 'check':
        report = check_range(repo, args.base, args.head)
        text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True)
        print(text)
        if args.json_out:
            Path(args.json_out).write_text(text + '\n', encoding='utf-8')
        return 0 if report['ok'] else 1
    entry = record_finding(repo, args.source, args.finding, args.disposition, args.reason, args.promoted_to, source_ref=args.source_ref)
    print(json.dumps(entry, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
