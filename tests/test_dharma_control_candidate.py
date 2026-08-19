import hashlib
import json
from pathlib import Path

from pangram_lab import dharma_control_candidate as candidate
from pangram_lab.corpus_acquire import canonicalize, iter_inventory_items


def _post(url: str, entry: str, *, labels: int = 1):
    return {
        "entry_id": f"tag:blogger.com,1999:blog-test.post-{entry}",
        "title": f"Thread {entry}",
        "published": "2014-01-01T00:00:00Z",
        "url": url,
        "target_label_count": labels,
        "raw_target_occurrences": labels,
        "explicit_speaker_labels": [],
    }


def test_candidate_extraction_replaces_provisional_overlap_and_stays_metadata_only(
    tmp_path: Path,
):
    greg_urls = [
        "https://example.blogspot.com/a.html",
        "https://example.blogspot.com/b.html",
        "https://example.blogspot.com/c.html",
        "https://example.blogspot.com/d.html",
        "https://example.blogspot.com/e.html",
    ]
    joel_overlap = greg_urls[1]
    configured_only = "https://example.blogspot.com/configured.html"

    def discover(blog, *, target_speaker, timeout=30):
        assert blog == "https://example.blogspot.com/"
        if target_speaker == "Greg Goode":
            posts = [_post(url, str(index)) for index, url in enumerate(greg_urls)]
        elif target_speaker == "Joel Rosenblum":
            posts = [_post(joel_overlap, "overlap")]
        else:
            raise AssertionError(target_speaker)
        return {
            "schema_version": 1,
            "target_speaker": target_speaker,
            "target_post_count": len(posts),
            "target_posts": posts,
            "feed_pages": [
                {
                    "page_number": 1,
                    "feed_sha256": hashlib.sha256(target_speaker.encode()).hexdigest(),
                    "target_post_count": len(posts),
                    "next_present": False,
                }
            ],
        }

    def acquire(inventory_path, *, out_dir, manifest_out, timeout=30):
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        out_dir.mkdir(parents=True, exist_ok=True)
        rows = []
        for item in iter_inventory_items(inventory):
            text = (f"Original prose for {item['sample_id']}. " * 120).strip()
            canon = canonicalize(text)
            local = out_dir / f"{item['sample_id']}.txt"
            local.write_text(canon.text + "\n", encoding="utf-8")
            rows.append(
                {
                    "sample_id": item["sample_id"],
                    "source_group": item["source_group"],
                    "speaker": "Greg Goode",
                    "canonical_sha256": canon.sha256,
                    "word_count": canon.word_count,
                    "target_marker_count": 1,
                    "quality_flags": [],
                    "local_text_path": str(local),
                    "url": item["url"],
                }
            )
        runtime = {
            "results": rows,
            "errors": [],
            "network_fetch_count": len(rows),
        }
        manifest_out.parent.mkdir(parents=True, exist_ok=True)
        manifest_out.write_text(json.dumps(runtime), encoding="utf-8")
        return runtime

    spec = {
        "schema_version": 1,
        "date": "2026-08-19",
        "blog": "https://example.blogspot.com/",
        "method_decision": "reuse",
        "overlap_exclusion_speakers": ["Joel Rosenblum"],
        "targets": [
            {
                "speaker": "Greg Goode",
                "author_id": "greg-goode",
                "role": "ordinary-control-candidate",
                "exclude_urls": [configured_only],
            }
        ],
        "manual_seed_pages_for_retrieval_crosscheck": [
            {"title": "A", "url": greg_urls[0]},
            {"title": "B", "url": greg_urls[1]},
        ],
        "feasibility_guidance": {
            "preferred_min_explicit_nonoverlap_posts": 4,
            "preferred_min_total_words": 1000,
            "preferred_max_largest_source_fraction": 0.7,
        },
        "required_post_extraction_checks": ["manual quotation review"],
        "forbidden_claims": ["not admitted"],
    }
    spec_path = tmp_path / "spec.json"
    receipt_path = tmp_path / "receipt.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")

    result = candidate.extract_control_candidate(
        spec_path,
        out_dir=tmp_path / "text",
        receipt_out=receipt_path,
        discover_fn=discover,
        acquire_fn=acquire,
    )

    assert result["status"] == "candidate-extraction-complete-manual-review-pending"
    assert result["fresh_overlap"]["fresh_overlap_count"] == 1
    assert result["fresh_overlap"]["configured_exclusion_count"] == 1
    assert result["fresh_overlap"]["effective_exclusion_count"] == 2
    assert result["fresh_overlap"]["fresh_only_count"] == 1
    assert result["fresh_overlap"]["configured_only_count"] == 1
    assert len(result["fresh_overlap"]["fresh_overlap_set_identity_sha256"]) == 64
    assert result["candidate"]["extracted_post_count"] == 4
    assert result["candidate"]["quantitative_feasibility_pass"] is True
    assert result["candidate_ready_for_manual_quality_review"] is True
    assert result["profile_admission_authorized"] is False
    assert result["profile_holdout_split_authorized"] is False
    assert result["manual_seed_coverage"][0]["discovered_as_explicit_target_post"] is True
    assert result["manual_seed_coverage"][1]["excluded_as_fresh_overlap"] is True

    encoded = receipt_path.read_text(encoding="utf-8")
    for forbidden in (
        "https://",
        "http://",
        "local_text_path",
        "Original prose",
        configured_only,
        joel_overlap,
    ):
        assert forbidden not in encoded


