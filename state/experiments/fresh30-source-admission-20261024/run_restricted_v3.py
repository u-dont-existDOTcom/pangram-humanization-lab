#!/usr/bin/env python3
"""Pre-registered 3-case real fresh-process study smoke. Never calls Pangram."""
import os,sys,json,hashlib,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parent
V=json.loads((R/'ISOLATED-PILOT-V3.json').read_text())
S={'model':'sonnet','effort':'medium'}
C={x['id']:x for x in json.loads((R/'COHORT.json').read_text())['source_texts']}
T=json.loads((R/'TEACHING.json').read_text())
E={x['id']:x for x in T['examples']}
A={x['target']:x['teacher'] for x in T['allocations']}
O=R/'PILOT-RESTRICTED-RESULTS';O.mkdir(exist_ok=True)
SHA=lambda t:hashlib.sha256(t.encode()).hexdigest()
CMD=['/home/joel/.local/bin/claude','-p','--model',S['model'],'--effort',S['effort'],
     '--tools','','--restricted','--strict-mcp-config','--disable-slash-commands',
     '--setting-sources','','--system-prompt',
     'You are a fresh literary model. Use only the present user message. Do not access earlier project data or inferred preferences.',
     '--no-session-persistence','--max-turns','1','--output-format','json']
def run(cid,stage,prompt):
    d=O/cid;d.mkdir(exist_ok=True)
    saved=d/(stage+'.json')
    if saved.exists():
        obj=json.loads(saved.read_text())
        if obj['prompt_sha256']!=SHA(prompt):
            raise RuntimeError('Stage prompt changed after result persisted: '+cid+':'+stage)
        print(json.dumps({'case':cid,'stage':stage,'cache':'EXACT_STAGE_REUSED','ok':bool(obj.get('result'))}),flush=True)
        return obj
    subdir=d/stage
    subdir.mkdir(exist_ok=False)
    (subdir/'PROMPT.txt').write_text(prompt)
    env=os.environ.copy()
    for key in ['ANTHROPIC_API_KEY','ANTHROPIC_AUTH_TOKEN','ANTHROPIC_BASE_URL',
                'OPENAI_API_KEY','CLAUDE_CODE_SESSION_ID']:env.pop(key,None)
    start=time.monotonic()
    try:
        p=subprocess.run(CMD,input=prompt,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                         text=True,cwd=subdir,env=env,timeout=180)
        stdout=p.stdout;stderr=p.stderr;code=p.returncode;error=None
    except subprocess.TimeoutExpired as ex:
        stdout=ex.stdout or '';stderr=ex.stderr or '';code=None;error='timeout'
    result={'case':cid,'stage':stage,'prompt_sha256':SHA(prompt),'elapsed_s':round(time.monotonic()-start,2),
            'return_code':code,'error':error,'result':None}
    (subdir/'RAW.json').write_text(str(stdout))
    (subdir/'STDERR.txt').write_text(str(stderr)[:1200])
    if code==0:
        try:
            j=json.loads(stdout);result['result']=j.get('result')
            result['usage']=j.get('usage');result['reported_cost_usd']=j.get('total_cost_usd')
            result['is_error']=j.get('is_error',False)
        except Exception as ex:result['error']='response_json_invalid:'+type(ex).__name__
    if isinstance(result['result'],str):result['result_sha256']=SHA(result['result'])
    (d/(stage+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'case':cid,'stage':stage,'ok':bool(result['result'] and not result.get('is_error')),
                      'response_chars':len(result['result'] or ''),'error':result['error']}),flush=True)
    return result
def dossier(cid):
    return ('Preserve claims, stance, agency, chronology, uncertainty, intentional metaphor, '
            'humor and useful qualifications. Avoid added facts, apology/therapy aftercare '
            'or a new lesson not in the paragraph.')

def fidelity_json(text):
    try:
        t=text[text.index('{'):text.rindex('}')+1]
        j=json.loads(t)
        return j['preserve_all_critical_units'] is True and all(not j.get(k) for k in
          ['omissions','additions','certainty_changes'])
    except Exception:return False
