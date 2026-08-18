from __future__ import annotations

import collections
import hashlib
import html as html_lib
import json
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable

from .blogger_discover import ATOM, _feed_url, _https_url, _root_from_url, fetch_atom
from .dharma_author_discover import _PERSON_LABEL_RE, _canonical_post_url, _entry_html


class OrdinaryControlCensusError(ValueError):
    pass


class ConfiguredSpeakerLabelScanner(HTMLParser):
    """Collect explicit person labels without broad one-token heading leakage."""

    _LABEL_TAGS = {"b", "strong", "cite"}

    def __init__(self, *, allowed_single_token_labels: Iterable[str] = ()):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.parts: list[str] = []
        self.labels: list[str] = []
        self.allowed_single_token_labels = {
            str(value).strip().rstrip(":").casefold()
            for value in allowed_single_token_labels
            if str(value).strip()
        }

    def handle_starttag(self, tag: str, attrs):
        if tag.lower() in self._LABEL_TAGS:
            if self.depth == 0:
                self.parts = []
            self.depth += 1

    def handle_endtag(self, tag: str):
        if tag.lower() not in self._LABEL_TAGS or self.depth <= 0:
            return
        self.depth -= 1
        if self.depth:
            return
        value = html_lib.unescape("".join(self.parts))
        value = re.sub(r"\s+", " ", value).strip()
        match = _PERSON_LABEL_RE.match(value)
        candidate = match.group(1).strip() if match else None
        if candidate is None:
            one_token = value.rstrip(":").strip()
            if (
                one_token
                and " " not in one_token
                and one_token.casefold() in self.allowed_single_token_labels
            ):
                candidate = one_token
        if candidate and not candidate.isupper():
            self.labels.append(candidate)
        self.parts = []

    def handle_data(self, data: str):
        if self.depth:
            self.parts.append(data)


def _speaker_labels(
    content_html: str, *, allowed_single_token_labels: Iterable[str] = ()
) -> list[str]:
    scanner = ConfiguredSpeakerLabelScanner(
        allowed_single_token_labels=allowed_single_token_labels
    )
    scanner.feed(content_html)
    return scanner.labels


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _post_identity(entry: ET.Element) -> str | None:
    entry_id = (entry.findtext(f"{ATOM}id") or "").strip()
    url = _canonical_post_url(entry) or ""
    if not entry_id and not url:
        return None
    return _sha256_text(f"{entry_id}\n{url}")


def scan_all_speakers_atom_page(
    body: bytes,
    *,
    target_author: str,
    allowed_single_token_labels: Iterable[str] = (),
) -> tuple[list[dict[str, Any]], str | None, dict[str, int]]:
    """Return explicit-label metadata for every post on one Atom page.

    Titles, URLs, entry IDs, and surrounding post prose are never returned.
    The post identity is a one-way hash over the source entry ID and canonical
    URL so repeated feed pages can be deduplicated without exposing either.
    """

    root = ET.fromstring(body)
    next_url = None
    for link in root.findall(f"{ATOM}link"):
        if link.attrib.get("rel") == "next" and link.attrib.get("href"):
            next_url = _https_url(link.attrib["href"])
            break

    target_key = target_author.casefold()
    rows: list[dict[str, Any]] = []
    total_entries = 0
    labeled_entries = 0
    for entry in root.findall(f"{ATOM}entry"):
        total_entries += 1
        identity = _post_identity(entry)
        if not identity:
            continue
        labels = _speaker_labels(
            _entry_html(entry),
            allowed_single_token_labels=allowed_single_token_labels,
        )
        if labels:
            labeled_entries += 1
        rows.append(
            {
                "post_identity_sha256": identity,
                "explicit_speaker_labels": labels,
                "target_explicitly_present": any(
                    label.casefold() == target_key for label in labels
                ),
            }
        )
    return rows, next_url, {
        "entry_count": total_entries,
        "explicitly_labeled_entry_count": labeled_entries,
    }


