from __future__ import annotations

import hashlib
import json
import math
import re
import statistics
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from . import idiolect


class PrescreenCalibrationError(ValueError):
    pass


@dataclass(frozen=True)
class Rule:
    kind: str
    threshold_surface: float | None = None
    threshold_content_light: float | None = None

    @property
    def complexity(self) -> int:
        return 2 if self.kind == "both" else 1

    def clears(self, row: dict[str, Any]) -> bool:
        surface = float(row["surface_profile_similarity"])
        content = float(row["content_light_profile_similarity"])
        if self.kind == "surface":
            return surface >= float(self.threshold_surface)
        if self.kind == "content_light":
            return content >= float(self.threshold_content_light)
        if self.kind == "both":
            return (
                surface >= float(self.threshold_surface)
                and content >= float(self.threshold_content_light)
            )
        raise PrescreenCalibrationError(f"unknown rule kind: {self.kind}")

    def public(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "threshold_surface": self.threshold_surface,
            "threshold_content_light": self.threshold_content_light,
        }


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _git(repo_root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise PrescreenCalibrationError(
            f"git {' '.join(args)} failed: {proc.stderr.strip()}"
        )
    return proc.stdout


def resolve_ref(repo_root: Path, ref: str) -> str:
    candidates = [ref]
    if not ref.startswith("origin/"):
        candidates.append(f"origin/{ref}")
    for candidate in candidates:
        proc = subprocess.run(
            ["git", "rev-parse", "--verify", candidate],
            cwd=repo_root,
            text=True,
            capture_output=True,
        )
        if proc.returncode == 0:
            return proc.stdout.strip()
    raise PrescreenCalibrationError(f"unable to resolve evidence ref: {ref}")


def _git_show(repo_root: Path, ref: str, path: str) -> str:
    return _git(repo_root, "show", f"{ref}:{path}")


def _prefix_words(text: str, count: int) -> str:
    if count <= 0:
        raise PrescreenCalibrationError("profile word limit must be positive")
    matches = list(idiolect._WORD_RE.finditer(text))
    if len(matches) <= count:
        return text.strip()
    return text[: matches[count - 1].end()].strip()


def extract_profile_sections(
    source_text: str,
    section_names: Iterable[str],
    *,
    max_words_per_section: int,
) -> list[dict[str, Any]]:
    header = re.compile(r"^=====\s*([^=\n]+?)\s*=====\s*$", re.MULTILINE)
    matches = list(header.finditer(source_text))
    by_name: dict[str, str] = {}
    for index, match in enumerate(matches):
        name = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source_text)
        by_name[name] = source_text[start:end].strip()

    rows = []
    for requested in section_names:
        text = by_name.get(str(requested))
        if text is None:
            raise PrescreenCalibrationError(f"missing profile section: {requested}")
        clipped = _prefix_words(text, max_words_per_section)
        words = len(idiolect._tokens(clipped))
        if words < 50:
            raise PrescreenCalibrationError(
                f"profile section {requested} is unexpectedly short: {words} words"
            )
        rows.append(
            {
                "section": str(requested),
                "text": clipped,
                "word_count": words,
                "sha256": _sha256_text(clipped),
            }
        )
    return rows


def _article_family(measurement_key: str) -> str | None:
    if measurement_key.startswith("spiritual-bypassing-"):
        return "spiritual-bypassing"
    if measurement_key.startswith("romance-") or measurement_key.startswith(
        "historical-whitespace-audit-"
    ):
        return "romance"
    return None


def _is_successful_v4(data: dict[str, Any]) -> bool:
    result = data.get("result")
    return (
        data.get("status") == "success"
        and isinstance(result, dict)
        and str(result.get("version")) == "4.0"
        and str(data.get("model")) == "pangram-4"
    )


def _strict_human(result: dict[str, Any]) -> bool:
    return (
        str(result.get("prediction_short")) == "Human"
        and abs(float(result.get("fraction_ai", 1.0))) <= 1e-12
        and abs(float(result.get("fraction_ai_assisted", 1.0))) <= 1e-12
    )


def _headline_human(result: dict[str, Any]) -> bool:
    return str(result.get("prediction_short")) == "Human"


