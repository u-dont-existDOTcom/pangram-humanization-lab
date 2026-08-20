from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Iterable, Mapping

from pangram_lab.git_sync import GitSync
from pangram_lab.gui_local_structured import (
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
from pangram_lab import gui_local as local


DEFAULT_OUTPUT_ROOT = Path("state/gui-runs")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


def _add_browser_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--profile-dir", type=Path, default=DEFAULT_PROFILE_DIR)
    parser.add_argument("--browser-executable", type=Path)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--allow-ordinary-profile", action="store_true")
    parser.add_argument("--allow-profile-in-git-repo", action="store_true")


def _add_inputs(parser: argparse.ArgumentParser, *, multiple: bool) -> None:
    if multiple:
        parser.add_argument("--input", dest="inputs", action="append", type=Path, required=True)
    else:
        parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--expect-sha",
        action="append",
        default=[],
        metavar="PATH_OR_NAME=SHA256",
        help="Optional exact SHA-256 gate; repeat for each input when used.",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pangram-local",
        description="Local headed Playwright transport for Pangram's authenticated GUI.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    bootstrap = sub.add_parser("bootstrap", help="Open the dedicated profile for one-time login.")
    _add_browser_options(bootstrap)

    verify = sub.add_parser("verify", help="Verify persisted Pangram login without submitting text.")
    _add_browser_options(verify)

    status = sub.add_parser("status", help="Show environment and optional input cache state.")
    _add_browser_options(status)
    status.add_argument("--input", dest="inputs", action="append", type=Path, default=[])
    status.add_argument("--expect-sha", action="append", default=[])
    status.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    status.add_argument("--launch-smoke", action="store_true")
    status.add_argument("--check-auth", action="store_true")

    run = sub.add_parser("run", help="Submit uncached exact inputs with durable duplicate protection.")
    _add_browser_options(run)
    _add_inputs(run, multiple=True)
    run.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    run.add_argument("--force", action="store_true")
    run.add_argument("--report-timeout-ms", type=int, default=180_000)

    recover = sub.add_parser(
        "recover",
        help="Recover an exact stored Pangram History result without detector submission.",
    )
    _add_browser_options(recover)
    _add_inputs(recover, multiple=False)
    recover.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    recover.add_argument("--max-candidates", type=int, default=100)
    return parser


def _config(args: argparse.Namespace) -> LocalPlaywrightConfig:
    return LocalPlaywrightConfig.from_env(
        profile_dir=args.profile_dir,
        browser_executable=args.browser_executable,
        headed=not args.headless,
        allow_ordinary_profile=args.allow_ordinary_profile,
        allow_profile_in_git_repo=args.allow_profile_in_git_repo,
    )


def repository_root(cwd: Path | None = None) -> Path:
    base = Path.cwd() if cwd is None else Path(cwd)
    cp = subprocess.run(
        ["git", "-C", str(base), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if cp.returncode != 0:
        raise RuntimeError("pangram-local must run inside the pangram-humanization-lab repository")
    return Path(cp.stdout.strip()).resolve()


def _resolve_output_root(repo_root: Path, supplied: Path) -> Path:
    candidate = supplied if supplied.is_absolute() else repo_root / supplied
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise RuntimeError(f"Pangram evidence output must remain inside the repository: {resolved}") from exc
    if resolved == repo_root:
        raise RuntimeError("Pangram evidence output cannot be the repository root")
    return resolved


def _parse_expected_sha(values: Iterable[str], paths: Iterable[Path]) -> dict[str, str] | None:
    values = tuple(values)
    paths = tuple(path.expanduser().resolve(strict=False) for path in paths)
    if not values:
        return None
    supplied: dict[str, str] = {}
    for raw in values:
        if "=" not in raw:
            raise RuntimeError(f"invalid --expect-sha value {raw!r}; use PATH_OR_NAME=SHA256")
        key, digest = raw.rsplit("=", 1)
        key = key.strip()
        digest = digest.strip().lower()
        if not key or not _HEX64_RE.fullmatch(digest):
            raise RuntimeError(f"invalid --expect-sha value {raw!r}")
        supplied[key] = digest
    result: dict[str, str] = {}
    for path in paths:
        digest = supplied.get(str(path)) or supplied.get(path.name)
        if digest is None:
            raise RuntimeError(f"no --expect-sha gate was supplied for {path}")
        result[str(path)] = digest
    return result


def _validate_inputs(paths: Iterable[Path]) -> tuple[Path, ...]:
    result = tuple(path.expanduser().resolve(strict=False) for path in paths)
    missing = [str(path) for path in result if not path.is_file()]
    if missing:
        raise RuntimeError("missing Pangram input(s): " + ", ".join(missing))
    return result


def _input_digests(
    paths: Iterable[Path], expected_sha256: Mapping[str, str] | None
) -> dict[Path, str]:
    result: dict[Path, str] = {}
    for path in paths:
        text = path.read_bytes().decode("utf-8")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if expected_sha256 is not None:
            expected = expected_sha256.get(str(path)) or expected_sha256.get(path.name)
            if expected is None or digest != expected:
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
            local.gui_core.measurement_dir(self.output_root, digest)
            for digest in digests.values()
        )

    def preflight(self, digests: Mapping[Path, str]) -> None:
        existing = tuple(path for path in self.evidence_directories(digests) if path.exists())
        if existing:
            self.git.sync_paths(existing, "sync existing local Pangram GUI evidence before browser work")
        else:
            self.git.ensure_remote_durable("local Pangram GUI preflight before browser work")

    def __call__(self, directory: Path, receipt: Mapping[str, object]) -> None:
        status = str(receipt.get("status", "evidence"))
        digest = str(receipt.get("input_sha256", "unknown"))
        self.git.sync_paths(
            [directory],
            f"pangram local GUI {status} {digest[:16]}",
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

    repo_root = repository_root()
    output_root = _resolve_output_root(repo_root, args.output_root)

    if args.command == "status":
        result: dict[str, object] = {"environment": environment_status(config)}
        if args.inputs:
            paths = _validate_inputs(args.inputs)
            expected = _parse_expected_sha(args.expect_sha, paths)
            result["inputs"] = input_status(
                paths,
                output_root=output_root,
                expected_sha256=expected,
            )
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
        paths = _validate_inputs(args.inputs)
        expected = _parse_expected_sha(args.expect_sha, paths)
        digests = _input_digests(paths, expected)
        durability = GitEvidenceDurability(repo_root, output_root)
        durability.preflight(digests)
        results = run_inputs(
            config,
            paths,
            output_root=output_root,
            force=args.force,
            report_timeout_ms=args.report_timeout_ms,
            expected_sha256=expected,
            evidence_callback=durability,
        )
        _json({"results": results})
        return 0

    if args.command == "recover":
        path = _validate_inputs([args.input])[0]
        expected_map = _parse_expected_sha(args.expect_sha, [path])
        expected = None if expected_map is None else expected_map[str(path)]
        digest = _input_digests([path], expected_map)
        durability = GitEvidenceDurability(repo_root, output_root)
        durability.preflight(digest)
        result = recover_existing_report(
            config,
            path,
            output_root=output_root,
            expected_sha256=expected,
            evidence_callback=durability,
            max_candidates=args.max_candidates,
        )
        _json({"result": result})
        return 0

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
