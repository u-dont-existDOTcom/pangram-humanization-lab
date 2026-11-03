#!/usr/bin/env python3
"""Score round-1 blind forecasts against the saved Pangram 4.1 results. No API calls."""
import json, pathlib, random, collections, statistics
D = pathlib.Path(__file__).resolve().parent
key = {k['id']: k for k in json.loads((D / 'answer_key.json').read_text())}
pack = {p['id']: p for p in json.loads((D / 'blind_packet.json').read_text())}
arms = {'A_cold': json.loads((D / 'arm_A_cold/forecasts.json').read_text()),
        'B_catalogue': json.loads((D / 'arm_B_catalogue/forecasts.json').read_text())}
ids = [p['id'] for p in json.loads((D / 'blind_packet.json').read_text())]
def truth3(k):
    fh = k['fraction_human']
    return 'Human' if fh == 1.0 else ('AI' if fh == 0.0 else 'Mixed')
y = {i: 1 if key[i]['fraction_human'] == 1.0 else 0 for i in ids}
def auc(ps, ys):
    pos = [p for p, t in zip(ps, ys) if t]; neg = [p for p, t in zip(ps, ys) if not t]
    if not pos or not neg: return float('nan')
    s = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return s / (len(pos) * len(neg))
def boot_auc(ps, ys, n=2000, seed=1):
    rng = random.Random(seed); idx = list(range(len(ps))); out = []
    for _ in range(n):
        b = [rng.choice(idx) for _ in idx]
        v = auc([ps[i] for i in b], [ys[i] for i in b])
        if v == v: out.append(v)
    out.sort(); return out[int(0.025 * len(out))], out[int(0.975 * len(out))]
report = {}
fc = {a: {f['id']: f for f in arms[a]} for a in arms}
fc['A+B_mean'] = {i: {'id': i, 'p_all_human': (fc['A_cold'][i]['p_all_human'] + fc['B_catalogue'][i]['p_all_human']) / 2,
                      'label': None, 'reason': ''} for i in ids}
ys = [y[i] for i in ids]
base = sum(ys) / len(ys)
report['n'] = len(ids); report['all_human'] = sum(ys)
report['baseline_always_human_accuracy'] = round(base, 3)
report['baseline_constant_brier'] = round(sum((base - t) ** 2 for t in ys) / len(ys), 3)
for a, f in fc.items():
    ps = [f[i]['p_all_human'] for i in ids]
    acc = sum((p >= 0.5) == bool(t) for p, t in zip(ps, ys)) / len(ys)
    brier = sum((p - t) ** 2 for p, t in zip(ps, ys)) / len(ys)
    r = {'accuracy_at_0.5': round(acc, 3), 'brier': round(brier, 3), 'auc': round(auc(ps, ys), 3),
         'auc_95ci': [round(x, 3) for x in boot_auc(ps, ys)]}
    if a != 'A+B_mean':
        r['label3_accuracy'] = round(sum(f[i]['label'] == truth3(key[i]) for i in ids) / len(ids), 3)
        conf = collections.Counter((f[i]['label'], truth3(key[i])) for i in ids)
        r['label_confusion_pred_vs_true'] = {f'{p}->{t}': c for (p, t), c in sorted(conf.items())}
    bins = {'<=90w': lambda w: w <= 90, '91-150w': lambda w: 90 < w <= 150, '>150w': lambda w: w > 150}
    r['auc_by_length'] = {}
    for b, fn in bins.items():
        sel = [i for i in ids if fn(pack[i]['words'])]
        r['auc_by_length'][b] = {'n': len(sel), 'human': sum(y[i] for i in sel),
                                 'auc': round(auc([f[i]['p_all_human'] for i in sel], [y[i] for i in sel]), 3)}
    report[a] = r
# Confidence among truly all-Human texts: does p separate all-High from lower-confidence passes?
hum = [i for i in ids if y[i]]
def all_high(i):
    return all(str(w.get('confidence', '')).lower() == 'high' for w in key[i]['windows'])
hh = [1 if all_high(i) else 0 for i in hum]
report['human_texts_all_windows_high'] = f'{sum(hh)}/{len(hum)}'
report['auc_high_vs_lower_within_human'] = {a: round(auc([fc[a][i]['p_all_human'] for i in hum], hh), 3) for a in fc}
# Confident misses for reading
misses = []
for a in ('A_cold', 'B_catalogue'):
    for i in ids:
        p = fc[a][i]['p_all_human']
        if (p >= 0.75 and not y[i]) or (p <= 0.25 and y[i]):
            misses.append({'arm': a, 'id': i, 'p': p, 'truth': truth3(key[i]), 'fraction_human': key[i]['fraction_human'],
                           'words': pack[i]['words'], 'lane': key[i]['lane'], 'reason': fc[a][i]['reason']})
report['confident_misses_count'] = collections.Counter(m['arm'] for m in misses)
both = collections.Counter(m['id'] for m in misses)
report['confident_misses_shared_by_both_arms'] = sorted(i for i, c in both.items() if c == 2)
(D / 'RESULTS.json').write_text(json.dumps(report, indent=1))
(D / 'confident_misses.json').write_text(json.dumps(misses, indent=1, ensure_ascii=False))
print(json.dumps(report, indent=1))
