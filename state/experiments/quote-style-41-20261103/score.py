#!/usr/bin/env python3
"""Score the quote-style flips against their census readings, and the repeats against the same census readings.
Reads FLIP-INPUTS.json, TEXTS.json and RESULTS.json (export of the API results); writes SCORE.json and prints the table.
No API calls.

A reading's rank, worst to best: AI (0), Mixed (1), Human with a window below High (2), Human at High throughout (3).
A flip "improves" when its rank rises, "worsens" when it falls; within the same rank the fraction human breaks no ties
(only the rank counts), and the fraction's change is reported separately."""
import json, math, pathlib

HERE = pathlib.Path(__file__).resolve().parent
F = json.loads((HERE / 'FLIP-INPUTS.json').read_text(encoding='utf-8'))
R = json.loads((HERE / 'RESULTS.json').read_text(encoding='utf-8'))


def rank(r):
    if r['prediction_short'] == 'AI':
        return 0
    if r['prediction_short'] != 'Human' or r['fraction_human'] < 1 - 1e-9:
        return 1
    return 3 if all(w['confidence'] == 'High' for w in r['windows']) else 2


def sign_p(k, n):
    """One-sided sign test, P(X >= k) for X ~ Bin(n, 1/2)."""
    return sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n if n else 1.0


rows, by = [], {}
for it in F['items']:
    r = R.get(it['name'])
    if not r:
        continue
    a, b = rank(it['original']), rank(r)
    d = {'name': it['name'], 'stratum': it['stratum'], 'before': a, 'after': b,
         'verdict_before': it['original']['prediction_short'], 'verdict_after': r['prediction_short'],
         'fh_before': it['original']['fraction_human'], 'fh_after': r['fraction_human'],
         'change': 'better' if b > a else 'worse' if b < a else 'same',
         'link_before': it['original']['link'], 'link_after': r.get('link')}
    rows.append(d)
    by.setdefault(it['stratum'], []).append(d)
reps = []
for name in F['repeat_controls']:
    r = R.get(name)
    if not r:
        continue
    cid = name.replace('q41-repeat-', '')
    it = next(i for i in F['items'] if i['id'] == cid)
    reps.append({'name': name, 'same_verdict': r['prediction_short'] == it['original']['prediction_short'],
                 'same_rank': rank(r) == rank(it['original']),
                 'fh_delta': r['fraction_human'] - it['original']['fraction_human'], 'link': r.get('link')})
summary = {}
for k, ds in by.items():
    n = len(ds)
    better = sum(d['change'] == 'better' for d in ds)
    worse = sum(d['change'] == 'worse' for d in ds)
    vflip = sum(d['verdict_before'] != d['verdict_after'] for d in ds)
    summary[k] = {'n': n, 'better': better, 'worse': worse, 'same': n - better - worse, 'verdict_changed': vflip,
                  'mean_fh_delta': round(sum(d['fh_after'] - d['fh_before'] for d in ds) / n, 4)}
ba = [d for d in rows if d['stratum'] in ('AI', 'BORDER')]
kb, kw = sum(d['change'] == 'better' for d in ba), sum(d['change'] == 'worse' for d in ba)
summary['AI+BORDER sign test'] = {'better': kb, 'worse': kw, 'p_one_sided': round(sign_p(kb, kb + kw), 4)}
summary['repeats'] = {'n': len(reps), 'same_verdict': sum(r['same_verdict'] for r in reps),
                      'same_rank': sum(r['same_rank'] for r in reps),
                      'max_abs_fh_delta': round(max((abs(r['fh_delta']) for r in reps), default=0), 4)}
(HERE / 'SCORE.json').write_text(json.dumps({'summary': summary, 'rows': rows, 'repeats': reps}, indent=1), encoding='utf-8')
for k, v in summary.items():
    print(k, v)
