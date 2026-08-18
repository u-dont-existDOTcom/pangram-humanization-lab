from pangram_lab import idiolect_snapshot_fingerprint as snapshot


def _manifest(role, rows, fetches=1):
    results = []
    for index, (sample, group, speaker, page_sha, canon_sha, words) in enumerate(rows, start=1):
        results.append(
            {
                "sample_id": sample,
                "source_group": group,
                "speaker": speaker,
                "site_group": "dharma",
                "date": "2014-01-01",
                "url": f"https://example.test/{group}",
                "source_html_sha256": page_sha,
                "canonical_sha256": canon_sha,
                "word_count": words,
                "redactions": [],
                "quality_flags": [],
                "target_marker_count": 1,
                "other_speaker_boundary_count": index,
                "standalone_boundary_count": 0,
                "ambiguous_single_word_line_count": 0,
                "local_text_path": f"/tmp/{role}-{sample}.txt",
            }
        )
    return {"results": results, "errors": [], "network_fetch_count": fetches}


def test_snapshot_is_deterministic_and_excludes_runtime_paths_and_text():
    supplement = _manifest("supplement", [("s1", "sg1", "A", "a" * 64, "b" * 64, 80)])
    control = _manifest("control", [("c1", "cg1", "B", "c" * 64, "d" * 64, 90)])
    matched = _manifest(
        "matched",
        [
            ("m1", "mg1", "A", "e" * 64, "f" * 64, 100),
            ("m2", "mg1", "B", "e" * 64, "1" * 64, 110),
        ],
    )
    a = snapshot.build_fingerprint(supplement, control, matched)
    b = snapshot.build_fingerprint(supplement, control, matched)
    assert a == b
    assert len(a["snapshot_sha256"]) == 64
    assert a["same_page_snapshot_consistent_within_role"] is True
    assert all("local_text_path" not in row for row in a["rows"])
    assert all("url" not in row for row in a["rows"])
    assert all("text" not in row for row in a["rows"])


def test_snapshot_rejects_same_page_hash_disagreement():
    supplement = _manifest("supplement", [("s1", "sg1", "A", "a" * 64, "b" * 64, 80)])
    control = _manifest("control", [("c1", "cg1", "B", "c" * 64, "d" * 64, 90)])
    matched = _manifest(
        "matched",
        [
            ("m1", "mg1", "A", "e" * 64, "f" * 64, 100),
            ("m2", "mg1", "B", "9" * 64, "1" * 64, 110),
        ],
    )
    try:
        snapshot.build_fingerprint(supplement, control, matched)
    except ValueError as exc:
        assert "same-page HTML hashes disagree" in str(exc)
    else:
        raise AssertionError("expected inconsistent same-page HTML hash failure")


def test_snapshot_rejects_training_group_overlap():
    supplement = _manifest("supplement", [("s1", "sg1", "A", "a" * 64, "b" * 64, 80)])
    control = _manifest("control", [("c1", "shared", "B", "c" * 64, "d" * 64, 90)])
    matched = _manifest("matched", [("m1", "shared", "A", "e" * 64, "f" * 64, 100)])
    try:
        snapshot.build_fingerprint(supplement, control, matched)
    except ValueError as exc:
        assert "training-only source-group overlap" in str(exc)
    else:
        raise AssertionError("expected source-group overlap failure")


def test_snapshot_rejects_acquisition_errors_and_bad_counts():
    good = _manifest("supplement", [("s1", "sg1", "A", "a" * 64, "b" * 64, 80)])
    bad = {"results": [], "errors": [{"sample_id": "x", "error": "boom"}], "network_fetch_count": 1}
    try:
        snapshot.build_fingerprint(good, bad, good)
    except ValueError as exc:
        assert "control acquisition errors" in str(exc)
    else:
        raise AssertionError("expected acquisition error failure")

    control = _manifest("control", [("c1", "cg1", "B", "c" * 64, "d" * 64, 90)])
    matched = _manifest("matched", [("m1", "mg1", "A", "e" * 64, "f" * 64, 100)])
    try:
        snapshot.build_fingerprint(
            good,
            control,
            matched,
            expected_counts={"supplement": 2, "control": 1, "matched": 1},
        )
    except ValueError as exc:
        assert "expected 2 supplement rows" in str(exc)
    else:
        raise AssertionError("expected count failure")
