#!/usr/bin/env python3
"""Paragraph census: every reader-visible paragraph of 25+ words in each registered joel-articles master.

Usage: python3 build_census.py JOEL_ARTICLES_ROOT OUT_JSON
Reads articles/INDEX.json, verifies each master's registered SHA-256, extracts reader-visible blocks
(Markdown: one non-empty line per block, consecutive list items joined; HTML: top-level p/h/li/blockquote text,
list items of one list joined), keeps blocks of 25+ words with their exact characters, and records the nearest
heading. Writes [{id, article, section, index, words, sha256, text}]. No API calls.
"""
import hashlib, json, pathlib, re, sys

from bs4 import BeautifulSoup

MIN_WORDS = 25
LINK = re.compile(r'\[([^\]]*)\]\([^)]*\)')


def md_blocks(text):
    blocks, heading, lst = [], '', []

    def flush():
        if lst:
            blocks.append((heading, '\n'.join(lst)))
            lst.clear()
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush(); continue
        if line.lstrip().startswith('#'):
            flush(); heading = line.lstrip('#').strip(); continue
        if line.startswith('[NATIVE IMAGE') or re.fullmatch(r'\[[^\]]*\]\([^)]*\)', line.strip()):
            flush(); continue
        clean = LINK.sub(r'\1', line)
        clean = re.sub(r'(\*\*|__)(.+?)\1', r'\2', clean)
        clean = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'\1', clean)
        m = re.match(r'\s*(?:[-*+]|\d+[.)])\s+(.*)', clean)
        if m:
            lst.append(m.group(1)); continue
        flush()
        blocks.append((heading, clean.strip()))
    flush()
    return blocks


def html_blocks(text):
    soup = BeautifulSoup(text, 'html.parser')
    root = soup.find(attrs={'data-testid': 'editor'}) or soup
    blocks, heading = [], ''
    for el in root.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'ul', 'ol', 'blockquote'], recursive=True):
        if el.find_parent(['ul', 'ol', 'blockquote', 'figure', 'figcaption']) and el.name not in ('ul', 'ol'):
            continue
        if el.name in ('ul', 'ol') and el.find_parent(['ul', 'ol']):
            continue
        if el.name.startswith('h'):
            heading = el.get_text(' ', strip=True); continue
        if 'button-wrapper' in (el.get('class') or []):
            continue
        if el.name in ('ul', 'ol'):
            items = [li.get_text(' ', strip=True) for li in el.find_all('li', recursive=False)]
            txt = '\n'.join(i for i in items if i)
        else:
            txt = el.get_text('', strip=False).strip()
            txt = re.sub(r'[ \t]+\n|\n[ \t]+', '\n', txt)
        if txt:
            blocks.append((heading, txt))
    return blocks


def main(root, out):
    root = pathlib.Path(root)
    idx = json.loads((root / 'articles/INDEX.json').read_text(encoding='utf-8'))
    arts = idx['articles'] if isinstance(idx, dict) else idx
    rows = []
    for a in arts:
        m = a['authority']['master']
        p = root / m['path']
        raw = p.read_bytes()
        if hashlib.sha256(raw).hexdigest() != m['sha256']:
            sys.exit('%s: master hash does not match the registry' % a['id'])
        text = raw.decode('utf-8')
        blocks = html_blocks(text) if p.suffix == '.html' else md_blocks(text)
        n = 0
        for heading, txt in blocks:
            if len(txt.split()) < MIN_WORDS:
                continue
            n += 1
            rows.append({'id': '%s-%03d' % (a['id'], n), 'article': a['id'], 'section': heading, 'index': n,
                         'words': len(txt.split()), 'sha256': hashlib.sha256(txt.encode('utf-8')).hexdigest(),
                         'master_sha256': m['sha256'], 'text': txt})
    pathlib.Path(out).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding='utf-8')
    by = {}
    for r in rows:
        by.setdefault(r['article'], [0, 0, 0])
        by[r['article']][0] += 1; by[r['article']][1] += r['words']; by[r['article']][2] += -(-r['words'] // 100)
    print(json.dumps({'paragraphs': len(rows), 'unique_texts': len({r['sha256'] for r in rows}),
                      'by_article [paragraphs, words, credits]': by,
                      'credits_total': sum(v[2] for v in by.values())}, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
