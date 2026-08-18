import json

from pangram_lab import dharma_speaker_acquire as ds


def test_multiline_target_label_collects_until_next_explicit_speaker():
    text = """
    Intro text that is not attributed to Joel.

    Joel Rosenblum:
    First Joel paragraph.
    It continues here.

    John Ahn:
    This belongs to John.

    Joel Rosenblum
    Second Joel paragraph.
    """
    result = ds.extract_named_speaker_blocks(text, "Joel Rosenblum")
    assert "Intro text" not in result.text
    assert "This belongs to John" not in result.text
    assert "First Joel paragraph." in result.text
    assert "It continues here." in result.text
    assert "Second Joel paragraph." in result.text
    assert result.target_marker_count == 2
    assert result.other_speaker_boundary_count == 1


def test_inline_target_label_is_preserved_and_other_inline_speaker_is_excluded():
    text = """
    Greg Goode: other person's thought
    Joel Rosenblum: First Joel thought.
    Another Joel sentence.
    Soh: other person's thought
    Joel Rosenblum: Third Joel thought.
    """
    result = ds.extract_named_speaker_blocks(text, "Joel Rosenblum")
    assert result.text == "First Joel thought.\nAnother Joel sentence.\nThird Joel thought."
    assert result.target_marker_count == 2
    assert result.other_speaker_boundary_count == 1


def test_bold_inline_speaker_labels_get_boundaries_without_leaking_other_speakers():
    html = """
    <div class="post-body entry-content">
      <div><b>Other Person:</b>Other text.
      <b>Joel Rosenblum:</b>Joel text here.
      <b>Greg Goode:</b>Greg text.</div>
    </div>
    """
    result = ds.extract_blogspot_named_speaker(html, "Joel Rosenblum")
    assert result.text == "Joel text here."
    assert result.target_marker_count == 1
    assert result.other_speaker_boundary_count == 1


def test_standalone_multiword_name_ends_active_target_block():
    text = """
    Joel Rosenblum
    This is Joel.
    Greg Goode
    This is Greg.
    """
    result = ds.extract_named_speaker_blocks(text, "Joel Rosenblum")
    assert result.text == "This is Joel."
    assert result.other_speaker_boundary_count == 1
    assert result.standalone_boundary_count == 1


def test_unlabeled_text_before_first_target_is_never_admitted():
    result = ds.extract_named_speaker_blocks(
        "Unlabeled paragraph.\nSomeone Else: not Joel.",
        "Joel Rosenblum",
    )
    assert result.text == ""
    assert result.target_marker_count == 0


def test_ambiguous_single_word_inside_active_block_is_flagged_not_silently_boundary():
    result = ds.extract_named_speaker_blocks(
        "Joel Rosenblum:\nInteresting\nThis is still ambiguous and needs review.",
        "Joel Rosenblum",
    )
    assert "Interesting" in result.text
    assert result.ambiguous_single_word_line_count == 1


def test_acquisition_writes_prose_only_to_local_path_and_metadata_only_manifest(tmp_path, monkeypatch):
    inventory = {
        "sources": [
            {
                "source_id": "dharma",
                "source_group": "dharma",
                "provenance": "natural-owner-confirmed",
                "modality": "written",
                "registers": ["dialogue-QA"],
                "known_threads": [
                    {
                        "sample_id": "thread-one",
                        "title": "Thread one",
                        "date": "2014-01-01",
                        "url": "https://example.blogspot.com/thread.html",
                        "extraction_mode": "speaker-prefix:Joel Rosenblum",
                    }
                ],
            }
        ]
    }
    inv = tmp_path / "inventory.json"
    inv.write_text(json.dumps(inventory), encoding="utf-8")
    html = """
    <div class="post-body entry-content">
      <div>John Ahn:</div><div>Other text.</div>
      <div>Joel Rosenblum:</div>
      <div>This is Joel's multiline comment with enough words to be a useful extraction fixture.</div>
      <div>Greg Goode:</div><div>Other text again.</div>
    </div>
    """
    monkeypatch.setattr(ds, "fetch_html", lambda url, timeout=30: (html, "rawhash"))

    out = tmp_path / "local" / "text"
    meta = tmp_path / "local" / "manifest.json"
    runtime = ds.acquire_speaker_inventory(inv, out_dir=out, manifest_out=meta)

    assert runtime["errors"] == []
    assert len(runtime["results"]) == 1
    assert runtime["network_fetch_count"] == 1
    result = runtime["results"][0]
    assert result["canonical_sha256"]
    assert result["target_marker_count"] == 1
    assert "text" not in result
    saved = json.loads(meta.read_text())
    assert saved["raw_or_canonical_prose_in_output"] is False
    assert saved["network_fetch_count"] == 1
    assert "Joel's multiline comment" in (out / "thread-one.txt").read_text()
    assert "Other text" not in (out / "thread-one.txt").read_text()


def test_acquisition_fetches_shared_thread_once_for_multiple_speakers(tmp_path, monkeypatch):
    shared_url = "https://example.blogspot.com/shared.html"
    inventory = {
        "sources": [
            {
                "source_id": "shared-thread-authors",
                "source_group": "shared-thread-authors",
                "provenance": "public-human-control-explicit-speaker",
                "modality": "written",
                "registers": ["dialogue-QA"],
                "known_threads": [
                    {
                        "sample_id": "shared-joel",
                        "source_group": "same-thread",
                        "url": shared_url,
                        "extraction_mode": "speaker-prefix:Joel Rosenblum",
                    },
                    {
                        "sample_id": "shared-david",
                        "source_group": "same-thread",
                        "url": shared_url,
                        "extraction_mode": "speaker-prefix:David Vardy",
                    },
                ],
            }
        ]
    }
    inv = tmp_path / "inventory.json"
    inv.write_text(json.dumps(inventory), encoding="utf-8")
    html = """
    <div class="post-body entry-content">
      <div><b>Joel Rosenblum:</b>Joel has enough distinct words for this extraction fixture to be nonempty.</div>
      <div><b>David Vardy:</b>David also has enough distinct words for this extraction fixture to be nonempty.</div>
    </div>
    """
    calls = []

    def fake_fetch(url, timeout=30):
        calls.append(url)
        return html, "shared-raw-hash"

    monkeypatch.setattr(ds, "fetch_html", fake_fetch)
    runtime = ds.acquire_speaker_inventory(
        inv,
        out_dir=tmp_path / "text",
        manifest_out=tmp_path / "manifest.json",
    )

    assert runtime["errors"] == []
    assert len(runtime["results"]) == 2
    assert runtime["network_fetch_count"] == 1
    assert calls == [shared_url]
    assert {row["speaker"] for row in runtime["results"]} == {"Joel Rosenblum", "David Vardy"}
    assert {row["source_html_sha256"] for row in runtime["results"]} == {"shared-raw-hash"}
