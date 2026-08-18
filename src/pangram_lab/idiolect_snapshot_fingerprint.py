from __future__ import annotations

import hashlib
import json
from pathlib import Path


_REQUIRED_ROW_FIELDS = (
    "sample_id",
    "source_group",
    "speaker",
    "source_html_sha256",
    "canonical_sha256",
    "word_count",
)


def _row(role: str, value: dict) -> dict:
    missing = [key for key in _REQUIRED_ROW_FIELDS if value.get(key) in (None, "")]
    if missing:
        raise ValueError(f"{role} row {value.get('sample_id')!r} missing fields: {missing}")
    return {
        "role": role,
        "sample_id": str(value["sample_id"]),
        "source_group": str(value["source_group"]),
        "speaker": str(value["speaker"]),
        "site_group": value.get("site_group"),
        "date": value.get("date"),
        "source_html_sha256": str(value["source_html_sha256"]),
        "canonical_sha256": str(value["canonical_sha256"]),
        "word_count": int(value["word_count"]),
        "redactions": list(value.get("redactions", [])),
        "quality_flags": list(value.get("quality_flags", [])),
        "target_marker_count": int(value.get("target_marker_count", 0)),
        "other_speaker_boundary_count": int(value.get("other_speaker_boundary_count", 0)),
        "standalone_boundary_count": int(value.get("standalone_boundary_count", 0)),
        "ambiguous_single_word_line_count": int(value.get("ambiguous_single_word_line_count", 0)),
    }


def _stable_sha(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_fingerprint(
    supplement: dict,
    control: dict,
    matched: dict,
    *,
    expected_counts: dict[str, int] | None = None,
) -> dict:
    manifests = {"supplement": supplement, "control": control, "matched": matched}
    for role, manifest in manifests.items():
        if manifest.get("errors"):
            raise ValueError(f"{role} acquisition errors: {manifest['errors']}")

    rows = []
    counts = {}
    fetch_counts = {}
    for role, manifest in manifests.items():
        role_rows = [_row(role, value) for value in manifest.get("results", [])]
        counts[role] = len(role_rows)
        fetch_counts[role] = int(manifest.get("network_fetch_count", 0))
        rows.extend(role_rows)

    if expected_counts:
        for role, expected in expected_counts.items():
            actual = counts.get(role, 0)
            if actual != int(expected):
                raise ValueError(f"expected {expected} {role} rows, got {actual}")

    identities = [(row["role"], row["sample_id"]) for row in rows]
    if len(identities) != len(set(identities)):
        raise ValueError("duplicate role/sample_id identity in snapshot")

    # Every speaker extracted from the same live page during one role-level
    # acquisition must share one raw HTML hash. The named-speaker acquisition
    # cache is intended to guarantee exactly this.
    by_role_page: dict[tuple[str, str], set[str]] = {}
    for role, manifest in manifests.items():
        source_rows = manifest.get("results", [])
        for value in source_rows:
            key = (role, str(value.get("url") or value.get("source_group") or ""))
            by_role_page.setdefault(key, set()).add(str(value["source_html_sha256"]))
    inconsistent = sorted(
        {key: sorted(hashes) for key, hashes in by_role_page.items() if len(hashes) != 1}.items()
    )
    if inconsistent:
        raise ValueError(f"same-page HTML hashes disagree inside acquisition role: {inconsistent}")

    # Training-only controls and Joel supplements must not accidentally reuse a
    # held-out matched source group.
    groups = {
        role: {row["source_group"] for row in rows if row["role"] == role}
        for role in manifests
    }
    overlap_control = sorted(groups["control"] & groups["matched"])
    overlap_supplement = sorted(groups["supplement"] & groups["matched"])
    if overlap_control or overlap_supplement:
        raise ValueError(
            "training-only source-group overlap with held-out matched set: "
            f"control={overlap_control}, supplement={overlap_supplement}"
        )

    rows = sorted(
        rows,
        key=lambda row: (
            row["role"],
            row["source_group"],
            row["speaker"],
            row["sample_id"],
        ),
    )
    snapshot_sha256 = _stable_sha(rows)
    source_html_hashes = sorted({row["source_html_sha256"] for row in rows})
    canonical_hashes = sorted({row["canonical_sha256"] for row in rows})
    return {
        "schema_version": 1,
        "raw_or_canonical_prose_in_output": False,
        "snapshot_sha256": snapshot_sha256,
        "rows": rows,
        "row_counts": counts,
        "network_fetch_counts": fetch_counts,
        "unique_source_html_sha256_count": len(source_html_hashes),
        "source_html_hash_set_sha256": _stable_sha(source_html_hashes),
        "canonical_hash_set_sha256": _stable_sha(canonical_hashes),
        "source_group_overlap": {
            "control_vs_matched": [],
            "supplement_vs_matched": [],
        },
        "same_page_snapshot_consistent_within_role": True,
    }


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="python -m pangram_lab.idiolect_snapshot_fingerprint")
    parser.add_argument("--supplement-manifest", required=True)
    parser.add_argument("--control-manifest", required=True)
    parser.add_argument("--matched-manifest", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--expected-supplement", type=int, default=2)
    parser.add_argument("--expected-control", type=int, default=12)
    parser.add_argument("--expected-matched", type=int, default=11)
    args = parser.parse_args(argv)

    supplement = json.loads(Path(args.supplement_manifest).read_text(encoding="utf-8"))
    control = json.loads(Path(args.control_manifest).read_text(encoding="utf-8"))
    matched = json.loads(Path(args.matched_manifest).read_text(encoding="utf-8"))
    try:
        result = build_fingerprint(
            supplement,
            control,
            matched,
            expected_counts={
                "supplement": args.expected_supplement,
                "control": args.expected_control,
                "matched": args.expected_matched,
            },
        )
    except Exception as exc:
        print(str(exc))
        return 1
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "snapshot_sha256": result["snapshot_sha256"],
        "row_counts": result["row_counts"],
        "network_fetch_counts": result["network_fetch_counts"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
