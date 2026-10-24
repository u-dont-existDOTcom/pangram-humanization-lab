#!/usr/bin/env python3
"""Offline identity/integrity checks; not a semantic or causal validator."""
from pathlib import Path
import json, hashlib, collections

def verify(root: Path) -> dict:
    corpus=json.loads((root/'CORPUS.json').read_text());records=corpus['records'];cs=corpus['comparisons'];summary=corpus['summary']
    lookup={r['sha256']:r for r in records};assert len(lookup)==len(records)==50
    api=gui=0
    for r in records:
        assert hashlib.sha256(r['text'].encode()).hexdigest()==r['sha256']
        assert r['ledger_result']['sha256']==r['sha256'] and r['version']=='4.1'
        if 'raw_gui_summary' in r:
            raw=r['raw_gui_summary'];assert raw['link']==r['ledger_result']['link'] and raw['version']=='4.1'
            human=all(x.split(',')[0].strip()=='Human' for x in raw['windows']);gui+=1
        else:
            end=0
            for w in r['windows']:
                assert w[3]==end and r['text'][w[3]:w[4]]==w[5];end=w[4]
            assert end==len(r['text']);human=all(w[0]=='Human Written' for w in r['windows']);api+=1
        assert human==r['all_human_segments']
    assert api==46 and gui==4 and len(cs)==30 and len({x['family_id'] for x in cs})==20
    counts=collections.Counter(x['status'] for x in cs);assert dict(counts)==summary['classification_counts']
    eligible=[x for x in cs if x['status'] in ['OWNER_APPROVED_SAME_THOUGHT','PROVISIONAL_SAME_THOUGHT']]
    assert len(eligible)==8 and len({x['family_id'] for x in eligible})==8
    outcomes=collections.Counter()
    for c in eligible:
        a,z=(lookup[c[k]]['all_human_segments'] for k in ['before_sha256','after_sha256'])
        outcomes['gain' if not a and z else 'regression' if a and not z else 'both_all_human' if a else 'both_not_all_human']+=1
    assert dict(outcomes)==summary['candidate_outcomes']
    assert sum(c['test_order_reversed'] for c in cs)==5
    assert hashlib.sha256((root/'CURATION.frozen.json').read_bytes()).hexdigest()==corpus['annotation_sha256']
    assert hashlib.sha256((root/'OWNER-ANSWERS.original.json').read_bytes()).hexdigest()=='76999d56f05d17acd2b7fd6c7e7dccd95cde7a45e9d665e9758aa4d459cd55d9'
    page=(root/'Pair_Curation.html').read_text()
    assert '<input' not in page and '<select' not in page and '<textarea' not in page
    assert page.count('<details>')==30 and 'color-scheme:only light' in page
    protocol=json.loads((root/'PILOT-RULES.json').read_text());assert protocol['calls_executed']==0 and summary['new_detector_calls']==0
    manifest_path=root/'MANIFEST.json'
    if manifest_path.exists():
        for p,sha in json.loads(manifest_path.read_text()).items():assert hashlib.sha256((root/p).read_bytes()).hexdigest()==sha,p
    return {'status':'PASS','exact_input_hashes':50,'API_complete_window_bindings':46,'GUI_text_ledger_link_bindings':4,'directed_comparisons':30,'families':20,'same_thought_candidates':8,'candidate_outcomes':dict(outcomes),'reversed_test_order_edges':5,'annotation_hash_verified':True,'owner_answers_hash_verified':True,'read_only_report':True,'new_detector_calls':0,'semantic_or_independent_validation':False}
if __name__=='__main__':
    print(json.dumps(verify(Path(__file__).resolve().parent),indent=2))
