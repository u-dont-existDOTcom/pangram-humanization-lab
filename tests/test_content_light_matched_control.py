from pangram_lab import content_light_matched_control as cl


def _row(tmp_path, sample, speaker, group, text):
    path = tmp_path / f"{sample}.txt"
    path.write_text(text, encoding="utf-8")
    return {
        "sample_id": sample,
        "speaker": speaker,
        "source_group": group,
        "word_count": len(text.split()),
        "local_text_path": str(path),
    }


def test_manual_metrics_match_expected_confusion_and_f1():
    authors = ["A", "B", "C"]
    predictions = [
        {"source_group": "g1", "actual": "A", "predicted": "A"},
        {"source_group": "g1", "actual": "B", "predicted": "B"},
        {"source_group": "g2", "actual": "A", "predicted": "B"},
        {"source_group": "g2", "actual": "C", "predicted": "C"},
    ]
    result = cl._metrics(predictions, authors, iterations=100, seed=7)
    assert result["accuracy"] == 0.75
    assert result["balanced_accuracy"] == 0.833333
    assert result["macro_f1"] == 0.777778
    assert result["confusion_matrix"]["rows_actual_columns_predicted"] == [
        [1, 1, 0],
        [0, 1, 0],
        [0, 0, 1],
    ]
    assert result["group_bootstrap_accuracy_95pct"]["groups"] == 2


def test_content_light_nearest_profile_separates_strong_synthetic_styles(tmp_path):
    train = [
        _row(tmp_path, "a1", "A", "a1", "I am here, and I am there, and I am here."),
        _row(tmp_path, "a2", "A", "a2", "I am here, but I am also there, and I am here."),
        _row(tmp_path, "b1", "B", "b1", "You'd go?! You'd go?! You'd go?!"),
        _row(tmp_path, "b2", "B", "b2", "You'd stay?! You'd stay?! You'd stay?!"),
        _row(tmp_path, "c1", "C", "c1", "THESE WORDS ARE LOUD. THESE WORDS ARE LOUD."),
        _row(tmp_path, "c2", "C", "c2", "THOSE WORDS ARE LOUD. THOSE WORDS ARE LOUD."),
    ]
    test = [
        _row(tmp_path, "ta", "A", "held", "I am here, and I am there, and I am here."),
        _row(tmp_path, "tb", "B", "held", "You'd go?! You'd stay?! You'd go?!"),
        _row(tmp_path, "tc", "C", "held", "THESE WORDS ARE LOUD. THOSE WORDS ARE LOUD."),
    ]
    predictions = cl.nearest_content_light_predictions(
        train,
        test,
        authors=["A", "B", "C"],
    )
    assert [row["predicted"] for row in predictions] == ["A", "B", "C"]
    assert all(row["correct"] for row in predictions)
    assert all(set(row["cosine_scores"]) == {"A", "B", "C"} for row in predictions)


def test_tie_break_uses_author_order(tmp_path):
    same = "we are here and we are there."
    train = [
        _row(tmp_path, "a", "A", "ga", same),
        _row(tmp_path, "b", "B", "gb", same),
    ]
    test = [_row(tmp_path, "x", "A", "held", same)]
    prediction = cl.nearest_content_light_predictions(
        train,
        test,
        authors=["A", "B"],
    )[0]
    assert prediction["predicted"] == "A"
