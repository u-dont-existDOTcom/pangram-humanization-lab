#!/usr/bin/env python3
"""Reconcile an in-place release overlay with the local Git repair baseline.

A clean existing Git worktree is authoritative and is never rewritten.  When a
new release ZIP is overlaid onto an older installed release, the worktree is
expected to be dirty because release files changed while ``.state`` and the
local Git repository were intentionally preserved.  This script proves that the
dirty files are exactly the new release payload before committing a new local
baseline.  Unrelated changes fail closed.

The script is intentionally standard-library only so it can run before the
package itself is trusted as repairable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
from typing import Iterable
import zipfile

RELEASE_FORMAT = "authorial-flow-release-v1"
ROOT_METADATA = {"MANIFEST.json", "SHA256SUMS.txt"}
RUNTIME_PREFIXES = (".state/", ".venv/", ".git/")


class BaselineError(RuntimeError):
    pass


EVIDENCE_FORMAT = "authorial-flow-evidence-v1"
EVIDENCE_PREFIX = "AUTHORIAL-FLOW-EVIDENCE-"


def _valid_evidence_zip(path: Path) -> bool:
    """Return True only for a complete Authorial Flow evidence package.

    The filename is not authority.  Validate the package marker and every checksum
    before treating a legacy root-level ZIP as runtime-owned state.
    """
    if not path.is_file() or not path.name.startswith(EVIDENCE_PREFIX) or path.suffix.lower() != ".zip":
        return False
    try:
        with zipfile.ZipFile(path) as zf:
            names = [name for name in zf.namelist() if name and not name.endswith("/")]
            if "PACKAGE.json" not in names or "SHA256SUMS.txt" not in names:
                return False
            package = json.loads(zf.read("PACKAGE.json"))
            if not isinstance(package, dict) or package.get("format") != EVIDENCE_FORMAT:
                return False
            if package.get("reason") not in {"final", "bounded-failure", "manual"}:
                return False
            sums: dict[str, str] = {}
            for line in zf.read("SHA256SUMS.txt").decode("utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    digest, rel = line.split("  ", 1)
                except ValueError:
                    return False
                rel = PurePosixPath(rel).as_posix()
                if rel in sums or rel == "SHA256SUMS.txt" or rel not in names:
                    return False
                if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest.lower()):
                    return False
                sums[rel] = digest.lower()
            expected = set(names) - {"SHA256SUMS.txt"}
            if set(sums) != expected:
                return False
            for rel, digest in sums.items():
                if hashlib.sha256(zf.read(rel)).hexdigest() != digest:
                    return False
            return True
    except (OSError, zipfile.BadZipFile, KeyError, UnicodeDecodeError, json.JSONDecodeError):
        return False


def _migrate_legacy_root_evidence(root: Path) -> list[Path]:
    """Move validated legacy evidence ZIPs into ignored runtime state.

    Older releases wrote these packages at repository root, which made the main
    worktree dirty and could block both release reconciliation and later Codex
    repair promotion.  Only verified Authorial Flow evidence packages migrate.
    """
    migrated: list[Path] = []
    target_dir = root / ".state" / "evidence"
    for source in sorted(root.glob(f"{EVIDENCE_PREFIX}*.zip")):
        if not _valid_evidence_zip(source):
            continue
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / source.name
        if target.exists():
            if _sha_file(target) != _sha_file(source):
                raise BaselineError(f"runtime evidence destination collision: {source.name}")
            source.unlink()
        else:
            os.replace(source, target)
        migrated.append(target)
    return migrated


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["git", *args], cwd=root, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if check and proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()
        raise BaselineError(f"git {' '.join(args)} failed: {detail}")
    return proc


def _sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_rel(value: str) -> str:
    value = str(value).replace("\\", "/")
    p = PurePosixPath(value)
    if not value or p.is_absolute() or ".." in p.parts or value in {".", ".."}:
        raise BaselineError(f"unsafe release path: {value!r}")
    if value in ROOT_METADATA:
        return value
    if value.startswith(RUNTIME_PREFIXES) or value in {".git", ".state", ".venv"}:
        raise BaselineError(f"release manifest may not own runtime path: {value}")
    return p.as_posix()


def _parse_manifest_payload(payload: object, *, source: str) -> dict:
    if not isinstance(payload, dict) or payload.get("format") != RELEASE_FORMAT:
        raise BaselineError(f"{source} is not a {RELEASE_FORMAT} manifest")
    members = payload.get("members")
    if not isinstance(members, list):
        raise BaselineError(f"{source} members must be a list")
    normalized: list[dict] = []
    seen: set[str] = set()
    for index, raw in enumerate(members, 1):
        if not isinstance(raw, dict):
            raise BaselineError(f"{source} member {index} is not an object")
        rel = _safe_rel(str(raw.get("path", "")))
        digest = str(raw.get("sha256", ""))
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest.lower()):
            raise BaselineError(f"{source} member has invalid SHA-256: {rel}")
        if rel in seen:
            raise BaselineError(f"{source} contains duplicate member: {rel}")
        seen.add(rel)
        try:
            size = int(raw.get("size_bytes"))
        except (TypeError, ValueError) as exc:
            raise BaselineError(f"{source} member has invalid size: {rel}") from exc
        normalized.append({
            "path": rel,
            "sha256": digest.lower(),
            "size_bytes": size,
            "executable": bool(raw.get("executable", False)),
        })
    result = dict(payload)
    result["members"] = normalized
    return result


def _load_manifest(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BaselineError("release MANIFEST.json required for dirty in-place update") from exc
    except json.JSONDecodeError as exc:
        raise BaselineError(f"release MANIFEST.json is invalid JSON: {exc}") from exc
    return _parse_manifest_payload(payload, source="release MANIFEST.json")


def _verify_checksums(root: Path, manifest: dict) -> None:
    sums_path = root / "SHA256SUMS.txt"
    try:
        lines = sums_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        raise BaselineError("release SHA256SUMS.txt is required") from exc
    parsed: dict[str, str] = {}
    for no, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            digest, raw_rel = line.split("  ", 1)
        except ValueError as exc:
            raise BaselineError(f"invalid SHA256SUMS.txt line {no}") from exc
        rel = _safe_rel(raw_rel)
        digest = digest.strip().lower()
        if rel in parsed:
            raise BaselineError(f"duplicate checksum entry: {rel}")
        parsed[rel] = digest
    expected = {row["path"]: row["sha256"] for row in manifest["members"]}
    if parsed != expected:
        missing = sorted(set(expected) - set(parsed))
        extra = sorted(set(parsed) - set(expected))
        mismatched = sorted(k for k in set(parsed) & set(expected) if parsed[k] != expected[k])
        raise BaselineError(
            "SHA256SUMS.txt does not match release manifest"
            f"; missing={missing[:5]} extra={extra[:5]} mismatched={mismatched[:5]}"
        )


def _verify_release_members(root: Path, manifest: dict) -> set[str]:
    members: set[str] = set()
    for row in manifest["members"]:
        rel = row["path"]
        path = root / rel
        if not path.is_file():
            raise BaselineError(f"release member missing after overlay: {rel}")
        if path.stat().st_size != row["size_bytes"]:
            raise BaselineError(f"release member size mismatch after overlay: {rel}")
        if _sha_file(path) != row["sha256"]:
            raise BaselineError(f"release member hash mismatch after overlay: {rel}")
        executable = bool(path.stat().st_mode & 0o111)
        if executable != row["executable"]:
            raise BaselineError(f"release member executable-bit mismatch after overlay: {rel}")
        members.add(rel)
    _verify_checksums(root, manifest)
    return members


def _is_git_repo(root: Path) -> bool:
    proc = _git(root, "rev-parse", "--is-inside-work-tree", check=False)
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def _status_entries(root: Path) -> list[tuple[str, str]]:
    proc = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise BaselineError(f"git status failed: {proc.stderr.decode(errors='replace').strip()}")
    fields = proc.stdout.split(b"\0")
    out: list[tuple[str, str]] = []
    index = 0
    while index < len(fields):
        raw = fields[index]
        index += 1
        if not raw:
            continue
        text = raw.decode("utf-8", errors="surrogateescape")
        if len(text) < 4 or text[2] != " ":
            raise BaselineError("cannot safely parse git status during release reconciliation")
        status = text[:2]
        rel = _safe_rel(text[3:])
        if "R" in status or "C" in status:
            # In porcelain -z mode renames/copies carry an additional origin path.
            if index < len(fields) and fields[index]:
                origin = fields[index].decode("utf-8", errors="surrogateescape")
                index += 1
                _safe_rel(origin)
            raise BaselineError("non-release working-tree changes: rename/copy present")
        out.append((status, rel))
    return out


def _head_manifest(root: Path) -> dict | None:
    proc = _git(root, "show", "HEAD:MANIFEST.json", check=False)
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        payload = json.loads(proc.stdout)
        return _parse_manifest_payload(payload, source="previous HEAD MANIFEST.json")
    except (json.JSONDecodeError, BaselineError):
        return None


def _ensure_git_identity(root: Path) -> None:
    if _git(root, "config", "--get", "user.name", check=False).returncode != 0:
        _git(root, "config", "user.name", "Authorial Flow Baseline")
    if _git(root, "config", "--get", "user.email", check=False).returncode != 0:
        _git(root, "config", "user.email", "authorial-flow@example.invalid")


def _chunks(values: Iterable[str], size: int = 100) -> Iterable[list[str]]:
    chunk: list[str] = []
    for value in values:
        chunk.append(value)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def _stage_paths(root: Path, paths: Iterable[str]) -> None:
    for chunk in _chunks(sorted(set(paths))):
        _git(root, "add", "--", *chunk)


def _write_state_metadata(root: Path, manifest: dict, local_commit: str) -> None:
    state = root / ".state"
    state.mkdir(parents=True, exist_ok=True)
    payload = {
        "format": "authorial-flow-release-baseline-v1",
        "release_source_commit": str(manifest.get("source_commit_sha", "")),
        "local_baseline_commit": local_commit,
        "manifest_sha256": _sha_file(root / "MANIFEST.json"),
    }
    (state / "release-baseline.json").write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _fallback_init(root: Path) -> str:
    _git(root, "init", "-q")
    _ensure_git_identity(root)
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "Authorial Flow Baseline")
    return _git(root, "rev-parse", "HEAD").stdout.strip()


def reconcile(root: Path) -> str:
    root = root.resolve()
    if not root.is_dir():
        raise BaselineError(f"root is not a directory: {root}")

    migrated_evidence = _migrate_legacy_root_evidence(root)
    for path in migrated_evidence:
        print(f"release_evidence_migrated={path.relative_to(root).as_posix()}")

    has_git = _is_git_repo(root)
    if has_git:
        status = _status_entries(root)
        if not status:
            head = _git(root, "rev-parse", "HEAD").stdout.strip()
            print(f"release_baseline=clean-existing-head commit={head}")
            return head
    else:
        status = []

    manifest_path = root / "MANIFEST.json"
    if not manifest_path.is_file():
        if has_git:
            raise BaselineError("release MANIFEST.json required for dirty in-place update")
        head = _fallback_init(root)
        print(f"release_baseline=initialized-development-head commit={head}")
        return head

    manifest = _load_manifest(manifest_path)
    new_members = _verify_release_members(root, manifest)
    allowed = set(new_members) | ROOT_METADATA

    if not has_git:
        # A release ZIP should contain exactly its declared payload plus generated
        # root metadata; runtime state and venv are deliberately outside Git.
        extras: list[str] = []
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            if rel.startswith(RUNTIME_PREFIXES):
                continue
            if rel not in allowed:
                extras.append(rel)
        if extras:
            raise BaselineError(
                "non-release working-tree changes: unexpected file(s) before baseline init: "
                + ", ".join(sorted(extras)[:10])
            )
        _git(root, "init", "-q")
        _ensure_git_identity(root)
        _stage_paths(root, allowed)
        _git(root, "commit", "-qm", f"Authorial Flow release baseline {manifest.get('source_commit_sha', '')}")
        head = _git(root, "rev-parse", "HEAD").stdout.strip()
        _write_state_metadata(root, manifest, head)
        print(f"release_baseline=initialized-release commit={head}")
        return head

    old_manifest = _head_manifest(root)
    if old_manifest is None:
        raise BaselineError(
            "non-release working-tree changes: previous release manifest unavailable; refusing dirty baseline rewrite"
        )
    old_members = {row["path"] for row in old_manifest["members"]}
    allowed |= old_members

    # Before mutating/staging anything, reject any path that cannot be explained
    # by either the previous release or the exact new release overlay.
    outside = sorted({rel for _, rel in status if rel not in allowed})
    if outside:
        raise BaselineError("non-release working-tree changes: " + ", ".join(outside[:10]))

    # An old-only member should be byte-identical to the committed prior release:
    # unzip overlays do not mutate/delete files that disappeared from a newer ZIP.
    # A dirty old-only path therefore represents an independent local change.
    dirty_paths = {rel for _, rel in status}
    dirty_old_only = sorted((old_members - new_members) & dirty_paths)
    if dirty_old_only:
        raise BaselineError(
            "non-release working-tree changes: obsolete release member modified locally: "
            + ", ".join(dirty_old_only[:10])
        )

    _ensure_git_identity(root)

    # Remove files owned by the previous release that the new release no longer owns.
    obsolete = sorted(old_members - new_members)
    for rel in obsolete:
        tracked = _git(root, "ls-files", "--error-unmatch", "--", rel, check=False)
        if tracked.returncode == 0:
            _git(root, "rm", "-q", "--ignore-unmatch", "--", rel)
        else:
            (root / rel).unlink(missing_ok=True)

    _stage_paths(root, set(new_members) | ROOT_METADATA)

    staged = {
        item for item in _git(root, "diff", "--cached", "--name-only", "-z").stdout.split("\0") if item
    }
    outside_staged = sorted(staged - allowed)
    if outside_staged:
        raise BaselineError("non-release working-tree changes staged unexpectedly: " + ", ".join(outside_staged[:10]))

    remaining = _status_entries(root)
    outside_remaining = sorted({rel for _, rel in remaining if rel not in allowed})
    if outside_remaining:
        raise BaselineError("non-release working-tree changes: " + ", ".join(outside_remaining[:10]))

    if _git(root, "diff", "--cached", "--quiet", check=False).returncode != 0:
        _git(root, "commit", "-qm", f"Authorial Flow release baseline {manifest.get('source_commit_sha', '')}")

    final_status = _status_entries(root)
    if final_status:
        unresolved = ", ".join(rel for _, rel in final_status[:10])
        raise BaselineError(f"non-release working-tree changes remain after reconciliation: {unresolved}")

    head = _git(root, "rev-parse", "HEAD").stdout.strip()
    _write_state_metadata(root, manifest, head)
    print(f"release_baseline=reconciled-release commit={head}")
    return head


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    try:
        reconcile(args.root)
    except BaselineError as exc:
        print(f"release baseline reconciliation failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
