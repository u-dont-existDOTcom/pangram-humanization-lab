#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any


FAMILY = Path(
    "state/experiments/somatic-r15-housemate-research-direct-reconstruction-20260831"
)
OUTPUT = FAMILY / "RESULT-PACKET.json"
GUI_ROOT = Path("state/gui-runs/pangram-4")
H0_PACKET = Path(
    "state/experiments/somatic-r15-housemate-nextday-green-research-tail-20260831/"
    "RESULT-PACKET-COMPONENTS-CDE.json"
)
ARTICLE_ROOT = Path(
    os.environ.get(
        "SOMATIC_ARTICLE_WORKTREE",
        "/mnt/hdd/home/joel/Téléchargements/joel-articles/canonical/worktrees/"
        "somatic-r15-clean-continuation-20260830",
    )
)
INPUT_ROOT = ARTICLE_ROOT / "tasks/somatic-r15-clean-continuation-20260830/surface-experiment-013"
CELLS = {
    "A": {
        "filename": "A-green-literature-plus-direct-claims-and-outcome-same-paragraph.txt",
        "sha": "77750e5e7e87d131c7e7701070edf3286fa7a67402a8fea22f26d9dcacbeff9d",
        "words": 429,
        "characters": 2422,
        "bytes": 2422,
        "fractions": {"human": 0.7687525749, "ai": 0.2312474102, "ai_assisted": 0.0},
        "windows": [(0, 1855, "Human", "High"), (1855, 2413, "AI-Generated", "High")],
    },
    "B": {
        "filename": "B-green-literature-plus-direct-claims-and-outcome-split-paragraphs.txt",
        "sha": "6ced58a1558b21164704e874a64651e62ed72ce1a269c1065044b8787ae7e564",
        "words": 429,
        "characters": 2424,
        "bytes": 2424,
        "fractions": {"human": 0.7687525749, "ai": 0.2312474102, "ai_assisted": 0.0},
        "windows": [(0, 1855, "Human", "High"), (1855, 2413, "AI-Generated", "High")],
    },
    "C": {
        "filename": "C-green-literature-plus-direct-community-claims-only.txt",
        "sha": "f110f587947534e95ca3f32df936b0a3d213ed5fb3946d0c332274691345f3d7",
        "words": 399,
        "characters": 2268,
        "bytes": 2268,
        "fractions": {"human": 0.82115978, "ai": 0.1788401902, "ai_assisted": 0.0},
        "windows": [(0, 1855, "Human", "High"), (1855, 2259, "AI-Generated", "High")],
    },
    "D": {
        "filename": "D-green-literature-plus-direct-patterns-outcome-only.txt",
        "sha": "29dc7e28c5168835f5a5067dddbd0f9d59a4ef5c27e46751b05bd2db57e28465",
        "words": 395,
        "characters": 2190,
        "bytes": 2190,
        "fractions": {"human": 0.4502521753, "ai": 0.5497478247, "ai_assisted": 0.0},
        "windows": [
            (0, 224, "AI-Generated", "Medium"),
            (224, 1206, "Human", "High"),
            (1206, 2181, "AI-Generated", "High"),
        ],
    },
}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} is not a JSON object")
    return value


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def fractions(result: dict[str, Any]) -> dict[str, float]:
    summary = result["summary"]
    return {
        "human": float(summary["fraction_human"]),
        "ai": float(summary["fraction_ai"]),
        "ai_assisted": float(summary["fraction_ai_assisted"]),
    }


def delta(left: dict[str, float], right: dict[str, float]) -> dict[str, float]:
    return {
        "fraction_human": left["human"] - right["human"],
        "fraction_ai": left["ai"] - right["ai"],
        "fraction_ai_assisted": left["ai_assisted"] - right["ai_assisted"],
    }


def window_metadata(localization: dict[str, Any]) -> list[dict[str, Any]]:
    windows: list[dict[str, Any]] = []
    for shape in localization["unresolved_candidate_shapes"]:
        path = shape.get("field_path")
        if not (
            isinstance(path, list)
            and len(path) == 4
            and path[:3] == ["response", "in_page", "windows"]
        ):
            continue
        metadata = shape.get("scalar_metadata")
        if not isinstance(metadata, dict) or "window_index" not in metadata:
            continue
        windows.append(
            {
                **metadata,
                "text_persisted": False,
                "text_field_length": int(shape["text_field_lengths"]["text"]),
                "transport_binding": shape["reason"],
            }
        )
    windows.sort(key=lambda item: int(item["window_index"]))
    return windows


