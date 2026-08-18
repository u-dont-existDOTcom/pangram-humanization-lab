from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from pangram_lab import gui_browserbase as gui_core
from pangram_lab.git_sync import GitSync
from pangram_lab.gui_local import (
    DEFAULT_PROFILE_DIR,
    LocalPlaywrightConfig,
    bootstrap_login,
    environment_status,
    input_status,
    launch_smoke_test,
    recover_existing_report,
    run_inputs,
    verify_login_persistence,
)


DEFAULT_OUTPUT_ROOT = Path("state/gui-runs")
SOURCE_REPOSITORY = "u-dont-existDOTcom/pangram-humanization-lab"
CURRENT_ROMANCE_BRANCH = "agent/romance-primal-crucible-gui-repair-20260817"
LAST_OBSERVED_ROMANCE_HEAD = "8e0d70d0ea51fbcb12e307ed0629ed75ee35ce8c"
CURRENT_ROMANCE_READER_SHA256 = "10359ab2119ffbe9a8a7a4a52cd0c3216bb1a6a2c0bffbd7e66fca01287f17ce"
CURRENT_ROMANCE_TOTAL_WORDS = 20_496
CURRENT_ROMANCE_MANIFEST_PATH = "work/romance-current-assembly/pangram-halves-manifest.json"
CURRENT_ROMANCE_PARTS: tuple[dict[str, object], ...] = (
    {
        "number": 1,
        "name": "pangram-part-1.txt",
        "source_path": "work/romance-current-assembly/pangram-part-1.txt",
        "sha256": "ae88df0f4156537239cb984337196703b88629c3588a5e58ee50c0888d3b39f8",
        "words": 10_236,
    },
    {
        "number": 2,
        "name": "pangram-part-2.txt",
        "source_path": "work/romance-current-assembly/pangram-part-2.txt",
        "sha256": "2df878093bc05fefa98ca30e9a97bdd52e212370f432bf0408e90f1b60c54bb0",
        "words": 10_260,
    },
)
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class PreparedInputs:
    paths: tuple[Path, ...]
    expected_sha256: dict[str, str] | None
    source_metadata: dict[str, dict[str, object]] | None
    source_receipt: dict[str, object] | None


def _add_browser_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--profile-dir", type=Path, default=DEFAULT_PROFILE_DIR)
    parser.add_argument("--browser-executable", type=Path)
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without a visible browser window. Headed mode is the safe default.",
    )
    parser.add_argument(
        "--allow-ordinary-profile",
        action="store_true",
        help="Dangerous explicit override; do not use without owner authorization.",
    )
    parser.add_argument(
        "--allow-profile-in-git-repo",
        action="store_true",
        help="Dangerous explicit override; persistent auth profiles must normally stay outside Git.",
    )


