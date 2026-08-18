from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from .corpus_acquire import (
    PostBodyParser,
    canonicalize,
    fetch_html,
    iter_inventory_items,
    normalize_visible_text,
)

_NAME_TOKEN = r"[A-Z][A-Za-zÀ-ÖØ-öø-ÿ.'’\-]*"
_COLON_SPEAKER_RE = re.compile(
    rf"^\s*({_NAME_TOKEN}(?:\s+{_NAME_TOKEN}){{0,4}})\s*:\s*(.*?)\s*$"
)
_STANDALONE_MULTIWORD_NAME_RE = re.compile(
    rf"^\s*({_NAME_TOKEN}(?:\s+{_NAME_TOKEN}){{1,4}})\s*$"
)
_PLATFORM_CONTROL_RE = re.compile(
    r"^(?:Like|Reply|Replies|Delete|Edit|Share|Show \d+ more replies|Load more|See more)$",
    re.IGNORECASE,
)
_PLATFORM_TIME_RE = re.compile(
    r"^(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)?\s*,?\s*"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)?\s*"
    r"\d{0,2}(?:st|nd|rd|th)?\s*,?\s*\d{4}?\s*,?\s*"
    r"\d{1,2}:\d{2}\s*(?:AM|PM)?(?:\s+via\s+\w+)?$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SpeakerExtraction:
    text: str
    target_marker_count: int
    other_speaker_boundary_count: int
    standalone_boundary_count: int
    ambiguous_single_word_line_count: int


def _speaker_key(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().rstrip(":"), flags=re.UNICODE).casefold()


def _looks_like_standalone_name(line: str) -> str | None:
    """Return a conservative multiword speaker-like label, else ``None``.

    Single-word capitalized lines are deliberately not treated as speaker
    boundaries: too many legitimate prose lines (for example, ``Interesting``)
    would become false boundaries. They are counted as ambiguous while a target
    speaker is active so manual review can catch a one-name discussion format.
    """
    m = _STANDALONE_MULTIWORD_NAME_RE.match(line)
    if not m:
        return None
    candidate = m.group(1).strip()
    if candidate.isupper():
        return None
    return candidate


def extract_named_speaker_blocks(text: str, speaker: str) -> SpeakerExtraction:
    """Extract only blocks explicitly introduced by ``speaker``.

    Unlike the original line-only helper, this parser supports discussion HTML
    where the speaker label and comment body survive extraction on different
    lines. It never assigns unlabeled text before the first target marker. Once
    active, collection stops at another explicit ``Name:`` label or a
    conservative standalone multiword human-name line.
    """
    normalized = normalize_visible_text(text)
    target = _speaker_key(speaker)
    active = False
    kept: list[str] = []
    target_markers = 0
    other_boundaries = 0
    standalone_boundaries = 0
    ambiguous_single_word = 0

    for raw_line in normalized.splitlines():
        line = raw_line.strip()

        if not line:
            if active and kept and kept[-1] != "":
                kept.append("")
            continue

        if _PLATFORM_CONTROL_RE.match(line) or _PLATFORM_TIME_RE.match(line):
            continue

        colon = _COLON_SPEAKER_RE.match(line)
        if colon:
            label, remainder = colon.group(1).strip(), colon.group(2).strip()
            if _speaker_key(label) == target:
                active = True
                target_markers += 1
                if remainder:
                    kept.append(remainder)
            else:
                if active:
                    other_boundaries += 1
                active = False
            continue

        if _speaker_key(line) == target:
            active = True
            target_markers += 1
            continue

        standalone = _looks_like_standalone_name(line)
        if standalone is not None:
            if _speaker_key(standalone) == target:
                active = True
                target_markers += 1
            else:
                if active:
                    other_boundaries += 1
                    standalone_boundaries += 1
                active = False
            continue

        if active and re.fullmatch(r"[A-Z][A-Za-zÀ-ÖØ-öø-ÿ.'’\-]{1,24}", line):
            ambiguous_single_word += 1

        if active:
            kept.append(line)

    while kept and kept[-1] == "":
        kept.pop()
    return SpeakerExtraction(
        text=normalize_visible_text("\n".join(kept)),
        target_marker_count=target_markers,
        other_speaker_boundary_count=other_boundaries,
        standalone_boundary_count=standalone_boundaries,
        ambiguous_single_word_line_count=ambiguous_single_word,
    )


