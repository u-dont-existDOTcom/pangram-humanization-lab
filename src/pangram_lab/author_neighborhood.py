from __future__ import annotations

import argparse
import collections
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any

_FORBIDDEN_KEY_FRAGMENTS = (
    "raw_text",
    "canonical_text",
    "prose",
    "local_text_path",
    "embedding",
)


def _finite_score(value: Any, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be a finite number")
    return number


def _sha256(value: Any, *, field: str) -> str:
    text = str(value or "").strip().lower()
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise ValueError(f"{field} must be 64 lowercase hex characters")
    return text


def _scan_forbidden_keys(value: Any, *, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).casefold()
            if any(fragment in lowered for fragment in _FORBIDDEN_KEY_FRAGMENTS):
                raise ValueError(f"durable input contains forbidden field {path}.{key}")
            _scan_forbidden_keys(child, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_forbidden_keys(child, path=f"{path}[{index}]")


def _validate_authors(dataset: dict, spec: dict) -> tuple[list[str], str, set[str]]:
    authors = [str(value).strip() for value in dataset.get("authors", [])]
    if len(authors) < int(spec["input_contract"]["required_author_count_minimum"]):
        raise ValueError("dataset has too few authors")
    if any(not author for author in authors) or len(authors) != len(set(authors)):
        raise ValueError("authors must be unique non-empty strings")

    owner = str(dataset.get("owner_author") or "").strip()
    if owner != str(spec.get("owner_author") or "").strip():
        raise ValueError("dataset owner_author does not match diagnostic spec")
    if owner not in authors:
        raise ValueError("owner_author is not in authors")

    declared = dataset.get("declared_neighbor_hypotheses")
    if declared is None:
        declared = [row["author"] for row in spec.get("owner_supplied_neighbor_hypotheses", [])]
    neighbors = {str(value).strip() for value in declared if str(value).strip()}
    unknown = sorted(neighbors - set(authors))
    if unknown:
        raise ValueError(f"declared neighbors are not in authors: {unknown}")
    if owner in neighbors:
        raise ValueError("owner_author cannot be its own neighbor")
    return authors, owner, neighbors


def _scores(row: dict, authors: list[str], *, field: str = "scores_by_author") -> dict[str, float]:
    raw = row.get(field)
    if not isinstance(raw, dict):
        raise ValueError(f"{field} must be an object")
    if set(raw) != set(authors):
        missing = sorted(set(authors) - set(raw))
        extra = sorted(set(raw) - set(authors))
        raise ValueError(f"{field} author mismatch: missing={missing} extra={extra}")
    return {
        author: _finite_score(raw[author], field=f"{field}.{author}")
        for author in authors
    }


def _prediction(scores: dict[str, float]) -> dict[str, Any]:
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    winner, winning_score = ranked[0]
    runner_up, runner_score = ranked[1]
    tied = math.isclose(winning_score, runner_score, rel_tol=0.0, abs_tol=1e-12)
    return {
        "winner": winner,
        "winning_score": winning_score,
        "runner_up": runner_up,
        "runner_up_score": runner_score,
        "winning_margin": winning_score - runner_score,
        "top_tie": tied,
    }


def _true_author_diagnostic(
    scores: dict[str, float], true_author: str
) -> dict[str, Any]:
    alternatives = {
        author: score for author, score in scores.items() if author != true_author
    }
    highest_alt = _prediction(alternatives)
    return {
        "true_author_score": scores[true_author],
        "highest_alternative": highest_alt["winner"],
        "highest_alternative_score": highest_alt["winning_score"],
        "true_author_margin": scores[true_author] - highest_alt["winning_score"],
    }


def _validate_profiles(dataset: dict, authors: list[str]) -> list[dict]:
    rows = dataset.get("profile_identities")
    if not isinstance(rows, list):
        raise ValueError("profile_identities must be a list")
    by_author: dict[str, dict] = {}
    public_rows: list[dict] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"profile_identities[{index}] must be an object")
        author = str(row.get("author") or "").strip()
        if author in by_author:
            raise ValueError(f"duplicate profile identity for {author}")
        if author not in authors:
            raise ValueError(f"unknown profile author: {author}")
        identity = str(row.get("profile_identity") or "").strip()
        if not identity:
            raise ValueError(f"profile identity is required for {author}")
        source_groups = sorted({str(value) for value in row.get("source_groups", []) if str(value)})
        if not source_groups:
            raise ValueError(f"profile source_groups are required for {author}")
        public = {
            "author": author,
            "profile_identity": identity,
            "source_groups": source_groups,
            "source_group_count": len(source_groups),
            "word_count": int(row.get("word_count", 0)),
        }
        if public["word_count"] <= 0:
            raise ValueError(f"profile word_count must be positive for {author}")
        if row.get("canonical_hash_set_sha256") is not None:
            public["canonical_hash_set_sha256"] = _sha256(
                row["canonical_hash_set_sha256"],
                field=f"profile_identities[{index}].canonical_hash_set_sha256",
            )
        by_author[author] = public
        public_rows.append(public)
    if set(by_author) != set(authors):
        raise ValueError("profile_identities must contain exactly one row per author")
    return sorted(public_rows, key=lambda row: row["author"])


def _validate_profile_matrix(dataset: dict, authors: list[str]) -> dict | None:
    matrix = dataset.get("profile_cosine_matrix")
    if matrix is None:
        return None
    if not isinstance(matrix, dict) or set(matrix) != set(authors):
        raise ValueError("profile_cosine_matrix must contain exactly the authors")
    normalized: dict[str, dict[str, float]] = {}
    for author in authors:
        row = matrix.get(author)
        if not isinstance(row, dict) or set(row) != set(authors):
            raise ValueError(f"profile_cosine_matrix row mismatch for {author}")
        normalized[author] = {
            other: _finite_score(
                row[other], field=f"profile_cosine_matrix.{author}.{other}"
            )
            for other in authors
        }
    for author in authors:
        if not math.isclose(normalized[author][author], 1.0, rel_tol=0.0, abs_tol=1e-6):
            raise ValueError(f"profile cosine diagonal must be 1 for {author}")
        for other in authors:
            if not math.isclose(
                normalized[author][other],
                normalized[other][author],
                rel_tol=0.0,
                abs_tol=1e-9,
            ):
                raise ValueError(f"profile cosine matrix is not symmetric: {author}/{other}")
    return normalized


def _summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "minimum": None,
            "maximum": None,
        }
    return {
        "count": len(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "minimum": min(values),
        "maximum": max(values),
    }


def _analyze_originals(
    dataset: dict,
    authors: list[str],
    owner: str,
    neighbors: set[str],
    eligible_literal: str,
) -> tuple[list[dict], dict]:
    originals = dataset.get("originals")
    if not isinstance(originals, list) or not originals:
        raise ValueError("originals must be a non-empty list")

    sample_ids: set[str] = set()
    rows: list[dict] = []
    confusion = {
        true: {predicted: 0 for predicted in authors} for true in authors
    }
    highest_alternative_counts: dict[str, collections.Counter[str]] = {
        author: collections.Counter() for author in authors
    }
    margins_by_author: dict[str, list[float]] = {author: [] for author in authors}
    margins_by_source_group: dict[str, list[float]] = collections.defaultdict(list)
    alternative_gaps: dict[tuple[str, str], list[float]] = collections.defaultdict(list)

    for index, raw in enumerate(originals):
        if not isinstance(raw, dict):
            raise ValueError(f"originals[{index}] must be an object")
        sample_id = str(raw.get("sample_id") or "").strip()
        if not sample_id or sample_id in sample_ids:
            raise ValueError("original sample_ids must be unique non-empty strings")
        sample_ids.add(sample_id)
        true_author = str(raw.get("true_author") or "").strip()
        if true_author not in authors:
            raise ValueError(f"unknown true_author for {sample_id}: {true_author}")
        source_group = str(raw.get("source_group") or "").strip()
        register = str(raw.get("register") or "").strip()
        if not source_group or not register:
            raise ValueError(f"source_group and register are required for {sample_id}")
        scores = _scores(raw, authors)
        prediction = _prediction(scores)
        true_diag = _true_author_diagnostic(scores, true_author)
        reliability_status = str(raw.get("original_reliability_status") or "").strip()
        if not reliability_status:
            raise ValueError(f"original_reliability_status is required for {sample_id}")
        eligible = reliability_status == eligible_literal
        if eligible and (
            prediction["winner"] != true_author or prediction["top_tie"]
        ):
            raise ValueError(
                f"eligible original must be uniquely attributed to its true author: {sample_id}"
            )

        confusion[true_author][prediction["winner"]] += 1
        highest_alt = str(true_diag["highest_alternative"])
        highest_alternative_counts[true_author][highest_alt] += 1
        margin = float(true_diag["true_author_margin"])
        margins_by_author[true_author].append(margin)
        margins_by_source_group[source_group].append(margin)
        for alternative in authors:
            if alternative == true_author:
                continue
            alternative_gaps[(true_author, alternative)].append(
                scores[true_author] - scores[alternative]
            )

        row = {
            "sample_id": sample_id,
            "true_author": true_author,
            "source_group": source_group,
            "register": register,
            "canonical_sha256": _sha256(
                raw.get("canonical_sha256"),
                field=f"originals[{index}].canonical_sha256",
            ),
            "word_count": int(raw.get("word_count", 0)),
            "scores_by_author": scores,
            "prediction": prediction,
            "true_author_diagnostic": true_diag,
            "original_reliability_status": reliability_status,
            "eligible_for_rewrite_degradation_interpretation": eligible,
            "winner_is_declared_owner_neighbor": bool(
                true_author == owner and prediction["winner"] in neighbors
            ),
            "highest_alternative_is_declared_owner_neighbor": bool(
                true_author == owner and highest_alt in neighbors
            ),
        }
        if row["word_count"] <= 0:
            raise ValueError(f"word_count must be positive for {sample_id}")
        rows.append(row)

    per_author = {}
    hard_negative_rankings = {}
    for true_author in authors:
        author_rows = [row for row in rows if row["true_author"] == true_author]
        correct = sum(
            1
            for row in author_rows
            if row["prediction"]["winner"] == true_author
            and not row["prediction"]["top_tie"]
        )
        per_author[true_author] = {
            "original_count": len(author_rows),
            "correct_unique_count": correct,
            "accuracy": correct / len(author_rows) if author_rows else None,
            "eligible_count": sum(
                1
                for row in author_rows
                if row["eligible_for_rewrite_degradation_interpretation"]
            ),
            "true_author_margin": _summary(margins_by_author[true_author]),
        }
        ranking = []
        for alternative in authors:
            if alternative == true_author:
                continue
            gaps = alternative_gaps[(true_author, alternative)]
            ranking.append(
                {
                    "alternative_author": alternative,
                    "times_highest_alternative": highest_alternative_counts[true_author][
                        alternative
                    ],
                    "times_predicted_instead_of_true_author": confusion[true_author][
                        alternative
                    ],
                    "true_minus_alternative_score_gap": _summary(gaps),
                }
            )
        ranking.sort(
            key=lambda row: (
                -int(row["times_predicted_instead_of_true_author"]),
                -int(row["times_highest_alternative"]),
                float(row["true_minus_alternative_score_gap"]["mean"]),
                str(row["alternative_author"]),
            )
        )
        hard_negative_rankings[true_author] = ranking

    owner_rows = [row for row in rows if row["true_author"] == owner]
    neighbor_confusions = sum(
        1
        for row in owner_rows
        if row["prediction"]["winner"] in neighbors
        and row["prediction"]["winner"] != owner
    )
    owner_neighbor_summary = {
        "owner_author": owner,
        "declared_neighbors": sorted(neighbors),
        "owner_original_count": len(owner_rows),
        "owner_to_declared_neighbor_confusion_count": neighbor_confusions,
        "owner_to_declared_neighbor_confusion_rate": (
            neighbor_confusions / len(owner_rows) if owner_rows else None
        ),
        "declared_neighbor_highest_alternative_count": sum(
            1
            for row in owner_rows
            if row["true_author_diagnostic"]["highest_alternative"] in neighbors
        ),
    }

    aggregate = {
        "original_count": len(rows),
        "eligible_original_count": sum(
            1
            for row in rows
            if row["eligible_for_rewrite_degradation_interpretation"]
        ),
        "confusion_matrix": confusion,
        "per_author": per_author,
        "true_author_margin_by_source_group": {
            source_group: _summary(values)
            for source_group, values in sorted(margins_by_source_group.items())
        },
        "hard_negative_rankings": hard_negative_rankings,
        "owner_neighbor_summary": owner_neighbor_summary,
    }
    return rows, aggregate


def _analyze_rewrites(
    dataset: dict,
    authors: list[str],
    owner: str,
    neighbors: set[str],
    originals: list[dict],
    eligible_literal: str,
) -> tuple[list[dict], dict]:
    rewrites = dataset.get("rewrites", [])
    if rewrites is None:
        rewrites = []
    if not isinstance(rewrites, list):
        raise ValueError("rewrites must be a list")
    originals_by_id = {row["sample_id"]: row for row in originals}
    candidate_ids: set[str] = set()
    rows: list[dict] = []

    for index, raw in enumerate(rewrites):
        if not isinstance(raw, dict):
            raise ValueError(f"rewrites[{index}] must be an object")
        candidate_id = str(raw.get("candidate_id") or "").strip()
        if not candidate_id or candidate_id in candidate_ids:
            raise ValueError("rewrite candidate_ids must be unique non-empty strings")
        candidate_ids.add(candidate_id)
        original_id = str(raw.get("original_sample_id") or "").strip()
        original = originals_by_id.get(original_id)
        if original is None:
            raise ValueError(f"rewrite references unknown original: {original_id}")
        scores = _scores(raw, authors)
        prediction = _prediction(scores)
        true_author = str(original["true_author"])
        true_diag = _true_author_diagnostic(scores, true_author)
        original_scores = original["scores_by_author"]
        score_deltas = {
            author: scores[author] - original_scores[author] for author in authors
        }
        eligible = (
            original["original_reliability_status"] == eligible_literal
            and original["prediction"]["winner"] == true_author
            and not original["prediction"]["top_tie"]
        )
        if not eligible:
            status = "not-eligible-original-ambiguous-or-insufficient"
        elif prediction["winner"] == true_author and not prediction["top_tie"]:
            status = "eligible-no-top1-attribution-loss"
        else:
            status = "eligible-top1-attribution-loss-observation"

        row = {
            "candidate_id": candidate_id,
            "original_sample_id": original_id,
            "true_author": true_author,
            "source_group": original["source_group"],
            "register": original["register"],
            "edit_condition": str(raw.get("edit_condition") or "").strip(),
            "edit_dose": str(raw.get("edit_dose") or "").strip(),
            "canonical_sha256": _sha256(
                raw.get("canonical_sha256"),
                field=f"rewrites[{index}].canonical_sha256",
            ),
            "word_count": int(raw.get("word_count", 0)),
            "scores_by_author": scores,
            "score_deltas_by_author": score_deltas,
            "prediction": prediction,
            "true_author_diagnostic": true_diag,
            "target_score_delta": score_deltas[true_author],
            "target_margin_delta": (
                float(true_diag["true_author_margin"])
                - float(original["true_author_diagnostic"]["true_author_margin"])
            ),
            "candidate_winner_is_declared_owner_neighbor": bool(
                true_author == owner and prediction["winner"] in neighbors
            ),
            "winning_alternative_was_original_highest_alternative": bool(
                prediction["winner"]
                == original["true_author_diagnostic"]["highest_alternative"]
            ),
            "eligible_for_rewrite_degradation_interpretation": eligible,
            "attribution_observation_status": status,
        }
        if not row["edit_condition"] or not row["edit_dose"]:
            raise ValueError(f"edit_condition and edit_dose are required for {candidate_id}")
        if row["word_count"] <= 0:
            raise ValueError(f"word_count must be positive for {candidate_id}")
        rows.append(row)

    eligible_rows = [
        row for row in rows if row["eligible_for_rewrite_degradation_interpretation"]
    ]
    loss_rows = [
        row
        for row in eligible_rows
        if row["attribution_observation_status"]
        == "eligible-top1-attribution-loss-observation"
    ]
    aggregate = {
        "rewrite_count": len(rows),
        "eligible_rewrite_count": len(eligible_rows),
        "eligible_top1_attribution_loss_observation_count": len(loss_rows),
        "eligible_top1_attribution_loss_to_declared_owner_neighbor_count": sum(
            1
            for row in loss_rows
            if row["candidate_winner_is_declared_owner_neighbor"]
        ),
        "target_score_delta": _summary(
            [float(row["target_score_delta"]) for row in rows]
        ),
        "target_margin_delta": _summary(
            [float(row["target_margin_delta"]) for row in rows]
        ),
        "ier_computed": False,
        "ier_reason": "This diagnostic does not compute IER. IER requires an authorized aligned condition with reliably attributable originals and a registered attribution-accuracy comparison.",
    }
    return rows, aggregate


def analyze_author_neighborhood(dataset: dict, spec: dict) -> dict:
    _scan_forbidden_keys(dataset)
    _scan_forbidden_keys(spec)
    if dataset.get("schema_version") != 1:
        raise ValueError("dataset schema_version must be 1")
    if spec.get("schema_version") != 1:
        raise ValueError("spec schema_version must be 1")

    authors, owner, neighbors = _validate_authors(dataset, spec)
    profiles = _validate_profiles(dataset, authors)
    profile_matrix = _validate_profile_matrix(dataset, authors)
    eligible_literal = str(
        spec["reliability_boundary"]["eligible_status_literal"]
    )
    originals, original_aggregate = _analyze_originals(
        dataset, authors, owner, neighbors, eligible_literal
    )
    rewrites, rewrite_aggregate = _analyze_rewrites(
        dataset, authors, owner, neighbors, originals, eligible_literal
    )

    receipt = {
        "schema_version": 1,
        "diagnostic_status": "natural-author-neighborhood-diagnostic-not-IER",
        "condition_id": str(dataset.get("condition_id") or "").strip(),
        "instrument": dataset.get("instrument"),
        "authors": authors,
        "owner_author": owner,
        "declared_neighbor_hypotheses": sorted(neighbors),
        "profile_identities": profiles,
        "profile_cosine_matrix": profile_matrix,
        "originals": originals,
        "original_aggregate": original_aggregate,
        "rewrites": rewrites,
        "rewrite_aggregate": rewrite_aggregate,
        "interpretation_guardrails": spec.get("interpretation_guardrails", []),
        "raw_or_canonical_prose_in_output": False,
        "embeddings_in_output": False,
        "operational_threshold_authorized": False,
        "validated_for_register": False,
    }
    if not receipt["condition_id"]:
        raise ValueError("condition_id is required")
    if not isinstance(receipt["instrument"], dict) or not receipt["instrument"]:
        raise ValueError("instrument must be a non-empty object")
    _scan_forbidden_keys(receipt)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m pangram_lab.author_neighborhood"
    )
    parser.add_argument("dataset")
    parser.add_argument(
        "--spec",
        default="state/IDIOLECT-AUTHOR-NEIGHBORHOOD-DIAGNOSTIC-SPEC-2026-08-18.json",
    )
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    try:
        dataset = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
        receipt = analyze_author_neighborhood(dataset, spec)
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
