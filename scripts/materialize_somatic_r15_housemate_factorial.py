#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


EXPERIMENT = "somatic-r15-housemate-human-anchor-hour-later-tail-20260831"
DETECTOR_HEAD = "ede777c4455d699f64f46e7850e92c707fa31378"
ARTICLE_HEAD = "c4544a1c36ac8861a10c0ad44b77575c28f0cfdf"
PACKET_REL = "tasks/somatic-r15-clean-continuation-20260830/CHAT-SURFACE-EXPERIMENT-007.md"
PACKET_BLOB = "7a84033ef8b5bec18f27af45932f94b6ab4daab9"
SOURCE_REL = "articles/somatic-therapies/experiments/R15-WHOLE-ARTICLE-PANGRAM-BOUNDARY-20260830.txt"
SOURCE_BLOB = "542012646469032eb836865b0e89b8fa368a1d0b"
SOURCE_SHA = "9a81bd04252a2ee851dd111040c600837bdf0a7bbf71c42c293e3b763c99a707"
CANDIDATE_REL = "articles/somatic-therapies/experiments/R15-EFT-REPAIR-CANDIDATE-20260831.md"
CANDIDATE_BLOB = "6f9251f51d79a6b322b8c6f6cae95a9a5d80f760"
CANDIDATE_SHA = "5a6226ca0056610b4492de7713a43bb152dde1079d81b5c05896c70fcf138679"
INPUT_BASE = "tasks/somatic-r15-clean-continuation-20260830/surface-experiment-007"
DIRECT_TAIL = (
    "I check again an hour later. If I'm still stewing just as hard, it probably didn't last, and I may need "
    "to work with it again. If I can remember the event and it doesn't grab me as hard, now that's interesting. "
    "I don't expect one pass to erase every trigger; EMDR often takes more than one session too."
)
DIRECT_TAIL_SHA = "d351ef58bd06ea4f6e2853f697d662d644b59e1e286884f1b10f82f47c608929"
VARIANTS = {
    "H0": ("H0-r15-human-anchor.txt", "d3846d9c0747f540a66fbe63208d7ecbb984d48c", "1d7bb2473eea7c4c42229726aaeb953fc5fb6f30c1cfc316f2673e90be56f3aa", 214, 1192, 1196),
    "A": ("A-r15-anchor-original-tail.txt", "13f043d23e44d3655437293a8bf8ea0d6f581189", "574a317204c05ac0e05a0d924db4a5dcb66f6dafcbfd27b1da8f16783e001d94", 291, 1591, 1595),
    "B": ("B-r15-anchor-direct-tail.txt", "a0202b4a631feb92f03898a2977f5cd5a5e0a9a9", "9796246dad4b35cb761939724a57e6bbb4b3a4d46119968741144401edae1e11", 273, 1496, 1500),
    "C": ("C-current-anchor.txt", "6850cd60a4a9d6d3a97994292dcfb0c8f1ef53c7", "dddae7f8802de8c38cc6df7ba03ab87fc12b9493736160f278f684ae26be2e4d", 223, 1257, 1257),
    "D": ("D-current-anchor-current-tail.txt", "8c76f61ac91354889c8184d207a15abcb578e2c9", "29d4af12b023c3a71ba2d16583b101e3ffe2f042652b36c4e57dce42e7d16abc", 292, 1637, 1637),
    "E": ("E-current-anchor-direct-tail.txt", "945b17ef01eceaf1ee8fd3586f703a2bda06279b", "13a08874c69e675d432c2e14a59aeab81933b6a2d5c31d9e736c402a71d3ded9", 282, 1561, 1561),
}
PLACEHOLDER = re.compile(r"^\*\*\[EXISTING .+\]\*\*$")
LINK = re.compile(r"\[([^\]]+)\]\([^\n)]+\)")
HEADING = re.compile(r"^#{1,6}\s+")
LIST = re.compile(r"^(?:[-+*]|\d+\.)\s+")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def reader_visible(source: str) -> str:
    lines = source.splitlines()
    start = lines.index("# Introduction")
    visible = []
    placeholders = 0
    for raw in lines[start:]:
        line = raw.rstrip()
        if line == "---":
            continue
        if PLACEHOLDER.fullmatch(line):
            placeholders += 1
            continue
        line = HEADING.sub("", line)
        line = LIST.sub("", line)
        line = LINK.sub(r"\1", line)
        visible.append(line.replace("**", "").replace("*", ""))
    if placeholders != 7:
        raise SystemExit("current candidate placeholder count mismatch")
    return re.sub(r"\n{3,}", "\n\n", "\n".join(visible)).strip() + "\n\n"


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    detector = Path.cwd().resolve()
    article = Path("/home/joel/Téléchargements/joel-articles/canonical/worktrees/somatic-r15-clean-continuation-20260830").resolve()
    dirty = git(detector, "status", "--porcelain").splitlines()
    if git(detector, "rev-parse", "HEAD") != DETECTOR_HEAD or dirty != ["?? scripts/materialize_somatic_r15_housemate_factorial.py"]:
        raise SystemExit("detector start head/worktree mismatch")
    if git(article, "rev-parse", "HEAD") != ARTICLE_HEAD or git(article, "status", "--porcelain"):
        raise SystemExit("article head/worktree mismatch")
    if git(article, "hash-object", PACKET_REL) != PACKET_BLOB:
        raise SystemExit("execution packet blob mismatch")
    source_raw = (article / SOURCE_REL).read_bytes()
    candidate_raw = (article / CANDIDATE_REL).read_bytes()
    if not (
        git(article, "hash-object", SOURCE_REL) == SOURCE_BLOB
        and digest(source_raw) == SOURCE_SHA
        and git(article, "hash-object", CANDIDATE_REL) == CANDIDATE_BLOB
        and digest(candidate_raw) == CANDIDATE_SHA
    ):
        raise SystemExit("article source/candidate identity mismatch")

    values: dict[str, str] = {}
    records: dict[str, Any] = {}
    for name, (filename, blob, expected_sha, words, chars, byte_count) in VARIANTS.items():
        rel = f"{INPUT_BASE}/{filename}"
        raw = (article / rel).read_bytes()
        text = raw.decode("utf-8")
        if not (
            git(article, "hash-object", rel) == blob
            and digest(raw) == expected_sha
            and len(text.split()) == words
            and len(text) == chars
            and len(raw) == byte_count
            and not text.endswith("\n")
        ):
            raise SystemExit(f"{name}: frozen input identity mismatch")
        values[name] = text

    source_text = source_raw.decode("utf-8")
    if values["H0"] != source_text[17379:18571] or values["A"] != source_text[17379:18970]:
        raise SystemExit("H0/A exact R15 slice mismatch")
    if not (values["A"].startswith(values["H0"]) and values["B"].startswith(values["H0"])):
        raise SystemExit("A/B H0 prefix mismatch")
    current_visible = reader_visible(candidate_raw.decode("utf-8"))
    c_start = current_visible.index("\n\nHow I Know Whether It Actually Helped")
    c_end_marker = "That only tells me what happened right then."
    c_end = current_visible.index(c_end_marker, c_start) + len(c_end_marker)
    if values["C"] != current_visible[c_start:c_end]:
        raise SystemExit("C current-candidate source binding mismatch")
    if not (values["D"].startswith(values["C"]) and values["E"].startswith(values["C"])):
        raise SystemExit("D/E current-anchor prefix mismatch")
    if digest(DIRECT_TAIL.encode("utf-8")) != DIRECT_TAIL_SHA:
        raise SystemExit("direct-tail literal hash mismatch")
    if values["B"][len(values["H0"]):] != "\n\n" + DIRECT_TAIL or values["E"][len(values["C"]):] != "\n\n" + DIRECT_TAIL:
        raise SystemExit("B/E direct-tail bytes mismatch")
    a_tail = values["A"][len(values["H0"]) + 2:]
    d_tail = values["D"][len(values["C"]) + 2:]
    if values["A"] != values["H0"] + "\n\n" + a_tail or values["D"] != values["C"] + "\n\n" + d_tail:
        raise SystemExit("A/D paragraph boundary mismatch")
    if digest(a_tail.encode("utf-8")) != "8c3a231b8189d760297ea4a8e241a637e6fd2ea0beb01adcd41d72f1a238832b":
        raise SystemExit("R15 original-tail hash mismatch")
    if digest(d_tail.encode("utf-8")) != "983402687ae007fd83e6aa1343a5369825513b751ae4da80276ade789791eda8":
        raise SystemExit("current-tail hash mismatch")
    preservation = {
        "one_hour_recheck": "an hour later" in DIRECT_TAIL,
        "still_stewing_means_did_not_last": "still stewing just as hard, it probably didn't last" in DIRECT_TAIL,
        "further_work_may_be_needed": "may need to work with it again" in DIRECT_TAIL,
        "memory_grabs_less_is_meaningful": "remember the event and it doesn't grab me as hard" in DIRECT_TAIL,
        "one_pass_does_not_erase_every_trigger": "one pass to erase every trigger" in DIRECT_TAIL,
        "emdr_often_more_than_one_session": "EMDR often takes more than one session" in DIRECT_TAIL,
    }
    if not all(preservation.values()):
        raise SystemExit("direct-tail preservation mismatch")

    prior_path = detector / "state/experiments/somatic-r15-api-gui-human-window-calibration-20260831/RESULT-PACKET.json"
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    h2 = prior["variants"]["H2"]
    if not (
        h2["input"]["sha256"] == VARIANTS["H0"][2]
        and h2["task_id"] == "6f8d20fe-4470-48ef-9867-7554f17f384f"
        and h2["api_result"]["version"] == "4.0"
        and h2["api_result"]["fraction_human"] == 1.0
        and h2["api_result"]["fraction_ai"] == 0.0
        and h2["api_result"]["windows"][0]["confidence"] == "High"
    ):
        raise SystemExit("H0 prior completed result mismatch")

    experiment = detector / "state" / "experiments" / EXPERIMENT
    inputs = experiment / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    for name, (filename, blob, expected_sha, words, chars, byte_count) in VARIANTS.items():
        raw = values[name].encode("utf-8")
        output = inputs / filename
        output.write_bytes(raw)
        key = f"{EXPERIMENT}-{name}"
        cache_dir = detector / "cache" / "pangram-4" / "4.0" / expected_sha
        cache_records = []
        if cache_dir.exists():
            for path in sorted(cache_dir.glob("*.json")):
                value = json.loads(path.read_text(encoding="utf-8"))
                cache_records.append({"path": path.relative_to(detector).as_posix(), "measurement_key": value.get("measurement_key"), "status": value.get("status"), "task_id": value.get("task_id")})
        statuses = {str(record["status"]) for record in cache_records}
        if name == "H0":
            classification = "EXACT_COMPLETED_RESULT_REUSE"
        elif "submit_ambiguous" in statuses:
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
            "source_path": f"{INPUT_BASE}/{filename}",
            "input_path": output.relative_to(detector).as_posix(),
            "git_blob": blob,
            "sha256": expected_sha,
            "whitespace_words": words,
            "unicode_characters": chars,
            "utf8_bytes": byte_count,
            "terminal_newline": False,
            "measurement_key": key,
            "cache_records": cache_records,
            "pre_submission_classification": classification,
        }
    packet = {
        "format": "somatic-r15-housemate-factorial-preflight-v1",
        "directive": {"id": "SOMATIC-R15-SURFACE-007", "packet_path": PACKET_REL, "packet_git_blob": PACKET_BLOB},
        "article": {"branch": "task/somatic-r15-clean-continuation-20260830", "head": ARTICLE_HEAD, "source_path": SOURCE_REL, "source_git_blob": SOURCE_BLOB, "source_sha256": SOURCE_SHA, "candidate_path": CANDIDATE_REL, "candidate_git_blob": CANDIDATE_BLOB, "candidate_sha256": CANDIDATE_SHA, "article_candidate_mutations": 0, "registered_master_mutations": 0},
        "detector": {"branch": "task/somatic-r15-exact-recovery-20260830", "starting_head": DETECTOR_HEAD, "model": "pangram-4", "required_version": "4.0", "transport": "SHORT_DOCUMENT_API"},
        "variants": records,
        "h0_reuse": {"result_packet_path": prior_path.relative_to(detector).as_posix(), "task_id": h2["task_id"], "result": h2["api_result"]},
        "direct_tail": {"sha256": DIRECT_TAIL_SHA, "preservation": {**{key: "PASS" if value else "FAIL" for key, value in preservation.items()}, "overall": "PASS"}},
        "mechanical_source_assertions": "PASS",
        "accounting_before_execution": {"reused_completed_results": 1, "completed_new_family_calls": 0, "maximum_authorized_new_calls": 5, "stable_family_result_cap": 6, "ambiguous_calls": 0, "gui_actions": 0, "whole_document_calls": 0},
        "preflight": "PASS",
    }
    write_json(experiment / "PREFLIGHT.json", packet)
    print(json.dumps({"preflight": "PASS", "variants": records, "preservation": packet["direct_tail"]["preservation"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