def collect_cache_rows(
    repo_root: Path,
    *,
    evidence_ref: str,
    cache_root: str,
    accepted_prefixes: list[str],
    minimum_words: int,
    profile: idiolect.AuthorProfile,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    resolved_sha = resolve_ref(repo_root, evidence_ref)
    ref_for_show = resolved_sha
    paths = [
        line.strip()
        for line in _git(
            repo_root,
            "ls-tree",
            "-r",
            "--name-only",
            ref_for_show,
            "--",
            cache_root,
        ).splitlines()
        if line.strip().endswith(".json")
    ]

    excluded = {
        "not_successful_pangram4_v4": 0,
        "measurement_key_out_of_scope": 0,
        "missing_text": 0,
        "text_hash_path_mismatch": 0,
        "under_minimum_words": 0,
        "unknown_article_family": 0,
        "duplicate_same_label": 0,
        "duplicate_label_conflict": 0,
        "invalid_json": 0,
    }
    by_text_sha: dict[str, dict[str, Any]] = {}
    conflict_shas: set[str] = set()

    for path in paths:
        try:
            data = json.loads(_git_show(repo_root, ref_for_show, path))
        except Exception:
            excluded["invalid_json"] += 1
            continue
        if not isinstance(data, dict) or not _is_successful_v4(data):
            excluded["not_successful_pangram4_v4"] += 1
            continue
        key = str(data.get("measurement_key") or Path(path).stem)
        if not any(key.startswith(prefix) for prefix in accepted_prefixes):
            excluded["measurement_key_out_of_scope"] += 1
            continue
        result = data["result"]
        text = result.get("text") or data.get("text")
        if not isinstance(text, str) or not text.strip():
            excluded["missing_text"] += 1
            continue
        text_sha = _sha256_text(text)
        parts = path.split("/")
        expected_sha = parts[3] if len(parts) > 4 else ""
        if expected_sha != text_sha:
            excluded["text_hash_path_mismatch"] += 1
            continue
        words = len(idiolect._tokens(text))
        if words < minimum_words:
            excluded["under_minimum_words"] += 1
            continue
        family = _article_family(key)
        if family is None:
            excluded["unknown_article_family"] += 1
            continue

        channels = idiolect._feature_channels(text)
        row = {
            "text_sha256": text_sha,
            "measurement_keys": [key],
            "article_family": family,
            "word_count": words,
            "prediction_short": str(result.get("prediction_short") or ""),
            "fraction_ai": float(result.get("fraction_ai", 0.0)),
            "fraction_ai_assisted": float(result.get("fraction_ai_assisted", 0.0)),
            "strict_full_human": _strict_human(result),
            "headline_human": _headline_human(result),
            "surface_profile_similarity": idiolect._cosine(
                profile.surface, channels["surface"]
            ),
            "content_light_profile_similarity": idiolect._cosine(
                profile.content_light, channels["content_light"]
            ),
        }

        previous = by_text_sha.get(text_sha)
        if previous is None:
            by_text_sha[text_sha] = row
            continue

        same_label = all(
            previous[field] == row[field]
            for field in (
                "prediction_short",
                "fraction_ai",
                "fraction_ai_assisted",
                "strict_full_human",
                "headline_human",
            )
        )
        if not same_label:
            conflict_shas.add(text_sha)
            excluded["duplicate_label_conflict"] += 1
            continue
        previous["measurement_keys"].append(key)
        excluded["duplicate_same_label"] += 1

    for sha in conflict_shas:
        by_text_sha.pop(sha, None)

    rows = sorted(by_text_sha.values(), key=lambda row: row["text_sha256"])
    return rows, {
        "evidence_ref_requested": evidence_ref,
        "evidence_ref_resolved_sha": resolved_sha,
        "cache_json_file_count": len(paths),
        "unique_eligible_text_count": len(rows),
        "excluded": excluded,
    }


def _rule_candidates(rows: list[dict[str, Any]], label_field: str) -> list[Rule]:
    safe = [row for row in rows if bool(row[label_field])]
    if not safe:
        return []
    surface_values = sorted({float(row["surface_profile_similarity"]) for row in safe})
    content_values = sorted(
        {float(row["content_light_profile_similarity"]) for row in safe}
    )
    candidates: list[Rule] = []
    candidates.extend(
        Rule("surface", threshold_surface=value) for value in surface_values
    )
    candidates.extend(
        Rule("content_light", threshold_content_light=value)
        for value in content_values
    )
    candidates.extend(
        Rule("both", threshold_surface=surface, threshold_content_light=content)
        for surface in surface_values
        for content in content_values
    )
    return candidates


def fit_zero_false_safe_rule(
    rows: list[dict[str, Any]],
    *,
    label_field: str,
    minimum_cleared: int = 3,
) -> tuple[Rule | None, dict[str, Any]]:
    safe_count = sum(bool(row[label_field]) for row in rows)
    unsafe_count = len(rows) - safe_count
    if safe_count < minimum_cleared or unsafe_count < 1:
        return None, {
            "reason": "insufficient_training_class_supply",
            "training_count": len(rows),
            "safe_count": safe_count,
            "unsafe_count": unsafe_count,
        }

    valid: list[tuple[tuple[Any, ...], Rule, int]] = []
    for rule in _rule_candidates(rows, label_field):
        cleared = [row for row in rows if rule.clears(row)]
        if len(cleared) < minimum_cleared:
            continue
        false_safe = sum(not bool(row[label_field]) for row in cleared)
        if false_safe:
            continue
        threshold_sum = sum(
            value
            for value in (
                rule.threshold_surface,
                rule.threshold_content_light,
            )
            if value is not None
        )
        # Maximize training coverage, then prefer lower-complexity rules, then
        # stricter thresholds, with kind as a stable final tie-breaker.
        key = (
            len(cleared),
            -rule.complexity,
            threshold_sum,
            rule.kind,
        )
        valid.append((key, rule, len(cleared)))

    if not valid:
        return None, {
            "reason": "no_zero_false_safe_monotone_rule",
            "training_count": len(rows),
            "safe_count": safe_count,
            "unsafe_count": unsafe_count,
        }
    _, best, cleared_count = max(valid, key=lambda item: item[0])
    return best, {
        "reason": "fit",
        "training_count": len(rows),
        "safe_count": safe_count,
        "unsafe_count": unsafe_count,
        "training_cleared": cleared_count,
        "training_coverage": cleared_count / len(rows),
        "training_false_safe_count": 0,
    }


def _evaluate_rule(
    rule: Rule | None,
    rows: list[dict[str, Any]],
    *,
    label_field: str,
) -> dict[str, Any]:
    if rule is None:
        return {
            "holdout_count": len(rows),
            "cleared_count": 0,
            "coverage": 0.0,
            "false_safe_count": 0,
            "true_safe_count": 0,
            "cleared": [],
        }
    cleared_rows = [row for row in rows if rule.clears(row)]
    false_safe = [row for row in cleared_rows if not bool(row[label_field])]
    true_safe = [row for row in cleared_rows if bool(row[label_field])]
    return {
        "holdout_count": len(rows),
        "cleared_count": len(cleared_rows),
        "coverage": len(cleared_rows) / len(rows) if rows else 0.0,
        "false_safe_count": len(false_safe),
        "true_safe_count": len(true_safe),
        "cleared": [
            {
                "text_sha256": row["text_sha256"],
                "article_family": row["article_family"],
                "strict_full_human": row["strict_full_human"],
                "headline_human": row["headline_human"],
                "fraction_ai": row["fraction_ai"],
                "surface_profile_similarity": row["surface_profile_similarity"],
                "content_light_profile_similarity": row[
                    "content_light_profile_similarity"
                ],
            }
            for row in cleared_rows
        ],
    }


def _wilson_upper(errors: int, trials: int, *, z: float = 1.6448536269514722) -> float:
    if trials <= 0:
        return 1.0
    p = errors / trials
    denominator = 1.0 + z * z / trials
    center = p + z * z / (2.0 * trials)
    radius = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * trials)) / trials)
    return min(1.0, (center + radius) / denominator)


