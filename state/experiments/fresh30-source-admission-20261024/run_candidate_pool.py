#!/usr/bin/env python3
"""Frozen two-family, three-architecture candidate-pool and independent selector. No detector."""
import os,sys,json,time,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parent
P=json.loads((R/'POOL-SELECTOR-PLAN.json').read_text())
C={x['id']:x for x in json.loads((R/'COHORT.json').read_text())['source_texts']}
V=R/'PILOT-RESTRICTED-RESULTS'
O=R/'PILOT-CANDIDATE-POOL'
O.mkdir(exist_ok=True)
SHA=lambda x:hashlib.sha256(x.encode()).hexdigest()
CMD=['/home/joel/.local/bin/claude','-p','--model','sonnet','--effort','medium','--tools','',
 '--restricted','--strict-mcp-config','--disable-slash-commands','--setting-sources','',
 '--no-session-persistence','--max-turns','1','--system-prompt',
 'You are a fresh source-grounded literary worker. Use only the current user request. Do not access prior projects or memory.',
 '--output-format','json']
JOBS={
'ATTENTION':('Follow one concrete question the reader is already facing within this exact supplied thought. '
 'Let attention shift with the actual question and answer, rather than making each sentence deliver a separate instruction. '
 'Keep the original claims, certainty, order of safety conditions, named options and voice. No new scene, anecdote, advice or facts.'),
'CONNECTED':('Develop the relationships among the people, options, boundaries and consequences as one unfolding argument; '
 'do not arrange sentences as a checklist of semantic duties. Preserve every source claim, condition, role and range. '
 'Do not invent any personal example, extra claim or therapeutic reassurance.'),
'SPARSE':('Use minimum-dose editorial judgment. If the draft is already intelligible and faithful, return it unchanged. '
 'Otherwise change only demonstrably awkward or over-engineered phrasing. Do not improve grammar by introducing extra explanation or shifting certainty.')
}
def go(cid,stage,prompt):
 d=O/cid/stage
 if d.exists():
  rec=d/'RECORD.json'
  if not rec.exists():raise RuntimeError('Existing incomplete stage '+str(d))
  obj=json.loads(rec.read_text())
  assert obj['prompt_sha256']==SHA(prompt),'Prompt differs from saved stage'
  print('EXACT_STAGE_REUSE',cid,stage,obj.get('result_sha256'),flush=True)
  return obj
 d.mkdir(parents=True)
 (d/'PROMPT.txt').write_text(prompt)
 env=os.environ.copy()
 for k in ('OPENAI_API_KEY','ANTHROPIC_API_KEY','ANTHROPIC_AUTH_TOKEN','ANTHROPIC_BASE_URL','CLAUDE_CODE_SESSION_ID'):
  env.pop(k,None)
 start=time.monotonic()
 try:
  r=subprocess.run(CMD,input=prompt,text=True,capture_output=True,cwd=d,env=env,timeout=170)
  raw=r.stdout;err=r.stderr;rc=r.returncode
 except subprocess.TimeoutExpired:
  raw='';err='TIMEOUT';rc=124
 (d/'RAW.json').write_text(raw)
 (d/'STDERR.txt').write_text(err[:1200])
 result=None;usage=None;cost=None
 if rc==0:
  try:
   z=json.loads(raw);result=z.get('result');usage=z.get('usage');cost=z.get('total_cost_usd')
  except Exception:pass
 obj={'case':cid,'stage':stage,'result':result,'result_sha256':SHA(result) if isinstance(result,str) else None,
  'prompt_sha256':SHA(prompt),'usage':usage,'reported_cost_usd':cost,'returncode':rc,'elapsed':round(time.monotonic()-start,2)}
 (d/'RECORD.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
 print('STAGE',cid,stage,'ok',rc==0 and bool(result),'chars',len(result or ''),flush=True)
 return obj
report=[]
for cid in P['cases']:
 base=json.loads((V/cid/'baseline.json').read_text())['result']
 gen={}
 for name,method in JOBS.items():
  prompt=('You are not writing from an editor instruction list: rewrite exactly ONE paragraph so it reads naturally. '
    'Preserve every assertion, attribution, timeline, actor, cause, condition, hedge and practical permission. '
    'Return one paragraph only, no notes or headings; unchanged is valid. '
    'You may NOT invent facts, examples, reassurances, autobiographical context or treatment advice.\n'
    'Specific thought-composition assignment: '+method+'\n\nSOURCE DRAFT:\n'+base)
  r=go(cid,'CANDIDATE_'+name,prompt)
  if not isinstance(r.get('result'),str) or not r['result'].strip() or '\n' in r['result'].strip():
   gen[name]=None
  else:gen[name]=r['result']
 candidates={'old_A':json.loads((V/cid/'arm_A.json').read_text())['result'],
  'old_B':json.loads((V/cid/'arm_B.json').read_text())['result'],**gen}
 mapping=P['selector_mapping_by_case'][cid]
 lines=[]
 for label,name in mapping.items():
  x=candidates.get(name)
  if x is not None:lines.append('Candidate '+label+':\n'+x)
  else:lines.append('Candidate '+label+': INVALID / unavailable')
 selector=('You are an external reader/editor in a fresh isolated model session. '
  'You did not generate these candidates. Keep the owner SOURCE thought and rhetorical purpose as the highest authority. '
  'Compare anonymous candidate texts for fidelity to all substantive units, exact qualifications and actual decision boundaries. '
  'Naturalness and idiosyncratic thinking are secondary; a polished but unfaithful version fails. '
  'Do not give credit for contractions, extra explanations or length alone. '
  'Do not attempt to infer AI authorship or Pangram results. '
  'Return a JSON object with keys: per_candidate (map of labels with faithful_boolean, material_losses array, added_claims array, naturalness_1_to_5, explanation); '
  'best_joint_choice (one label or NONE); best_naturalness (one label or NONE); reason string. '
  'If all have serious fidelity damage, choose NONE.\n\nORIGINAL SOURCE:\n'+C[cid]['source_text']+
  '\n\n'+'\n\n'.join(lines))
 rev=go(cid,'SELECTOR',selector)
 report.append({'id':cid,'target_source_sha256':C[cid]['source_sha256'],
  'candidates':[{ 'id':name,'sha256':SHA(x) if x else None,'valid':x is not None}
                for name,x in candidates.items()],
  'anonymous_mapping':mapping,
  'selector_output_sha256':rev.get('result_sha256'),'selector_available':bool(rev.get('result')),
  'no_Pangram_calls':True})
 (O/'CHECKPOINT.json').write_text(json.dumps({'schema':'fixed-candidate-pool-v1','cases':report,
  'status':'IN_PROGRESS' if len(report)<len(P['cases']) else 'FIRST_ATTEMPTS_COMPLETE',
  'no_Pangram_calls':True,'owner_approval':False},ensure_ascii=False,indent=2)+'\n')
print('POOL_FINISHED',len(report),'selector_results',sum(x['selector_available'] for x in report),'pangram',0,flush=True)
