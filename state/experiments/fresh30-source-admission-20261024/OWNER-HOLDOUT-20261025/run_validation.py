#!/usr/bin/env python3
"""New-family owner comparison. Evaluator receives no owner ratings or detector outcomes."""
from __future__ import annotations
import os,json,hashlib,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parent
DATA=json.loads((R/'BLIND-INPUTS.json').read_text())
PROMPTS=json.loads((R/'PROMPTS.json').read_text())
OUT=R/'OUTPUTS';OUT.mkdir(exist_ok=True)
SHA=lambda x:hashlib.sha256(x.encode()).hexdigest()
CLI=['/home/joel/.local/bin/claude','-p','--model','sonnet','--effort','medium','--tools','',
 '--restricted','--strict-mcp-config','--disable-slash-commands','--setting-sources','',
 '--no-session-persistence','--max-turns','1','--system-prompt',
 'You are a fresh source-grounded editor. Use only the current explicit task, not prior projects or remembered evaluations.',
 '--output-format','json']
def call(ident,stage,prompt,meta):
 d=OUT/ident/stage;d.mkdir(parents=True,exist_ok=True)
 f=d/'RECORD.json'
 ph=SHA(prompt)
 if f.exists():
  z=json.loads(f.read_text());assert z['prompt_sha256']==ph,'Changed prompt: '+ident+stage
  print('REUSE',ident,stage,flush=True);return z
 (d/'INPUT.json').write_text(json.dumps({'prompt':prompt,'sha256':ph,'presentation':meta},ensure_ascii=False,indent=2)+'\n')
 env=os.environ.copy()
 for k in ('ANTHROPIC_API_KEY','ANTHROPIC_AUTH_TOKEN','ANTHROPIC_BASE_URL','CLAUDE_CODE_SESSION_ID','OPENAI_API_KEY'):env.pop(k,None)
 start=time.monotonic();error=None
 try:
  v=subprocess.run(CLI,input=prompt,text=True,capture_output=True,cwd=d,env=env,timeout=170)
  code=v.returncode
  raw=json.loads(v.stdout) if code==0 else {}
 except subprocess.TimeoutExpired:
  raw={};code=124;error='TIMEOUT'
 except json.JSONDecodeError:
  raw={};code=125;error='UNPARSEABLE_PROVIDER_JSON'
 text=raw.get('result') or ''
 try:parsed=json.loads(text[text.index('{'):text.rindex('}')+1])
 except Exception:parsed=None
 z={'id':ident,'stage':stage,'prompt_sha256':ph,'response_sha256':SHA(text),'result':text,
 'parsed':parsed,'returncode':code,'error':error,'usage':raw.get('usage'),
 'reported_cost_usd':raw.get('total_cost_usd'),'elapsed_s':round(time.monotonic()-start,2),
 'model_config':'sonnet/medium/restricted/no-tools/fresh-process','presentation':meta}
 f.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n')
 print('CAPTURED',ident,stage,'valid_json',parsed is not None,'chars',len(text),flush=True)
 return z
# No GOLD-KEY is opened until all outputs are frozen on disk.
for idx,c in enumerate(DATA['style']):
 for order in (0,1):
  order=(order+idx)%2
  m={'X':'A','Y':'B'} if order==0 else {'X':'B','Y':'A'}
  prompt=PROMPTS['style_prefix_exact']+c['heading']+'\nCANDIDATE X:\n'+c['versions'][m['X']]+'\nCANDIDATE Y:\n'+c['versions'][m['Y']]
  call(c['id'],'order-'+str(order),prompt,{'X':m['X'],'Y':m['Y']})
for c in DATA['function']:
 prompt=(PROMPTS['function_prefix']+'\nHEADING: '+c['heading']+
  '\nSOURCE EXCERPT:\n'+c['before']+'\n\nPROPOSED DELETION:\n'+c['deleted_text']+
  '\n\nRESULTING EXCERPT (punctuation may need mechanical cleanup):\n'+c['proposed_after'])
 call(c['id'],'function',prompt,{'scope':'delete nominated wording only'})
print('OUTPUT_FREEZE_COMPLETE','style_cases',len(DATA['style']),'style_trials',2*len(DATA['style']),
 'function_cases',len(DATA['function']),'Pangram',0,flush=True)
