#!/usr/bin/env python3
"""Pangram results for a TEXTS file, from pangram_api.py's cache, in the lane's RESULTS form (verdict, fraction, link,
every window with its label, confidence, words and text). Run on the laptop after `pangram_api.py check`; no API calls.

  python3 export_results.py TEXTS.json OUTDIR RESULTS.json      # adds to RESULTS.json if it exists
"""
import hashlib, json, pathlib, sys

texts = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
cache = pathlib.Path(sys.argv[2]) / 'cache'
outp = pathlib.Path(sys.argv[3])
out = json.loads(outp.read_text(encoding='utf-8')) if outp.exists() else {}
missing = []
for name, text in texts.items():
    sha = hashlib.sha256(text.encode('utf-8')).hexdigest()
    f = cache / (sha + '.json')
    if not f.exists():
        missing.append(name)
        continue
    r = json.loads(f.read_text(encoding='utf-8'))['result']
    out[name] = {'sha256': sha, 'words': len(text.split()), 'prediction_short': r['prediction_short'],
                 'fraction_human': r['fraction_human'], 'fraction_ai': r['fraction_ai'], 'version': r['version'],
                 'link': r.get('dashboard_link'),
                 'windows': [{'label': w['label'], 'confidence': w['confidence'], 'words': w.get('word_count'), 'text': w['text']}
                             for w in r['windows']]}
outp.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
for name in texts:
    if name in out and name not in missing:
        r = out[name]
        print(name, r['prediction_short'], '%d%% human' % round(100 * r['fraction_human']),
              '; '.join('%s %s %s' % ('H' if w['label'].startswith('Human') else 'AI', w['confidence'], w['words']) for w in r['windows']))
if missing:
    print('no result yet:', ', '.join(missing))