def _label_summary(rows: list[dict[str, Any]], label_field: str) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for label_name, predicate in (
        ("safe", True),
        ("unsafe", False),
    ):
        subset = [row for row in rows if bool(row[label_field]) is predicate]
        output[label_name] = {
            "count": len(subset),
            "surface_median": (
                statistics.median(
                    float(row["surface_profile_similarity"]) for row in subset
                )
                if subset
                else None
            ),
            "content_light_median": (
                statistics.median(
                    float(row["content_light_profile_similarity"])
                    for row in subset
                )
                if subset
                else None
            ),
        }
    return output


def cross_article_calibration(
    rows: list[dict[str, Any]],
    *,
    label_field: str,
    article_groups: list[str],
    substitution_acceptance: dict[str, Any],
) -> dict[str, Any]:
    folds = []
    heldout_cleared = 0
    heldout_false_safe = 0
    heldout_true_safe = 0

    for holdout_group in article_groups:
        train = [row for row in rows if row["article_family"] != holdout_group]
        holdout = [row for row in rows if row["article_family"] == holdout_group]
        rule, fit = fit_zero_false_safe_rule(train, label_field=label_field)
        evaluation = _evaluate_rule(rule, holdout, label_field=label_field)
        heldout_cleared += int(evaluation["cleared_count"])
        heldout_false_safe += int(evaluation["false_safe_count"])
        heldout_true_safe += int(evaluation["true_safe_count"])
        folds.append(
            {
                "holdout_article_family": holdout_group,
                "training_article_families": sorted(
                    {row["article_family"] for row in train}
                ),
                "rule": rule.public() if rule else None,
                "fit": fit,
                "evaluation": evaluation,
            }
        )

    upper = _wilson_upper(heldout_false_safe, heldout_cleared)
    observed_groups = sorted({row["article_family"] for row in rows})
    accepted = (
        len(observed_groups)
        >= int(substitution_acceptance["required_independent_article_families"])
        and heldout_cleared
        >= int(substitution_acceptance["required_total_heldout_cleared"])
        and heldout_false_safe
        == int(substitution_acceptance["required_false_safe_count"])
        and upper
        <= float(
            substitution_acceptance[
                "maximum_one_sided_95pct_false_safe_upper_bound"
            ]
        )
    )
    blockers = []
    if len(observed_groups) < int(
        substitution_acceptance["required_independent_article_families"]
    ):
        blockers.append("insufficient_independent_article_families")
    if heldout_cleared < int(
        substitution_acceptance["required_total_heldout_cleared"]
    ):
        blockers.append("insufficient_heldout_cleared_examples")
    if heldout_false_safe != int(
        substitution_acceptance["required_false_safe_count"]
    ):
        blockers.append("heldout_false_safe_detected")
    if upper > float(
        substitution_acceptance["maximum_one_sided_95pct_false_safe_upper_bound"]
    ):
        blockers.append("false_safe_confidence_bound_too_high")

    return {
        "label_field": label_field,
        "article_family_count": len(observed_groups),
        "article_families": observed_groups,
        "label_summary": _label_summary(rows, label_field),
        "folds": folds,
        "heldout_cleared_count": heldout_cleared,
        "heldout_true_safe_count": heldout_true_safe,
        "heldout_false_safe_count": heldout_false_safe,
        "heldout_false_safe_rate_among_cleared": (
            heldout_false_safe / heldout_cleared if heldout_cleared else None
        ),
        "one_sided_95pct_false_safe_upper_bound": upper,
        "substitution_authorized": accepted,
        "substitution_blockers": blockers,
    }