def main() -> int:
    if file_sha256(H0_PACKET) != "4ba1c19c7a7baccc99539000cec28369d7da23b86d09c79282077923cafd33c2":
        raise RuntimeError("H0 source packet hash mismatch")
    h0_source = read_json(H0_PACKET)
    h0 = h0_source["variants"]["C"]
    h0_values = fractions(h0["result"])
    if not (
        h0_source["family_state"] == "CLOSED_6_OF_6_COMPONENT_MAP_COMPLETE"
        and h0["input_sha256"]
        == "209b33a716848584103a87cde0553d4c50e30a164beb3345b5f37b76cfa51419"
        and h0_values == {"human": 1.0, "ai": 0.0, "ai_assisted": 0.0}
        and h0["result"]["detector_version"] == "4.0"
        and h0["result"]["detector_stage"] == "STAGE_SUCCESS"
        and h0["history_api_exact_identity"]["transport_match_mode"] == "exact_utf8"
    ):
        raise RuntimeError("H0 reuse authority mismatch")

    variants: dict[str, Any] = {}
    result_table: dict[str, Any] = {"H0": h0_values}
    source_bundle: dict[str, Any] = {"H0": h0}
    for cell, spec in CELLS.items():
        sha = str(spec["sha"])
        input_path = INPUT_ROOT / str(spec["filename"])
        raw = input_path.read_bytes()
        text = raw.decode("utf-8")
        identity = {
            "whitespace_words": len(text.split()),
            "unicode_characters": len(text),
            "utf8_bytes": len(raw),
            "terminal_newline": raw.endswith(b"\n"),
        }
        expected_identity = {
            "whitespace_words": spec["words"],
            "unicode_characters": spec["characters"],
            "utf8_bytes": spec["bytes"],
            "terminal_newline": False,
        }
        if sha256_bytes(raw) != sha or identity != expected_identity:
            raise RuntimeError(f"variant {cell} input identity mismatch")

        receipt = read_json(GUI_ROOT / sha / "result.json")
        localization = read_json(GUI_ROOT / sha / "localization.json")
        result = receipt["parsed"]
        values = fractions(result)
        exact_identity = receipt["history_api_exact_identity"]
        windows = window_metadata(localization)
        observed_windows = [
            (item["start_index"], item["end_index"], item["label"], item["confidence"])
            for item in windows
        ]
        if not (
            receipt["status"] == "complete"
            and receipt["input_sha256"] == sha
            and receipt["detector_version"] == "4.0"
            and result["detector_stage"] == "STAGE_SUCCESS"
            and values == spec["fractions"]
            and exact_identity["authorized_text_sha256"] == sha
            and exact_identity["stored_text_sha256"] == sha
            and exact_identity["transport_match_mode"] == "exact_utf8"
            and localization["input_sha256"] == sha
            and localization["detector_submission_attempted"] is False
            and localization["history_record_identity"] == exact_identity
            and observed_windows == spec["windows"]
        ):
            raise RuntimeError(f"variant {cell} failed exact detector gates")

        source_bundle[cell] = {"result": receipt, "localization": localization}
        variants[cell] = {
            "classification_before_action": "EXACT_GUI_NEVER_SUBMITTED",
            "classification_after_action": "EXACT_GUI_RESULT_EXISTS",
            "input_path": str(input_path.relative_to(ARTICLE_ROOT)),
            "input_sha256": sha,
            "input_identity": identity,
            "detector_submission_attempted": True,
            "captured_at_utc": receipt["captured_at_utc"],
            "prediction": exact_identity["record_prediction"],
            "prediction_short": result["prediction_short"],
            "headline": result["headline"],
            "confidence": {
                "overall": None,
                "window_levels": [item["confidence"] for item in windows],
            },
            "history_api_exact_identity": exact_identity,
            "result": result,
            "window_metadata": windows,
            "localization": {
                "status": localization["status"],
                "localized_span_count": localization["localized_span_count"],
                "validated_full_overall_window_count": localization[
                    "validated_full_overall_window_count"
                ],
                "all_returned_window_metadata_recovered": True,
                "full_window_text_persisted": False,
                "history_list_candidate_count": localization["history_list_candidate_count"],
                "detector_submission_attempted": False,
            },
            "report_body_sha256": receipt["report_body_sha256"],
            "report_pdf_sha256": receipt["report_pdf_sha256"],
            "reservation": receipt["submission_reservation"],
        }
        result_table[cell] = values

    rendered_sources = json.dumps(source_bundle)
    if "https://www.pangram.com/history/" in rendered_sources.replace(
        "https://www.pangram.com/history/<uuid>", ""
    ):
        raise RuntimeError("private History route present")

    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    packet = {
        "format": "somatic-r15-housemate-research-direct-result-v1",
        "directive_id": "SOMATIC-R15-SURFACE-013",
        "family": "somatic-r15-housemate-research-direct-reconstruction-20260831",
        "family_state": "CLOSED_A_B_C_D_COMPLETE_BELOW_HUMAN_1_0",
        "detector": {
            "branch": "task/somatic-r15-exact-recovery-20260830",
            "model": "pangram-4",
            "required_version": "4.0",
            "starting_head": "957dbb45d494313b2c65e59402d4ad013a0f4194",
            "after_measurements_localizations_and_recovery_fix_before_packet": head,
        },
        "article_authority": {
            "branch": "task/somatic-r15-clean-continuation-20260830",
            "packet_head": "186f57725361672a2b9b494d009efdf061901437",
            "candidate_sha256": "1e08284ce544b851b516eebdf38f3f8efb2497e477a0104270880f49aab7d81e",
            "registered_master_sha256": "1e7e94717f40e7a4de77974a896f600a1bf2769d9c1846cbe84275e136ff5202",
        },
        "known_human_control": {
            "classification": "EXACT_GUI_RESULT_EXISTS_REUSED",
            "existing_results_reused": 1,
            "source_packet": str(H0_PACKET),
            "source_packet_sha256": file_sha256(H0_PACKET),
            "identity": h0["input_identity"],
            "input_sha256": h0["input_sha256"],
            "prediction": h0["prediction"],
            "prediction_short": h0["prediction_short"],
            "headline": h0["headline"],
            "confidence": {"overall": None, "window_levels": ["High"]},
            "history_api_exact_identity": h0["history_api_exact_identity"],
            "result": h0["result"],
            "window_metadata": h0["window_metadata"],
        },
        "variants": variants,
        "fraction_table": result_table,
        "deltas": {
            "H0_to_A": delta(result_table["A"], h0_values),
            "A_to_B": delta(result_table["B"], result_table["A"]),
            "H0_to_C": delta(result_table["C"], h0_values),
            "H0_to_D": delta(result_table["D"], h0_values),
        },
        "conditional_cells": {
            "A": "EXECUTED_COMPLETE_BELOW_HUMAN_1_0",
            "B": "EXECUTED_COMPLETE_BELOW_HUMAN_1_0",
            "C": "EXECUTED_COMPLETE_BELOW_HUMAN_1_0",
            "D": "EXECUTED_COMPLETE_BELOW_HUMAN_1_0",
            "unexecuted": [],
        },
        "accounting": {
            "existing_results_reused": 1,
            "new_results": 4,
            "cache_hits_before_action": 0,
            "reservations": 4,
            "history_recoveries_before_click": 0,
            "read_only_localizations": 4,
            "new_api_calls": 0,
            "new_short_gui_clicks": 4,
            "whole_document_calls": 0,
            "force_overrides": 0,
            "article_mutations": 0,
            "registered_master_mutations": 0,
        },
        "ci_disposition": {
            "FULL_HISTORY_FIX": "PASS",
            "REMAINING_VALIDATOR_FINDINGS": "PRE_EXISTING_UNRELATED_MERGE_DEBT",
            "MERGE_BLOCKED_UNTIL_RECONCILED": "YES",
        },
        "article_application_performed": False,
        "final_whole_document_measurement_performed": False,
        "privacy": "NO_PRIVATE_HISTORY_URL_UUID_CREDENTIAL_COOKIE_STORAGE_OR_UNRELATED_TEXT_PERSISTED",
    }
    FAMILY.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "family_state": packet["family_state"],
                "fraction_table": result_table,
                "head": head,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
