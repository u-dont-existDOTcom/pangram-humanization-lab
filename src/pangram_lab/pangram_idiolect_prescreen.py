from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .idiolect import _cosine, _feature_channels, _tokens, build_profile

SCHEMA_VERSION = 1
INSTRUMENT_VERSION = "pangram-idiolect-prescreen-pilot-v1"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _score(profile, text: str) -> tuple[float, float]:
    features = _feature_channels(text)
    return (
        _cosine(profile.surface, features["surface"]),
        _cosine(profile.content_light, features["content_light"]),
    )


def _load_examples(spec: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cached = spec["cached_case"]
    data = json.loads(Path(cached["results_path"]).read_text(encoding="utf-8"))
    for key, result in data.items():
        if result.get("stage") != "STAGE_SUCCESS":
            continue
        text = str(result.get("text") or "")
        if not text.strip():
            continue
        pangram_short = str(result.get("prediction_short") or "")
        rows.append(
            {
                "id": str(key),
                "group_id": str(cached["group_id"]),
                "pangram_label": "Human" if pangram_short == "Human" else "NonHuman",
                "pangram_prediction_short": pangram_short,
                "pangram_fraction_ai": result.get("fraction_ai"),
                "evidence_class": str(cached["evidence_class"]),
                "text": text,
            }
        )
    for row in spec.get("recorded_examples", []):
        rows.append(dict(row))
    return rows


def _best_zero_false_safe_rule(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    eligible = [row for row in rows if not row["weak_short_boundary"]]
    if not eligible:
        return None
    surface_values = sorted({float(row["surface_similarity"]) for row in eligible})
    content_values = sorted({float(row["content_light_similarity"]) for row in eligible})
    candidates: list[dict[str, Any]] = []
    for surface in surface_values:
        for content in content_values:
            safe = [
                row for row in eligible
                if float(row["surface_similarity"]) >= surface
                and float(row["content_light_similarity"]) >= content
            ]
            false_safe = sum(row["pangram_label"] != "Human" for row in safe)
            if false_safe:
                continue
            candidates.append(
                {
                    "surface_threshold": surface,
                    "content_light_threshold": content,
                    "safe_count": len(safe),
                    "eligible_count": len(eligible),
                    "safe_coverage": len(safe) / len(eligible),
                    "false_safe_count": 0,
                }
            )
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda row: (
            int(row["safe_count"]),
            min(float(row["surface_threshold"]), float(row["content_light_threshold"])),
            float(row["surface_threshold"]) + float(row["content_light_threshold"]),
        ),
    )


def _apply_rule(rule: dict[str, Any] | None, row: dict[str, Any]) -> bool:
    if rule is None or row["weak_short_boundary"]:
        return False
    return (
        float(row["surface_similarity"]) >= float(rule["surface_threshold"])
        and float(row["content_light_similarity"]) >= float(rule["content_light_threshold"])
    )


def calibrate(spec_path: Path, profile_dir: Path, out_path: Path) -> dict[str, Any]:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    profile_paths = sorted(path for path in profile_dir.glob("*.txt") if path.is_file())
    if not profile_paths:
        raise ValueError("profile directory contains no .txt samples")
    profile_texts = [path.read_text(encoding="utf-8") for path in profile_paths]
    profile = build_profile(profile_texts)

    rows = _load_examples(spec)
    for row in rows:
        text = str(row.pop("text"))
        surface, content_light = _score(profile, text)
        words = len(_tokens(text))
        row.update(
            {
                "text_sha256": _sha(text),
                "word_count": words,
                "weak_short_boundary": words < 50,
                "surface_similarity": round(surface, 6),
                "content_light_similarity": round(content_light, 6),
            }
        )

    groups = sorted({str(row["group_id"]) for row in rows})
    folds: list[dict[str, Any]] = []
    for holdout_group in groups:
        training = [row for row in rows if row["group_id"] != holdout_group]
        holdout = [row for row in rows if row["group_id"] == holdout_group]
        rule = _best_zero_false_safe_rule(training)
        evaluated = [row for row in holdout if not row["weak_short_boundary"]]
        safe_rows = [row for row in evaluated if _apply_rule(rule, row)]
        false_safe = [row for row in safe_rows if row["pangram_label"] != "Human"]
        folds.append(
            {
                "holdout_group": holdout_group,
                "training_group_count": len(groups) - 1,
                "training_rule": (
                    None if rule is None else {
                        **rule,
                        "surface_threshold": round(float(rule["surface_threshold"]), 6),
                        "content_light_threshold": round(float(rule["content_light_threshold"]), 6),
                        "safe_coverage": round(float(rule["safe_coverage"]), 6),
                    }
                ),
                "holdout_eligible_count": len(evaluated),
                "holdout_safe_count": len(safe_rows),
                "holdout_safe_coverage": round(len(safe_rows) / len(evaluated), 6) if evaluated else None,
                "holdout_false_safe_count": len(false_safe),
                "holdout_false_safe_ids": [str(row["id"]) for row in false_safe],
                "holdout_safe_ids": [str(row["id"]) for row in safe_rows],
            }
        )

    eligible = [row for row in rows if not row["weak_short_boundary"]]
    total_safe = sum(int(fold["holdout_safe_count"]) for fold in folds)
    total_false_safe = sum(int(fold["holdout_false_safe_count"]) for fold in folds)
    nonhuman = sum(row["pangram_label"] != "Human" for row in eligible)
    minimums = spec["evaluation"]["validation_minimums"]
    minimum_sample_structure_met = (
        len(groups) >= int(minimums["independent_groups"])
        and len(eligible) >= int(minimums["examples"])
        and nonhuman >= int(minimums["nonhuman_examples"])
    )
    coverage = total_safe / len(eligible) if eligible else 0.0
    substitution_validated = (
        minimum_sample_structure_met
        and total_false_safe <= int(minimums["heldout_false_safe_count"])
        and coverage >= float(minimums["heldout_safe_coverage_minimum"])
    )

    result = {
        "schema_version": SCHEMA_VERSION,
        "instrument_version": INSTRUMENT_VERSION,
        "status": "validated-prescreen" if substitution_validated else "pilot-not-validated",
        "purpose": spec["purpose"],
        "no_new_pangram_calls": True,
        "profile": {
            "sample_count": profile.sample_count,
            "word_count": profile.word_count,
            "corpus_sha256": profile.corpus_sha256,
            "sample_sha256": list(profile.sample_sha256),
            "provenance": spec["profile"]["provenance"],
            "register": spec["profile"]["register"],
        },
        "dataset": {
            "group_count": len(groups),
            "groups": groups,
            "example_count": len(rows),
            "eligible_50plus_count": len(eligible),
            "eligible_nonhuman_count": nonhuman,
            "short_descriptive_only_count": sum(row["weak_short_boundary"] for row in rows),
            "examples": rows,
        },
        "leave_one_group_out": {
            "rule_family": spec["evaluation"]["candidate_rule_family"],
            "folds": folds,
            "heldout_safe_count": total_safe,
            "heldout_false_safe_count": total_false_safe,
            "heldout_safe_coverage": round(coverage, 6),
        },
        "validation": {
            "minimums": minimums,
            "minimum_sample_structure_met": minimum_sample_structure_met,
            "substitution_validated": substitution_validated,
            "decision": (
                "Idiolect proxy may replace Pangram for qualifying safe cases."
                if substitution_validated
                else "Do not skip Pangram based on this proxy; evidence is insufficient or unsafe."
            ),
        },
        "interpretation_guardrails": {
            "not_ier": True,
            "not_human_authorship_proof": True,
            "pangram_prediction_only": True,
            "do_not_fit_article_specific_phrase_rules": True,
            "no_raw_profile_prose_in_output": True,
        },
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec")
    parser.add_argument("--profile-dir", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    result = calibrate(Path(args.spec), Path(args.profile_dir), Path(args.out))
    print(json.dumps({
        "status": result["status"],
        "group_count": result["dataset"]["group_count"],
        "eligible_50plus_count": result["dataset"]["eligible_50plus_count"],
        "heldout_safe_count": result["leave_one_group_out"]["heldout_safe_count"],
        "heldout_false_safe_count": result["leave_one_group_out"]["heldout_false_safe_count"],
        "heldout_safe_coverage": result["leave_one_group_out"]["heldout_safe_coverage"],
        "substitution_validated": result["validation"]["substitution_validated"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
