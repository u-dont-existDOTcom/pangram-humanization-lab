#!/usr/bin/env python3
"""Dash-style flips on census paragraphs (Pangram 4.1): each em dash becomes a spaced en dash (" – "), the form in
Joel's own Human-at-High paragraphs (41 spaced en dashes in prose there, against 12 em dashes and 1 spaced hyphen).
Nothing else changes. Reads the census's frozen inputs and results (branch research/paragraph-census-41-20261103,
commit 8b3a009); writes FLIP-INPUTS.json and TEXTS.json. No API calls.

  python3 build_sample.py CENSUS_INPUTS.json CENSUS_RESULTS.json
"""
import hashlib, json, pathlib, random, re, sys

HERE = pathlib.Path(__file__).resolve().parent
CENSUS_COMMIT = '8b3a009'
inputs = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
results = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8'))


def flip(t):
    return re.sub(r' ?— ?', ' – ', t)


def stratum(r):
    if r['prediction_short'] == 'AI':
        return 'AI'
    if r['prediction_short'] == 'Human' and r['fraction_human'] >= 1 - 1e-9 and all(w['confidence'] == 'High' for w in r['windows']):
        return 'HUMAN_HIGH'
    return 'BORDER'


pool = {}
for it in inputs:
    r = results.get(it['id'])
    if r and 25 <= it['words'] <= 100 and '—' in it['text']:
        pool.setdefault(stratum(r), []).append(it)
SIZES = {'AI': 30, 'BORDER': len(pool['BORDER']), 'HUMAN_HIGH': len(pool['HUMAN_HIGH'])}
rng = random.Random(20261103)
items, texts = [], {}
for k, n in SIZES.items():
    for it in sorted(rng.sample(pool[k], n), key=lambda x: x['id']):
        f = flip(it['text'])
        assert f != it['text'] and '—' not in f
        name = 'd41-%s' % it['id']
        texts[name] = f
        items.append({'name': name, 'id': it['id'], 'stratum': k, 'words': it['words'], 'dashes': it['text'].count('—'),
                      'original_sha256': it['sha256'], 'flip_sha256': hashlib.sha256(f.encode('utf-8')).hexdigest(),
                      'original': {kk: results[it['id']][kk] for kk in ('prediction_short', 'fraction_human', 'link', 'windows')}})
(HERE / 'FLIP-INPUTS.json').write_text(json.dumps({'census_commit': CENSUS_COMMIT, 'sizes': SIZES,
                                                     'pool_sizes': {k: len(v) for k, v in pool.items()},
                                                     'items': items, 'repeat_controls': []}, ensure_ascii=False, indent=1), encoding='utf-8')
(HERE / 'TEXTS.json').write_text(json.dumps(texts, ensure_ascii=False, indent=1), encoding='utf-8')
print({k: len(v) for k, v in pool.items()}, '->', len(texts), 'flips;', sum(-(-i['words'] // 100) for i in items), 'credits')
