#!/usr/bin/env python3
"""Score round 2. Reads, from this folder: input_key.json, out/rewrites.json, out/meaning_verdicts.json,
out/forecasts.json and out/pangram_results.json ({name: result}). Writes out/RESULTS.json and out/per_paragraph.json.
No API calls."""
import json, pathlib, collections

D = pathlib.Path(__file__).resolve().parent
O = D / 'out'
key = {k['id']: k for k in json.loads((D / 'input_key.json').read_text(encoding='utf-8'))}
rows = json.loads((O / 'rewrites.json').read_text(encoding='utf-8'))
verdicts = {v['id']: v for v in json.loads((O / 'meaning_verdicts.json').read_text(encoding='utf-8'))}
forecasts = {f['id']: f for f in json.loads((O / 'forecasts.json').read_text(encoding='utf-8'))}
results = json.loads((O / 'pangram_results.json').read_text(encoding='utf-8'))


def all_high(windows):
    return bool(windows) and all(str(w.get('confidence', '')).lower() == 'high' for w in windows)


def auc(ps, ys):
    pos = [p for p, t in zip(ps, ys) if t]; neg = [p for p, t in zip(ps, ys) if not t]
    if not pos or not neg:
        return None
    return round(sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg)), 3)


per = []
for r in rows:
    k = key[r['pid']]
    if r['unchanged']:
        fh, wins, meaning, link = k['orig_fraction_human'], k['orig_windows'], 'UNCHANGED', None
        fai = k['orig_fraction_ai']
    else:
        res = results['r2-%s-%s' % (r['arm'], r['pid'])]
        fh, fai, wins, link = res['fraction_human'], res['fraction_ai'], res.get('windows') or [], res.get('dashboard_link')
        meaning = verdicts[r['blind_id']]['verdict']
    per.append({'arm': r['arm'], 'pid': r['pid'], 'set': k['set'], 'lane': k['lane'], 'unchanged': r['unchanged'],
                'meaning': meaning, 'orig_fraction_human': k['orig_fraction_human'], 'fraction_human': fh,
                'fraction_ai': fai, 'all_human': fh == 1.0, 'all_high': fh == 1.0 and all_high(wins),
                'added_characters': r['added_characters'], 'words': r['words'], 'orig_words': r['orig_words'],
                'blind_id': r.get('blind_id'), 'dashboard_link': link,
                'p_all_human': forecasts.get(r.get('blind_id'), {}).get('p_all_human')})

rep = {}
for arm in ('M1', 'M2'):
    a = [p for p in per if p['arm'] == arm]
    T = [p for p in a if p['set'] == 'T']; R = [p for p in a if p['set'] == 'R']
    ch = [p for p in a if not p['unchanged']]
    good_T = [p for p in T if p['all_human'] and p['meaning'] == 'PASS']
    rep[arm] = {
        'T_n': len(T), 'T_unchanged': sum(p['unchanged'] for p in T),
        'T_all_human': sum(p['all_human'] for p in T),
        'T_all_human_and_meaning_pass': len(good_T),
        'T_all_human_all_high_and_meaning_pass': sum(p['all_high'] for p in good_T),
        'T_mean_fraction_human_change': round(sum(p['fraction_human'] - p['orig_fraction_human'] for p in T) / len(T), 3),
        'R_n': len(R), 'R_unchanged': sum(p['unchanged'] for p in R),
        'R_regressed': sum(not p['all_human'] for p in R),
        'R_regressed_among_changed': '%d/%d' % (sum(not p['all_human'] for p in R if not p['unchanged']),
                                                sum(not p['unchanged'] for p in R)),
        'meaning_fail': '%d/%d' % (sum(p['meaning'] == 'FAIL' for p in ch), len(ch)),
        'added_characters': sum(bool(p['added_characters']) for p in a),
    }
by = collections.defaultdict(dict)
for p in per:
    by[p['pid']][p['arm']] = p
succ = lambda p: p['all_human'] and p['meaning'] in ('PASS',)
paired = collections.Counter()
for pid, d in by.items():
    if d['M1']['set'] != 'T':
        continue
    paired[('M1 ok' if succ(d['M1']) else 'M1 no') + ' / ' + ('M2 ok' if succ(d['M2']) else 'M2 no')] += 1
rep['T_paired_success'] = dict(paired)
fc = [p for p in per if not p['unchanged'] and p['p_all_human'] is not None]
rep['forecast_on_rewrites'] = {
    'n': len(fc), 'all_human': sum(p['all_human'] for p in fc),
    'accuracy_at_0.5': round(sum((p['p_all_human'] >= 0.5) == p['all_human'] for p in fc) / len(fc), 3) if fc else None,
    'always_majority': round(max(sum(p['all_human'] for p in fc), len(fc) - sum(p['all_human'] for p in fc)) / len(fc), 3) if fc else None,
    'auc': auc([p['p_all_human'] for p in fc], [p['all_human'] for p in fc]),
}
(O / 'per_paragraph.json').write_text(json.dumps(per, indent=1, ensure_ascii=False), encoding='utf-8')
(O / 'RESULTS.json').write_text(json.dumps(rep, indent=1), encoding='utf-8')
print(json.dumps(rep, indent=1))
