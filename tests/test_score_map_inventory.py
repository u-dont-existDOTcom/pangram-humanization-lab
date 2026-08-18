import json
import zipfile
from pathlib import Path

from pangram_lab.score_map_inventory import inventory_inputs, inventory_json


AUTHORS = ["Joel Rosenblum", "Stian Gudmundsen Høiland", "David Vardy"]


def test_inventory_finds_exact_numeric_author_map_with_nearest_metadata():
    data = {
        "folds": [
            {
                "source_group": "shared-thread",
                "predictions": [
                    {
                        "sample_id": "joel-one",
                        "speaker": "Joel Rosenblum",
                        "word_count": 300,
                        "canonical_sha256": "a" * 64,
                        "cosines": {
                            "Joel Rosenblum": 0.9,
                            "Stian Gudmundsen Høiland": 0.8,
                            "David Vardy": 0.4,
                        },
                    }
                ],
            }
        ]
    }
    rows = inventory_json(data, source_name="fixture.json", authors=AUTHORS)
    assert len(rows) == 1
    row = rows[0]
    assert row["score_field"] == "cosines"
    assert row["classification"] == "natural-original-or-profile-candidate"
    assert row["metadata"]["sample_id"] == "joel-one"
    assert row["metadata"]["source_group"] == "shared-thread"
    assert row["scores_by_author"]["Stian Gudmundsen Høiland"] == 0.8


def test_inventory_rejects_partial_or_nonnumeric_maps_by_omission():
    data = {
        "partial": {
            "Joel Rosenblum": 0.9,
            "Stian Gudmundsen Høiland": 0.8,
        },
        "nonnumeric": {
            "Joel Rosenblum": 0.9,
            "Stian Gudmundsen Høiland": 0.8,
            "David Vardy": "not-a-number",
        },
    }
    assert inventory_json(data, source_name="fixture.json", authors=AUTHORS) == []


def test_candidate_metadata_changes_classification():
    data = {
        "candidate_id": "rewrite-one",
        "pair_id": "pair-one",
        "scores_by_author": {
            "Joel Rosenblum": 0.91,
            "Stian Gudmundsen Høiland": 0.92,
            "David Vardy": 0.3,
        },
    }
    rows = inventory_json(data, source_name="fixture.json", authors=AUTHORS)
    assert rows[0]["classification"] == "aligned-or-transformation-candidate"


def test_zip_inventory_is_metadata_only(tmp_path: Path):
    archive_path = tmp_path / "artifact.zip"
    payload = {
        "sample_id": "joel-two",
        "true_author": "Joel Rosenblum",
        "scores_by_author": {
            "Joel Rosenblum": 0.88,
            "Stian Gudmundsen Høiland": 0.84,
            "David Vardy": 0.22,
        },
    }
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("receipt.json", json.dumps(payload))
        archive.writestr("ignored.txt", "raw prose is not parsed or returned")

    receipt = inventory_inputs([archive_path], authors=AUTHORS)
    assert receipt["score_map_count"] == 1
    assert receipt["errors"] == []
    assert receipt["raw_or_canonical_prose_in_output"] is False
    assert receipt["embeddings_in_output"] is False
    encoded = json.dumps(receipt)
    assert "raw prose is not parsed or returned" not in encoded


def test_missing_and_unsupported_inputs_are_recorded(tmp_path: Path):
    unsupported = tmp_path / "input.txt"
    unsupported.write_text("ignored", encoding="utf-8")
    receipt = inventory_inputs(
        [tmp_path / "missing.json", unsupported], authors=AUTHORS
    )
    assert receipt["score_map_count"] == 0
    assert {row["error"] for row in receipt["errors"]} == {
        "file-not-found",
        "unsupported-file-type",
    }


def test_author_list_must_be_unique_and_nonempty():
    try:
        inventory_inputs([], authors=["Joel", "Joel"])
    except ValueError as exc:
        assert "unique" in str(exc)
    else:
        raise AssertionError("duplicate authors should fail")
