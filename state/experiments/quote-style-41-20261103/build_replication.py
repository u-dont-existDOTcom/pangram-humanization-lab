#!/usr/bin/env python3
"""Replication of the BORDER arm: every other census paragraph in the same pool (25 to 100 words, two or more quote
marks, all curly; Mixed, or Human with a window below High), curly to straight. Same rules as build_sample.py.
Writes REPL-INPUTS.json and REPL-TEXTS.json. No API calls.

  python3 build_replication.py CENSUS_INPUTS.json CENSUS_RESULTS.json
"""
import hashlib, json, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent
sys.argv, args = sys.argv[:1], sys.argv[1:]
ns = {'__file__': str(HERE / 'build_sample.py'), '__name__': 'lib'}
src = (HERE / 'build_sample.py').read_text(encoding='utf-8').split('pool = {}')[0]
sys.argv = ['build_sample.py'] + args
exec(src, ns)
inputs, results, stratum, to_straight = ns['inputs'], ns['results'], ns['stratum'], ns['to_straight']
used = {i['id'] for i in json.loads((HERE / 'FLIP-INPUTS.json').read_text(encoding='utf-8'))['items']}
items, texts = [], {}
for it in inputs:
    r = results.get(it['id'])
    if not r or not 25 <= it['words'] <= 100 or it['id'] in used or stratum(it['text'], r) != 'BORDER':
        continue
    flip = to_straight(it['text'])
    assert flip != it['text'] and len(flip) == len(it['text'])
    name = 'q41r-%s' % it['id']
    texts[name] = flip
    items.append({'name': name, 'id': it['id'], 'stratum': 'BORDER', 'words': it['words'],
                  'marks_changed': sum(a != b for a, b in zip(flip, it['text'])), 'original_sha256': it['sha256'],
                  'flip_sha256': hashlib.sha256(flip.encode('utf-8')).hexdigest(),
                  'original': {k: r[k] for k in ('prediction_short', 'fraction_human', 'link', 'windows')}})
(HERE / 'REPL-INPUTS.json').write_text(json.dumps({'census_commit': ns['CENSUS_COMMIT'], 'items': items, 'repeat_controls': []},
                                                  ensure_ascii=False, indent=1), encoding='utf-8')
(HERE / 'REPL-TEXTS.json').write_text(json.dumps(texts, ensure_ascii=False, indent=1), encoding='utf-8')
import collections
print(len(items), 'items;', dict(collections.Counter(i['id'].rsplit('-', 1)[0] for i in items)), ';',
      sum(-(-i['words'] // 100) for i in items), 'credits')
