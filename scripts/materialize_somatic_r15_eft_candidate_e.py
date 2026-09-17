#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


EXPERIMENT = "somatic-r15-eft-human-anchor-tail-factorial-20260831"
DETECTOR_HEAD = "caf33baebea29856e4f780a70367e969e53e69f4"
ARTICLE_HEAD = "ac1570f3e8945fecf80585d8fbe336c2a19ffbd6"
PACKET_REL = "tasks/somatic-r15-clean-continuation-20260830/CHAT-SURFACE-EXPERIMENT-006.md"
PACKET_BLOB = "417961ccdb042eebbc130a7dea5b00d9f8207584"
SOURCE_REL = "articles/somatic-therapies/experiments/R15-DIRECT-OWNER-VOICE-CANDIDATE-20260830.md"
SOURCE_SHA256 = "9c2e8fe57335d51ac925bc9b63cee8125c24e471e2b9b8fda50cc44cf28f5b31"
E_REL = "tasks/somatic-r15-clean-continuation-20260830/surface-experiment-005/E-current-anchor-direct-tail.txt"
E_BLOB = "46f7c1f8f735a648ef9808007bd1929cf924d206"
E_SHA256 = "e9d2969aadbdd648ccd6b5aa36d6b7712b059a5b24a2acfcf95d29a4d458b7eb"
C_REL = "tasks/somatic-r15-clean-continuation-20260830/surface-experiment-005/C-separate-direct-tail.txt"
MEASUREMENT_KEY = f"{EXPERIMENT}-E"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def main() -> int:
    detector = Path.cwd().resolve()
    article = Path(
        "/home/joel/Téléchargements/joel-articles/canonical/worktrees/somatic-r15-clean-continuation-20260830"
    ).resolve()
    detector_dirty = git(detector, "status", "--porcelain").splitlines()
    if git(detector, "rev-parse", "HEAD") != DETECTOR_HEAD or detector_dirty != [
        "?? scripts/materialize_somatic_r15_eft_candidate_e.py"
    ]:
        raise SystemExit("detector start head/worktree mismatch")
    if git(article, "rev-parse", "HEAD") != ARTICLE_HEAD or git(article, "status", "--porcelain"):
        raise SystemExit("article head/worktree mismatch")
    if git(article, "hash-object", PACKET_REL) != PACKET_BLOB:
        raise SystemExit("packet blob mismatch")

    source_raw = (article / SOURCE_REL).read_bytes()
    if digest(source_raw) != SOURCE_SHA256:
        raise SystemExit("source candidate identity mismatch")
    e_raw = (article / E_REL).read_bytes()
    e_text = e_raw.decode("utf-8")
    if git(article, "hash-object", E_REL) != E_BLOB or digest(e_raw) != E_SHA256:
        raise SystemExit("Candidate E identity mismatch")
    if not (
        len(e_text.split()) == 104
        and len(e_text) == 570
        and len(e_raw) == 574
        and not e_text.endswith("\n")
        and e_text.count("\n\n") == 1
        and len(e_text.split("\n\n")) == 2
    ):
        raise SystemExit("Candidate E count/boundary mismatch")

    e_anchor, e_tail = e_text.split("\n\n")
    source_text = source_raw.decode("utf-8")
    source_paragraphs = source_text.split("\n\n")
    source_anchor = next(
        paragraph
        for paragraph in source_paragraphs
        if paragraph.startswith("I think of the different tapping points")
    )
    if not source_anchor.endswith("maybe even better than EFT.") or e_anchor.encode("utf-8") != source_anchor.encode("utf-8"):
        raise SystemExit("current attribution-correct anchor mismatch")
    c_text = (article / C_REL).read_text(encoding="utf-8")
    c_tail = c_text.rsplit("\n\n", 1)[1]
    if e_tail.encode("utf-8") != c_tail.encode("utf-8"):
        raise SystemExit("proven direct-tail mismatch")

    preservation = {
        "brain_relation_is_joel_thought_not_proven_neuroscience": all(
            phrase in e_anchor
            for phrase in (
                "I think of the different tapping points as activating different parts of the brain.",
                "That is my thought; I am not presenting it here as a neuroscience result I proved.",
            )
        ),
        "moves_through_points_and_notices_feeling": "I move through the points and see how I feel at each one." in e_anchor,
        "tapping_as_small_massage": "It is also a little massage." in e_anchor,
        "head_shaving_massage_comparison": "shaving my head and massaging it works really well for me—maybe even better than EFT" in e_anchor,
        "eft_portability": "I can use EFT almost anywhere" in e_tail,
        "before_hard_conversation": "before a hard conversation" in e_tail,
        "immediately_after_trigger": "right after somebody triggers me" in e_tail,
        "mind_loop_and_body_participation": "my mind is looping and my body has joined in" in e_tail,
        "pressure_reduction": "It takes some pressure off." in e_tail,
        "deeper_trauma_not_removed": "The deeper trauma can still be sitting there." in e_tail,
    }
    if not all(preservation.values()):
        raise SystemExit("Candidate E preservation mismatch")

    cache_dir = detector / "cache" / "pangram-4" / "4.0" / E_SHA256
    cache_records = []
    if cache_dir.exists():
        for path in sorted(cache_dir.glob("*.json")):
            value = json.loads(path.read_text(encoding="utf-8"))
            cache_records.append(
                {
                    "path": path.relative_to(detector).as_posix(),
                    "measurement_key": value.get("measurement_key"),
                    "status": value.get("status"),
                    "task_id": value.get("task_id"),
                }
            )
    statuses = {str(record["status"]) for record in cache_records}
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

    experiment = detector / "state" / "experiments" / EXPERIMENT
    input_path = experiment / "inputs" / "E-current-anchor-direct-tail.txt"
    input_path.write_bytes(e_raw)
    packet = {
        "format": "somatic-r15-eft-candidate-e-preflight-v1",
        "directive": {"id": "SOMATIC-R15-SURFACE-006", "packet_path": PACKET_REL, "packet_git_blob": PACKET_BLOB},
        "article": {
            "branch": "task/somatic-r15-clean-continuation-20260830",
            "head": ARTICLE_HEAD,
            "candidate_path": SOURCE_REL,
            "candidate_sha256": SOURCE_SHA256,
            "article_candidate_mutations": 0,
            "registered_master_mutations": 0,
        },
        "detector": {
            "branch": "task/somatic-r15-exact-recovery-20260830",
            "starting_head": DETECTOR_HEAD,
            "model": "pangram-4",
            "required_version": "4.0",
            "transport": "SHORT_DOCUMENT_API",
        },
        "candidate_e": {
            "source_path": E_REL,
            "input_path": input_path.relative_to(detector).as_posix(),
            "git_blob": E_BLOB,
            "sha256": E_SHA256,
            "measurement_key": MEASUREMENT_KEY,
            "whitespace_words": len(e_text.split()),
            "unicode_characters": len(e_text),
            "utf8_bytes": len(e_raw),
            "terminal_newline": e_text.endswith("\n"),
            "paragraphs": 2,
            "cache_records": cache_records,
            "pre_submission_classification": classification,
        },
        "mechanical_source_assertions": "PASS",
        "preservation": {**{key: "PASS" if value else "FAIL" for key, value in preservation.items()}, "overall": "PASS"},
        "accounting_before_execution": {
            "stable_family_call_cap": 6,
            "completed_family_calls": 5,
            "maximum_authorized_new_calls": 1,
            "new_paid_api_calls": 0,
            "ambiguous_calls": 0,
            "gui_actions": 0,
            "whole_document_calls": 0,
        },
        "preflight": "PASS",
    }
    output = experiment / "PREFLIGHT-E.json"
    output.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"preflight": "PASS", "classification": classification, "input": packet["candidate_e"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
