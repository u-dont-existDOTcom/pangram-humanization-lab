#!/usr/bin/env python3
"""Quote-style flips on census paragraphs (Pangram 4.1): the same paragraph with only its apostrophes and quote marks
changed, curly to straight or straight to curly. Reads the census's frozen inputs and results from the census branch
(commit given below, files copied to a scratch folder by the caller) and writes FLIP-INPUTS.json and TEXTS.json.
No API calls.

  python3 build_sample.py CENSUS_INPUTS.json CENSUS_RESULTS.json
"""
import hashlib, json, pathlib, random, re, sys

HERE = pathlib.Path(__file__).resolve().parent
CENSUS_COMMIT = '8b3a009'  # research/paragraph-census-41-20261103
inputs = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
results = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8'))
CURLY = re.compile('[‘’“”]')
STRAIGHT = re.compile('[\'"]')


def to_straight(t):
    return t.translate(str.maketrans({'‘': "'", '’': "'", '“': '"', '”': '"'}))


def to_curly(t):
    """Typographic quotes the way an editor's smart quotes make them: an apostrophe inside or at the end of a word is
    a right single quote; a quote after a space, an opening bracket or a dash (or at the start) opens; else it closes."""
    out = []
    for i, ch in enumerate(t):
        prev = t[i - 1] if i else ' '
        if ch == "'":
            out.append('‘' if (prev.isspace() or prev in '([{—–-"“') else '’')
        elif ch == '"':
            out.append('“' if (prev.isspace() or prev in '([{—–-‘') else '”')
        else:
            out.append(ch)
    return ''.join(out)


def stratum(t, r):
    c, s = len(CURLY.findall(t)), len(STRAIGHT.findall(t))
    if c >= 2 and s == 0:
        if r['prediction_short'] == 'AI':
            return 'AI'
        if r['prediction_short'] == 'Human' and all(w['confidence'] == 'High' for w in r['windows']):
            return 'HUMAN_HIGH'
        return 'BORDER'  # Mixed, or Human with a window below High
    if s >= 2 and c == 0 and r['prediction_short'] == 'Human':
        return 'STRAIGHT_HUMAN'
    return None


pool = {}
for it in inputs:
    r = results.get(it['id'])
    if not r or not 25 <= it['words'] <= 100:
        continue
    k = stratum(it['text'], r)
    if k:
        pool.setdefault(k, []).append(it)
SIZES = {'AI': 25, 'BORDER': 25, 'HUMAN_HIGH': 20, 'STRAIGHT_HUMAN': 20}
rng = random.Random(20261103)
picked, texts = [], {}
for k, n in SIZES.items():
    for it in sorted(rng.sample(pool[k], n), key=lambda x: x['id']):
        flip = to_straight(it['text']) if k != 'STRAIGHT_HUMAN' else to_curly(it['text'])
        assert flip != it['text'] and len(flip) == len(it['text'])
        changed = sum(a != b for a, b in zip(flip, it['text']))
        name = 'q41-%s' % it['id']
        texts[name] = flip
        picked.append({'name': name, 'id': it['id'], 'stratum': k, 'words': it['words'], 'marks_changed': changed,
                       'original_sha256': it['sha256'], 'flip_sha256': hashlib.sha256(flip.encode('utf-8')).hexdigest(),
                       'original': {kk: results[it['id']][kk] for kk in ('prediction_short', 'fraction_human', 'link', 'windows')}})
# repeat control: ten originals resubmitted unchanged (fresh output folder, so no cache), five AI and five BORDER
ctrl = [p for p in picked if p['stratum'] == 'AI'][:5] + [p for p in picked if p['stratum'] == 'BORDER'][:5]
controls = {}
for p in ctrl:
    t = next(i['text'] for i in inputs if i['id'] == p['id'])
    assert hashlib.sha256(t.encode('utf-8')).hexdigest() == p['original_sha256']
    controls['q41-repeat-%s' % p['id']] = t
(HERE / 'FLIP-INPUTS.json').write_text(json.dumps({'census_commit': CENSUS_COMMIT, 'sizes': SIZES,
                                                     'pool_sizes': {k: len(v) for k, v in pool.items()},
                                                     'items': picked, 'repeat_controls': sorted(controls)},
                                                    ensure_ascii=False, indent=1), encoding='utf-8')
(HERE / 'TEXTS.json').write_text(json.dumps({**texts, **controls}, ensure_ascii=False, indent=1), encoding='utf-8')
print({k: len(v) for k, v in pool.items()}, '->', len(texts), 'flips +', len(controls), 'repeats;',
      sum(-(-p['words'] // 100) for p in picked) + len(controls), 'credits at one per started 100 words')
