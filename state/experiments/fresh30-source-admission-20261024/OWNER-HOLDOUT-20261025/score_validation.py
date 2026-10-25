#!/usr/bin/env python3
"""Score already frozen fresh evaluator outputs; no model calls and no detector calls."""
import json,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parent
D=json.loads((R/'BLIND-INPUTS.json').read_text());G=json.loads((R/'GOLD-KEY.json').read_text())
SG={x['id']:x for x in G['style']};FG={x['id']:x for x in G['function']}
style=[];functions=[];usage=[]
for case in D['style']:
 trials=[]
 for order in [0,1]:
  path=R/'OUTPUTS'/case['id']/('order-'+str(order))/'RECORD.json'
  z=json.loads(path.read_text());usage.append(z);j=z.get('parsed');mp=z['presentation']
  assert hashlib.sha256(z['result'].encode()).hexdigest()==z['response_sha256']
  if j:
   arms={mp[k]:j[k] for k in ['X','Y']}
   a=float(arms['A']['voice_score_1_to_5']);b=float(arms['B']['voice_score_1_to_5'])
   vote='A' if a>b else 'B' if b>a else 'TIE'
   pref=mp.get(j.get('preference'),j.get('preference'))
  else:a=b=None;vote=pref='INVALID';arms={}
  trials.append({'order':order,'owner_preference':SG[case['id']]['owner_style_preference'],
    'numeric_rank':vote,'textual_preference':pref,'agrees':vote==SG[case['id']]['owner_style_preference'],
    'scores':{'A':a,'B':b},'by_original_version':arms,'why':j.get('why') if j else None,
    'response_sha256':z['response_sha256']})
 stable=trials[0]['numeric_rank']==trials[1]['numeric_rank']
 style.append({'id':case['id'],'family':case['family'],'label_strength':SG[case['id']]['label_strength'],
    'owner_preference':SG[case['id']]['owner_style_preference'],
    'both_AI_like_according_to_owner':SG[case['id']]['both_still_AI_like'],
    'stable_between_orders':stable,'both_orders_agree_with_owner':all(x['agrees'] for x in trials),
    'any_order_agrees_with_owner':any(x['agrees'] for x in trials),'trials':trials})
for case in D['function']:
 z=json.loads((R/'OUTPUTS'/case['id']/'function'/'RECORD.json').read_text());usage.append(z);j=z.get('parsed') or {}
 assert hashlib.sha256(z['result'].encode()).hexdigest()==z['response_sha256']
 pred=j.get('recommendation','INVALID');answer=FG[case['id']]['owner_choice']
 functions.append({'id':case['id'],'heading':case['heading'],'owner_recommendation':answer,
    'model_recommendation':pred,'matches':pred==answer,'material_function_lost':j.get('material_function_lost'),
    'functions_retained':j.get('functions_retained'),'functions_lost':j.get('functions_lost'),
    'exact_supporting_words':j.get('exact_supporting_words'),'why':j.get('why'),
    'owner_answer_verbatim':FG[case['id']]['owner_answer_verbatim'],'response_sha256':z['response_sha256']})
flat=[t for s in style for t in s['trials']]
summary={'schema':'owner-different-family-evaluator-results-v1','style':style,'function':functions,
 'counts':{'style_cases':len(style),'style_trials':len(flat),'numeric_rank_trial_agreement':sum(t['agrees'] for t in flat),
 'stable_both_order_owner_matches':sum(s['both_orders_agree_with_owner'] for s in style),
 'at_least_one_order_owner_matches':sum(s['any_order_agrees_with_owner'] for s in style),
 'stable_order_rankings':sum(s['stable_between_orders'] for s in style),
 'function_cases':len(functions),'function_owner_agreement':sum(f['matches'] for f in functions),
 'owner_keep':sum(f['owner_recommendation']=='KEEP' for f in functions),
 'owner_cut':sum(f['owner_recommendation']=='CUT' for f in functions),
 'model_keep':sum(f['model_recommendation']=='KEEP' for f in functions),
 'model_cut':sum(f['model_recommendation']=='CUT' for f in functions),
 'keep_recall_numerator':sum(f['matches'] and f['owner_recommendation']=='KEEP' for f in functions),
 'cut_recall_numerator':sum(f['matches'] and f['owner_recommendation']=='CUT' for f in functions)},
 'no_new_Pangram_calls':True,'provider_calls':len(usage),
 'inherited_cache_read_tokens':sum((x.get('usage') or {}).get('cache_read_input_tokens',0) for x in usage),
 'provider_reported_cost_estimate_usd':sum(x.get('reported_cost_usd') or 0 for x in usage),
 'limits':['Five distinct style comparisons, not ten independent tests; swapped order repeats are dependence diagnostics.',
  'Style and function pools were curated with owner labels visible to the curator, but hidden from fresh model calls.',
  'Historically developed source families are new to this unchanged style prompt calibration, not virgin project data.',
  'Function labels are owner editorial KEEP/CUT decisions, not externally verified truth or medical guidance.',
  'One writer, same model family; no claim of population accuracy or owner style equivalence.']}
(R/'RESULTS.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary['counts'],indent=2));print('STYLE',[(s['id'],s['owner_preference'],[t['numeric_rank'] for t in s['trials']]) for s in style]);print('FUNCTION',[(x['id'],x['owner_recommendation'],x['model_recommendation']) for x in functions])