def run(
    spec_path: Path,
    *,
    repo_root: Path,
    profile_source_path: Path,
    out_path: Path,
) -> dict[str, Any]:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if spec.get("schema_version") != 1:
        raise PrescreenCalibrationError("spec schema_version must be 1")
    if int(spec.get("pangram_calls_authorized", -1)) != 0:
        raise PrescreenCalibrationError("cached calibration must authorize zero Pangram calls")

    profile_spec = spec["profile"]
    profile_rows = extract_profile_sections(
        profile_source_path.read_text(encoding="utf-8"),
        profile_spec["sections"],
        max_words_per_section=int(profile_spec["max_words_per_section"]),
    )
    profile = idiolect.build_profile([row["text"] for row in profile_rows])
    cache_rows, cache_receipt = collect_cache_rows(
        repo_root,
        evidence_ref=str(spec["pangram_cache_ref"]),
        cache_root=str(spec["pangram_cache_root"]),
        accepted_prefixes=[str(value) for value in spec["accepted_measurement_key_prefixes"]],
        minimum_words=int(spec["minimum_candidate_words"]),
        profile=profile,
    )
    if not cache_rows:
        raise PrescreenCalibrationError("no eligible cached Pangram texts were recovered")

    groups = [str(value) for value in spec["holdout_design"]["groups"]]
    missing_groups = [
        group for group in groups if not any(row["article_family"] == group for row in cache_rows)
    ]
    if missing_groups:
        raise PrescreenCalibrationError(
            f"predeclared holdout groups missing from cache: {missing_groups}"
        )

    primary = cross_article_calibration(
        cache_rows,
        label_field="strict_full_human",
        article_groups=groups,
        substitution_acceptance=spec["substitution_acceptance"],
    )
    secondary = cross_article_calibration(
        cache_rows,
        label_field="headline_human",
        article_groups=groups,
        substitution_acceptance=spec["substitution_acceptance"],
    )

    public_rows = [
        {
            key: row[key]
            for key in (
                "text_sha256",
                "measurement_keys",
                "article_family",
                "word_count",
                "prediction_short",
                "fraction_ai",
                "fraction_ai_assisted",
                "strict_full_human",
                "headline_human",
                "surface_profile_similarity",
                "content_light_profile_similarity",
            )
        }
        for row in cache_rows
    ]
    result = {
        "schema_version": 1,
        "status": "cached-idiolect-to-pangram-prescreen-calibration-complete",
        "report_type": "detector-call-prescreen-calibration-not-IER",
        "pangram_calls_made": 0,
        "pangram_substitution_currently_authorized": bool(
            primary["substitution_authorized"]
        ),
        "profile": {
            "repository": profile_spec["repository"],
            "commit": profile_spec["commit"],
            "path": profile_spec["path"],
            "provenance": profile_spec["provenance"],
            "sections": [
                {
                    "section": row["section"],
                    "word_count": row["word_count"],
                    "sha256": row["sha256"],
                }
                for row in profile_rows
            ],
            "sample_count": profile.sample_count,
            "word_count": profile.word_count,
            "corpus_sha256": profile.corpus_sha256,
            "algorithm_version": idiolect.ALGORITHM_VERSION,
            "register_limit": profile_spec["register_limit"],
        },
        "cache": cache_receipt,
        "primary_strict_full_human": primary,
        "secondary_headline_human": secondary,
        "candidate_rows": public_rows,
        "interpretation_guardrails": {
            "this_predicts_pangram_not_human_authorship": True,
            "this_is_not_idiolect_erasure_rate": True,
            "do_not_count_exact_repeats_as_new_evidence": True,
            "do_not_random_split_near_duplicate_article_variants": True,
            "do_not_replace_pangram_unless_primary_substitution_authorized": True,
            "false_safe_is_primary_error": True,
        },
        "privacy": {
            "raw_candidate_text_in_output": False,
            "raw_profile_text_in_output": False,
        },
    }

    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True)
    for forbidden in ("\"text\":", "\"raw_text\":", "\"canonical_text\":"):
        if forbidden in encoded:
            raise PrescreenCalibrationError(
                f"metadata-only output contains forbidden raw-text key: {forbidden}"
            )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m pangram_lab.idiolect_pangram_prescreen"
    )
    parser.add_argument(
        "spec",
        nargs="?",
        default="state/IDIOLECT-PANGRAM-PRESCREEN-SPEC-2026-08-19.json",
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--profile-source", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        result = run(
            Path(args.spec),
            repo_root=Path(args.repo_root),
            profile_source_path=Path(args.profile_source),
            out_path=Path(args.out),
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "status": result["status"],
                "pangram_calls_made": result["pangram_calls_made"],
                "eligible_texts": result["cache"]["unique_eligible_text_count"],
                "strict_substitution_authorized": result[
                    "primary_strict_full_human"
                ]["substitution_authorized"],
                "strict_heldout_cleared": result["primary_strict_full_human"][
                    "heldout_cleared_count"
                ],
                "strict_false_safe": result["primary_strict_full_human"][
                    "heldout_false_safe_count"
                ],
                "strict_false_safe_upper_95": result[
                    "primary_strict_full_human"
                ]["one_sided_95pct_false_safe_upper_bound"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