def test_candidate_extraction_reports_hard_errors_without_urls(tmp_path: Path):
    target_url = "https://example.blogspot.com/a.html"

    def discover(blog, *, target_speaker, timeout=30):
        posts = [_post(target_url, "1")] if target_speaker == "Greg Goode" else []
        return {
            "target_post_count": len(posts),
            "target_posts": posts,
            "feed_pages": [],
        }

    def acquire(inventory_path, *, out_dir, manifest_out, timeout=30):
        return {
            "results": [],
            "network_fetch_count": 1,
            "errors": [
                {
                    "sample_id": "sample",
                    "url": target_url,
                    "speaker": "Greg Goode",
                    "error": "HTTP Error 429: Too Many Requests",
                }
            ],
        }

    spec = {
        "schema_version": 1,
        "blog": "https://example.blogspot.com/",
        "targets": [
            {
                "speaker": "Greg Goode",
                "author_id": "greg-goode",
                "role": "ordinary-control-candidate",
            }
        ],
        "feasibility_guidance": {},
    }
    spec_path = tmp_path / "spec.json"
    receipt_path = tmp_path / "receipt.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")

    result = candidate.extract_control_candidate(
        spec_path,
        out_dir=tmp_path / "text",
        receipt_out=receipt_path,
        discover_fn=discover,
        acquire_fn=acquire,
    )

    assert result["status"] == "candidate-extraction-failed"
    assert result["hard_error_count"] == 1
    assert result["candidate_ready_for_manual_quality_review"] is False
    encoded = receipt_path.read_text(encoding="utf-8")
    assert target_url not in encoded
    assert "https://" not in encoded


def test_spec_requires_one_target_and_overlap_speaker():
    try:
        candidate._validate_spec({"schema_version": 1, "targets": []})
    except candidate.ControlCandidateError as exc:
        assert "exactly one target" in str(exc)
    else:
        raise AssertionError("empty targets should fail")

    spec = {
        "schema_version": 1,
        "blog": "https://example.blogspot.com/",
        "targets": [{"speaker": "Greg Goode", "author_id": "greg"}],
        "overlap_exclusion_speakers": ["Greg Goode"],
    }
    try:
        candidate._validate_spec(spec)
    except candidate.ControlCandidateError as exc:
        assert "overlap exclusion speaker" in str(exc)
    else:
        raise AssertionError("self-only overlap speakers should fail")
