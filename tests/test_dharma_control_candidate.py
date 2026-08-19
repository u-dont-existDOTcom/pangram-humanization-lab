import json
from pathlib import Path

from pangram_lab import dharma_control_candidate as cc


def _spec(tmp_path: Path) -> Path:
    spec = {
        "schema_version": 1,
        "date": "2026-08-19",
        "purpose": "test",
        "method_decision": "reuse",
        "blog": "https://example.blogspot.com/",
        "target": {
            "speaker": "Greg Goode",
            "author_id": "greg-goode",
            "role": "ordinary-control-candidate",
        },
        "overlap_speakers": ["Joel Rosenblum"],
        "static_exclude_urls": ["https://example.blogspot.com/static.html"],
        "network": {
            "feed_page_size": 100,
            "max_feed_pages": 5,
            "source_request_spacing_seconds": 2,
            "timeout_seconds": 30,
        },
        "partition": {
            "reserved_holdout_count": 2,
            "minimum_holdout_words_per_source": 100,
            "selection_salt": "test-v1",
        },
        "feasibility_guidance": {
            "preferred_min_explicit_nonoverlap_posts": 2,
            "preferred_min_total_words": 500,
            "preferred_max_largest_source_fraction": 0.7,
            "preferred_min_reserved_holdout_posts": 2,
        },
        "forbidden_claims": ["not admitted"],
    }
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec), encoding="utf-8")
    return path


def test_build_inventory_excludes_dynamic_and_static_overlap(tmp_path):
    spec = json.loads(_spec(tmp_path).read_text())
    discovery = {
        "target_explicit_post_count": 4,
        "target_posts": [
            {
                "entry_id": "post-1",
                "title": "keep",
                "published": "2013-01-01T00:00:00Z",
                "url": "https://example.blogspot.com/keep.html",
                "target_label_count": 2,
                "overlap_speakers_present": [],
            },
            {
                "entry_id": "post-2",
                "title": "overlap",
                "published": "2013-01-02T00:00:00Z",
                "url": "https://example.blogspot.com/overlap.html",
                "target_label_count": 1,
                "overlap_speakers_present": ["Joel Rosenblum"],
            },
            {
                "entry_id": "post-3",
                "title": "static",
                "published": "2013-01-03T00:00:00Z",
                "url": "https://example.blogspot.com/static.html",
                "target_label_count": 1,
                "overlap_speakers_present": [],
            },
            {
                "entry_id": "post-4",
                "title": "mention",
                "published": "2013-01-04T00:00:00Z",
                "url": "https://example.blogspot.com/mention.html",
                "target_label_count": 0,
                "overlap_speakers_present": [],
            },
        ],
    }
    inventory, census = cc.build_candidate_inventory(spec, discovery)
    rows = inventory["sources"][0]["known_threads"]
    assert [row["title"] for row in rows] == ["keep"]
    assert census["selected_nonoverlap_posts"] == 1
    assert census["rejected_dynamic_overlap_posts"] == 1
    assert census["rejected_static_exclude_posts"] == 1
    assert census["rejected_name_only_posts"] == 1


def test_partition_is_deterministic_disjoint_and_metadata_only(tmp_path):
    spec = json.loads(_spec(tmp_path).read_text())
    rows = []
    for index, words in enumerate((300, 280, 260, 240, 220), start=1):
        rows.append(
            {
                "speaker": "Greg Goode",
                "sample_id": f"s{index}",
                "source_group": f"g{index}",
                "title": f"t{index}",
                "date": "2013-01-01",
                "url": f"https://example.blogspot.com/{index}.html",
                "source_html_sha256": f"{index}" * 64,
                "canonical_sha256": f"{index + 1}" * 64,
                "word_count": words,
                "target_marker_count": 1,
                "other_speaker_boundary_count": 1,
                "quality_flags": [],
            }
        )
    first = cc.partition_candidate_rows(rows, spec)
    second = cc.partition_candidate_rows(list(reversed(rows)), spec)
    assert first == second
    assert first["reserved_holdout"]["source_count"] == 2
    assert first["profile"]["source_count"] == 3
    p = {row["source_group"] for row in first["profile"]["samples"]}
    h = {row["source_group"] for row in first["reserved_holdout"]["samples"]}
    assert not p & h
    assert first["exact_duplicate_groups"] == []
    assert "local_text_path" not in json.dumps(first)


