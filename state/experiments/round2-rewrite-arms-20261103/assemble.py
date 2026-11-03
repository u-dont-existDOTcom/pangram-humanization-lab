#!/usr/bin/env python3
"""Round 2: merge the writers' chunks, run the character check, and build the blind packets.

Usage: python3 assemble.py WRITERS_DIR OUT_DIR
WRITERS_DIR holds M1/chunk_[ABC].json and M2/chunk_[ABC].json. Writes into OUT_DIR:
  rewrites.json            every rewrite with arm, paragraph id and flags (the unblinding key for the packets below)
  meaning_packet_[1-4].json  changed rewrites beside their originals, shuffled, arm hidden
  forecast_packet.json     changed rewrites alone, shuffled, arm and original hidden
  pangram_texts.json       {name: text} for every changed rewrite, for pangram_api.py check
No API calls.
"""
import hashlib, json, pathlib, random, sys

HERE = pathlib.Path(__file__).resolve().parent
CURLY = {'‘': "'", '’': "'", '“': '"', '”': '"', '—': 'em dash', '–': 'en dash'}


def main(wdir, odir):
    wdir, odir = pathlib.Path(wdir), pathlib.Path(odir)
    odir.mkdir(parents=True, exist_ok=True)
    inputs = {x['id']: x for x in json.loads((HERE / 'inputs.json').read_text(encoding='utf-8'))}
    rows, problems = [], []
    for arm in ('M1', 'M2'):
        got = []
        for c in 'ABC':
            got += json.loads((wdir / arm / ('chunk_%s.json' % c)).read_text(encoding='utf-8'))
        ids = [g['id'] for g in got]
        if ids != list(inputs):
            problems.append('%s: ids do not match the inputs' % arm)
        for g in got:
            orig = inputs[g['id']]['text']
            text = g['rewrite']
            unchanged = text == orig
            if bool(g.get('unchanged')) != unchanged:
                problems.append('%s %s: unchanged flag %s but text %s' % (arm, g['id'], g.get('unchanged'),
                                                                          'identical' if unchanged else 'differs'))
            added = sorted({CURLY[ch] for ch in CURLY if text.count(ch) > orig.count(ch)})
            rows.append({'arm': arm, 'pid': g['id'], 'unchanged': unchanged, 'text': text,
                         'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
                         'words': len(text.split()), 'orig_words': len(orig.split()),
                         'added_characters': added, 'what_changed': g.get('what_changed', ''),
                         'examples_used': g.get('examples_used', [])})
    rng = random.Random(20261103)
    changed = [r for r in rows if not r['unchanged']]
    order = changed[:]
    rng.shuffle(order)
    for n, r in enumerate(order, 1):
        r['blind_id'] = 'X%03d' % n
    meaning = [{'id': r['blind_id'], 'original': inputs[r['pid']]['text'], 'rewrite': r['text']} for r in order]
    k = 4
    for i in range(k):
        part = meaning[i::k]
        (odir / ('meaning_packet_%d.json' % (i + 1))).write_text(json.dumps(part, ensure_ascii=False, indent=1), encoding='utf-8')
    forecast = [{'id': r['blind_id'], 'words': r['words'], 'text': r['text']} for r in order]
    (odir / 'forecast_packet.json').write_text(json.dumps(forecast, ensure_ascii=False, indent=1), encoding='utf-8')
    texts = {'r2-%s-%s' % (r['arm'], r['pid']): r['text'] for r in changed}
    (odir / 'pangram_texts.json').write_text(json.dumps(texts, ensure_ascii=False, indent=1), encoding='utf-8')
    (odir / 'rewrites.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding='utf-8')
    credits = sum(-(-r['words'] // 100) for r in {r['sha256']: r for r in changed}.values())
    print(json.dumps({'rewrites': len(rows), 'changed': len(changed),
                      'unchanged_by_arm': {a: sum(1 for r in rows if r['arm'] == a and r['unchanged']) for a in ('M1', 'M2')},
                      'identical_across_arms': len(changed) - len({r['sha256'] for r in changed}),
                      'added_characters': [(r['arm'], r['pid'], r['added_characters']) for r in rows if r['added_characters']],
                      'estimated_credits': credits, 'problems': problems}, indent=1))
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
