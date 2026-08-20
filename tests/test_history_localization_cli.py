from __future__ import annotations

from pangram_lab.local_cli import _parser


def test_localize_accepts_multiple_exact_inputs_and_hash_gates() -> None:
    args = _parser().parse_args(
        [
            "localize",
            "--input",
            "part1.txt",
            "--input",
            "part2.txt",
            "--expect-sha",
            "part1.txt=" + "a" * 64,
            "--expect-sha",
            "part2.txt=" + "b" * 64,
            "--max-candidates",
            "120",
        ]
    )
    assert args.command == "localize"
    assert [path.name for path in args.inputs] == ["part1.txt", "part2.txt"]
    assert args.max_candidates == 120
    assert len(args.expect_sha) == 2
    assert args.report_url is None


def test_localize_accepts_known_stored_report_route_for_single_input() -> None:
    report_url = "https://www.pangram.com/history/58db9b2b-9a3d-43cf-8970-2e2b7410a0e8"
    args = _parser().parse_args(
        [
            "localize",
            "--input",
            "part2.txt",
            "--expect-sha",
            "part2.txt=" + "b" * 64,
            "--report-url",
            report_url,
        ]
    )
    assert args.command == "localize"
    assert len(args.inputs) == 1
    assert args.report_url == report_url
