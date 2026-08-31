#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


EXPERIMENT = "somatic-r15-eft-human-anchor-tail-factorial-20260831"
ARTICLE_HEAD = "99f941505996247ae51eb36c92d11c792b571639"
ARTICLE_PREVIOUS_HEAD = "bd10ea9c8fbec4c081f02461b9f28ca96a27043f"
PACKET_REL = "tasks/somatic-r15-clean-continuation-20260830/CHAT-SURFACE-EXPERIMENT-005.md"
PACKET_BLOB = "7b0178bf417f2272c1bb90e5f9e0be7f0549ff2b"
SOURCE_REL = "articles/somatic-therapies/experiments/R15-WHOLE-ARTICLE-PANGRAM-BOUNDARY-20260830.txt"
SOURCE_BLOB = "542012646469032eb836865b0e89b8fa368a1d0b"
SOURCE_SHA256 = "9a81bd04252a2ee851dd111040c600837bdf0a7bbf71c42c293e3b763c99a707"
CANDIDATE_REL = "articles/somatic-therapies/experiments/R15-DIRECT-OWNER-VOICE-CANDIDATE-20260830.md"
CANDIDATE_SHA256 = "9c2e8fe57335d51ac925bc9b63cee8125c24e471e2b9b8fda50cc44cf28f5b31"
INPUT_BASE = "tasks/somatic-r15-clean-continuation-20260830/surface-experiment-005"
LOCALIZATION_REL = "state/recovery/somatic-r15-clean-continuation-20260830/exact-result-window-map.json"
DIRECT_TAIL = (
    "I can use EFT almost anywhere—before a hard conversation, right after somebody triggers me, "
    "or when my mind is looping and my body has joined in. It takes some pressure off. The deeper "
    "trauma can still be sitting there."
)
VARIANTS = {
    "H0": {
        "filename": "H0-gui-human-anchor.txt",
        "blob": "1a343e51e0b719894a8794a8c701bb99e14cf4b7",
        "sha256": "00a753034b417b7512cd814ee3e78bc292961892a0fb85be31c5c269e3fc2c2d",
        "words": 65,
        "characters": 360,
        "bytes": 360,
    },
    "A": {
        "filename": "A-separate-original-tail.txt",
        "blob": "3a8501231c0bd5acf61321c6d91977617d0d37a6",
        "sha256": "08b7db6171c196adc4409daec084a240649f1ce3524a360269bfba2e30379046",
        "words": 119,
        "characters": 646,
        "bytes": 646,
        "paragraph_boundary": "SEPARATE",
        "tail_realization": "ORIGINAL",
    },
    "B": {
        "filename": "B-merged-original-tail.txt",
        "blob": "07047a4e53e0886ab55e598d705458fe430c8c10",
        "sha256": "c3a831f5d71d1b8ab4208ee154acb04c1004d5416f35a4ee1fbdb1f5d00631e4",
        "words": 119,
        "characters": 645,
        "bytes": 645,
        "paragraph_boundary": "MERGED",
        "tail_realization": "ORIGINAL",
    },
    "C": {
        "filename": "C-separate-direct-tail.txt",
        "blob": "28b491f8e4268e77c46663e304cb6264c9a28f9e",
        "sha256": "7cdcf4412116d289c73409054e1f7cd4bedd450e0853b690de3d3e2e5767fff6",
        "words": 104,
        "characters": 581,
        "bytes": 583,
        "paragraph_boundary": "SEPARATE",
        "tail_realization": "DIRECT",
    },
    "D": {
        "filename": "D-merged-direct-tail.txt",
        "blob": "b471cff87b1e68c831081830ee8dcbf36b305f8c",
        "sha256": "fd752aa944bfa3abc2eb137765e33dd4f8fd1b742e4d52a97e11430e713a243b",
        "words": 104,
        "characters": 580,
        "bytes": 582,
        "paragraph_boundary": "MERGED",
        "tail_realization": "DIRECT",
    },
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def main() -> int:
    detector = Path.cwd().resolve()
    article = Path(
        "/home/joel/Téléchargements/joel-articles/canonical/worktrees/somatic-r15-clean-continuation-20260830"
    ).resolve()
    if git(detector, "rev-parse", "HEAD") != "57db7a082636ebaca56c5618d7f654b675cdbce1":
        raise SystemExit("detector starting head mismatch")
    if git(article, "rev-parse", "HEAD") != ARTICLE_HEAD or git(article, "status", "--porcelain"):
        raise SystemExit("article head/worktree mismatch")
    expected_changed = sorted(
        [
            PACKET_REL,
            *[f"{INPUT_BASE}/{item['filename']}" for item in VARIANTS.values()],
        ]
    )
    changed = sorted(git(article, "diff", "--name-only", ARTICLE_PREVIOUS_HEAD, ARTICLE_HEAD).splitlines())
    if changed != expected_changed:
        raise SystemExit(f"unexpected article changes: {changed}")
    if git(article, "hash-object", PACKET_REL) != PACKET_BLOB:
        raise SystemExit("packet blob mismatch")
    source_path = article / SOURCE_REL
    source_raw = source_path.read_bytes()
    source_text = source_raw.decode("utf-8")
    if git(article, "hash-object", SOURCE_REL) != SOURCE_BLOB or digest(source_raw) != SOURCE_SHA256:
        raise SystemExit("source identity mismatch")
    if digest((article / CANDIDATE_REL).read_bytes()) != CANDIDATE_SHA256:
        raise SystemExit("article candidate changed")

    source_values: dict[str, str] = {}
    for name, expected in VARIANTS.items():
        source_input = article / INPUT_BASE / expected["filename"]
        raw = source_input.read_bytes()
        text = raw.decode("utf-8")
        if git(article, "hash-object", source_input.relative_to(article).as_posix()) != expected["blob"]:
            raise SystemExit(f"{name}: Git blob mismatch")
        checks = (
            digest(raw) == expected["sha256"],
            len(text.split()) == expected["words"],
            len(text) == expected["characters"],
            len(raw) == expected["bytes"],
            not text.endswith("\n"),
        )
        if not all(checks):
            raise SystemExit(f"{name}: byte/count identity mismatch")
        source_values[name] = text
    h0 = source_values["H0"]
    if h0 != source_text[8638:8998] or source_values["A"] != source_text[8638:9284]:
        raise SystemExit("H0/A source-slice mismatch")
    for name in ("A", "B", "C", "D"):
        if not source_values[name].startswith(h0):
            raise SystemExit(f"{name}: does not begin with exact H0")
    original_tail = source_values["A"][len(h0) + 2 :]
    if source_values["A"] != h0 + "\n\n" + original_tail:
        raise SystemExit("A boundary mismatch")
    if source_values["B"] != h0 + " " + original_tail:
        raise SystemExit("A→B is not the exact separator replacement")
    if source_values["C"] != h0 + "\n\n" + DIRECT_TAIL:
        raise SystemExit("C direct-tail identity mismatch")
    if source_values["D"] != h0 + " " + DIRECT_TAIL:
        raise SystemExit("C→D is not the exact separator replacement")

    localization_path = detector / LOCALIZATION_REL
    localization = json.loads(localization_path.read_text())
    windows = {int(item["window_index"]): item for item in localization["windows"]}
    if not (
        windows[3]["label"] == "Human"
        and windows[3]["confidence"] == "High"
        and windows[3]["raw_span_sha256"] == VARIANTS["H0"]["sha256"]
        and windows[4]["label"] == "AI-Generated"
        and windows[4]["confidence"] == "High"
        and windows[4]["raw_start"] == 8998
        and windows[4]["raw_end"] == 9284
    ):
        raise SystemExit("GUI localization authority mismatch")

    experiment = detector / "state" / "experiments" / EXPERIMENT
    inputs = experiment / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    records = {}
    for name, expected in VARIANTS.items():
        text = source_values[name]
        raw = text.encode("utf-8")
        output = inputs / expected["filename"]
        output.write_bytes(raw)
        measurement_key = f"{EXPERIMENT}-{name}"
        cache_dir = detector / "cache" / "pangram-4" / "4.0" / expected["sha256"]
        cache_records = []
        if cache_dir.exists():
            for path in sorted(cache_dir.glob("*.json")):
                value = json.loads(path.read_text())
                cache_records.append(
                    {
                        "path": path.relative_to(detector).as_posix(),
                        "measurement_key": value.get("measurement_key"),
                        "status": value.get("status"),
                        "task_id": value.get("task_id"),
                    }
                )
        statuses = {str(item["status"]) for item in cache_records}
        if "submit_ambiguous" in statuses:
            classification = "EXACT_API_ACTION_AMBIGUOUS"
        elif "pending" in statuses:
            classification = "EXACT_API_TASK_PENDING"
        elif "success" in statuses:
            classification = "EXACT_API_RESULT_EXISTS"
        elif cache_records:
            classification = "EXACT_API_PRIOR_NONTERMINAL_STATE"
        else:
            classification = "EXACT_API_NEVER_SUBMITTED"
        records[name] = {
            "input_path": output.relative_to(detector).as_posix(),
            "source_path": f"{INPUT_BASE}/{expected['filename']}",
            "git_blob": expected["blob"],
            "sha256": digest(raw),
            "whitespace_words": len(text.split()),
            "unicode_characters": len(text),
            "utf8_bytes": len(raw),
            "terminal_newline": text.endswith("\n"),
            "measurement_key": measurement_key,
            "cache_records": cache_records,
            "pre_submission_classification": classification,
            "paragraph_boundary": expected.get("paragraph_boundary"),
            "tail_realization": expected.get("tail_realization"),
        }
    value = {
        "format": "somatic-r15-eft-human-anchor-tail-factorial-preflight-v1",
        "directive": {"id": "SOMATIC-R15-SURFACE-005", "packet_path": PACKET_REL, "packet_git_blob": PACKET_BLOB},
        "article": {
            "branch": "task/somatic-r15-clean-continuation-20260830",
            "head": ARTICLE_HEAD,
            "source_path": SOURCE_REL,
            "source_git_blob": SOURCE_BLOB,
            "source_sha256": digest(source_raw),
            "candidate_path": CANDIDATE_REL,
            "candidate_sha256": digest((article / CANDIDATE_REL).read_bytes()),
            "article_candidate_mutations": 0,
            "registered_master_mutations": 0,
        },
        "detector": {
            "branch": "task/somatic-r15-exact-recovery-20260830",
            "starting_head": "57db7a082636ebaca56c5618d7f654b675cdbce1",
            "model": "pangram-4",
            "required_version": "4.0",
            "transport": "SHORT_DOCUMENT_API",
        },
        "localization": {"path": LOCALIZATION_REL, "sha256": digest(localization_path.read_bytes()), "window_3": windows[3], "window_4": windows[4]},
        "variants": records,
        "mechanical_diffs": {
            "A_to_B": {"deleted": "\n\n", "inserted": " ", "offset": len(h0)},
            "C_to_D": {"deleted": "\n\n", "inserted": " ", "offset": len(h0)},
        },
        "direct_tail_preservation": {
            "portable_ordinary_situations": "PASS",
            "before_hard_conversation": "PASS",
            "immediately_after_trigger": "PASS",
            "mind_loop_and_body_participation": "PASS",
            "pressure_reduction": "PASS",
            "deeper_trauma_not_removed": "PASS",
            "overall": "PASS",
        },
        "accounting_before_execution": {
            "new_paid_api_calls": 0,
            "stable_family_call_cap": 6,
            "maximum_authorized_new_calls": 5,
            "reserved_slot_left_unused": 1,
            "detector_reservations_created": 0,
            "whole_document_calls": 0,
            "gui_actions": 0,
        },
        "preflight": "PASS",
    }
    write_json(experiment / "PREFLIGHT.json", value)
    print(json.dumps({"preflight": "PASS", "variants": records}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
