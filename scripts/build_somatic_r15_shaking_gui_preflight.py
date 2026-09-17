#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


EXPERIMENT = "somatic-r15-shaking-human-anchor-guidance-social-tail-20260831"
DETECTOR_HEAD = "8a82359db155de4871594d6e6b17d8b898c24893"
ARTICLE_HEAD = "8b46107c5716a9cae7a2526502b2c4044ff6eba4"
ARTICLE_ROOT = Path(
    "/home/joel/Téléchargements/joel-articles/canonical/worktrees/"
    "somatic-r15-clean-continuation-20260830"
)
PACKET = (
    "tasks/somatic-r15-clean-continuation-20260830/"
    "CHAT-SURFACE-EXPERIMENT-008-GUI-COMPLETION.md"
)
PACKET_BLOB = "c84829af11aed69603bc51bce891d0d963191fd6"
CANDIDATE = "articles/somatic-therapies/experiments/R15-EFT-REPAIR-CANDIDATE-20260831.md"
CANDIDATE_BLOB = "6f9251f51d79a6b322b8c6f6cae95a9a5d80f760"
CANDIDATE_SHA = "5a6226ca0056610b4492de7713a43bb152dde1079d81b5c05896c70fcf138679"
SOURCE_DIR = (
    "tasks/somatic-r15-clean-continuation-20260830/surface-experiment-008"
)
VARIANTS = {
    "C": {
        "filename": "C-current-anchor.txt",
        "blob": "2993757f24707297f1c8dd7b3fbf6c4e017e9e0b",
        "sha256": "b36e1e46c06d764a080d407dce5412defe76ccb9202deb1a8a14e265acf40370",
        "words": 293,
        "characters": 1631,
        "bytes": 1641,
    },
    "D": {
        "filename": "D-current-anchor-current-tail.txt",
        "blob": "261e9410bbc89e335a31f10e0e5e7e844788382e",
        "sha256": "b27446d695044a6749a2780f7629599177160d4a619758784b915b3cdc013900",
        "words": 328,
        "characters": 1838,
        "bytes": 1848,
    },
    "E": {
        "filename": "E-current-anchor-direct-tail.txt",
        "blob": "ad9e793d8073f859b555d5e0262c651303e6972b",
        "sha256": "75fb8426a498dcedb99bb7ed84d9f5a6e1653a29b6e2b7d5ff8f61fe5fb8563f",
        "words": 333,
        "characters": 1857,
        "bytes": 1867,
    },
}


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    detector = Path.cwd().resolve()
    if git(detector, "rev-parse", "HEAD") != DETECTOR_HEAD:
        raise SystemExit("detector head mismatch")
    if git(ARTICLE_ROOT, "rev-parse", "HEAD") != ARTICLE_HEAD:
        raise SystemExit("article head mismatch")
    if git(ARTICLE_ROOT, "hash-object", PACKET) != PACKET_BLOB:
        raise SystemExit("GUI directive packet blob mismatch")
    candidate_raw = (ARTICLE_ROOT / CANDIDATE).read_bytes()
    if not (
        git(ARTICLE_ROOT, "hash-object", CANDIDATE) == CANDIDATE_BLOB
        and sha256(candidate_raw) == CANDIDATE_SHA
    ):
        raise SystemExit("candidate identity mismatch")

    experiment = detector / "state" / "experiments" / EXPERIMENT
    records: dict[str, object] = {}
    for name, expected in VARIANTS.items():
        article_path = ARTICLE_ROOT / SOURCE_DIR / str(expected["filename"])
        copied_path = experiment / "inputs" / str(expected["filename"])
        article_raw = article_path.read_bytes()
        copied_raw = copied_path.read_bytes()
        text = article_raw.decode("utf-8")
        if not (
            article_raw == copied_raw
            and git(ARTICLE_ROOT, "hash-object", article_path.relative_to(ARTICLE_ROOT).as_posix())
            == expected["blob"]
            and sha256(article_raw) == expected["sha256"]
            and len(text.split()) == expected["words"]
            and len(text) == expected["characters"]
            and len(article_raw) == expected["bytes"]
            and not text.endswith("\n")
        ):
            raise SystemExit(f"{name} exact input mismatch")

        gui_dir = detector / "state" / "gui-runs" / "pangram-4" / str(expected["sha256"])
        result_path = gui_dir / "result.json"
        reservation_path = gui_dir / "reservation.json"
        failure_path = gui_dir / "failure.json"
        if result_path.exists() or reservation_path.exists() or failure_path.exists():
            raise SystemExit(f"{name} local GUI evidence unexpectedly exists")

        probe_path = experiment / "gui-preflight" / f"{name}-history-probe.json"
        probe = json.loads(probe_path.read_text(encoding="utf-8"))
        if not (
            probe.get("status") == "not_found"
            and probe.get("current_exact_history_record_found") is False
            and probe.get("target_history_record_found") is False
            and probe.get("detector_submission_attempted") is False
            and probe.get("browser_history_candidate_count") == 62
            and probe.get("browser_history_candidates_inspected") == 62
        ):
            raise SystemExit(f"{name} exact History probe mismatch")
        records[name] = {
            **expected,
            "input_path": copied_path.relative_to(detector).as_posix(),
            "local_gui_result_exists": False,
            "local_gui_reservation_exists": False,
            "local_gui_ambiguous_failure_exists": False,
            "history_probe_path": probe_path.relative_to(detector).as_posix(),
            "history_candidates_inspected": 62,
            "history_api_records_observed": probe.get("history_api_records_observed"),
            "classification": "EXACT_GUI_NEVER_SUBMITTED",
        }

    c_api = detector / "cache" / "pangram-4" / "4.0" / VARIANTS["C"]["sha256"] / f"{EXPERIMENT}-C.json"
    c_api_record = json.loads(c_api.read_text(encoding="utf-8"))
    if not (
        c_api_record.get("status") == "failed"
        and c_api_record.get("task_id") == ""
        and "HTTP 402" in str(c_api_record.get("last_error"))
    ):
        raise SystemExit("C API 402 classification mismatch")

    packet = {
        "format": "somatic-r15-shaking-gui-cde-preflight-v1",
        "directive": {
            "id": "SOMATIC-R15-SHAKING-GUI-COMPLETION-001",
            "article_head": ARTICLE_HEAD,
            "packet_path": PACKET,
            "packet_git_blob": PACKET_BLOB,
        },
        "article": {
            "candidate_path": CANDIDATE,
            "candidate_git_blob": CANDIDATE_BLOB,
            "candidate_sha256": CANDIDATE_SHA,
            "article_mutations": 0,
            "registered_master_mutations": 0,
        },
        "detector": {
            "branch": "task/somatic-r15-exact-recovery-20260830",
            "starting_head": DETECTOR_HEAD,
            "transport": "local_playwright",
            "browser": "Brave",
            "dedicated_profile": True,
            "authentication_read_only_check": "PASS",
            "model": "pangram-4",
            "required_version": "4.0",
        },
        "variants": records,
        "c_api_prior_failure": {
            "status": "HTTP_402_BEFORE_TASK_CREATION",
            "task_id": "",
            "gui_action": False,
            "ambiguous": False,
            "retry_authorized": False,
        },
        "accounting_before_click": {
            "exact_gui_results_recovered": 0,
            "exact_gui_ambiguous_actions": 0,
            "exact_gui_never_submitted": 3,
            "new_api_calls_authorized": 0,
            "maximum_new_short_gui_clicks": 3,
            "whole_document_calls_authorized": 0,
        },
        "preflight": "PASS",
    }
    output = experiment / "GUI-CDE-PREFLIGHT.json"
    output.write_text(
        json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"preflight": "PASS", "classifications": {key: value["classification"] for key, value in records.items()}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