def extract_blogspot_named_speaker(html: str, speaker: str) -> SpeakerExtraction:
    parser = PostBodyParser(drop_blockquotes=True)
    parser.feed(html)
    if not parser.found_body:
        raise ValueError("no recognized authored post-body container found")
    return extract_named_speaker_blocks(parser.text(), speaker)


def acquire_speaker_inventory(
    inventory_path: Path,
    *,
    out_dir: Path,
    manifest_out: Path,
    sample_ids: set[str] | None = None,
    timeout: int = 30,
) -> dict:
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    errors: list[dict] = []

    for item in iter_inventory_items(inventory):
        sample_id = item.get("sample_id")
        if not sample_id or (sample_ids and sample_id not in sample_ids):
            continue
        mode = item.get("extraction_mode", "")
        if not mode.startswith("speaker-prefix:"):
            continue
        url = item.get("url")
        speaker = mode.split(":", 1)[1].strip()
        if not url or not speaker:
            errors.append({"sample_id": sample_id, "error": "missing-url-or-speaker"})
            continue
        try:
            raw_html, raw_sha = fetch_html(url, timeout=timeout)
            extraction = extract_blogspot_named_speaker(raw_html, speaker)
            if extraction.target_marker_count == 0:
                raise ValueError("target-speaker-marker-not-found")
            canon = canonicalize(extraction.text)
            if canon.word_count == 0:
                raise ValueError("target-speaker-marker-found-but-no-authored-words")
            path = out_dir / f"{sample_id}.txt"
            path.write_text(canon.text + "\n", encoding="utf-8")
            flags = list(canon.quality_flags)
            if extraction.ambiguous_single_word_line_count:
                flags.append("ambiguous-single-word-lines-inside-speaker-block")
            results.append(
                {
                    "sample_id": sample_id,
                    "site_group": item.get("site_group"),
                    "source_group": item.get("source_group"),
                    "title": item.get("title"),
                    "date": item.get("date"),
                    "url": url,
                    "speaker": speaker,
                    "provenance": item.get("provenance"),
                    "modality": item.get("modality"),
                    "registers": item.get("registers", []),
                    "source_html_sha256": raw_sha,
                    "canonical_sha256": canon.sha256,
                    "word_count": canon.word_count,
                    "redactions": canon.redactions,
                    "quality_flags": flags,
                    "target_marker_count": extraction.target_marker_count,
                    "other_speaker_boundary_count": extraction.other_speaker_boundary_count,
                    "standalone_boundary_count": extraction.standalone_boundary_count,
                    "ambiguous_single_word_line_count": extraction.ambiguous_single_word_line_count,
                    "local_text_path": str(path),
                }
            )
        except Exception as exc:
            errors.append({"sample_id": sample_id, "url": url, "speaker": speaker, "error": str(exc)})

    runtime = {
        "schema_version": 1,
        "inventory": str(inventory_path),
        "raw_or_canonical_prose_in_output": False,
        "results": results,
        "errors": errors,
    }
    manifest_out.write_text(
        json.dumps(runtime, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return runtime


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="python -m pangram_lab.dharma_speaker_acquire")
    parser.add_argument(
        "inventory",
        nargs="?",
        default="state/IDIOLECT-LEGACY-TRIAGE-QUEUE-2026-08-18.json",
    )
    parser.add_argument("--out-dir", default=".local/idiolect-corpus/dharma-speaker-text")
    parser.add_argument(
        "--manifest-out",
        default=".local/idiolect-corpus/dharma-speaker-manifest.json",
    )
    parser.add_argument("--sample-id", action="append", default=[])
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args(argv)

    runtime = acquire_speaker_inventory(
        Path(args.inventory),
        out_dir=Path(args.out_dir),
        manifest_out=Path(args.manifest_out),
        sample_ids=set(args.sample_id) if args.sample_id else None,
        timeout=args.timeout,
    )
    print(
        json.dumps(
            {
                "acquired": len(runtime["results"]),
                "errors": len(runtime["errors"]),
                "manifest": args.manifest_out,
            },
            indent=2,
        )
    )
    if runtime["errors"]:
        print(json.dumps(runtime["errors"], ensure_ascii=False, indent=2), file=sys.stderr)
    return 0 if runtime["results"] or not runtime["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
