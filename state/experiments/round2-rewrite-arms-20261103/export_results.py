#!/usr/bin/env python3
"""Collect pangram_api.py results for round 2 into out/pangram_results.json.

Usage: python3 export_results.py PANGRAM_OUTDIR
Reads out/pangram_texts.json, finds each text's cached result (PANGRAM_OUTDIR/cache/<sha256>.json) and writes
{name: {sha256, version, stage, fraction_human, fraction_ai, fraction_ai_assisted, headline, dashboard_link,
windows: [{label, confidence, word_count}]}}. Texts without a result are listed and left out. No API calls.
"""
import hashlib, json, pathlib, sys

D = pathlib.Path(__file__).resolve().parent


def main(pdir):
    cache = pathlib.Path(pdir) / 'cache'
    texts = json.loads((D / 'out' / 'pangram_texts.json').read_text(encoding='utf-8'))
    out, missing = {}, []
    for name, text in texts.items():
        sha = hashlib.sha256(text.encode('utf-8')).hexdigest()
        f = cache / (sha + '.json')
        if not f.exists():
            missing.append(name)
            continue
        r = json.loads(f.read_text(encoding='utf-8'))['result']
        out[name] = {'sha256': sha, 'version': r.get('version'), 'stage': r.get('stage'),
                     'fraction_human': r.get('fraction_human'), 'fraction_ai': r.get('fraction_ai'),
                     'fraction_ai_assisted': r.get('fraction_ai_assisted'), 'headline': r.get('headline'),
                     'dashboard_link': r.get('dashboard_link'),
                     'windows': [{'label': w.get('label'), 'confidence': w.get('confidence'),
                                  'word_count': w.get('word_count')} for w in r.get('windows') or []]}
    (D / 'out' / 'pangram_results.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'exported': len(out), 'missing': missing,
                      'versions': sorted({v['version'] for v in out.values()})}))
    return 1 if missing else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