def _load_role_spec(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if obj.get("schema_version") != 1:
        raise OrdinaryControlCensusError("role spec schema_version must be 1")
    if not isinstance(obj.get("active_authors"), list) or not obj["active_authors"]:
        raise OrdinaryControlCensusError("role spec active_authors must be non-empty")
    return obj


def _active_roles(role_spec: dict[str, Any]) -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    for index, row in enumerate(role_spec.get("active_authors", [])):
        if not isinstance(row, dict):
            raise OrdinaryControlCensusError(
                f"active_authors[{index}] must be an object"
            )
        if str(row.get("status") or "active") != "active":
            continue
        author = str(row.get("author") or "").strip()
        role = str(row.get("role") or "").strip()
        if not author or not role:
            raise OrdinaryControlCensusError(
                f"active_authors[{index}] requires author and role"
            )
        key = author.casefold()
        if key in output:
            raise OrdinaryControlCensusError(f"duplicate active author: {author}")
        output[key] = {"author": author, "role": role}
    return output


def _configured_path(spec_path: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    cwd_path = Path.cwd() / path
    if cwd_path.exists():
        return cwd_path
    return spec_path.resolve().parent.parent / path


def _choose_display_name(counts: collections.Counter[str]) -> str:
    if not counts:
        raise OrdinaryControlCensusError("speaker has no display-name counts")
    return sorted(
        counts,
        key=lambda value: (-counts[value], value.casefold(), value),
    )[0]


def _speaker_identity_hash(post_ids: set[str]) -> str:
    return _sha256_text("\n".join(sorted(post_ids)))


def _build_speaker_rows(
    posts: list[dict[str, Any]],
    *,
    target_author: str,
    active_roles: dict[str, dict[str, str]],
    thresholds: dict[str, int],
) -> list[dict[str, Any]]:
    display_counts: dict[str, collections.Counter[str]] = collections.defaultdict(
        collections.Counter
    )
    marker_counts: collections.Counter[str] = collections.Counter()
    thread_ids: dict[str, set[str]] = collections.defaultdict(set)
    target_overlap_ids: dict[str, set[str]] = collections.defaultdict(set)

    target_key = target_author.casefold()
    for post in posts:
        post_id = str(post["post_identity_sha256"])
        labels = [str(value).strip() for value in post["explicit_speaker_labels"]]
        target_present = bool(post["target_explicitly_present"])
        unique_keys: set[str] = set()
        for label in labels:
            if not label:
                continue
            key = label.casefold()
            display_counts[key][label] += 1
            marker_counts[key] += 1
            unique_keys.add(key)
        for key in unique_keys:
            thread_ids[key].add(post_id)
            if target_present:
                target_overlap_ids[key].add(post_id)

    rows: list[dict[str, Any]] = []
    for key in sorted(thread_ids):
        display = _choose_display_name(display_counts[key])
        total_threads = len(thread_ids[key])
        overlap_threads = len(target_overlap_ids[key])
        non_overlap_threads = total_threads - overlap_threads
        active = active_roles.get(key)
        excluded_as_active = active is not None
        qualifies = (
            not excluded_as_active
            and key != target_key
            and total_threads >= thresholds["minimum_explicit_threads"]
            and non_overlap_threads
            >= thresholds["minimum_non_target_overlap_threads"]
            and overlap_threads >= thresholds["minimum_target_overlap_threads"]
        )
        rows.append(
            {
                "speaker": display,
                "exact_casefold_identity": key,
                "explicit_thread_count": total_threads,
                "marker_count": int(marker_counts[key]),
                "target_overlap_thread_count": overlap_threads,
                "non_target_overlap_thread_count": non_overlap_threads,
                "post_identity_set_sha256": _speaker_identity_hash(thread_ids[key]),
                "active_role": active["role"] if active else None,
                "excluded_from_new_candidate_ranking_as_active": excluded_as_active,
                "preliminary_ordinary_control_candidate": qualifies,
                "identity_review_required": qualifies,
                "word_sufficiency_unchecked": qualifies,
            }
        )

    rows.sort(
        key=lambda row: (
            not bool(row["preliminary_ordinary_control_candidate"]),
            -int(row["non_target_overlap_thread_count"]),
            -int(row["explicit_thread_count"]),
            -int(row["target_overlap_thread_count"]),
            -int(row["marker_count"]),
            str(row["speaker"]).casefold(),
        )
    )
    return rows


def _validate_spec(spec: dict[str, Any]) -> None:
    if spec.get("schema_version") != 1:
        raise OrdinaryControlCensusError("spec schema_version must be 1")
    for field in ("blog_root", "target_author", "role_spec"):
        if not isinstance(spec.get(field), str) or not spec[field].strip():
            raise OrdinaryControlCensusError(f"spec field {field} is required")
    thresholds = spec.get("candidate_thresholds")
    if not isinstance(thresholds, dict):
        raise OrdinaryControlCensusError("candidate_thresholds must be an object")
    for field in (
        "minimum_explicit_threads",
        "minimum_non_target_overlap_threads",
        "minimum_target_overlap_threads",
    ):
        value = thresholds.get(field)
        if not isinstance(value, int) or value < 0:
            raise OrdinaryControlCensusError(
                f"candidate_thresholds.{field} must be a nonnegative integer"
            )


def _assert_metadata_only(value: Any, *, path: str = "$") -> None:
    forbidden_keys = {
        "local_text_path",
        "raw_text",
        "canonical_text",
        "post_title",
        "post_url",
        "entry_id",
        "title",
        "url",
        "content",
        "summary",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in forbidden_keys:
                raise OrdinaryControlCensusError(
                    f"forbidden metadata key at {path}: {key}"
                )
            _assert_metadata_only(child, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_metadata_only(child, path=f"{path}[{index}]")


def run_census(
    spec_path: Path,
    *,
    out_path: Path,
    timeout: int = 30,
    page_size: int = 100,
    max_pages: int = 10,
) -> dict[str, Any]:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    _validate_spec(spec)
    role_spec = _load_role_spec(_configured_path(spec_path, spec["role_spec"]))
    active_roles = _active_roles(role_spec)

    target_author = str(spec["target_author"])
    target_key = target_author.casefold()
    target_active = active_roles.get(target_key)
    if not target_active or target_active["role"] != "target-author":
        raise OrdinaryControlCensusError(
            "target_author must be the active target-author in the role spec"
        )

    thresholds = {
        key: int(value) for key, value in spec["candidate_thresholds"].items()
    }
    allowed_single = [
        str(value) for value in spec.get("allowed_single_token_labels", [])
    ]

    root = _root_from_url(spec["blog_root"])
    next_feed_url = _feed_url(root, start_index=1, max_results=page_size)
    seen_feed_urls: set[str] = set()
    posts_by_id: dict[str, dict[str, Any]] = {}
    page_rows: list[dict[str, Any]] = []

    for page_number in range(1, max_pages + 1):
        if next_feed_url in seen_feed_urls:
            raise OrdinaryControlCensusError("Blogger feed pagination loop detected")
        seen_feed_urls.add(next_feed_url)
        body, feed_sha = fetch_atom(next_feed_url, timeout=timeout)
        posts, returned_next_url, page_stats = scan_all_speakers_atom_page(
            body,
            target_author=target_author,
            allowed_single_token_labels=allowed_single,
        )
        page_rows.append(
            {
                "page_number": page_number,
                "feed_sha256": feed_sha,
                "entry_count": page_stats["entry_count"],
                "explicitly_labeled_entry_count": page_stats[
                    "explicitly_labeled_entry_count"
                ],
                "next_present": bool(returned_next_url),
            }
        )
        for post in posts:
            identity = str(post["post_identity_sha256"])
            existing = posts_by_id.get(identity)
            if existing is not None and existing != post:
                raise OrdinaryControlCensusError(
                    f"conflicting duplicate post identity: {identity}"
                )
            posts_by_id[identity] = post
        if not returned_next_url:
            break
        next_feed_url = returned_next_url
    else:
        raise OrdinaryControlCensusError(
            f"Blogger feed paging exceeded max_pages={max_pages}"
        )

    posts = [posts_by_id[key] for key in sorted(posts_by_id)]
    speaker_rows = _build_speaker_rows(
        posts,
        target_author=target_author,
        active_roles=active_roles,
        thresholds=thresholds,
    )
    if not any(row["exact_casefold_identity"] == target_key for row in speaker_rows):
        raise OrdinaryControlCensusError(
            "target author was not found as an explicit speaker label"
        )

    active_ordinary = sum(
        1 for row in active_roles.values() if row["role"] == "ordinary-matched-control"
    )
    minimum_ordinary = int(
        (role_spec.get("minimum_evidence") or {}).get(
            "ordinary_matched_controls_before_rewrite_degradation_claim", 2
        )
    )
    needed = max(0, minimum_ordinary - active_ordinary)
    candidates = [
        row for row in speaker_rows if row["preliminary_ordinary_control_candidate"]
    ]

    feed_identity = _sha256_text(
        "\n".join(
            f"{row['page_number']}\t{row['feed_sha256']}\t{row['entry_count']}"
            for row in page_rows
        )
    )
    speaker_identity = _sha256_text(
        "\n".join(
            f"{row['exact_casefold_identity']}\t{row['explicit_thread_count']}\t"
            f"{row['marker_count']}\t{row['post_identity_set_sha256']}"
            for row in sorted(
                speaker_rows, key=lambda item: item["exact_casefold_identity"]
            )
        )
    )
    result = {
        "schema_version": 1,
        "date": spec.get("date"),
        "status": "ordinary-control-speaker-census-not-profile-admission",
        "raw_or_canonical_prose_in_output": False,
        "method_decision": spec.get("method_decision"),
        "target_author": target_author,
        "active_author_roles": [active_roles[key] for key in sorted(active_roles)],
        "candidate_thresholds": thresholds,
        "allowed_single_token_labels": allowed_single,
        "feed_page_count": len(page_rows),
        "archive_post_count": len(posts),
        "explicitly_labeled_post_count": sum(
            1 for post in posts if post["explicit_speaker_labels"]
        ),
        "feed_snapshot_sha256": feed_identity,
        "speaker_census_sha256": speaker_identity,
        "feed_pages": page_rows,
        "speaker_count": len(speaker_rows),
        "speakers": speaker_rows,
        "preliminary_candidate_count": len(candidates),
        "preliminary_candidates": candidates,
        "active_ordinary_matched_control_count": active_ordinary,
        "minimum_ordinary_matched_controls_required": minimum_ordinary,
        "additional_ordinary_controls_required": needed,
        "candidate_supply_meets_count_requirement": len(candidates) >= needed,
        "identity_and_word_audit_still_required": True,
        "profile_extraction_authorized": False,
        "interpretation_rule": spec.get("interpretation_rule"),
    }

    _assert_metadata_only(result)
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True)
    if "http://" in encoded or "https://" in encoded:
        raise OrdinaryControlCensusError(
            "metadata census unexpectedly contains a raw URL"
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m pangram_lab.dharma_ordinary_control_census"
    )
    parser.add_argument(
        "spec",
        nargs="?",
        default="state/IDIOLECT-ORDINARY-CONTROL-CENSUS-SPEC-2026-08-18.json",
    )
    parser.add_argument(
        "--out",
        default=".local/idiolect-corpus/dharma-ordinary-control-census.json",
    )
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--max-pages", type=int, default=10)
    args = parser.parse_args(argv)

    try:
        result = run_census(
            Path(args.spec),
            out_path=Path(args.out),
            timeout=args.timeout,
            page_size=args.page_size,
            max_pages=args.max_pages,
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
