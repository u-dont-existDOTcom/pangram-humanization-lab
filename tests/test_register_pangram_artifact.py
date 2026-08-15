from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.register_pangram_artifact import RegistrationError, build_registration


def test_build_registration_preserves_literal_text_and_binds_spec_hash(tmp_path: Path) -> None:
    text_path = tmp_path / "visible.txt"
    text = "Exact visible text.\nSecond byte-line."
    text_path.write_bytes(text.encode("utf-8"))
    expected_text_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()

    spec_bytes, request_bytes = build_registration(
        text_path=text_path,
        expected_text_sha256=expected_text_sha,
        experiment_id="romance-final-r1",
        audit_id="romance-final-audit",
        section_id="FULL_ARTICLE",
        variant_id="current-reader-visible",
        spec_path="experiments/romance-final-r1.json",
    )

    spec = json.loads(spec_bytes.decode("utf-8"))
    request = json.loads(request_bytes.decode("utf-8"))
    assert spec["format"] == "pangram-fixed-batch-v1"
    assert spec["experiment_id"] == "romance-final-r1"
    assert spec["audit_id"] == "romance-final-audit"
    assert spec["variants"] == [
        {
            "id": "current-reader-visible",
            "section_id": "FULL_ARTICLE",
            "text": text,
        }
    ]
    assert request == {
        "format": "pangram-paid-run-request-v1",
        "request_id": "romance-final-r1",
        "spec_path": "experiments/romance-final-r1.json",
        "spec_sha256": hashlib.sha256(spec_bytes).hexdigest(),
        "confirmation": "RUN_PAID_PANGRAM_FIXED_BATCH",
    }


def test_build_registration_fails_closed_on_text_hash_mismatch(tmp_path: Path) -> None:
    text_path = tmp_path / "visible.txt"
    text_path.write_text("actual", encoding="utf-8")

    with pytest.raises(RegistrationError, match="text SHA-256 mismatch"):
        build_registration(
            text_path=text_path,
            expected_text_sha256="0" * 64,
            experiment_id="romance-final-r1",
            audit_id="romance-final-audit",
            section_id="FULL_ARTICLE",
            variant_id="current-reader-visible",
            spec_path="experiments/romance-final-r1.json",
        )
