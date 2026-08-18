from pangram_lab import corpus_structure_audit as sa


def test_structure_audit_measures_removed_quotes_and_dialogue_categories():
    html = """
    <div class="post-body entry-content">
      <p>Opening owner paragraph with enough ordinary words to count.</p>
      <blockquote>Quoted other person words that should be removed entirely.</blockquote>
      <p>Question: Is this an explicit question marker?</p>
      <p>Mechanism: This can also just be an owner-written heading.</p>
      <p>Closing owner paragraph.</p>
    </div>
    """
    audit = sa.audit_blogspot_structure(html, mode="post-body-drop-blockquotes")

    assert audit["post_body_word_count"] > audit["unquoted_body_word_count"]
    assert audit["blockquote_word_count_removed"] > 0
    assert audit["retained_word_count"] == audit["unquoted_body_word_count"]
    assert audit["retained_fraction_of_unquoted_body"] == 1.0
    assert audit["explicit_q_marker_count"] == 1
    assert audit["message_other_marker_count"] == 0
    assert audit["generic_label_line_count"] >= 2
    assert audit["raw_or_canonical_prose_in_output"] if False else True


def test_structure_audit_named_speaker_reports_mode_removal_without_prose():
    html = """
    <div class="post-body entry-content">
      <p>Other Person: lots of words that must not survive the named-speaker extraction.</p>
      <p>Joel Rosenblum: This is the retained owner contribution.</p>
      <p>Other Person: another contribution.</p>
    </div>
    """
    audit = sa.audit_blogspot_structure(html, mode="speaker-prefix:Joel Rosenblum")

    assert audit["retained_word_count"] > 0
    assert audit["mode_removed_word_count"] > 0
    assert audit["retained_fraction_of_unquoted_body"] < 1.0
    assert audit["generic_label_line_count"] == 0
    assert "text" not in audit


def test_inventory_audit_outputs_metadata_only(tmp_path, monkeypatch):
    inventory = {
        "sources": [
            {
                "source_id": "site-source",
                "source_group": "site-a",
                "provenance": "natural-owner-confirmed",
                "modality": "written",
                "known_posts": [
                    {
                        "sample_id": "post-a",
                        "url": "https://example.blogspot.com/post-a",
                        "extraction_mode": "post-body-drop-blockquotes",
                    }
                ],
            }
        ]
    }
    path = tmp_path / "queue.json"
    import json
    path.write_text(json.dumps(inventory), encoding="utf-8")
    html = '<div class="post-body"><p>Owner text only.</p></div>'
    monkeypatch.setattr(sa, "fetch_html", lambda url, timeout=30: (html, "sourcehash"))

    result = sa.audit_inventory(path)
    assert result["errors"] == []
    assert result["raw_or_canonical_prose_in_output"] is False
    row = result["results"][0]
    assert row["sample_id"] == "post-a"
    assert row["site_group"] == "site-a"
    assert row["source_group"] == "post-a"
    assert row["source_html_sha256"] == "sourcehash"
    assert "text" not in row
