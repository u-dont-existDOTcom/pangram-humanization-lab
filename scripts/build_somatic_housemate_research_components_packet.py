#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


FAMILY = Path(
    "state/experiments/somatic-r15-housemate-nextday-green-research-tail-20260831"
)
OUTPUT = FAMILY / "RESULT-PACKET-COMPONENTS-CDE.json"
BASE_PACKET = FAMILY / "RESULT-PACKET.json"
GUI_ROOT = Path("state/gui-runs/pangram-4")
CELLS = {
    "C": {
        "sha": "209b33a716848584103a87cde0553d4c50e30a164beb3345b5f37b76cfa51419",
        "words": 365,
        "characters": 2036,
        "bytes": 2036,
        "fractions": {"human": 1.0, "ai": 0.0, "ai_assisted": 0.0},
        "offsets": [(0, 2027)],
    },
    "D": {
        "sha": "45ee706e0d3d75067d86ab5c5b189589f1c7aa4bd5526a5d38fb1466a39b7d17",
        "words": 379,
        "characters": 2160,
        "bytes": 2160,
        "fractions": {
            "human": 0.8623895645,
            "ai": 0.1376104206,
            "ai_assisted": 0.0,
        },
        "offsets": [(0, 1855), (1855, 2151)],
    },
    "E": {
        "sha": "b5548fd2ca42e6cbeb7bd06fb67fd6a19c53e42d4b8af60464a755a3d9621dfd",
        "words": 373,
        "characters": 2086,
        "bytes": 2086,
        "fractions": {
            "human": 0.8931150436,
            "ai": 0.1068849266,
            "ai_assisted": 0.0,
        },
        "offsets": [(0, 1855), (1855, 2077)],
    },
}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} is not a JSON object")
    return value


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
    base = read_json(BASE_PACKET)
    h0_values = base["fraction_table"]["H0"]
    if not (
        base["family_state"] == "CLOSED_A_AND_B_COMPLETE_BELOW_HUMAN_1_0"
        and base["fraction_table"]["H0"]
        == {"human": 1.0, "ai": 0.0, "ai_assisted": 0.0}
        and base["fraction_table"]["A"]
        == {"human": 0.6725773215, "ai": 0.3274226785, "ai_assisted": 0.0}
        and base["fraction_table"]["B"]
        == {"human": 0.7833614945, "ai": 0.2166385204, "ai_assisted": 0.0}
    ):
        raise RuntimeError("existing H0/A/B family authority mismatch")

    variants: dict[str, Any] = {}
    result_table: dict[str, Any] = {
        "H0": base["fraction_table"]["H0"],
        "A": base["fraction_table"]["A"],
        "B": base["fraction_table"]["B"],
    }
    deltas: dict[str, Any] = {}
    source_bundle: dict[str, Any] = {"base": base}
    for cell, spec in CELLS.items():
        sha = str(spec["sha"])
        result_receipt = read_json(GUI_ROOT / sha / "result.json")
        localization = read_json(GUI_ROOT / sha / "localization.json")
        result = result_receipt["parsed"]
        values = fractions(result)
        identity = result_receipt["history_api_exact_identity"]
        windows = window_metadata(localization)
        offsets = [(item["start_index"], item["end_index"]) for item in windows]
        if not (
            result_receipt["status"] == "complete"
            and result_receipt["input_sha256"] == sha
            and result_receipt["detector_version"] == "4.0"
            and result["detector_stage"] == "STAGE_SUCCESS"
            and values == spec["fractions"]
            and identity["authorized_text_sha256"] == sha
            and identity["stored_text_sha256"] == sha
            and identity["transport_match_mode"] == "exact_utf8"
            and localization["input_sha256"] == sha
            and localization["detector_submission_attempted"] is False
            and localization["history_record_identity"] == identity
            and offsets == spec["offsets"]
            and all(item["confidence"] == "High" for item in windows)
        ):
            raise RuntimeError(f"component {cell} failed exact authority gates")
        source_bundle[cell] = {
            "result": result_receipt,
            "localization": localization,
        }
        variants[cell] = {
            "classification_before_action": "EXACT_GUI_NEVER_SUBMITTED",
            "classification": "EXACT_GUI_RESULT_EXISTS",
            "input_sha256": sha,
            "input_identity": {
                "whitespace_words": spec["words"],
                "unicode_characters": spec["characters"],
                "utf8_bytes": spec["bytes"],
                "terminal_newline": False,
            },
            "detector_submission_attempted": True,
            "captured_at_utc": result_receipt["captured_at_utc"],
            "prediction": identity["record_prediction"],
            "prediction_short": result["prediction_short"],
            "headline": result["headline"],
            "history_api_exact_identity": identity,
            "result": result,
            "window_metadata": windows,
            "localization": {
                "status": localization["status"],
                "all_window_offsets_recovered": True,
                "full_window_text_persisted": False,
                "history_list_candidate_count": localization["history_list_candidate_count"],
                "detector_submission_attempted": False,
            },
            "report_body_sha256": result_receipt["report_body_sha256"],
            "report_pdf_sha256": result_receipt["report_pdf_sha256"],
            "reservation": result_receipt["submission_reservation"],
        }
        result_table[cell] = values
        deltas[f"H0_to_{cell}"] = delta(values, h0_values)

    serialized = json.dumps(source_bundle)
    if "https://www.pangram.com/history/" in serialized.replace(
        "https://www.pangram.com/history/<uuid>", ""
    ):
        raise RuntimeError("private History route present")

    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    packet = {
        "format": "somatic-r15-housemate-research-components-result-v1",
        "directive_id": "SOMATIC-R15-SURFACE-012",
        "family": "somatic-r15-housemate-nextday-green-research-tail-20260831",
        "family_state": "CLOSED_6_OF_6_COMPONENT_MAP_COMPLETE",
        "detector": {
            "branch": "task/somatic-r15-exact-recovery-20260830",
            "model": "pangram-4",
            "required_version": "4.0",
            "starting_head": "92e0cfcc3e30f85f6f7b7ad962fd40cb9d39b0d8",
            "after_measurements_and_localizations_before_packet": head,
        },
        "article_authority": {
            "branch": "task/somatic-r15-clean-continuation-20260830",
            "packet_head": "ff5044b9e86afbc29571cbe54b6323963e5d1213",
            "candidate_sha256": "1e08284ce544b851b516eebdf38f3f8efb2497e477a0104270880f49aab7d81e",
            "registered_master_sha256": "1e7e94717f40e7a4de77974a896f600a1bf2769d9c1846cbe84275e136ff5202",
        },
        "existing_family_evidence": {
            "existing_results_reused": 3,
            "result_packet": str(BASE_PACKET),
            "result_packet_sha256": "53fd27e7f666b8dfbfde7bef7f206357477eb513f03100de7face65528465d2e",
            "fraction_table": {
                "H0": base["fraction_table"]["H0"],
                "A": base["fraction_table"]["A"],
                "B": base["fraction_table"]["B"],
            },
        },
        "variants": variants,
        "component_result_table": result_table,
        "deltas": {**deltas, "status": "C_D_E_COMPLETE"},
        "accounting": {
            "existing_results_reused": 3,
            "new_component_results": 3,
            "c_cache_hits_before_action": 0,
            "d_cache_hits_before_action": 0,
            "e_cache_hits_before_action": 0,
            "c_recent_history_candidates_inspected_before_action": 10,
            "d_recent_history_candidates_inspected_before_action": 10,
            "e_recent_history_candidates_inspected_before_action": 10,
            "c_reservations": 1,
            "d_reservations": 1,
            "e_reservations": 1,
            "c_clicks": 1,
            "d_clicks": 1,
            "e_clicks": 1,
            "read_only_localizations": 3,
            "new_api_calls": 0,
            "new_short_gui_clicks": 3,
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
    OUTPUT.write_text(
        json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "family_state": packet["family_state"],
                "component_result_table": result_table,
                "head": head,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
