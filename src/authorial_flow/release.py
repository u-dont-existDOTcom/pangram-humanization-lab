from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import tempfile
import zipfile

from .version import GRAPH_VERSION


FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
PROJECT_INSTRUCTIONS_LIMIT = 8000
RELEASE_ARCHIVE_ROOT = "authorial-flow-graph-v1"
EXCLUDED_PARTS = {
    ".git", ".state", ".venv", ".pytest_cache", "__pycache__", ".worktrees",
}
EXCLUDED_PREFIXES = ("RESULT-", "UPLOAD-", "AUTHORIAL-SUPERVISOR-LIVE-SNAPSHOT-")
EXCLUDED_SUFFIXES = (".pyc", ".pyo")


class ReleaseError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReleaseManifest:
    archive_root: str
    source_commit_sha: str
    graph_version: str
    policy_version: str
    member_count: int


@dataclass(frozen=True)
class ReleaseVerification:
    pass_: bool
    errors: tuple[str, ...]
    archive_root: str
    project_instructions_chars: int
    member_count: int


def _sha(data: bytes) -> str:
    return sha256(data).hexdigest()


def _source_commit(repo_root: Path) -> str:
    try:
        p = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10,
        )
        if p.returncode == 0 and p.stdout.strip():
            return p.stdout.strip()
    except Exception:
        pass
    return "unversioned"


def _project_name(repo_root: Path) -> str:
    return RELEASE_ARCHIVE_ROOT


def _policy_version(repo_root: Path) -> str:
    policy = repo_root / "policy"
    dirs = sorted(p.name for p in policy.iterdir() if p.is_dir()) if policy.is_dir() else []
    return dirs[-1] if dirs else "unknown"


def _validate_project_instructions(repo_root: Path) -> int:
    path = repo_root / "PASTE_INTO_PROJECT_INSTRUCTIONS.txt"
    if not path.is_file():
        raise ReleaseError("Missing PASTE_INTO_PROJECT_INSTRUCTIONS.txt")
    count = len(path.read_text(encoding="utf-8"))
    if count > PROJECT_INSTRUCTIONS_LIMIT:
        raise ReleaseError(
            f"PASTE_INTO_PROJECT_INSTRUCTIONS.txt is {count} characters; release limit is 8,000"
        )
    return count


def _include_file(repo_root: Path, path: Path, out_zip: Path) -> bool:
    rel = path.relative_to(repo_root)
    if path.resolve() == out_zip.resolve():
        return False
    if any(part in EXCLUDED_PARTS for part in rel.parts):
        return False
    if path.name.startswith(EXCLUDED_PREFIXES):
        return False
    if path.name.endswith(EXCLUDED_SUFFIXES):
        return False
    if path.name in {"MANIFEST.json", "SHA256SUMS.txt"} and len(rel.parts) == 1:
        # Root release metadata is generated from the exact build, never copied from an old build.
        return False
    return True


def _source_members(repo_root: Path, out_zip: Path) -> list[tuple[str, bytes, int]]:
    members: list[tuple[str, bytes, int]] = []
    for path in sorted(repo_root.rglob("*"), key=lambda p: p.as_posix()):
        if not path.is_file() or not _include_file(repo_root, path, out_zip):
            continue
        rel = path.relative_to(repo_root).as_posix()
        mode = stat.S_IMODE(path.stat().st_mode)
        members.append((rel, path.read_bytes(), mode))
    return members


