from __future__ import annotations

import argparse
import json
import math
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable

_METADATA_KEYS = (
    "sample_id",
    "candidate_id",
    "pair_id",
    "original_sample_id",
    "source_group",
    "speaker",
    "true_author",
    "author",
    "word_count",
    "canonical_sha256",
    "condition",
    "condition_id",
    "variant_id",
    "prediction",
    "predicted_author",
    "register",
    "role",
)

_FORBIDDEN_OUTPUT_KEYS = {
    "raw_text",
    "canonical_text",
    "prose",
    "local_text_path",
    "embedding",
    "embeddings",
}


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _iter_objects(
    value: Any,
    *,
    path: str = "root",
    ancestors: tuple[dict[str, Any], ...] = (),
) -> Iterable[tuple[str, dict[str, Any], tuple[dict[str, Any], ...]]]:
    if isinstance(value, dict):
        yield path, value, ancestors
        next_ancestors = ancestors + (value,)
        for key, child in value.items():
            yield from _iter_objects(
                child,
                path=f"{path}.{key}",
                ancestors=next_ancestors,
            )
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _iter_objects(
                child,
                path=f"{path}[{index}]",
                ancestors=ancestors,
            )


def _nearest_metadata(
    ancestors: tuple[dict[str, Any], ...], current: dict[str, Any]
) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    for obj in (*ancestors, current):
        for key in _METADATA_KEYS:
            if key in obj:
                metadata[key] = obj[key]
    return metadata


def _classify(metadata: dict[str, Any]) -> str:
    if metadata.get("candidate_id") or metadata.get("pair_id") or metadata.get("variant_id"):
        return "aligned-or-transformation-candidate"
    if metadata.get("sample_id") and (
        metadata.get("speaker")
        or metadata.get("true_author")
        or metadata.get("author")
    ):
        return "natural-original-or-profile-candidate"
    return "unclassified-score-map"


def _scan_forbidden_output(value: Any, *, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).casefold() in _FORBIDDEN_OUTPUT_KEYS:
                raise ValueError(f"output contains forbidden key {path}.{key}")
            _scan_forbidden_output(child, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_forbidden_output(child, path=f"{path}[{index}]")


def inventory_json(
    data: Any,
    *,
    source_name: str,
    authors: list[str],
) -> list[dict[str, Any]]:
    author_set = set(authors)
    rows: list[dict[str, Any]] = []
    for object_path, obj, ancestors in _iter_objects(data):
        for field, value in obj.items():
            if not isinstance(value, dict):
                continue
            if set(value) != author_set:
                continue
            if not all(_finite_number(number) for number in value.values()):
                continue
            metadata = _nearest_metadata(ancestors, obj)
            rows.append(
                {
                    "source_name": source_name,
                    "object_path": object_path,
                    "score_field": str(field),
                    "classification": _classify(metadata),
                    "metadata": metadata,
                    "scores_by_author": {
                        author: float(value[author]) for author in authors
                    },
                }
            )
    return rows


def inventory_inputs(paths: list[Path], *, authors: list[str]) -> dict[str, Any]:
    if len(authors) < 2 or len(authors) != len(set(authors)) or any(not author for author in authors):
        raise ValueError("authors must contain at least two unique non-empty names")

    records: list[dict[str, Any]] = []
    inspected_members: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for path in paths:
        if not path.is_file():
            errors.append({"source": str(path), "error": "file-not-found"})
            continue
        if path.suffix.casefold() == ".zip":
            try:
                with zipfile.ZipFile(path) as archive:
                    for member in archive.namelist():
                        if not member.casefold().endswith(".json"):
                            continue
                        source_name = f"{path.name}:{member}"
                        try:
                            data = json.loads(archive.read(member))
                            found = inventory_json(
                                data,
                                source_name=source_name,
                                authors=authors,
                            )
                            records.extend(found)
                            inspected_members.append(
                                {
                                    "source_name": source_name,
                                    "score_map_count": len(found),
                                }
                            )
                        except Exception as exc:
                            errors.append(
                                {"source": source_name, "error": str(exc)}
                            )
            except Exception as exc:
                errors.append({"source": str(path), "error": str(exc)})
            continue

        if path.suffix.casefold() == ".json":
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                found = inventory_json(
                    data,
                    source_name=path.name,
                    authors=authors,
                )
                records.extend(found)
                inspected_members.append(
                    {"source_name": path.name, "score_map_count": len(found)}
                )
            except Exception as exc:
                errors.append({"source": str(path), "error": str(exc)})
            continue

        errors.append({"source": str(path), "error": "unsupported-file-type"})

    records.sort(
        key=lambda row: (
            row["source_name"],
            row["object_path"],
            row["score_field"],
        )
    )
    receipt = {
        "schema_version": 1,
        "status": "metadata-only-frozen-score-map-inventory",
        "authors": authors,
        "input_count": len(paths),
        "inspected_json_member_count": len(inspected_members),
        "score_map_count": len(records),
        "score_map_counts_by_classification": {
            classification: sum(
                1 for row in records if row["classification"] == classification
            )
            for classification in sorted(
                {row["classification"] for row in records}
            )
        },
        "inspected_members": inspected_members,
        "records": records,
        "errors": errors,
        "raw_or_canonical_prose_in_output": False,
        "embeddings_in_output": False,
        "interpretation": (
            "This inventory establishes where complete per-author numeric score "
            "vectors are recoverable. It does not assign reliability, classify "
            "authorship, compute IER, or authorize a new model run."
        ),
    }
    _scan_forbidden_output(receipt)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m pangram_lab.score_map_inventory"
    )
    parser.add_argument("inputs", nargs="+")
    parser.add_argument("--author", action="append", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    try:
        receipt = inventory_inputs(
            [Path(value) for value in args.inputs], authors=list(args.author)
        )
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
    return 0 if not receipt["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