def _add_input_options(parser: argparse.ArgumentParser, *, multiple: bool) -> None:
    parser.add_argument(
        "--input",
        action="append" if multiple else None,
        type=Path,
        dest="inputs" if multiple else "input",
    )
    parser.add_argument(
        "--expect-sha",
        action="append",
        default=[],
        metavar="PATH_OR_NAME=SHA256",
        help="Exact pre-browser SHA gate for explicit inputs; repeat as needed.",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pangram-local",
        description=(
            "Deterministic Pangram GUI automation through a dedicated local Playwright profile."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    bootstrap = sub.add_parser(
        "bootstrap",
        help="Open the dedicated visible profile for one-time manual Pangram login.",
    )
    _add_browser_options(bootstrap)

    verify = sub.add_parser(
        "verify",
        help="Verify saved Pangram authentication and bounded controls without submitting text.",
    )
    _add_browser_options(verify)

    run = sub.add_parser(
        "run",
        help="Submit exact uncached inputs with SHA, cache, ambiguity, and Git-durability gates.",
    )
    _add_browser_options(run)
    _add_input_options(run, multiple=True)
    run.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    run.add_argument(
        "--force",
        action="store_true",
        help="Bypass a completed/ambiguous exact-SHA block only after explicit evidence review.",
    )
    run.add_argument("--report-timeout-ms", type=int, default=180_000)
    run.add_argument(
        "--no-fetch",
        action="store_true",
        help="Use an already-fetched current Romance source commit for the default run.",
    )

    recover = sub.add_parser(
        "recover",
        help="Capture a matching Pangram History report without a detector submission.",
    )
    _add_browser_options(recover)
    _add_input_options(recover, multiple=False)
    recover.add_argument("--part", choices=(1, 2), type=int)
    recover.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    recover.add_argument("--no-fetch", action="store_true")

    status = sub.add_parser(
        "status",
        help="Report environment, exact source/cache state, and optional read-only browser checks.",
    )
    _add_browser_options(status)
    _add_input_options(status, multiple=True)
    status.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    status.add_argument("--environment-only", action="store_true")
    status.add_argument("--launch-smoke", action="store_true")
    status.add_argument("--check-auth", action="store_true")
    status.add_argument("--no-fetch", action="store_true")
    return parser


def _config(args: argparse.Namespace) -> LocalPlaywrightConfig:
    return LocalPlaywrightConfig.from_env(
        profile_dir=args.profile_dir,
        browser_executable=args.browser_executable,
        headed=not args.headless,
        allow_ordinary_profile=args.allow_ordinary_profile,
        allow_profile_in_git_repo=args.allow_profile_in_git_repo,
    )


def _git(
    repo_root: Path,
    args: Iterable[str],
    *,
    text: bool,
    check: bool = True,
) -> subprocess.CompletedProcess[Any]:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=text,
    )
    if check and completed.returncode != 0:
        if text:
            detail = completed.stderr.strip() or completed.stdout.strip()
        else:
            detail = (
                completed.stderr.decode("utf-8", errors="replace").strip()
                or completed.stdout.decode("utf-8", errors="replace").strip()
            )
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return completed


def repository_root(cwd: Path | None = None) -> Path:
    base = Path.cwd() if cwd is None else Path(cwd)
    completed = subprocess.run(
        ["git", "-C", str(base), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "pangram-local must run inside the pangram-humanization-lab Git repository"
        )
    return Path(completed.stdout.strip()).resolve()


def _resolve_output_root(repo_root: Path, supplied: Path) -> Path:
    candidate = supplied if supplied.is_absolute() else repo_root / supplied
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise RuntimeError(
            f"Pangram evidence output must remain inside the repository: {resolved}"
        ) from exc
    if resolved == repo_root.resolve():
        raise RuntimeError("Pangram evidence output cannot be the repository root")
    return resolved


def _parse_expected_sha(values: Iterable[str]) -> dict[str, str] | None:
    parsed: dict[str, str] = {}
    for raw in values:
        if "=" not in raw:
            raise RuntimeError(f"invalid --expect-sha value {raw!r}; use PATH_OR_NAME=SHA256")
        key, digest = raw.rsplit("=", 1)
        key = key.strip()
        digest = digest.strip().lower()
        if not key or not _HEX64_RE.fullmatch(digest):
            raise RuntimeError(f"invalid --expect-sha value {raw!r}")
        parsed[key] = digest
    return parsed or None


def _fetch_current_romance_commit(repo_root: Path, *, no_fetch: bool) -> str:
    remote_ref = f"refs/remotes/origin/{CURRENT_ROMANCE_BRANCH}"
    if not no_fetch:
        _git(
            repo_root,
            [
                "fetch",
                "--quiet",
                "origin",
                f"{CURRENT_ROMANCE_BRANCH}:{remote_ref}",
            ],
            text=True,
        )
    completed = _git(repo_root, ["rev-parse", f"{remote_ref}^{{commit}}"], text=True)
    return str(completed.stdout).strip()


def _read_git_file(repo_root: Path, commit: str, source_path: str) -> bytes:
    completed = _git(
        repo_root,
        ["show", f"{commit}:{source_path}"],
        text=False,
    )
    return bytes(completed.stdout)


def _validate_manifest(manifest: Mapping[str, object]) -> None:
    expected = {
        "schema_version": 1,
        "reader_visible_sha256": CURRENT_ROMANCE_READER_SHA256,
        "total_words": CURRENT_ROMANCE_TOTAL_WORDS,
        "part1_sha256": str(CURRENT_ROMANCE_PARTS[0]["sha256"]),
        "part1_words": int(CURRENT_ROMANCE_PARTS[0]["words"]),
        "part2_sha256": str(CURRENT_ROMANCE_PARTS[1]["sha256"]),
        "part2_words": int(CURRENT_ROMANCE_PARTS[1]["words"]),
    }
    mismatches = [
        f"{key}: expected={value!r} actual={manifest.get(key)!r}"
        for key, value in expected.items()
        if manifest.get(key) != value
    ]
    if mismatches:
        raise RuntimeError(
            "the live Romance detector manifest no longer matches the authorized exact boundary: "
            + "; ".join(mismatches)
        )


def materialize_current_romance_inputs(
    repo_root: Path,
    *,
    no_fetch: bool,
) -> PreparedInputs:
    commit = _fetch_current_romance_commit(repo_root, no_fetch=no_fetch)
    manifest_bytes = _read_git_file(repo_root, commit, CURRENT_ROMANCE_MANIFEST_PATH)
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("the current Romance Pangram manifest is not valid UTF-8 JSON") from exc
    if not isinstance(manifest, dict):
        raise RuntimeError("the current Romance Pangram manifest is not a JSON object")
    _validate_manifest(manifest)

    cache_root = Path.home() / ".cache" / "pangram-local" / "inputs" / commit
    cache_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        cache_root.chmod(0o700)
    except OSError:
        pass

    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    paths: list[Path] = []
    expected: dict[str, str] = {}
    source_metadata: dict[str, dict[str, object]] = {}

    for part in CURRENT_ROMANCE_PARTS:
        name = str(part["name"])
        source_path = str(part["source_path"])
        expected_digest = str(part["sha256"])
        expected_words = int(part["words"])
        data = _read_git_file(repo_root, commit, source_path)
        digest = hashlib.sha256(data).hexdigest()
        if digest != expected_digest:
            raise RuntimeError(
                f"current Romance {name} failed exact byte SHA-256 gate: "
                f"expected={expected_digest} actual={digest}"
            )
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RuntimeError(f"current Romance {name} is not UTF-8") from exc
        words = len(text.split())
        if words != expected_words:
            raise RuntimeError(
                f"current Romance {name} failed exact word-count gate: "
                f"expected={expected_words} actual={words}"
            )

        local_path = cache_root / name
        local_path.write_bytes(data)
        try:
            local_path.chmod(0o600)
        except OSError:
            pass
        paths.append(local_path)
        expected[str(local_path)] = expected_digest
        source = {
            "repository": SOURCE_REPOSITORY,
            "source_branch": CURRENT_ROMANCE_BRANCH,
            "source_commit": commit,
            "source_path": source_path,
            "source_manifest_path": CURRENT_ROMANCE_MANIFEST_PATH,
            "source_manifest_sha256": manifest_sha256,
            "reader_visible_sha256": CURRENT_ROMANCE_READER_SHA256,
            "part_number": int(part["number"]),
            "last_observed_branch_head": LAST_OBSERVED_ROMANCE_HEAD,
        }
        source_metadata[str(local_path)] = source
        source_metadata[name] = source

    return PreparedInputs(
        paths=tuple(paths),
        expected_sha256=expected,
        source_metadata=source_metadata,
        source_receipt={
            "repository": SOURCE_REPOSITORY,
            "source_branch": CURRENT_ROMANCE_BRANCH,
            "source_commit": commit,
            "last_observed_branch_head": LAST_OBSERVED_ROMANCE_HEAD,
            "manifest_path": CURRENT_ROMANCE_MANIFEST_PATH,
            "manifest_sha256": manifest_sha256,
            "reader_visible_sha256": CURRENT_ROMANCE_READER_SHA256,
            "total_words": CURRENT_ROMANCE_TOTAL_WORDS,
        },
    )


def prepare_explicit_inputs(
    paths: Iterable[Path],
    *,
    expected_values: Iterable[str],
) -> PreparedInputs:
    inputs = tuple(Path(path).expanduser().resolve(strict=False) for path in paths)
    if not inputs:
        raise RuntimeError("at least one explicit Pangram input is required")
    missing = [str(path) for path in inputs if not path.is_file()]
    if missing:
        raise RuntimeError("missing Pangram input(s): " + ", ".join(missing))
    supplied = _parse_expected_sha(expected_values)
    expected: dict[str, str] | None = None
    if supplied is not None:
        expected = {}
        for path in inputs:
            digest = supplied.get(str(path)) or supplied.get(path.name)
            if digest is None:
                raise RuntimeError(f"no --expect-sha gate was supplied for {path}")
            expected[str(path)] = digest
    return PreparedInputs(
        paths=inputs,
        expected_sha256=expected,
        source_metadata=None,
        source_receipt=None,
    )


def _input_digests(
    paths: Iterable[Path],
    expected_sha256: Mapping[str, str] | None,
) -> dict[Path, str]:
    result: dict[Path, str] = {}
    for path in paths:
        data = path.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RuntimeError(f"Pangram input must be UTF-8: {path}") from exc
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if expected_sha256 is not None:
            expected = expected_sha256.get(str(path)) or expected_sha256.get(path.name)
            if expected is None:
                raise RuntimeError(f"no expected SHA-256 gate was supplied for {path}")
            if digest != expected:
                raise RuntimeError(
                    f"refusing Pangram browser work because exact SHA-256 changed for {path}: "
                    f"expected={expected} actual={digest}"
                )
        result[path] = digest
    return result


class GitEvidenceDurability:
    def __init__(self, repo_root: Path, output_root: Path) -> None:
        self.repo_root = repo_root.resolve()
        self.output_root = output_root.resolve()
        self.git = GitSync(self.repo_root, require_remote=True)

    def evidence_directories(self, digests: Mapping[Path, str]) -> tuple[Path, ...]:
        return tuple(
            gui_core.measurement_dir(self.output_root, digest)
            for digest in digests.values()
        )

    def preflight(self, digests: Mapping[Path, str]) -> None:
        directories = self.evidence_directories(digests)
        existing = tuple(path for path in directories if path.exists())
        if existing:
            self.git.sync_paths(existing, "sync existing local Pangram evidence before browser work")
        else:
            self.git.ensure_remote_durable("local Pangram preflight before browser work")

    def __call__(self, directory: Path, receipt: Mapping[str, object]) -> None:
        status = str(receipt.get("status", "evidence"))
        digest = str(receipt.get("input_sha256", "unknown"))
        attempted = receipt.get("detector_submission_attempted") is True
        ambiguity = " ambiguous" if status == "failed" and attempted else ""
        self.git.sync_paths(
            [directory],
            f"pangram local {status}{ambiguity} {digest[:16]}",
        )


def _prepare_for_args(
    args: argparse.Namespace,
    repo_root: Path,
    *,
    single_part: int | None = None,
) -> PreparedInputs:
    explicit = getattr(args, "inputs", None)
    explicit_single = getattr(args, "input", None)
    if explicit:
        return prepare_explicit_inputs(explicit, expected_values=args.expect_sha)
    if explicit_single is not None:
        return prepare_explicit_inputs([explicit_single], expected_values=args.expect_sha)
    current = materialize_current_romance_inputs(repo_root, no_fetch=args.no_fetch)
    if single_part is None:
        return current
    index = single_part - 1
    selected = current.paths[index]
    expected = {str(selected): str(CURRENT_ROMANCE_PARTS[index]["sha256"])}
    source = current.source_metadata or {}
    selected_source = source.get(str(selected)) or source.get(selected.name)
    selected_metadata = None
    if selected_source is not None:
        selected_metadata = {str(selected): selected_source, selected.name: selected_source}
    return PreparedInputs(
        paths=(selected,),
        expected_sha256=expected,
        source_metadata=selected_metadata,
        source_receipt=current.source_receipt,
    )


def _json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    config = _config(args)

    if args.command == "bootstrap":
        _json(bootstrap_login(config))
        return 0

    if args.command == "verify":
        _json(verify_login_persistence(config))
        return 0

    if args.command == "status" and args.environment_only:
        result: dict[str, object] = {"environment": environment_status(config)}
        if args.launch_smoke:
            result["launch_smoke"] = launch_smoke_test(config)
        if args.check_auth:
            result["authentication"] = verify_login_persistence(config)
        else:
            result["authentication"] = {
                "status": "not_checked",
                "read_only_check_available": True,
            }
        _json(result)
        return 0

    repo_root = repository_root()
    output_root = _resolve_output_root(repo_root, args.output_root)

    if args.command == "status":
        prepared = _prepare_for_args(args, repo_root)
        result = {
            "environment": environment_status(config),
            "source": prepared.source_receipt,
            "inputs": input_status(
                prepared.paths,
                output_root=output_root,
                expected_sha256=prepared.expected_sha256,
            ),
        }
        if args.launch_smoke:
            result["launch_smoke"] = launch_smoke_test(config)
        if args.check_auth:
            result["authentication"] = verify_login_persistence(config)
        else:
            result["authentication"] = {
                "status": "not_checked",
                "read_only_check_available": True,
            }
        _json(result)
        return 0

    if args.command == "run":
        prepared = _prepare_for_args(args, repo_root)
        digests = _input_digests(prepared.paths, prepared.expected_sha256)
        durability = GitEvidenceDurability(repo_root, output_root)
        durability.preflight(digests)
        results = run_inputs(
            config,
            prepared.paths,
            output_root=output_root,
            force=args.force,
            report_timeout_ms=args.report_timeout_ms,
            expected_sha256=prepared.expected_sha256,
            source_metadata=prepared.source_metadata,
            evidence_callback=durability,
        )
        _json({"source": prepared.source_receipt, "results": results})
        return 0

    if args.command == "recover":
        if args.input is not None and args.part is not None:
            raise RuntimeError("recover accepts either --input or --part, not both")
        if args.input is None and args.part is None:
            raise RuntimeError("recover requires --input or --part 1/2")
        prepared = _prepare_for_args(args, repo_root, single_part=args.part)
        selected = prepared.paths[0]
        expected = None
        if prepared.expected_sha256 is not None:
            expected = prepared.expected_sha256.get(str(selected)) or prepared.expected_sha256.get(
                selected.name
            )
        source = None
        if prepared.source_metadata is not None:
            source = prepared.source_metadata.get(str(selected)) or prepared.source_metadata.get(
                selected.name
            )
        durability = GitEvidenceDurability(repo_root, output_root)
        result = recover_existing_report(
            config,
            selected,
            output_root=output_root,
            expected_sha256=expected,
            source_metadata=source,
            evidence_callback=durability,
        )
        _json({"source": prepared.source_receipt, "result": result})
        return 0

    raise AssertionError(f"unhandled command: {args.command}")
