from __future__ import annotations

import json
import sys
from html.parser import HTMLParser
from pathlib import Path

from .corpus_acquire import fetch_html, iter_inventory_items


class SpeakerMarkupScanner(HTMLParser):
    """Record only tag/id/class paths where a target speaker name occurs.

    No surrounding prose is retained. This is a structural diagnostic for
    selecting the correct Blogger comment/thread extractor without exposing or
    committing comment text.
    """

    def __init__(self, speaker: str):
        super().__init__(convert_charrefs=True)
        self.speaker = speaker.casefold()
        self.stack: list[tuple[str, str, tuple[str, ...]]] = []
        self.paths: list[str] = []
        self.data_occurrences = 0

    @staticmethod
    def _node(tag: str, attrs) -> tuple[str, str, tuple[str, ...]]:
        amap = {str(k).lower(): (v or "") for k, v in attrs}
        node_id = amap.get("id", "")
        classes = tuple(part for part in amap.get("class", "").split() if part)
        return tag.lower(), node_id, classes

    @staticmethod
    def _format_node(node: tuple[str, str, tuple[str, ...]]) -> str:
        tag, node_id, classes = node
        out = tag
        if node_id:
            out += "#" + node_id
        if classes:
            out += "." + ".".join(classes)
        return out

    def handle_starttag(self, tag: str, attrs):
        self.stack.append(self._node(tag, attrs))

    def handle_startendtag(self, tag: str, attrs):
        self.stack.append(self._node(tag, attrs))
        self.stack.pop()

    def handle_endtag(self, tag: str):
        tag = tag.lower()
        for idx in range(len(self.stack) - 1, -1, -1):
            if self.stack[idx][0] == tag:
                del self.stack[idx:]
                return

    def handle_data(self, data: str):
        count = data.casefold().count(self.speaker)
        if not count:
            return
        self.data_occurrences += count
        path = " > ".join(self._format_node(node) for node in self.stack[-10:])
        if path and path not in self.paths:
            self.paths.append(path)


def diagnose_html(html: str, speaker: str) -> dict:
    scanner = SpeakerMarkupScanner(speaker)
    scanner.feed(html)
    return {
        "raw_html_name_occurrences": html.casefold().count(speaker.casefold()),
        "visible_data_name_occurrences": scanner.data_occurrences,
        "speaker_markup_paths": scanner.paths[:12],
    }


def diagnose_inventory(inventory_path: Path, *, timeout: int = 30) -> dict:
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    results = []
    errors = []
    for item in iter_inventory_items(inventory):
        mode = item.get("extraction_mode", "")
        if not mode.startswith("speaker-prefix:"):
            continue
        sample_id = item.get("sample_id")
        url = item.get("url")
        speaker = mode.split(":", 1)[1].strip()
        try:
            html, source_sha = fetch_html(url, timeout=timeout)
            results.append(
                {
                    "sample_id": sample_id,
                    "source_html_sha256": source_sha,
                    "speaker": speaker,
                    **diagnose_html(html, speaker),
                }
            )
        except Exception as exc:
            errors.append({"sample_id": sample_id, "error": str(exc)})
    return {
        "schema_version": 1,
        "raw_or_canonical_prose_in_output": False,
        "results": results,
        "errors": errors,
    }


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="python -m pangram_lab.dharma_markup_diagnostic")
    parser.add_argument(
        "inventory",
        nargs="?",
        default="state/IDIOLECT-LEGACY-TRIAGE-QUEUE-2026-08-18.json",
    )
    parser.add_argument("--out", default=".local/idiolect-corpus/dharma-markup-diagnostic.json")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args(argv)

    result = diagnose_inventory(Path(args.inventory), timeout=args.timeout)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if result["errors"]:
        print(json.dumps(result["errors"], ensure_ascii=False, indent=2), file=sys.stderr)
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
