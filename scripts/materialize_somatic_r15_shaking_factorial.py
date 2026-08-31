#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


EXPERIMENT = "somatic-r15-shaking-human-anchor-guidance-social-tail-20260831"
DETECTOR_HEAD = "6604fb2f215e1bf3fe5df3605ba973d2d7490ebc"
ARTICLE_PACKET_HEAD = "6be6e6513326bb437faceeed2579a87c41ff1d83"
ARTICLE_LIVE_HEAD = "f3d23bba5cf3ce92679475c1be33f5d06a8a6e57"
PACKET_REL = "tasks/somatic-r15-clean-continuation-20260830/CHAT-SURFACE-EXPERIMENT-008.md"
PACKET_BLOB = "2dd0708d3a29cbd3ca07358b5079c809705874da"
SOURCE_REL = "articles/somatic-therapies/experiments/R15-WHOLE-ARTICLE-PANGRAM-BOUNDARY-20260830.txt"
SOURCE_BLOB = "542012646469032eb836865b0e89b8fa368a1d0b"
SOURCE_SHA = "9a81bd04252a2ee851dd111040c600837bdf0a7bbf71c42c293e3b763c99a707"
CANDIDATE_REL = "articles/somatic-therapies/experiments/R15-EFT-REPAIR-CANDIDATE-20260831.md"
CANDIDATE_BLOB = "6f9251f51d79a6b322b8c6f6cae95a9a5d80f760"
CANDIDATE_SHA = "5a6226ca0056610b4492de7713a43bb152dde1079d81b5c05896c70fcf138679"
INPUT_BASE = "tasks/somatic-r15-clean-continuation-20260830/surface-experiment-008"
DIRECT_TAIL = (
    "The class gives people more than one way in. There is guidance, but it isn't one fixed TRE routine, and "
    "people are doing it together instead of alone. Somebody who gets nowhere with stripped-down TRE may do "
    "better with that."
)
DIRECT_TAIL_SHA = "0dd08ace8f74a3a1aac3f6bf6010808940ffcdd4b7da9e1a7a650b74a17d1e38"
VARIANTS = {
    "H0": ("H0-r15-human-anchor.txt", "ec0d902ba29b25ccf517b15cc7093c4a2e356ffe", "d9a1fcd6ed832117b32e07844300f5b30d9067884481b14a63740dcc5bfe5d3b", 224, 1218, 1232),
    "A": ("A-r15-anchor-original-tail.txt", "3fb584e04843408ee43b530a6c2b1f9cbb2346b7", "683a76b075325bcacdf2d8a92b835add258964890a27764f96d1072922035119", 273, 1512, 1528),
    "B": ("B-r15-anchor-direct-tail.txt", "8d87fd74e96baf306c325b8da97711389ced0b7c", "fcdc545d9d14ebe588755e705a5ea185f7508b9d465f5851a1ca3c47523297fd", 264, 1444, 1458),
    "C": ("C-current-anchor.txt", "2993757f24707297f1c8dd7b3fbf6c4e017e9e0b", "b36e1e46c06d764a080d407dce5412defe76ccb9202deb1a8a14e265acf40370", 293, 1631, 1641),
    "D": ("D-current-anchor-current-tail.txt", "261e9410bbc89e335a31f10e0e5e7e844788382e", "b27446d695044a6749a2780f7629599177160d4a619758784b915b3cdc013900", 328, 1838, 1848),
    "E": ("E-current-anchor-direct-tail.txt", "ad9e793d8073f859b555d5e0262c651303e6972b", "75fb8426a498dcedb99bb7ed84d9f5a6e1653a29b6e2b7d5ff8f61fe5fb8563f", 333, 1857, 1867),
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
    if git(detector, "rev-parse", "HEAD") != DETECTOR_HEAD or dirty != ["?? scripts/materialize_somatic_r15_shaking_factorial.py"]:
        raise SystemExit("detector start head/worktree mismatch")
    if git(article, "rev-parse", "HEAD") != ARTICLE_LIVE_HEAD or git(article, "status", "--porcelain"):
        raise SystemExit("article live head/worktree mismatch")
    if subprocess.run(["git", "merge-base", "--is-ancestor", ARTICLE_PACKET_HEAD, ARTICLE_LIVE_HEAD], cwd=article).returncode != 0:
        raise SystemExit("article packet head is not an ancestor")
    intervening = git(article, "diff", "--name-only", ARTICLE_PACKET_HEAD, ARTICLE_LIVE_HEAD).splitlines()
    if intervening != [".github/workflows/content-integrity.yml", "tests/test_content_integrity_full_history.py"]:
        raise SystemExit(f"unexpected post-packet article changes: {intervening}")
    if git(article, "hash-object", PACKET_REL) != PACKET_BLOB:
        raise SystemExit("execution packet blob mismatch")
    source_raw = (article / SOURCE_REL).read_bytes()
    candidate_raw = (article / CANDIDATE_REL).read_bytes()
    if not (git(article, "hash-object", SOURCE_REL) == SOURCE_BLOB and digest(source_raw) == SOURCE_SHA and git(article, "hash-object", CANDIDATE_REL) == CANDIDATE_BLOB and digest(candidate_raw) == CANDIDATE_SHA):
        raise SystemExit("article source/candidate identity mismatch")

    values: dict[str, str] = {}
    records: dict[str, Any] = {}
    for name, (filename, blob, expected_sha, words, chars, byte_count) in VARIANTS.items():
        rel = f"{INPUT_BASE}/{filename}"
        raw = (article / rel).read_bytes()
        text = raw.decode("utf-8")
        if not (git(article, "hash-object", rel) == blob and digest(raw) == expected_sha and len(text.split()) == words and len(text) == chars and len(raw) == byte_count and not text.endswith("\n")):
            raise SystemExit(f"{name}: frozen input identity mismatch")
        values[name] = text

    source_text = source_raw.decode("utf-8")
    if values["H0"] != source_text[9284:10502] or values["A"] != source_text[9284:10796]:
        raise SystemExit("H0/A exact R15 slice mismatch")
    if not (values["A"].startswith(values["H0"]) and values["B"].startswith(values["H0"])):
        raise SystemExit("A/B H0 prefix mismatch")
    current_visible = reader_visible(candidate_raw.decode("utf-8"))
    c_start = current_visible.index("\n\nShaking Qigong / Shaking Medicine")
    c_end_marker = "Guided shaking plus qigong also seems like a middle ground between a fully predictable TRE structure and completely unstructured shaking."
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
    if digest(a_tail.encode("utf-8")) != "72855e976212f494b05bd3fa1abc7caa01e273904456220d62d04991c33f3eee" or digest(d_tail.encode("utf-8")) != "3a96a5bb9b7dd0d670f36b16ccaceca355243a7878b69afa753c847e78c2f349":
        raise SystemExit("original/current tail hash mismatch")
    preservation = {
        "multiple_entry_routes": "more than one way in" in DIRECT_TAIL,
        "guidance": "There is guidance" in DIRECT_TAIL,
        "not_fixed_tre_routine": "isn't one fixed TRE routine" in DIRECT_TAIL,
        "together_not_alone": "doing it together instead of alone" in DIRECT_TAIL,
        "social_group_condition": "together" in DIRECT_TAIL,
        "standard_tre_nonresponse_may_improve": "gets nowhere with stripped-down TRE may do better" in DIRECT_TAIL,
    }
    if not all(preservation.values()):
        raise SystemExit("direct-tail preservation mismatch")

    prior_path = detector / "state/experiments/somatic-r15-api-gui-human-window-calibration-20260831/RESULT-PACKET.json"
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    h1 = prior["variants"]["H1"]
    if not (h1["input"]["sha256"] == VARIANTS["H0"][2] and h1["task_id"] == "8ce5a703-e012-40f6-a260-9517a40eeb74" and h1["api_result"]["version"] == "4.0" and h1["api_result"]["fraction_human"] == 1.0 and h1["api_result"]["fraction_ai"] == 0.0 and h1["api_result"]["windows"][0]["confidence"] == "High"):
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
        if name == "H0": classification = "EXACT_COMPLETED_RESULT_REUSE"
        elif "submit_ambiguous" in statuses: classification = "EXACT_API_ACTION_AMBIGUOUS"
        elif "pending" in statuses: classification = "EXACT_API_TASK_PENDING"
        elif "success" in statuses: classification = "EXACT_API_RESULT_EXISTS"
        elif cache_records: classification = "EXACT_API_PRIOR_NONTERMINAL_STATE"
        else: classification = "EXACT_API_NEVER_SUBMITTED"
        records[name] = {"source_path": f"{INPUT_BASE}/{filename}", "input_path": output.relative_to(detector).as_posix(), "git_blob": blob, "sha256": expected_sha, "whitespace_words": words, "unicode_characters": chars, "utf8_bytes": byte_count, "terminal_newline": False, "measurement_key": key, "cache_records": cache_records, "pre_submission_classification": classification}
    packet = {
        "format": "somatic-r15-shaking-factorial-preflight-v1",
        "directive": {"id": "SOMATIC-R15-CI-AND-SURFACE-008", "packet_path": PACKET_REL, "packet_git_blob": PACKET_BLOB},
        "article": {"branch": "task/somatic-r15-clean-continuation-20260830", "packet_head": ARTICLE_PACKET_HEAD, "live_head_after_ci_fix": ARTICLE_LIVE_HEAD, "source_path": SOURCE_REL, "source_git_blob": SOURCE_BLOB, "source_sha256": SOURCE_SHA, "candidate_path": CANDIDATE_REL, "candidate_git_blob": CANDIDATE_BLOB, "candidate_sha256": CANDIDATE_SHA, "article_candidate_mutations": 0, "registered_master_mutations": 0},
        "detector": {"branch": "task/somatic-r15-exact-recovery-20260830", "starting_head": DETECTOR_HEAD, "model": "pangram-4", "required_version": "4.0", "transport": "SHORT_DOCUMENT_API"},
        "variants": records,
        "h0_reuse": {"result_packet_path": prior_path.relative_to(detector).as_posix(), "task_id": h1["task_id"], "result": h1["api_result"]},
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
