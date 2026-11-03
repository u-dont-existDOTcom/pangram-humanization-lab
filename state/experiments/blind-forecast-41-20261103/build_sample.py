#!/usr/bin/env python3
"""Round 1 sample builder: already-scored Pangram 4.1 texts -> blind packet + answer key. No API calls."""
import json, pathlib, random, re, hashlib, collections
HOME = pathlib.Path('/home/joel')
OUT = pathlib.Path(__file__).resolve().parent
lists = [l.strip() for l in open('/tmp/pg_results_list.txt') if l.strip()]
recs = {}
for rel in lists:
    lane = str(pathlib.Path(rel).parent)
    cache = HOME / lane / 'cache'
    if not cache.is_dir():
        continue
    for f in cache.glob('*.json'):
        if f.name.endswith('.pending.json'):
            continue
        try:
            d = json.loads(f.read_text(encoding='utf-8'))
        except Exception:
            continue
        r = d.get('result', d)
        if not isinstance(r, dict) or not str(r.get('version', '')).startswith('4.1'):
            continue
        text = r.get('text') or ''
        sha = hashlib.sha256(text.encode('utf-8')).hexdigest()
        words = len(text.split())
        if sha in recs or not (25 <= words <= 400):
            continue
        wins = [{'label': w.get('label'), 'confidence': w.get('confidence'), 'words': w.get('word_count')} for w in (r.get('windows') or [])]
        recs[sha] = {'sha256': sha, 'lane': lane, 'name': d.get('name'), 'words': words, 'text': text,
                     'headline': r.get('headline'), 'prediction_short': r.get('prediction_short'),
                     'fraction_human': r.get('fraction_human'), 'fraction_ai': r.get('fraction_ai'),
                     'fraction_ai_assisted': r.get('fraction_ai_assisted'), 'version': r.get('version'), 'windows': wins}
items = list(recs.values())
def shingles(t):
    w = re.findall(r"[a-z']+", t.lower())
    return {tuple(w[i:i+3]) for i in range(max(1, len(w)-2))}
sh = [shingles(x['text']) for x in items]
parent = list(range(len(items)))
def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i
for i in range(len(items)):
    for j in range(i+1, len(items)):
        a, b = sh[i], sh[j]
        if a and b and len(a & b) / len(a | b) >= 0.4:
            parent[find(i)] = find(j)
fams = collections.defaultdict(list)
for i, x in enumerate(items):
    fams[find(i)].append(x)
rng = random.Random(20261103)
reps = []
for k in sorted(fams, key=lambda k: min(x['sha256'] for x in fams[k])):
    members = sorted(fams[k], key=lambda x: x['sha256'])
    rep = rng.choice(members)
    rep = dict(rep, family_size=len(members))
    reps.append(rep)
def cls(x):
    return 'all_human' if x['fraction_human'] == 1.0 else 'not_all_human'
by = collections.defaultdict(list)
for x in reps:
    by[cls(x)].append(x)
chosen = []
for c in ('all_human', 'not_all_human'):
    pool = by[c][:]
    rng.shuffle(pool)
    per_lane = collections.Counter(); pick = []
    for x in pool:
        if per_lane[x['lane']] >= 8:
            continue
        pick.append(x); per_lane[x['lane']] += 1
        if len(pick) >= 50:
            break
    chosen += pick
rng.shuffle(chosen)
blind, key = [], []
for n, x in enumerate(chosen, 1):
    bid = 'B%03d' % n
    blind.append({'id': bid, 'words': x['words'], 'text': x['text']})
    key.append(dict({k: v for k, v in x.items() if k != 'text'}, id=bid))
(OUT / 'blind_packet.json').write_text(json.dumps(blind, ensure_ascii=False, indent=1), encoding='utf-8')
(OUT / 'answer_key.json').write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding='utf-8')
print('4.1 texts (25-400 words):', len(items), '| families:', len(fams), '| family classes:', {c: len(v) for c, v in by.items()})
print('chosen:', len(chosen), collections.Counter(cls(x) for x in chosen), '| lanes:', len({x['lane'] for x in chosen}))
print('blind packet sha256:', hashlib.sha256((OUT / 'blind_packet.json').read_bytes()).hexdigest())
