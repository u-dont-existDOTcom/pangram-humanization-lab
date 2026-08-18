import json
from pathlib import Path

import pytest

from pangram_lab import dharma_ordinary_control_census as census


def _entry(entry_id: str, path: str, labels: list[str]) -> str:
    label_html = "".join(f"<b>{label}:</b>text" for label in labels)
    return f"""
      <entry>
        <id>{entry_id}</id>
        <title>Hidden from receipt</title>
        <published>2013-01-01T00:00:00Z</published>
        <link rel="alternate" href="http://example.blogspot.com/{path}"/>
        <content type="html">{label_html.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')}</content>
      </entry>
    """


def _feed(entries: list[str], *, next_url: str | None = None) -> bytes:
    next_link = (
        f'<link rel="next" href="{next_url.replace("&", "&amp;")}"/>'
        if next_url
        else ""
    )
    return (
        '<feed xmlns="http://www.w3.org/2005/Atom">'
        + next_link
        + "".join(entries)
        + "</feed>"
    ).encode("utf-8")


def _role_spec(path: Path, *, ordinary_minimum: int = 2) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "active_authors": [
                    {
                        "author": "Joel Rosenblum",
                        "role": "target-author",
                        "status": "active",
                    },
                    {
                        "author": "Stian Gudmundsen Høiland",
                        "role": "owner-identified-hard-negative",
                        "status": "active",
                    },
                    {
                        "author": "David Vardy",
                        "role": "ordinary-matched-control",
                        "status": "active",
                    },
                ],
                "minimum_evidence": {
                    "ordinary_matched_controls_before_rewrite_degradation_claim": ordinary_minimum
                },
            }
        ),
        encoding="utf-8",
    )


def _spec(path: Path, role_path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "date": "2026-08-18",
                "blog_root": "https://example.blogspot.com/",
                "target_author": "Joel Rosenblum",
                "role_spec": str(role_path),
                "allowed_single_token_labels": ["Soh"],
                "candidate_thresholds": {
                    "minimum_explicit_threads": 3,
                    "minimum_non_target_overlap_threads": 2,
                    "minimum_target_overlap_threads": 1,
                },
                "method_decision": "adapt-existing-atom-speaker-discovery",
                "interpretation_rule": "census only",
            }
        ),
        encoding="utf-8",
    )


def test_configured_single_token_label_is_exactly_allowlisted():
    html = "<b>Soh:</b>x<b>Interesting:</b>heading<b>Greg Goode:</b>y"
    assert census._speaker_labels(
        html, allowed_single_token_labels=["Soh"]
    ) == ["Soh", "Greg Goode"]
    assert census._speaker_labels(html) == ["Greg Goode"]


def test_atom_page_scan_returns_hashes_and_labels_but_no_post_metadata():
    body = _feed(
        [
            _entry(
                "post-1",
                "2013/01/thread.html",
                ["Joel Rosenblum", "Greg Goode", "Soh"],
            )
        ]
    )
    rows, next_url, stats = census.scan_all_speakers_atom_page(
        body,
        target_author="Joel Rosenblum",
        allowed_single_token_labels=["Soh"],
    )
    assert next_url is None
    assert stats == {"entry_count": 1, "explicitly_labeled_entry_count": 1}
    assert len(rows) == 1
    row = rows[0]
    assert len(row["post_identity_sha256"]) == 64
    assert row["explicit_speaker_labels"] == [
        "Joel Rosenblum",
        "Greg Goode",
        "Soh",
    ]
    assert row["target_explicitly_present"] is True
    assert "url" not in row
    assert "title" not in row
    assert "entry_id" not in row


