#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pangram_lab.gui_browserbase import BrowserbaseConfig, bootstrap_login, run_inputs


DEFAULT_INPUTS = (
    Path("work/romance-current-assembly/pangram-part-1.txt"),
    Path("work/romance-current-assembly/pangram-part-2.txt"),
)
DEFAULT_OUTPUT_ROOT = Path("state/gui-runs")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Pangram's authenticated GUI through a persistent Browserbase Context."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    bootstrap = sub.add_parser(
        "bootstrap",
        help="Create/reuse a persistent Browserbase Context and perform one-time manual Pangram login.",
    )
    bootstrap.set_defaults(command="bootstrap")

    run = sub.add_parser("run", help="Run exact Pangram GUI measurements for one or more UTF-8 text files.")
    run.add_argument(
        "--input",
        action="append",
        type=Path,
        dest="inputs",
        help="UTF-8 detector input. Repeat for multiple inputs; defaults to current Romance Part 1 and Part 2.",
    )
    run.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    run.add_argument("--force", action="store_true", help="Re-run even if this exact SHA already completed with this runner.")
    run.add_argument("--report-timeout-ms", type=int, default=180_000)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    if args.command == "bootstrap":
        config = BrowserbaseConfig.from_env(
            require_context=False,
            require_project_if_context_missing=True,
        )
        result = bootstrap_login(config)
        print(json.dumps(result, indent=2, sort_keys=True))
        print("Store the returned context_id as BROWSERBASE_CONTEXT_ID for future unattended runs.")
        return 0

    if args.command == "run":
        config = BrowserbaseConfig.from_env(require_context=True)
        inputs = tuple(args.inputs) if args.inputs else DEFAULT_INPUTS
        missing = [str(path) for path in inputs if not path.is_file()]
        if missing:
            raise SystemExit("Missing Pangram GUI input(s): " + ", ".join(missing))
        results = run_inputs(
            config,
            inputs,
            output_root=args.output_root,
            force=args.force,
            report_timeout_ms=args.report_timeout_ms,
        )
        print(json.dumps(results, indent=2, sort_keys=True))
        return 0

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
