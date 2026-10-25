#!/usr/bin/env python3
"""Four prior owner judgments, hidden from fresh rubric-matched evaluators."""
import os,json,hashlib,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parent
DATA=json.loads((R/'INPUTS.json').read_text())
CLI=['/home/joel/.local/bin/claude','-p','--model','sonnet','--effort','medium','--tools','','--restricted','--strict-mcp-config','--disable-slash-commands','--setting-sources','','--no-session-persistence','--max-turns','1','--system-prompt','You are a fresh source-grounded editor. Use only the current explicit task, not prior projects or remembered evaluations.','--output-format','json']
rows=[]
for c in DATA['cases']:
 d=R/c['id']/'STYLE_ONLY';d.mkdir(exist_ok=True)
 variants={'A':c['before'],'B':c['after']};m=c['anonymous_map']
 prompt=('Assess only the human-sounding naturalness of these two essay excerpts. Neither is privileged as a source or original. Do not infer actual authorship or detector scores. Do not score semantic fidelity in this stage. Judge the writing as a reader, including the relationships between thoughts, pacing, voice, and rhetorical effects. Clear, short, polished prose is not automatically more natural; a long sentence is not automatically worse. Do not penalize a version merely because it changes syntax or point of view compared with the other. Return JSON with X and Y objects containing voice_score_1_to_5 and prose_comment, plus preference X/Y/TIE and why.\nHEADING: '+c['heading']+'\nCANDIDATE X:\n'+variants[m['X']]+'\nCANDIDATE Y:\n'+variants[m['Y']])
 ph=hashlib.sha256(prompt.encode()).hexdigest();record=d/'RECORD.json'
 if record.exists():
  obj=json.loads(record.read_text());assert obj['prompt_sha256']==ph
 else:
  (d/'PROMPT.txt').write_text(prompt)
  env=os.environ.copy()
  for k in ['ANTHROPIC_API_KEY','ANTHROPIC_AUTH_TOKEN','ANTHROPIC_BASE_URL','CLAUDE_CODE_SESSION_ID']:env.pop(k,None)
  z=subprocess.run(CLI,input=prompt,text=True,capture_output=True,cwd=d,env=env,timeout=170)
  raw=json.loads(z.stdout) if z.returncode==0 else {}
  obj={'case':c['id'],'prompt_sha256':ph,'returncode':z.returncode,'result':raw.get('result'),'usage':raw.get('usage'),'reported_cost_usd':raw.get('total_cost_usd')}
  record.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
 text=obj.get('result') or '';j=json.loads(text[text.index('{'):text.rindex('}')+1]);byarm={m[a]:j[a] for a in ['X','Y']}
 a=float(byarm['A']['voice_score_1_to_5']);b=float(byarm['B']['voice_score_1_to_5']);pref='B' if b>a else 'A' if a>b else 'TIE'
 rows.append({'case':c['id'],'owner_naturalness':c['owner_naturalness'],'model_naturalness':pref,'naturalness_matches_owner':pref==c['owner_naturalness'],'owner_fidelity_B':c['owner_fidelity_B'],'model_fidelity_B':None,'fidelity_matches_owner':None,'joint_preference':m.get(j['preference'],j['preference']),'model_by_original_label':byarm,'why':j['why']})
 print('CALIBRATION',c['id'],'style',pref,'owner',c['owner_naturalness'],'fidelity_B','NOT_MEASURED','owner',c['owner_fidelity_B'],flush=True)
 (R/'STYLE-ONLY-RESULTS.json').write_text(json.dumps({'schema':'style-only-owner-calibration-results-v1','n':len(rows),'cases':rows,'new_Pangram_calls':0,'limitations':'four familiar hand-selected calibration cases; fresh reviewer contexts but same provider, not held-out population accuracy; owners prior direct judgments remain authoritative'},ensure_ascii=False,indent=2)+'\n')
print('COMPLETE',len(rows),'style_matches',sum(x['naturalness_matches_owner'] for x in rows),'of',len(rows),'fidelity_matches',sum(x['fidelity_matches_owner'] is True for x in rows),'of',sum(x['fidelity_matches_owner'] is not None for x in rows),flush=True)
