import json

from pangram_lab import corpus_acquire as ca


def test_blogspot_body_preserves_anchor_text_drops_quote_and_redacts_nonstyle_tokens():
    html = """
    <html><body>
      <div class="post-body entry-content">
        <p>Hello <a href="https://example.com/hidden">friend</a>.</p>
        <blockquote>Another author's quoted paragraph.</blockquote>
        <p>Email joel@example.com, call 267-270-2057, or see https://example.com/x.</p>
      </div>
      <footer>platform chrome</footer>
    </body></html>
    """
    visible = ca.extract_blogspot(html, mode="post-body-drop-blockquotes")
    canon = ca.canonicalize(visible)

    assert "Hello friend." in canon.text
    assert "quoted paragraph" not in canon.text
    assert "platform chrome" not in canon.text
    assert "joel@example.com" not in canon.text
    assert "267-270-2057" not in canon.text
    assert "https://example.com/x" not in canon.text
    assert canon.redactions == {"email": 1, "phone": 1, "url": 1}


def test_speaker_extraction_keeps_only_named_author():
    text = """
    John Ahn: other person's text
    Joel Rosenblum: First Joel thought.
    Joel Rosenblum Second Joel thought.
    Someone Else: more other text
    Joel Rosenblum: Third Joel thought.
    """
    assert ca.extract_speaker_lines(text, "Joel Rosenblum") == (
        "First Joel thought.\n\nSecond Joel thought.\n\nThird Joel thought."
    )


def test_message_by_you_extraction_removes_export_timestamp():
    text = """
    Message by You: first thought, Friday, March 8 2019, 10:35 PM
    first thought
    Message by Usman: other person's text, Friday, March 8 2019, 10:36 PM
    Message by You: second thought, Saturday, March 9 2019, 4:37 PM
    """
    assert ca.extract_message_by_you(text) == "first thought\n\nsecond thought"


def test_canonical_hash_is_stable_and_paragraph_sensitive():
    a = ca.canonicalize("One  thought.\n\nAnother thought.")
    b = ca.canonicalize("One thought.\n\nAnother thought.")
    c = ca.canonicalize("One thought. Another thought.")

    assert a.sha256 == b.sha256
    assert a.sha256 != c.sha256
    assert a.word_count == 4


def test_acquire_inventory_writes_only_canonical_text_and_metadata(tmp_path, monkeypatch):
    inventory = {
        "sources": [
            {
                "source_id": "legacy-blog",
                "source_group": "legacy-blog",
                "provenance": "natural-owner-confirmed",
                "modality": "written",
                "registers": ["polemical-irreverent"],
                "known_posts": [
                    {
                        "sample_id": "sample-one",
                        "title": "Sample one",
                        "date": "2020-01-01",
                        "url": "https://example.blogspot.com/2020/01/sample.html",
                        "extraction_mode": "post-body-drop-blockquotes",
                    }
                ],
            }
        ]
    }
    inv = tmp_path / "inventory.json"
    inv.write_text(json.dumps(inventory), encoding="utf-8")

    html = """
    <div class="post-body entry-content">
      <p>This is Joel's own paragraph with enough words to make the fixture readable.</p>
      <blockquote>This is not Joel's text.</blockquote>
    </div>
    """
    monkeypatch.setattr(ca, "fetch_html", lambda url, timeout=30: (html, "rawhash"))

    out = tmp_path / "local" / "text"
    meta = tmp_path / "local" / "manifest.json"
    runtime = ca.acquire_inventory(inv, out_dir=out, manifest_out=meta)

    assert runtime["errors"] == []
    assert len(runtime["results"]) == 1
    result = runtime["results"][0]
    assert result["source_html_sha256"] == "rawhash"
    assert result["canonical_sha256"]
    assert "This is not Joel's text." not in (out / "sample-one.txt").read_text()
    saved = json.loads(meta.read_text())
    assert saved["raw_text_committed"] is False
    assert "text" not in saved["results"][0]