def _write_zip_member(zf: zipfile.ZipFile, name: str, data: bytes, mode: int) -> None:
    info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
    info.create_system = 3
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (mode & 0o777) << 16
    zf.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build_release(repo_root: Path, out_zip: Path) -> ReleaseManifest:
    repo_root = Path(repo_root).resolve()
    out_zip = Path(out_zip).resolve()
    _validate_project_instructions(repo_root)
    for required in ["INSTALL-AND-RUN.sh", "RUN.sh", "requirements.lock", "pyproject.toml", "README.md"]:
        if not (repo_root / required).is_file():
            raise ReleaseError(f"Missing required release asset: {required}")

    archive_root = _project_name(repo_root)
    source_commit = _source_commit(repo_root)
    policy_version = _policy_version(repo_root)
    source_members = _source_members(repo_root, out_zip)
    rows = []
    sums = []
    for rel, data, mode in source_members:
        digest = _sha(data)
        executable = bool(mode & 0o111)
        rows.append({
            "path": rel,
            "size_bytes": len(data),
            "sha256": digest,
            "executable": executable,
        })
        sums.append(f"{digest}  {rel}")

    manifest_payload = {
        "format": "authorial-flow-release-v1",
        "archive_root": archive_root,
        "source_commit_sha": source_commit,
        "graph_version": GRAPH_VERSION,
        "policy_version": policy_version,
        "members": rows,
    }
    manifest_bytes = (json.dumps(manifest_payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    sums_bytes = ("\n".join(sums) + "\n").encode()

    out_zip.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_zip.with_suffix(out_zip.suffix + ".tmp")
    try:
        with zipfile.ZipFile(tmp, "w") as zf:
            for rel, data, mode in source_members:
                _write_zip_member(zf, f"{archive_root}/{rel}", data, mode)
            _write_zip_member(zf, f"{archive_root}/MANIFEST.json", manifest_bytes, 0o644)
            _write_zip_member(zf, f"{archive_root}/SHA256SUMS.txt", sums_bytes, 0o644)
        os.replace(tmp, out_zip)
    finally:
        tmp.unlink(missing_ok=True)

    return ReleaseManifest(
        archive_root=archive_root,
        source_commit_sha=source_commit,
        graph_version=GRAPH_VERSION,
        policy_version=policy_version,
        member_count=len(source_members) + 2,
    )


def _safe_member(name: str) -> bool:
    p = PurePosixPath(name)
    return bool(name) and not p.is_absolute() and ".." not in p.parts


def verify_release(path: Path, *, run_install: bool = False) -> ReleaseVerification:
    path = Path(path).resolve()
    errors: list[str] = []
    instruction_chars = 0
    archive_root = ""
    if not path.is_file():
        return ReleaseVerification(False, (f"release does not exist: {path}",), "", 0, 0)

    try:
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            if len(names) != len(set(names)):
                errors.append("duplicate ZIP members")
            unsafe = [n for n in names if not _safe_member(n)]
            if unsafe:
                errors.append("unsafe ZIP members: " + ", ".join(unsafe))
            roots = {PurePosixPath(n).parts[0] for n in names if PurePosixPath(n).parts}
            if len(roots) != 1:
                errors.append(f"expected one archive root, found {sorted(roots)}")
            else:
                archive_root = next(iter(roots))
            prefix = archive_root + "/" if archive_root else ""
            required = [
                "INSTALL-AND-RUN.sh", "RUN.sh", "requirements.lock",
                "PASTE_INTO_PROJECT_INSTRUCTIONS.txt", "MANIFEST.json", "SHA256SUMS.txt",
            ]
            for rel in required:
                if prefix + rel not in names:
                    errors.append(f"missing required member: {rel}")
            if prefix + "PASTE_INTO_PROJECT_INSTRUCTIONS.txt" in names:
                text = zf.read(prefix + "PASTE_INTO_PROJECT_INSTRUCTIONS.txt").decode("utf-8")
                instruction_chars = len(text)
                if instruction_chars > PROJECT_INSTRUCTIONS_LIMIT:
                    errors.append(f"project instructions exceed 8,000 characters: {instruction_chars}")

            manifest = None
            if prefix + "MANIFEST.json" in names:
                try:
                    manifest = json.loads(zf.read(prefix + "MANIFEST.json"))
                except Exception as exc:
                    errors.append(f"release MANIFEST.json invalid: {exc}")
            if isinstance(manifest, dict):
                listed = {row["path"]: row for row in manifest.get("members", []) if isinstance(row, dict) and "path" in row}
                for rel, row in listed.items():
                    member = prefix + rel
                    if member not in names:
                        errors.append(f"manifest points to missing member: {rel}")
                        continue
                    data = zf.read(member)
                    if _sha(data) != row.get("sha256"):
                        errors.append(f"manifest hash mismatch: {rel}")
                    mode = (zf.getinfo(member).external_attr >> 16) & 0o777
                    if bool(mode & 0o111) != bool(row.get("executable")):
                        errors.append(f"manifest executable mismatch: {rel}")

            if prefix + "SHA256SUMS.txt" in names:
                for no, line in enumerate(zf.read(prefix + "SHA256SUMS.txt").decode().splitlines(), 1):
                    if not line.strip():
                        continue
                    try:
                        digest, rel = line.split("  ", 1)
                    except ValueError:
                        errors.append(f"invalid checksum line {no}")
                        continue
                    member = prefix + rel
                    if member not in names:
                        errors.append(f"checksum points to missing member: {rel}")
                    elif _sha(zf.read(member)) != digest:
                        errors.append(f"checksum mismatch: {rel}")

            for launcher in ["INSTALL-AND-RUN.sh", "RUN.sh"]:
                member = prefix + launcher
                if member in names:
                    mode = (zf.getinfo(member).external_attr >> 16) & 0o777
                    if not mode & 0o111:
                        errors.append(f"launcher is not executable: {launcher}")

            # Validate nested authority manifests as JSON; their own hash contracts are checked by runtime.
            for name in names:
                if name.endswith("/project/MANIFEST.json") or ("/policy/" in name and name.endswith("/MANIFEST.json")):
                    try:
                        json.loads(zf.read(name))
                    except Exception as exc:
                        errors.append(f"invalid nested manifest {name}: {exc}")

            member_count = len(names)

        if run_install and not errors:
            with tempfile.TemporaryDirectory(prefix="authorial-flow-release-") as td:
                target = Path(td)
                with zipfile.ZipFile(path) as zf:
                    zf.extractall(target)
                root = target / archive_root
                p = subprocess.run(
                    ["python3", "-m", "venv", ".verify-venv"], cwd=root,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120,
                )
                if p.returncode != 0:
                    errors.append("clean-ZIP virtualenv creation failed")
                else:
                    # Network/package installation is intentionally not attempted unless explicitly requested
                    # by a CI/target-machine caller with its dependency cache/network available.
                    q = subprocess.run(
                        [str(root / ".verify-venv/bin/python"), "-m", "compileall", "-q", "src", "tests"],
                        cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120,
                    )
                    if q.returncode != 0:
                        errors.append("clean-ZIP compile verification failed")
    except zipfile.BadZipFile as exc:
        errors.append(f"invalid ZIP: {exc}")
        member_count = 0

    return ReleaseVerification(
        pass_=not errors,
        errors=tuple(errors),
        archive_root=archive_root,
        project_instructions_chars=instruction_chars,
        member_count=member_count,
    )


def _main(argv: list[str] | None = None) -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(prog="python -m authorial_flow.release")
    sub = parser.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("verify", help="verify an Authorial Flow release ZIP")
    verify.add_argument("path", type=Path)
    verify.add_argument("--clean-zip-compile", action="store_true")
    args = parser.parse_args(argv)

    if args.command == "verify":
        report = verify_release(args.path, run_install=args.clean_zip_compile)
        print(f"archive_root={report.archive_root}")
        print(f"member_count={report.member_count}")
        print(f"project_instructions_chars={report.project_instructions_chars}")
        if not report.pass_:
            for error in report.errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 2
        print("verification=PASS")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(_main())
