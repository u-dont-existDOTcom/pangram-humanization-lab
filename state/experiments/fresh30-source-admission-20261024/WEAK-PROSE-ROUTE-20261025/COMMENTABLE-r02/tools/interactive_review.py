#!/usr/bin/env python3
"""Generate Joel's interactive side-by-side article review interface.

This is the implemented counterpart to REVIEW-INTERFACE-SPEC.md. It preserves
and generalizes the previously browser-tested Somatic Article interface:
comments, exact selected-text notes, Keep/Remove/Brainstorm, reasoning, four
second-line rhetoric sliders, local persistence, changed-only filtering, search,
JSON/MD exports, comparison baselines, and a one-column full-draft commentable mode.

Usage:
  python interactive_review.py original.html revised.html --template review_interface_template.html --out review.html
  python interactive_review.py --full-draft revised.html --template review_interface_template.html --out full-draft-review.html
  python interactive_review.py --quick-diff changes.diff.html --template review_interface_template.html --out review.html
  python interactive_review.py --selftest --template review_interface_template.html

The script writes files only and never opens or renders them.
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import html
import json
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:  # pragma: no cover
    BeautifulSoup = None

BLOCK_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "pre", "figcaption"}
INTERFACE_FORMAT = "joel-commentable-diff-review-v4"
GENERATOR_VERSION = "4.3-context"


@dataclass
class Block:
    kind: str
    text: str
    section: str
    source_html: str = ""
    native_type: str = ""
    canonical_url: str = ""

    @property
    def norm(self) -> str:
        return normalize(self.text)

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.norm.encode("utf-8")).hexdigest()


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(text or "")).strip()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "article-review"


def class_tokens(node) -> set[str]:
    if not getattr(node, "attrs", None):
        return set()
    cls = node.get("class") or []
    if isinstance(cls, str):
        cls = cls.split()
    return {str(x) for x in cls}


def component_name(node) -> str:
    return str(node.get("data-component-name") or "") if getattr(node, "get", None) else ""


def first_url(node) -> str:
    if not getattr(node, "find", None):
        return ""
    for attr in ("href", "src", "data-url", "data-post-url"):
        if node.get(attr):
            return str(node.get(attr))
    child = node.find(
        lambda t: getattr(t, "get", None)
        and any(t.get(a) for a in ("href", "src", "data-url", "data-post-url"))
    )
    if child:
        for attr in ("href", "src", "data-url", "data-post-url"):
            if child.get(attr):
                return str(child.get(attr))
    return ""


def detect_native(node) -> tuple[str, str] | None:
    if not getattr(node, "name", None):
        return None
    cls = class_tokens(node)
    comp = component_name(node).lower()
    joined = " ".join(cls).lower()

    if "digest-post-embed" in cls or "digest-post-embed" in joined:
        return ("post preview", first_url(node))
    if "comment" in cls or "comment-card" in joined or "comment" in comp:
        return ("comment card", first_url(node))
    if "subscription-widget-wrap-editor" in cls or "subscribewidgettodom" in comp:
        return ("subscribe widget", first_url(node))
    if "buttoncreatebutton" in comp or ("share" in joined and "button" in joined):
        return ("share button", first_url(node))
    if "paywall" in joined or "paywall" in comp or node.get("data-paywall") is not None:
        return ("paywall marker", first_url(node))
    if "instagram" in joined or "instagram" in comp:
        return ("post preview", first_url(node))
    if node.name in {"iframe", "video"} or "youtube" in joined or "youtube" in comp or "video" in comp:
        return ("video embed", first_url(node))
    if "captioned-image-container" in cls or (
        node.name in {"figure", "picture"} and node.find(["img", "picture", "source"])
    ):
        return ("image", first_url(node))
    if node.name == "img":
        return ("image", first_url(node))
    if node.get("data-component-name") or node.get("data-attrs"):
        return ("unknown native object", first_url(node))
    return None


def native_label(kind: str, url: str, caption: str = "") -> str:
    base = f"[{kind}]"
    if caption:
        base += " " + normalize(caption)
    if url:
        base += " — " + url
    return base


def extract_blocks(raw: str) -> list[Block]:
    if BeautifulSoup is None:
        raise RuntimeError("BeautifulSoup4 is required for interactive review generation")
    soup = BeautifulSoup(raw, "html.parser")
    root = soup.find("article") or soup.select_one(".body.markup") or soup.find("main") or soup.body or soup
    blocks: list[Block] = []
    current_section = "Opening"

    def emit(kind: str, text: str, source_html: str = "", native_type: str = "", canonical_url: str = "") -> None:
        nonlocal current_section
        text = normalize(text)
        if not text:
            return
        if kind.startswith("h") and len(kind) == 2 and kind[1].isdigit():
            current_section = text
        blocks.append(
            Block(
                kind=kind,
                text=text,
                section=current_section,
                source_html=source_html,
                native_type=native_type,
                canonical_url=canonical_url,
            )
        )

    def walk(node) -> None:
        if not getattr(node, "name", None):
            return
        native = detect_native(node)
        if native:
            kind, url = native
            caption_node = node.find("figcaption") if getattr(node, "find", None) else None
            caption = caption_node.get_text(" ", strip=True) if caption_node else ""
            emit(kind, native_label(kind, url, caption), str(node), kind, url)
            return
        name = str(node.name).lower()
        if name in BLOCK_TAGS:
            emit(name, node.get_text(" ", strip=True), str(node))
            return
        for child in getattr(node, "children", []):
            if getattr(child, "name", None):
                walk(child)

    walk(root)
    return blocks


def blocks_from_quick_diff(raw: str) -> tuple[list[Block], list[Block]]:
    if BeautifulSoup is None:
        raise RuntimeError("BeautifulSoup4 is required")
    soup = BeautifulSoup(raw, "html.parser")
    old: list[Block] = []
    new: list[Block] = []

    def collect(container, target: list[Block], section: str) -> None:
        if not container:
            return
        nodes = []
        for node in container.find_all(list(BLOCK_TAGS), recursive=True):
            parent_block = node.find_parent(list(BLOCK_TAGS))
            if parent_block and parent_block is not container:
                continue
            nodes.append(node)
        if nodes:
            for node in nodes:
                text = normalize(node.get_text(" ", strip=True))
                if text:
                    target.append(Block(str(node.name).lower(), text, section, str(node)))
        else:
            text = normalize(container.get_text(" ", strip=True))
            if text:
                target.append(Block("p", text, section, str(container)))

    for sec in soup.find_all("section"):
        heading_node = sec.find(["h1", "h2", "h3"])
        section = normalize(heading_node.get_text(" ", strip=True)) if heading_node else "Changed passage"
        # Matching synthetic section headings create hard alignment boundaries so
        # a previous-wording placeholder cannot be paired with a later section.
        old.append(Block("h2", section, section, ""))
        new.append(Block("h2", section, section, ""))
        add = sec.select_one(".addition") or sec.select_one(".revised")
        delete = sec.select_one(".deletion") or sec.select_one(".removed")
        collect(delete, old, section)
        collect(add, new, section)
    return old, new


def token_markup(old: str, new: str, side: str) -> str:
    old_tokens = re.findall(r"\s+|[^\s]+", old)
    new_tokens = re.findall(r"\s+|[^\s]+", new)
    sm = difflib.SequenceMatcher(a=old_tokens, b=new_tokens, autojunk=False)
    out: list[str] = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if side == "old":
            chunk = "".join(old_tokens[i1:i2])
            if not chunk:
                continue
            esc = html.escape(chunk)
            out.append(esc if op == "equal" else f"<del>{esc}</del>")
        else:
            chunk = "".join(new_tokens[j1:j2])
            if not chunk:
                continue
            esc = html.escape(chunk)
            out.append(esc if op == "equal" else f"<mark>{esc}</mark>")
    return "".join(out)


def passage_tag(kind: str) -> str:
    return kind if kind in BLOCK_TAGS else "p"


def passage_html(block: Block, content: str) -> str:
    tag = passage_tag(block.kind)
    cls_kind = re.sub(r"[^a-z0-9_-]+", "-", block.kind.lower())
    return f'<{tag} class="passage passage-{cls_kind}">{content}</{tag}>'


def tuner_html() -> str:
    return (
        '<div class="tuners" aria-label="Passage revision settings">'
        '<label class="tuner" title="Humor"><span>Humor</span><input class="humor-slider" type="range" min="0" max="4" step="1" value="2" aria-label="Humor"><output>Cur</output></label>'
        '<label class="tuner" title="Technical detail"><span>Technical detail</span><input class="tech-slider" type="range" min="0" max="4" step="1" value="2" aria-label="Technical detail"><output>Cur</output></label>'
        '<label class="tuner" title="Length"><span>Length</span><input class="length-slider" type="range" min="0" max="4" step="1" value="2" aria-label="Length"><output>Cur</output></label>'
        '<label class="tuner" title="Bluntness"><span>Bluntness</span><input class="blunt-slider" type="range" min="0" max="4" step="1" value="2" aria-label="Bluntness"><output>Cur</output></label>'
        '</div>'
    )

def actions_html() -> str:
    return (
        '<div class="cell-actions">'
        '<button type="button" class="decision-btn keep-btn" data-decision="keep">Keep</button>'
        '<button type="button" class="decision-btn remove-btn" data-decision="remove">Remove</button>'
        '<button type="button" class="decision-btn brainstorm-btn" data-decision="brainstorm">Brainstorm</button>'
        '<button type="button" class="why-btn" title="Why was this changed?">?</button>'
        '<button type="button" class="comment-btn" title="Add or edit the comment for this box">＋</button>'
        '</div>'
    )


def relation_chip(relation: str, target: str) -> str:
    if not relation:
        return ""
    css_class = re.sub(r"[^a-z0-9_-]+", "-", relation.lower())
    return (
        f'<button type="button" class="relation-chip relation-{css_class}" '
        f'data-target-row="{html.escape(target or "", quote=True)}" title="Show relation details">'
        f'{html.escape(relation.title())}</button>'
    )


def cell_html(
    row_id: str,
    side: str,
    label: str,
    block: Block | None,
    content: str,
    relation: str = "",
    target: str = "",
    *,
    context_only: bool = False,
    context_position: str = "",
    empty_message: str = "—",
) -> str:
    if block is None:
        return f'<div class="diff-cell empty"><span>{html.escape(empty_message)}</span></div>'
    if context_only:
        kicker = "Context"
        if context_position == "before":
            kicker = "Context immediately before"
        elif context_position == "after":
            kicker = "Context immediately after"
        return (
            f'<div class="diff-cell context-cell {side}" data-context-only="true">'
            f'<div class="context-kicker">{html.escape(kicker)}</div>'
            f'<div class="passage-wrap">{passage_html(block, html.escape(block.text))}</div>'
            '</div>'
        )
    key = f"{row_id}:{side}"
    return (
        f'<div class="diff-cell {side}" data-cell-key="{html.escape(key)}" data-row-id="{row_id}" data-side="{side}">'
        f'<div class="cell-top"><div class="cell-headline"><span class="cell-id">{html.escape(label)} · {row_id}</span>'
        f'{relation_chip(relation, target)}{actions_html()}</div>{tuner_html()}</div>'
        f'<div class="passage-wrap">{passage_html(block, content)}</div>'
        '<span class="comment-badge" aria-label="comment saved"></span></div>'
    )

def default_reason(state: str) -> dict:
    if state == "equal":
        return {
            "summary": "Preserved unchanged because it still performs a distinct function and no correction applied.",
            "origin": "original source",
            "instructions": [
                "Edit Contract: preserve propositions, certainty, links, and actor/action/object relations unless Joel authorizes a change."
            ],
        }
    if state == "added":
        return {
            "summary": "Added in the revised version. Review the addition's function, provenance, and permission before approval.",
            "origin": "revised source",
            "instructions": [
                "Confirm that the addition is authorized and that its required context, audience, and evidence remain intact."
            ],
        }
    if state == "removed":
        return {
            "summary": "Absent from the revised version. Confirm whether it was moved, consolidated, owner-deleted, or structurally removed before approving deletion.",
            "origin": "original source",
            "instructions": [
                "Run the dependency and orphan audits before treating absence as deletion."
            ],
        }
    return {
        "summary": "Rewritten in the revised version. Compare meaning, certainty, voice, audience, and rhetorical function rather than assuming newer wording is better.",
        "origin": "original and revised source",
        "instructions": [
            "Preserve propositions, certainty, links, actor/action/object relations, rhetorical function, and required context unless the edit contract authorizes change."
        ],
    }


def load_reason_map(path: Path | None) -> dict:
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Reason map must be a JSON object")
    return data.get("by_row", data)


def align_blocks(old: list[Block], new: list[Block], reason_map: dict | None = None) -> list[dict]:
    reason_map = reason_map or {}
    sm = difflib.SequenceMatcher(a=[b.norm for b in old], b=[b.norm for b in new], autojunk=False)
    rows: list[dict] = []
    counter = 0

    def add(state: str, old_block: Block | None, new_block: Block | None) -> None:
        nonlocal counter
        counter += 1
        row_id = f"r{counter:04d}"
        classification = {
            "equal": "Preserved",
            "changed": "Rewritten",
            "added": "Added",
            "removed": "Structurally removed",
        }[state]
        row = {
            "id": row_id,
            "state": state,
            "classification": classification,
            "relation": "",
            "target": "",
            "old": old_block,
            "new": new_block,
            "reason": default_reason(state),
            "audience_status": "",
            "audience_drift_type": "",
        }
        patch = reason_map.get(row_id)
        if isinstance(patch, dict):
            for key in ("classification", "relation", "target", "audience_status", "audience_drift_type"):
                if key in patch:
                    row[key] = patch[key]
            if isinstance(patch.get("reason"), dict):
                row["reason"] = {**row["reason"], **patch["reason"]}
        rows.append(row)

    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for old_block, new_block in zip(old[i1:i2], new[j1:j2]):
                add("equal", old_block, new_block)
        elif op == "replace":
            old_slice = old[i1:i2]
            new_slice = new[j1:j2]
            for index in range(max(len(old_slice), len(new_slice))):
                old_block = old_slice[index] if index < len(old_slice) else None
                new_block = new_slice[index] if index < len(new_slice) else None
                add("changed" if old_block and new_block else "removed" if old_block else "added", old_block, new_block)
        elif op == "delete":
            for old_block in old[i1:i2]:
                add("removed", old_block, None)
        elif op == "insert":
            for new_block in new[j1:j2]:
                add("added", None, new_block)

    removed_by_text: dict[str, list[dict]] = {}
    added_by_text: dict[str, list[dict]] = {}
    for row in rows:
        if row["state"] == "removed" and row["old"]:
            removed_by_text.setdefault(row["old"].norm, []).append(row)
        if row["state"] == "added" and row["new"]:
            added_by_text.setdefault(row["new"].norm, []).append(row)
    for text, removed_rows in removed_by_text.items():
        added_rows = added_by_text.get(text, [])
        if len(removed_rows) == 1 and len(added_rows) == 1:
            removed_row = removed_rows[0]
            added_row = added_rows[0]
            reason = {
                "summary": "Moved intact to another location.",
                "origin": "original and revised source",
                "instructions": [
                    "Verify that the moved passage retains its setup, antecedent, section function, links, and media anchors."
                ],
            }
            for row, target in ((removed_row, added_row), (added_row, removed_row)):
                row["classification"] = "Moved"
                row["relation"] = "moved"
                row["target"] = target["id"]
                row["reason"] = reason
    return rows


def contextual_changed_rows(rows: list[dict], radius: int = 1) -> list[dict]:
    """Keep each changed row plus nearby unchanged rows as read-only placement context."""
    changed = [i for i, row in enumerate(rows) if row["state"] != "equal"]
    if not changed:
        return []
    keep: set[int] = set()
    for i in changed:
        for j in range(max(0, i - radius), min(len(rows), i + radius + 1)):
            keep.add(j)
    out: list[dict] = []
    changed_set = set(changed)
    for i in sorted(keep):
        row = dict(rows[i])
        row["context_only"] = row["state"] == "equal"
        row["context_position"] = ""
        row["placement"] = ""
        if row["context_only"]:
            before = any(j in changed_set for j in range(i + 1, min(len(rows), i + radius + 1)))
            after = any(j in changed_set for j in range(max(0, i - radius), i))
            row["context_position"] = "before" if before and not after else "after" if after and not before else ""
            row["classification"] = "Context"
        else:
            row["placement"] = {
                "added": "Inserted here — between the surrounding passages shown in context.",
                "changed": "Replaces the source passage at this exact position.",
                "removed": "Removed from this exact position.",
            }.get(row["state"], "Changed at this exact position.")
        out.append(row)
    return out


def full_draft_rows(blocks: list[Block], reason_map: dict | None = None) -> list[dict]:
    """Create one commentable row per semantic block in the current full draft."""
    reason_map = reason_map or {}
    rows: list[dict] = []
    for index, block in enumerate(blocks, 1):
        row_id = f"r{index:04d}"
        row = {
            "id": row_id,
            "state": "current",
            "classification": "Preserved",
            "relation": "",
            "target": "",
            "old": None,
            "new": block,
            "reason": {
                "summary": "Current full-draft passage. Comment on the whole block or highlight exact wording before pressing ＋.",
                "origin": "current draft",
                "instructions": [
                    "A comment on a heading may address the whole section. A selected-text note records the exact quote and character offsets."
                ],
            },
            "audience_status": "",
            "audience_drift_type": "",
        }
        patch = reason_map.get(row_id)
        if isinstance(patch, dict):
            for key in ("classification", "relation", "target", "audience_status", "audience_drift_type"):
                if key in patch:
                    row[key] = patch[key]
            if isinstance(patch.get("reason"), dict):
                row["reason"] = {**row["reason"], **patch["reason"]}
        rows.append(row)
    return rows


def rows_html(rows: list[dict], source_label: str, new_label: str, view_mode: str = "comparison") -> tuple[str, dict]:
    chunks: list[str] = []
    if view_mode == "comparison":
        chunks.append(
            '<div class="column-heads"><div class="column-head">'
            + html.escape(source_label)
            + '</div><div class="column-head">'
            + html.escape(new_label)
            + "</div></div>"
        )
    row_data: dict[str, dict] = {}
    last_section: str | None = None

    def block_data(block: Block | None) -> dict | None:
        if block is None:
            return None
        return {
            "section": block.section,
            "text": block.text,
            "kind": block.kind,
            "sha256": block.sha256,
            "native_type": block.native_type,
            "canonical_url": block.canonical_url,
        }

    for row in rows:
        row_id = row["id"]
        old_block = row["old"]
        new_block = row["new"]
        section = (new_block.section if new_block else old_block.section if old_block else "") or "Unheaded"
        if section != last_section:
            chunks.append(
                f'<div class="section-label" data-section="{html.escape(section, quote=True)}">'
                f'<span class="section-kicker">Article section</span>{html.escape(section)}</div>'
            )
            last_section = section

        if row.get("placement"):
            chunks.append(
                f'<div class="placement-note state-{html.escape(row["state"])}">'
                f'<strong>{html.escape(row["classification"])}</strong>'
                f'<span>{html.escape(row["placement"])}</span></div>'
            )

        state = row["state"]
        context_only = bool(row.get("context_only"))
        context_position = row.get("context_position", "")
        if view_mode == "full-draft":
            if not new_block:
                continue
            new_content = html.escape(new_block.text)
            chunks.append(
                f'<div class="diff-row state-current single-row" id="{row_id}" data-state="current">'
                + cell_html(row_id, "new", new_label, new_block, new_content, row["relation"], row["target"])
                + "</div>"
            )
        else:
            if old_block and new_block:
                old_content = html.escape(old_block.text) if state == "equal" else token_markup(old_block.text, new_block.text, "old")
                new_content = html.escape(new_block.text) if state == "equal" else token_markup(old_block.text, new_block.text, "new")
            elif old_block:
                old_content = f"<del>{html.escape(old_block.text)}</del>"
                new_content = ""
            else:
                old_content = ""
                new_content = f"<mark>{html.escape(new_block.text)}</mark>"

            old_empty = "New insertion — there was no source passage at this position." if state == "added" else "—"
            new_empty = "Removed — no revised passage occupies this position." if state == "removed" else "—"
            classes = f"diff-row state-{state}" + (" context-row" if context_only else "")
            chunks.append(
                f'<div class="{classes}" id="{row_id}" data-state="{state}">'
                + cell_html(row_id, "old", source_label, old_block, old_content, row["relation"], row["target"],
                            context_only=context_only, context_position=context_position, empty_message=old_empty)
                + cell_html(row_id, "new", new_label, new_block, new_content, row["relation"], row["target"],
                            context_only=context_only, context_position=context_position, empty_message=new_empty)
                + "</div>"
            )
        if not context_only:
            row_data[row_id] = {
                "state": state,
                "classification": row["classification"],
                "relation": row["relation"],
                "target": row["target"],
                "old": block_data(old_block),
                "new": block_data(new_block),
                "reason": row["reason"],
                "audience_status": row["audience_status"],
                "audience_drift_type": row["audience_drift_type"],
            }
    return "".join(chunks), row_data

def build_document(
    template: str,
    *,
    title: str,
    artifact_id: str,
    baseline_type: str,
    row_scope: str,
    source_label: str,
    new_label: str,
    source_filename: str,
    revised_filename: str,
    source_version: str,
    new_version: str,
    source_sha: str,
    revised_sha: str,
    rows: list[dict],
    export_basename: str,
    audience_contract: dict | None = None,
    view_mode: str = "comparison",
) -> str:
    main_html, row_data = rows_html(rows, source_label, new_label, view_mode=view_mode)
    meta = {
        "interface_format": INTERFACE_FORMAT,
        "generator_version": GENERATOR_VERSION,
        "title": title,
        "artifact_id": artifact_id,
        "baseline_type": baseline_type,
        "row_scope": row_scope,
        "view_mode": view_mode,
        "source_label": source_label,
        "new_label": new_label,
        "source_filename": source_filename,
        "revised_filename": revised_filename,
        "source_version": source_version,
        "new_version": new_version,
        "source_sha256": source_sha,
        "revised_sha256": revised_sha,
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "export_basename": export_basename,
        "required_features": [
            "exact selected-text comments", "whole-cell comments", "Keep", "Remove", "Brainstorm", "reasoning",
            "Humor", "Technical detail", "Length", "Bluntness", "Copy JSON", "Copy Markdown",
            "Export JSON", "Export Markdown", "local persistence", "search", "changed-only filtering",
            "full-draft commentable mode",
        ],
        "audience_contract": audience_contract or {},
        "static_slider_behavior": (
            "Humor, technical detail, length, and bluntness settings record passage-level revision instructions; "
            "they do not rewrite text inside this static file or authorize changes to claims, evidence, certainty, "
            "recommendations, attribution, causal meaning, links, or native-object placement."
        ),
        "rows": row_data,
    }
    review_json = json.dumps(meta, ensure_ascii=False).replace("</", "<\\/")
    body_class = "single-view" if view_mode == "full-draft" else "comparison-view"
    return (
        template.replace("__TITLE__", html.escape(title))
        .replace("__BODY_CLASS__", body_class)
        .replace("__MAIN__", main_html)
        .replace("__REVIEW_DATA__", review_json)
    )

def run_selftest(template_path: Path) -> int:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        old_path = root / "old.html"
        new_path = root / "new.html"
        old_path.write_text(
            "<article><h2>Start</h2><p>Plain old sentence.</p><p>Moved sentence.</p></article>",
            encoding="utf-8",
        )
        new_path.write_text(
            "<article><h2>Start</h2><p>Plain new sentence with detail.</p><p>Added sentence.</p><p>Moved sentence.</p></article>",
            encoding="utf-8",
        )
        old_blocks = extract_blocks(old_path.read_text())
        new_blocks = extract_blocks(new_path.read_text())
        rows = align_blocks(old_blocks, new_blocks)
        template = template_path.read_text(encoding="utf-8")
        document = build_document(
            template,
            title="Selftest",
            artifact_id="selftest",
            baseline_type="original-vs-current",
            row_scope="all-passages",
            source_label="Original",
            new_label="Revised",
            source_filename=old_path.name,
            revised_filename=new_path.name,
            source_version="r00-approved",
            new_version="r01-candidate",
            source_sha=file_sha(old_path),
            revised_sha=file_sha(new_path),
            rows=rows,
            export_basename="selftest-review",
        )
        changed_rows = [row for row in rows if row["state"] != "equal"]
        changed_document = build_document(
            template,
            title="Selftest changed only",
            artifact_id="selftest-changed",
            baseline_type="original-vs-current",
            row_scope="changed-passages-only",
            source_label="Original · r00-approved",
            new_label="Revised · r01-candidate",
            source_filename=old_path.name,
            revised_filename=new_path.name,
            source_version="r00-approved",
            new_version="r01-candidate",
            source_sha=file_sha(old_path),
            revised_sha=file_sha(new_path),
            rows=changed_rows,
            export_basename="selftest-changed-review",
        )
        context_rows = contextual_changed_rows(rows, radius=1)
        context_document = build_document(
            template,
            title="Selftest contextual changes",
            artifact_id="selftest-context",
            baseline_type="contextual-changes",
            row_scope="contextual-changes",
            source_label="Original · r00-approved",
            new_label="Revised · r01-candidate",
            source_filename=old_path.name,
            revised_filename=new_path.name,
            source_version="r00-approved",
            new_version="r01-candidate",
            source_sha=file_sha(old_path),
            revised_sha=file_sha(new_path),
            rows=context_rows,
            export_basename="selftest-context-review",
        )
        full_rows = full_draft_rows(new_blocks)
        full_document = build_document(
            template,
            title="Selftest full draft",
            artifact_id="selftest-full",
            baseline_type="full-draft-commentable",
            row_scope="full-draft",
            source_label="Draft",
            new_label="Draft · r01-candidate",
            source_filename=new_path.name,
            revised_filename=new_path.name,
            source_version="r01-candidate",
            new_version="r01-candidate",
            source_sha=file_sha(new_path),
            revised_sha=file_sha(new_path),
            rows=full_rows,
            export_basename="selftest-full-review",
            view_mode="full-draft",
        )
        required = [
            "Keep", "Remove", "Brainstorm", "Humor", "Technical detail", "Length", "Bluntness",
            "Export JSON", "Export Markdown", "Copy JSON", "Copy Markdown", "localStorage",
            INTERFACE_FORMAT, "changedOnly", "commentOverlay", "rememberSelection", "selectionSnapshots",
            "review-form-controls-v1", "color-scheme:only light", "-webkit-text-fill-color:#1f2937", "select option:checked",
        ]
        missing = [item for item in required if item not in document]
        cell_count = sum(1 for row in rows for side in ("old", "new") if row[side] is not None)
        changed_scope_ok = '"row_scope": "changed-passages-only"' in changed_document and 'class="diff-row state-equal"' not in changed_document
        contextual_scope_ok = (
            '"row_scope": "contextual-changes"' in context_document
            and 'class="diff-row state-equal context-row"' in context_document
            and 'class="placement-note state-' in context_document
            and 'data-context-only="true"' in context_document
        )
        full_scope_ok = (
            '"row_scope": "full-draft"' in full_document
            and '"view_mode": "full-draft"' in full_document
            and 'class="single-view"' in full_document
            and full_document.count('class="diff-cell new"') == len(full_rows)
            and 'class="diff-cell empty"' not in full_document
        )
        if missing or document.count('class="tuners"') != cell_count or not changed_scope_ok or not contextual_scope_ok or not full_scope_ok:
            print(json.dumps({"status": "fail", "missing": missing, "expected_cells": cell_count, "changed_scope_ok": changed_scope_ok, "contextual_scope_ok": contextual_scope_ok, "full_scope_ok": full_scope_ok}, indent=2), file=sys.stderr)
            return 1
        print(json.dumps({
            "status": "pass",
            "rows": len(rows),
            "cells": cell_count,
            "controls": ["Keep", "Remove", "Brainstorm", "Humor", "Technical detail", "Length", "Bluntness", "Copy JSON", "Copy Markdown", "Export JSON", "Export Markdown"],
            "changed_passages_only_rows": len(changed_rows),
            "contextual_rows": len(context_rows),
            "full_draft_rows": len(full_rows),
            "selection_snapshot": "exact quote and offsets captured before control focus clears selection",
            "export_schema": INTERFACE_FORMAT,
            "generator_version": GENERATOR_VERSION,
        }, indent=2))
        return 0

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("original", nargs="?")
    parser.add_argument("revised", nargs="?")
    parser.add_argument("--quick-diff", type=Path)
    parser.add_argument("--full-draft", type=Path, help="generate a one-column commentable review of every semantic block in one current draft")
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--title", default="Article review — original vs revised")
    parser.add_argument("--source-label", default="Original")
    parser.add_argument("--new-label", default="Revised")
    parser.add_argument(
        "--baseline-type",
        default="original-vs-current",
        choices=["original-vs-current", "previous-delivery-vs-corrected", "changed-passages-only", "contextual-changes", "full-draft-commentable"],
    )
    parser.add_argument("--artifact-id", default="")
    parser.add_argument("--export-basename", default="")
    parser.add_argument("--source-version", default="")
    parser.add_argument("--new-version", default="")
    parser.add_argument(
        "--changed-passages-only",
        action="store_true",
        help="omit equal rows after full alignment while retaining the complete v4 interface and exact file hashes",
    )
    parser.add_argument("--contextual-changes", action="store_true", help="show each change with one unchanged passage before and after plus explicit placement labels")
    parser.add_argument("--reasons", type=Path)
    parser.add_argument("--audience-contract", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        return run_selftest(args.template)
    if args.out is None:
        parser.error("--out is required")
    mode_count = sum(bool(x) for x in (args.quick_diff, args.full_draft))
    if mode_count > 1:
        parser.error("choose only one of --quick-diff or --full-draft")

    reason_map = load_reason_map(args.reasons)
    row_scope = "contextual-changes" if args.contextual_changes else "changed-passages-only" if args.changed_passages_only else "all-passages"
    view_mode = "comparison"
    source_filename = ""
    revised_filename = ""
    if args.full_draft:
        if not args.full_draft.is_file():
            parser.error("--full-draft file must exist")
        new_blocks = extract_blocks(args.full_draft.read_text(encoding="utf-8"))
        rows = full_draft_rows(new_blocks, reason_map)
        source_sha = file_sha(args.full_draft)
        revised_sha = source_sha
        source_filename = args.full_draft.name
        revised_filename = args.full_draft.name
        row_scope = "full-draft"
        view_mode = "full-draft"
        args.baseline_type = "full-draft-commentable"
        old_blocks: list[Block] = []
    elif args.quick_diff:
        old_blocks, new_blocks = blocks_from_quick_diff(args.quick_diff.read_text(encoding="utf-8"))
        source_sha = text_sha("\n".join(block.text for block in old_blocks))
        revised_sha = text_sha("\n".join(block.text for block in new_blocks))
        source_filename = args.quick_diff.name + "#previous-wording"
        revised_filename = args.quick_diff.name + "#revised-wording"
        row_scope = "changed-passages-only"
        if args.baseline_type == "original-vs-current":
            args.baseline_type = "changed-passages-only"
        rows = align_blocks(old_blocks, new_blocks, reason_map)
    else:
        if not args.original or not args.revised:
            parser.error("provide original and revised HTML, --full-draft, or --quick-diff")
        original_path = Path(args.original)
        revised_path = Path(args.revised)
        if not original_path.is_file() or not revised_path.is_file():
            parser.error("input files must exist")
        old_blocks = extract_blocks(original_path.read_text(encoding="utf-8"))
        new_blocks = extract_blocks(revised_path.read_text(encoding="utf-8"))
        source_sha = file_sha(original_path)
        revised_sha = file_sha(revised_path)
        source_filename = original_path.name
        revised_filename = revised_path.name
        rows = align_blocks(old_blocks, new_blocks, reason_map)

    if row_scope == "contextual-changes":
        rows = contextual_changed_rows(rows, radius=1)
        args.baseline_type = "contextual-changes"
    elif row_scope == "changed-passages-only":
        rows = [row for row in rows if row["state"] != "equal"]
    audience_contract = {}
    if args.audience_contract:
        audience_contract = json.loads(args.audience_contract.read_text(encoding="utf-8"))
    artifact_id = args.artifact_id or slugify(args.title)
    export_basename = args.export_basename or artifact_id + "-review"
    source_display_label = args.source_label + (f" · {args.source_version}" if args.source_version else "")
    new_display_label = args.new_label + (f" · {args.new_version}" if args.new_version else "")
    if view_mode == "full-draft":
        label = args.new_label if args.new_label != "Revised" else "Draft"
        new_display_label = label + (f" · {args.new_version}" if args.new_version else "")
        source_display_label = new_display_label
        source_version = args.new_version or args.source_version
    else:
        source_version = args.source_version
    output = build_document(
        args.template.read_text(encoding="utf-8"),
        title=args.title,
        artifact_id=artifact_id,
        baseline_type=args.baseline_type,
        row_scope=row_scope,
        source_label=source_display_label,
        new_label=new_display_label,
        source_filename=source_filename,
        revised_filename=revised_filename,
        source_version=source_version,
        new_version=args.new_version,
        source_sha=source_sha,
        revised_sha=revised_sha,
        rows=rows,
        export_basename=export_basename,
        audience_contract=audience_contract,
        view_mode=view_mode,
    )
    args.out.write_text(output, encoding="utf-8")
    source_count = len(old_blocks) if view_mode == "comparison" else 0
    revised_count = len(new_blocks)
    print(f"Wrote {args.out} ({len(rows)} rows, scope={row_scope}, view={view_mode}, {source_count} source blocks, {revised_count} revised blocks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
