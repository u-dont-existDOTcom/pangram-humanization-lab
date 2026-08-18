from pangram_lab import dharma_control_profiles as dp


def test_profile_inventory_keeps_only_explicit_labels_and_excludes_overlap():
    spec = {
        "targets": [
            {
                "speaker": "David Vardy",
                "author_id": "david-vardy",
                "exclude_urls": ["https://example.blogspot.com/shared.html"],
            }
        ]
    }
    discoveries = {
        "David Vardy": {
            "target_post_count": 3,
            "target_posts": [
                {
                    "entry_id": "tag-x-1",
                    "title": "Profile",
                    "published": "2014-01-01T00:00:00Z",
                    "url": "https://example.blogspot.com/profile.html",
                    "target_label_count": 2,
                },
                {
                    "entry_id": "tag-x-2",
                    "title": "Mention only",
                    "published": "2014-01-02T00:00:00Z",
                    "url": "https://example.blogspot.com/mention.html",
                    "target_label_count": 0,
                },
                {
                    "entry_id": "tag-x-3",
                    "title": "Shared",
                    "published": "2014-01-03T00:00:00Z",
                    "url": "https://example.blogspot.com/shared.html",
                    "target_label_count": 1,
                },
            ],
        }
    }
    inventory, census = dp.build_profile_inventory(spec, discoveries)
    posts = inventory["sources"][0]["known_threads"]
    assert len(posts) == 1
    assert posts[0]["url"].endswith("profile.html")
    assert posts[0]["extraction_mode"] == "speaker-prefix:David Vardy"
    assert census[0]["selected_explicit_nonoverlap_posts"] == 1
    assert census[0]["rejected_name_only_posts"] == 1
    assert census[0]["rejected_overlap_posts"] == 1


def test_summary_reports_word_depth_and_concentration_flags():
    spec = {
        "feasibility_guidance": {
            "preferred_min_explicit_nonoverlap_posts": 2,
            "preferred_min_total_words": 1000,
            "preferred_max_largest_source_fraction": 0.7,
        },
        "targets": [{"speaker": "David Vardy", "author_id": "david-vardy"}],
    }
    results = [
        {
            "speaker": "David Vardy",
            "sample_id": "a",
            "source_group": "g1",
            "canonical_sha256": "x",
            "word_count": 900,
            "target_marker_count": 2,
            "quality_flags": [],
        },
        {
            "speaker": "David Vardy",
            "sample_id": "b",
            "source_group": "g2",
            "canonical_sha256": "y",
            "word_count": 100,
            "target_marker_count": 1,
            "quality_flags": ["thin-for-authorship-attribution"],
        },
    ]
    receipt = dp.summarize_profiles(
        results,
        spec,
        [{"speaker": "David Vardy", "selected_explicit_nonoverlap_posts": 2}],
    )
    author = receipt["authors"]["David Vardy"]
    assert author["total_words"] == 1000
    assert author["largest_source_fraction"] == 0.9
    assert "largest-source-overconcentrated" in author["feasibility_flags"]
    assert "one-or-more-samples-require-manual-quality-review" in author["feasibility_flags"]
