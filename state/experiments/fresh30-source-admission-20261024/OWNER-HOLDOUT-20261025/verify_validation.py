#!/usr/bin/env python3
"""Read-only source/result verification; does not call providers or detectors."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent
sha=lambda s:hashlib.sha256(s.encode()).hexdigest()
def load(name):return json.loads((R/name).read_text())
D,G,P,C,CR,RES=map(load,['BLIND-INPUTS.json','GOLD-KEY.json','PROMPTS.json','CONTEXT-DIAGNOSTIC.json','CONTEXT-RESULTS.json','RESULTS.json'])
assert len(D['style'])==5 and len(D['function'])==12
assert len({c['family'] for c in D['function']})==12
for c in D['style']:
 for version,text in c['versions'].items():assert sha(text)==c['sha256'][version]
for c in D['function']:
 assert sha(c['before'])==c['source_sha256'] and sha(c['proposed_after'])==c['proposed_after_sha256']
 assert c['deleted_text'] in c['before'] and c['deleted_text'] not in c['proposed_after']
for s in load('SOURCE-SNAPSHOTS.json')['sources']:assert sha(s['content'])==s['sha256']
assert sha(P['style_prefix_exact'])==P['style_prefix_sha256']
assert sha(P['function_prefix'])==P['function_prefix_sha256']
style_gold={x['id']:x for x in G['style']};fun_gold={x['id']:x for x in G['function']}
checks=0;computed=[]
for c in D['style']:
 votes=[]
 for order in [0,1]:
  directory=R/'OUTPUTS'/c['id']/('order-'+str(order))
  z=json.loads((directory/'RECORD.json').read_text());i=json.loads((directory/'INPUT.json').read_text())
  assert sha(i['prompt'])==z['prompt_sha256'] and sha(z['result'])==z['response_sha256']
  assert i['prompt'].startswith(P['style_prefix_exact'])
  m=i['presentation'];assert m==({'X':'A','Y':'B'} if order==0 else {'X':'B','Y':'A'})
  expected=P['style_prefix_exact']+c['heading']+'\nCANDIDATE X:\n'+c['versions'][m['X']]+'\nCANDIDATE Y:\n'+c['versions'][m['Y']]
  assert i['prompt']==expected
  j=z['parsed'];by={m[k]:j[k] for k in ['X','Y']}
  a=float(by['A']['voice_score_1_to_5']);b=float(by['B']['voice_score_1_to_5'])
  vote='A' if a>b else 'B' if b>a else 'TIE';votes.append(vote);checks+=1
 computed.append((c['id'],votes,style_gold[c['id']]['owner_style_preference']))
assert sum(all(v==label for v in votes) for _,votes,label in computed)==4
assert sum(v==label for _,votes,label in computed for v in votes)==8
assert sum(v[0]==v[1] for _,v,_ in computed)==4
fun=[]
for c in D['function']:
 directory=R/'OUTPUTS'/c['id']/'function';z=json.loads((directory/'RECORD.json').read_text());i=json.loads((directory/'INPUT.json').read_text())
 assert sha(i['prompt'])==z['prompt_sha256'] and sha(z['result'])==z['response_sha256']
 expected=P['function_prefix']+'\nHEADING: '+c['heading']+'\nSOURCE EXCERPT:\n'+c['before']+'\n\nPROPOSED DELETION:\n'+c['deleted_text']+'\n\nRESULTING EXCERPT (punctuation may need mechanical cleanup):\n'+c['proposed_after']
 assert i['prompt']==expected
 pred=z['parsed']['recommendation'];gold=fun_gold[c['id']]['owner_choice'];fun.append((pred,gold));checks+=1
assert sum(x==y for x,y in fun)==3
assert sum(x=='UNCERTAIN' for x,y in fun)==3
assert sum(x in ['KEEP','CUT'] and x!=y for x,y in fun)==6
assert [sum(y==v for x,y in fun) for v in ['KEEP','CUT']]==[6,6]
context_good=0
for c in C['cases']:
 assert sha(c['whole_section'])==c['whole_section_sha256'] and c['before'] in c['whole_section']
 directory=R/'OUTPUTS'/c['id']/'full-context';z=json.loads((directory/'RECORD.json').read_text());i=json.loads((directory/'INPUT.json').read_text())
 assert sha(i['prompt'])==z['prompt_sha256'] and sha(z['result'])==z['response_sha256']
 assert i['prompt'].startswith(P['function_prefix']) and c['whole_section'] in i['prompt']
 context_good+=z['parsed']['recommendation']==fun_gold[c['id']]['owner_choice'];checks+=1
assert len(C['cases'])==6 and context_good==3
assert checks==28 and len(list((R/'OUTPUTS').glob('*/*/RECORD.json')))==28
assert RES['counts']['stable_both_order_owner_matches']==4 and RES['counts']['function_owner_agreement']==3
assert CR['n']==6 and CR['now_matches_owner']==3
assert RES['no_new_Pangram_calls'] is True and CR['new_Pangram_calls']==0
print(json.dumps({'result':'PASS','new_style_comparisons':5,'style_order_trials':10,'stable_owner_style_matches':4,'new_function_cases':12,'initial_owner_function_agreement':3,'context_diagnostic_cases':6,'context_corrected':3,'verified_prompt_response_pairs':checks,'new_Pangram_calls':0}))