summaries=[]
for spec in V['cases']:
    cid=spec['id'];src=C[cid]['source_text'];d=dossier(cid)
    p0=("Rewrite the EXACT registered source paragraph in a compact, clear, natural expository register. "
        "Retain each actual assertion, author point of view, agency, attribution, chronology, numbers, uncertainty, qualifications and rhetorical function. "
        "This is a prose transformation, not a new argument or general lesson. "
        "Do not add, remove or fact-check claims. No additional examples, interpretations or recommendations. "
        "Keep approximately the same detail and length. Return the revised paragraph only.\n\nEXACT SOURCE PARAGRAPH:\n"+src)
    if spec['baseline_mode']=='recovered_frozen_V2':
        prev=json.loads((R/'PILOT-SOURCE-RESULTS'/cid/'baseline.json').read_text())
        base=(prev.get('result') or '').strip()
        if SHA(base)!=spec['exact_baseline_sha256']:
            raise RuntimeError('Frozen prior baseline changed: '+cid)
        b={'result':base,'result_sha256':SHA(base),'is_error':False}
        (O/cid).mkdir(exist_ok=True)
        (O/cid/'BASELINE-PROVENANCE.json').write_text(json.dumps(
            {'status':'REUSED_FROM_EXACT_V2_SAVED_BASELINE_NOT_FRESH_REGENERATION',
             'sha256':SHA(base),'source_record':'PILOT-SOURCE-RESULTS/'+cid+'/baseline.json'},
            indent=2)+'\n')
    else:
        b=run(cid,'baseline',p0)
        base=(b.get('result') or '').strip()
    if not b.get('result') or b.get('is_error'):
        summaries.append({'case':cid,'status':'BASELINE_CALL_FAILED'});continue
    if '\n' in base:
        summaries.append({'case':cid,'status':'BASELINE_FORMAT_REJECTED','baseline_sha256':SHA(base)});continue
    fp=("In a fresh editorial context, compare SOURCE and DRAFT for MATERIAL preservation. "
        "Count only reader-relevant changes in assertions, numerical details, certainty, agency, causality, attributions, qualifications, rhetorical functions or practical advice; "
        "a harmless synonym or new grammar alone is not a material omission/addition. "
        "Do not fact-check beyond these texts. Return only JSON: preserve_all_critical_units (boolean), "
        "omissions (material only), additions (material only), certainty_changes (material only), notes.\nSOURCE:\n"+src+"\nDRAFT:\n"+base)
    f=run(cid,'baseline_fidelity',fp)
    if not fidelity_json(f.get('result') or ''):
        summaries.append({'case':cid,'status':'BASELINE_FIDELITY_NOT_ADMITTED',
                          'baseline_sha256':SHA(base)});continue
    candidates={}
    for arm in spec['arm_order']:
        prompt=('One first-attempt faithful prose revision. Keep every claim, actor, causal link, '
          'qualification, rhetorical job and source distinction. Do not invent facts or personal history. '
          'If already good, unchanged is allowed. Return exactly ONE paragraph with no line breaks, no headings and no notes.\n'+
          d+'\nMODEL DRAFT:\n'+base)
        if arm=='B':
            e=E[A[cid]]
            prompt+=('\nLITERAL TEACHING EXAMPLE FROM A DIFFERENT SOURCE ARTICLE:\n'
              'Before: '+e['source_before']+'\nAfter: '+e['source_after']+
              '\nLimits: '+e['limits']+'\nLearn the transformation, not its facts or phrases.')
        candidates[arm]=run(cid,'arm_'+arm,prompt)
    if not all(isinstance(candidates[a].get('result'),str) and candidates[a]['result']
               for a in ('A','B')):
        summaries.append({'case':cid,'status':'ONE_OR_BOTH_ARMS_FAILED'});continue
    # Shuffle visible labels; assessor never sees arms, teaching cards, or detector outcomes.
    order=['A','B'] if cid not in ('T09','T16','T28') else ['B','A']
    rp=('Fresh editorial review. Compare both candidates with the original SOURCE text '
        'for *meaning and rhetorical function* rather than factual truth. The candidates '
        'are anonymous. Evaluate voice/naturalness independently of fidelity. '
        'Return JSON with X/Y objects: fidelity_ok, missing, added, '
        'voice_score_1_to_5, prose_comment; preference X/Y/TIE and why. '
        'Do not infer authorship or detector labels.\nSOURCE:\n'+src+
        '\nCANDIDATE X:\n'+candidates[order[0]]['result']+
        '\nCANDIDATE Y:\n'+candidates[order[1]]['result'])
    rev=run(cid,'blind_review',rp)
    (O/cid/'anonymous-label-map.json').write_text(json.dumps({'X':order[0],'Y':order[1]},indent=2))
    summaries.append({'case':cid,'status':'FIRST_ATTEMPTS_AND_REVIEW_CAPTURED' if rev.get('result')
                      else 'REVIEW_FAILED','baseline_sha256':SHA(base),
                      'arm_a_sha256':candidates['A'].get('result_sha256'),
                      'arm_b_sha256':candidates['B'].get('result_sha256'),
                      'format_pass_A':('\n' not in candidates['A']['result'].strip()),
                      'format_pass_B':('\n' not in candidates['B']['result'].strip())})
summary={'schema':'fresh30-restricted-pilot-v3','method':'distinct_fresh_restricted_no_autoload_cli_contexts',
         'model':S['model'],'effort':S['effort'],'cases':summaries,
         'calls_pangram':0,'owner_style_approval':False,'independent_across_authors':False,
         'pilot_only':True}
(O/'SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print('SMOKE_FINAL',json.dumps({'cases':len(summaries),'complete':sum(x['status']=='FIRST_ATTEMPTS_AND_REVIEW_CAPTURED' for x in summaries),'Pangram':0}),flush=True)