def test_run_candidate_extraction_writes_receipt_without_prose(tmp_path):
    spec_path = _spec(tmp_path)
    discovery = {
        "feed_page_count": 1,
        "target_explicit_post_count": 6,
        "feed_snapshot_sha256": "a" * 64,
        "target_post_set_sha256": "b" * 64,
        "target_posts": [
            {
                "entry_id": f"post-{index}",
                "title": f"title {index}",
                "published": "2013-01-01T00:00:00Z",
                "url": f"https://example.blogspot.com/{index}.html",
                "target_label_count": 1,
                "overlap_speakers_present": [],
            }
            for index in range(1, 7)
        ],
    }

    def fake_acquire(inventory_path, *, out_dir, manifest_out, sample_ids, timeout):
        inventory = json.loads(Path(inventory_path).read_text())
        item = next(
            row
            for source in inventory["sources"]
            for row in source["known_threads"]
            if row["sample_id"] in sample_ids
        )
        n = int(item["url"].rsplit("/", 1)[-1].split(".")[0])
        return {
            "network_fetch_count": 1,
            "errors": [],
            "results": [
                {
                    **item,
                    "speaker": "Greg Goode",
                    "source_html_sha256": f"{n}" * 64,
                    "canonical_sha256": f"{n + 1}" * 64,
                    "word_count": 250 + n * 10,
                    "target_marker_count": 1,
                    "other_speaker_boundary_count": 1,
                    "quality_flags": [],
                    "local_text_path": f"/private/{n}.txt",
                }
            ],
        }

    receipt_path = tmp_path / "receipt.json"
    result = cc.run_candidate_extraction(
        spec_path,
        out_dir=tmp_path / "out",
        receipt_out=receipt_path,
        discovery_fn=lambda spec: discovery,
        acquire_fn=fake_acquire,
        sleep_fn=lambda _: None,
    )
    assert result["automated_feasibility_pass"] is True
    assert result["role_activation_ready"] is False
    assert result["partitions"]["profile"]["source_count"] == 4
    assert result["partitions"]["reserved_holdout"]["source_count"] == 2
    encoded = receipt_path.read_text()
    assert "/private/" not in encoded
    assert "local_text_path" not in encoded
    assert "raw_text" not in encoded
    assert "canonical_text" not in encoded


def test_archive_scan_marks_explicit_overlap_in_one_feed_pass(tmp_path):
    atom = b'''<feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>tag:blogger.com,1999:blog-1.post-1</id>
        <title>Shared</title>
        <published>2013-01-01T00:00:00Z</published>
        <link rel="alternate" href="http://example.blogspot.com/shared.html" />
        <content type="html">&lt;b&gt;Greg Goode:&lt;/b&gt;A&lt;b&gt;Joel Rosenblum:&lt;/b&gt;B</content>
      </entry>
      <entry>
        <id>tag:blogger.com,1999:blog-1.post-2</id>
        <title>Greg only</title>
        <published>2013-01-02T00:00:00Z</published>
        <link rel="alternate" href="http://example.blogspot.com/greg.html" />
        <content type="html">&lt;b&gt;Greg Goode:&lt;/b&gt;C</content>
      </entry>
    </feed>'''
    spec = json.loads(_spec(tmp_path).read_text())
    calls = []
    result = cc.discover_explicit_target_posts(
        spec,
        fetch_fn=lambda url, timeout: (calls.append((url, timeout)) or atom, "f" * 64),
    )
    assert len(calls) == 1
    assert result["target_explicit_post_count"] == 2
    by_title = {row["title"]: row for row in result["target_posts"]}
    assert by_title["Shared"]["overlap_speakers_present"] == ["Joel Rosenblum"]
    assert by_title["Greg only"]["overlap_speakers_present"] == []