def test_one_pass_census_separates_active_roles_and_preliminary_candidates(
    monkeypatch, tmp_path: Path
):
    page_1 = _feed(
        [
            _entry("a", "a.html", ["Joel Rosenblum", "Greg Goode", "David Vardy"]),
            _entry("b", "b.html", ["Joel Rosenblum", "Greg Goode", "Greg Goode"]),
        ],
        next_url="http://example.blogspot.com/feeds/posts/default?start-index=3",
    )
    page_2 = _feed(
        [
            _entry("c", "c.html", ["Greg Goode", "John Ahn", "Soh"]),
            _entry("d", "d.html", ["Greg Goode", "Stian Gudmundsen Høiland"]),
            _entry("e", "e.html", ["John Ahn"]),
        ]
    )
    pages = [page_1, page_2]
    fetched = []

    def fake_fetch(url, timeout=30):
        fetched.append(url)
        body = pages.pop(0)
        return body, f"sha-{len(fetched)}"

    monkeypatch.setattr(census, "fetch_atom", fake_fetch)
    role_path = tmp_path / "roles.json"
    spec_path = tmp_path / "spec.json"
    _role_spec(role_path)
    _spec(spec_path, role_path)
    out_path = tmp_path / "receipt.json"

    result = census.run_census(spec_path, out_path=out_path)

    assert len(fetched) == 2
    assert result["feed_page_count"] == 2
    assert result["archive_post_count"] == 5
    assert result["additional_ordinary_controls_required"] == 1
    assert result["candidate_supply_meets_count_requirement"] is True
    assert result["profile_extraction_authorized"] is False

    by_name = {row["speaker"]: row for row in result["speakers"]}
    assert by_name["Joel Rosenblum"]["active_role"] == "target-author"
    assert (
        by_name["Stian Gudmundsen Høiland"]["active_role"]
        == "owner-identified-hard-negative"
    )
    assert by_name["David Vardy"]["active_role"] == "ordinary-matched-control"

    greg = by_name["Greg Goode"]
    assert greg["explicit_thread_count"] == 4
    assert greg["marker_count"] == 5
    assert greg["target_overlap_thread_count"] == 2
    assert greg["non_target_overlap_thread_count"] == 2
    assert greg["preliminary_ordinary_control_candidate"] is True
    assert greg["identity_review_required"] is True
    assert greg["word_sufficiency_unchecked"] is True

    assert by_name["John Ahn"]["preliminary_ordinary_control_candidate"] is False
    assert by_name["Soh"]["preliminary_ordinary_control_candidate"] is False
    assert [row["speaker"] for row in result["preliminary_candidates"]] == [
        "Greg Goode"
    ]

    encoded = out_path.read_text(encoding="utf-8")
    assert "Hidden from receipt" not in encoded
    assert "example.blogspot.com" not in encoded
    assert "http://" not in encoded
    assert "https://" not in encoded
    assert "local_text_path" not in encoded


def test_census_groups_case_variants_without_alias_merging():
    posts = [
        {
            "post_identity_sha256": "a" * 64,
            "explicit_speaker_labels": ["Greg Goode", "GREG Goode"],
            "target_explicitly_present": True,
        },
        {
            "post_identity_sha256": "b" * 64,
            "explicit_speaker_labels": ["Greg Goode"],
            "target_explicitly_present": False,
        },
    ]
    rows = census._build_speaker_rows(
        posts,
        target_author="Joel Rosenblum",
        active_roles={
            "joel rosenblum": {
                "author": "Joel Rosenblum",
                "role": "target-author",
            }
        },
        thresholds={
            "minimum_explicit_threads": 2,
            "minimum_non_target_overlap_threads": 1,
            "minimum_target_overlap_threads": 1,
        },
    )
    assert len(rows) == 1
    assert rows[0]["speaker"] == "Greg Goode"
    assert rows[0]["explicit_thread_count"] == 2
    assert rows[0]["marker_count"] == 3


def test_missing_explicit_target_fails_closed(monkeypatch, tmp_path: Path):
    page = _feed([_entry("a", "a.html", ["Greg Goode"])])
    monkeypatch.setattr(census, "fetch_atom", lambda url, timeout=30: (page, "sha"))
    role_path = tmp_path / "roles.json"
    spec_path = tmp_path / "spec.json"
    _role_spec(role_path)
    _spec(spec_path, role_path)

    with pytest.raises(census.OrdinaryControlCensusError, match="target author was not found"):
        census.run_census(spec_path, out_path=tmp_path / "out.json")


def test_active_author_is_never_ranked_as_new_candidate():
    posts = [
        {
            "post_identity_sha256": f"{index:064x}",
            "explicit_speaker_labels": ["David Vardy"],
            "target_explicitly_present": index == 0,
        }
        for index in range(6)
    ]
    rows = census._build_speaker_rows(
        posts,
        target_author="Joel Rosenblum",
        active_roles={
            "joel rosenblum": {
                "author": "Joel Rosenblum",
                "role": "target-author",
            },
            "david vardy": {
                "author": "David Vardy",
                "role": "ordinary-matched-control",
            },
        },
        thresholds={
            "minimum_explicit_threads": 5,
            "minimum_non_target_overlap_threads": 4,
            "minimum_target_overlap_threads": 1,
        },
    )
    assert rows[0]["speaker"] == "David Vardy"
    assert rows[0]["excluded_from_new_candidate_ranking_as_active"] is True
    assert rows[0]["preliminary_ordinary_control_candidate"] is False
