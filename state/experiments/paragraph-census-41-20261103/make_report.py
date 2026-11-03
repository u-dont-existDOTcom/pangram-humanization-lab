#!/usr/bin/env python3
"""CENSUS-REPORT.md from census_inputs.json and CENSUS-RESULTS.json: per article, the counts and every paragraph that
is not 100% Human at High confidence in every window, with its section, first words and Pangram link. No API calls."""
import collections, json, pathlib
D = pathlib.Path(__file__).resolve().parent
inp = {r['id']: r for r in json.loads((D / 'census_inputs.json').read_text(encoding='utf-8'))}
res = json.loads((D / 'CENSUS-RESULTS.json').read_text(encoding='utf-8'))
order = list(dict.fromkeys(r['article'] for r in inp.values()))


def status(r):
    if r['fraction_human'] == 1.0 and all(str(w['confidence']).lower() == 'high' for w in r['windows']):
        return 'pass'
    if r['fraction_human'] == 1.0:
        return 'human-below-high'
    return 'ai' if r['fraction_human'] == 0.0 else 'mixed'


out = ['# Paragraph census: the registered articles on Pangram 4.1', '',
       'Every reader-visible block of 25+ words in each registered joel-articles master (registry at `1cac9dd`, 2026-11-03), each checked alone through the API. "Passes" means 100% Human with every window at High confidence, Joel\'s standard. Each master is the registered one: for articles whose humanizing happens in lane drafts (Inner Child, Inner Signal, Somatic Therapies, Neuro De-Armoring), it can be an older source than the lane\'s current draft, so read those rows as a map of the registered text, not of the lane\'s latest work.', '',
       '| article | paragraphs | passes | Human below High | Mixed | AI |', '|---|---|---|---|---|---|']
rows = collections.defaultdict(list)
for k, r in res.items():
    rows[inp[k]['article']].append((k, r, status(r)))
for a in order:
    c = collections.Counter(s for _, _, s in rows[a])
    out.append('| %s | %d | %d | %d | %d | %d |' % (a, len(rows[a]), c['pass'], c['human-below-high'], c['mixed'], c['ai']))
c = collections.Counter(s for a in order for _, _, s in rows[a])
out.append('| all | %d | %d | %d | %d | %d |' % (sum(len(rows[a]) for a in order), c['pass'], c['human-below-high'], c['mixed'], c['ai']))
for a in order:
    bad = [(k, r, s) for k, r, s in rows[a] if s != 'pass']
    out += ['', '## %s: %d paragraphs to look at' % (a, len(bad)), '']
    if not bad:
        continue
    out += ['| id | section | starts | result | link |', '|---|---|---|---|---|']
    for k, r, s in bad:
        t = inp[k]
        wins = ', '.join('%s %s' % ('H' if w['label'].startswith('Human') else 'AI', w['confidence']) for w in r['windows'])
        start = t['text'][:60].replace('|', '/').replace('\n', ' ')
        out.append('| %s | %s | %s… | %d%% human (%s) | [result](%s) |' % (k, (t['section'] or '')[:40].replace('|', '/'), start, round(100 * r['fraction_human']), wins, r['link']))
(D / 'CENSUS-REPORT.md').write_text('\n'.join(out) + '\n', encoding='utf-8')
print('written')
