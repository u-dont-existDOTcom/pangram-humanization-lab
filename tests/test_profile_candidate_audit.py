import json

from pangram_lab import profile_candidate_audit as pa


def test_dialogue_label_tokens_return_only_prefixes_and_dedupe():
    text = """
    Question: What follows is not returned by the audit.
    Joel Rosenblum: Nor is this sentence.
    Question: Another line.
    ordinary prose: lowercase prefixes do not match the person-label rule.
    """
    assert pa.dialogue_label_tokens(text) == ["Question", "Joel Rosenblum"]


def test_candidate_audit_contains_metadata_not_prose(tmp_path):
    text_path = tmp_path / "sample.txt"
    text_path.write_text("Question: secret prose here.\nOwner prose here.\n", encoding="utf-8")
    manifest = {
        "results": [
            {
                "sample_id": "sample",
                "site_group": "site",
                "source_group": "group",
                "canonical_sha256": "abc",
                "word_count": 7,
                "redactions": {"email": 0, "phone": 0, "url": 0},
                "quality_flags": ["possible-unremoved-dialogue"],
                "local_text_path": str(text_path),
            }
        ],
        "errors": [],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    receipt = pa.audit_acquired_candidates(manifest_path)
    encoded = json.dumps(receipt)
    assert receipt["samples"][0]["dialogue_label_tokens"] == ["Question"]
    assert "secret prose" not in encoded
    assert "Owner prose" not in encoded
    assert receipt["site_totals"]["site"]["total_words"] == 7
