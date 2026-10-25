#!/usr/bin/env python3
"""Owner-directed local writing research. No detector or article mutation."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent
DATA=json.loads((R/'INPUTS.json').read_text())
STYLE=json.loads((R/'STYLE-PROMPT.json').read_text())
OUT=R/'OUTPUTS';OUT.mkdir(exist_ok=True)
SHA=lambda s:hashlib.sha256(s.encode('utf-8')).hexdigest()
CLI=['/home/joel/.local/bin/claude','-p','--model','sonnet','--effort','medium',
 '--tools','','--restricted','--strict-mcp-config','--disable-slash-commands',
 '--setting-sources','','--no-session-persistence','--max-turns','1',
 '--system-prompt','You are a fresh literary research worker. Use only this explicit task; no prior projects, memory, tools or external knowledge.',
 '--output-format','json']
def call(cid,stage,prompt):
    d=OUT/cid/stage;d.mkdir(parents=True,exist_ok=True)
    f=d/'RECORD.json';ph=SHA(prompt)
    if f.exists():
        z=json.loads(f.read_text());assert z['prompt_sha256']==ph,'Changed prompt after output'
        print('REUSE',cid,stage,flush=True);return z
    (d/'PROMPT.txt').write_text(prompt,encoding='utf-8')
    env=os.environ.copy()
    for key in ('ANTHROPIC_API_KEY','ANTHROPIC_AUTH_TOKEN','ANTHROPIC_BASE_URL','OPENAI_API_KEY','CLAUDE_CODE_SESSION_ID'):env.pop(key,None)
    start=time.monotonic();error=None
    try:
        proc=subprocess.run(CLI,input=prompt,text=True,capture_output=True,cwd=d,env=env,timeout=170)
        code=proc.returncode;raw=json.loads(proc.stdout) if code==0 else {}
    except subprocess.TimeoutExpired:raw={};code=124;error='TIMEOUT_NO_RETRY'
    except json.JSONDecodeError:raw={};code=125;error='PROVIDER_SERIALIZATION_FAILURE'
    text=raw.get('result') or ''
    try:parsed=json.loads(text[text.index('{'):text.rindex('}')+1])
    except (ValueError,json.JSONDecodeError):parsed=None
    z={'case':cid,'stage':stage,'prompt_sha256':ph,'response_sha256':SHA(text),'result':text,'parsed':parsed,
       'returncode':code,'error':error,'usage':raw.get('usage'),'reported_cost_usd':raw.get('total_cost_usd'),
       'elapsed_s':round(time.monotonic()-start,2),'configuration':'sonnet/medium/restricted/fresh-process/no-tools'}
    f.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('CAPTURED',cid,stage,'json',parsed is not None,'characters',len(text),flush=True)
    return z

def assemble(c,edits):
    b=c['baseline'];assert SHA(b)==c['baseline_sha256']
    if not isinstance(edits,list) or len(edits)>2:raise ValueError('Not zero-to-two edits')
    positions=[]
    locks=[(b.index(x),b.index(x)+len(x)) for x in c['locked_spans']]
    for e in edits:
        if not isinstance(e,dict) or not all(isinstance(e.get(k),str) for k in ('old','new','why')):raise ValueError('Bad edit schema')
        old,new=e['old'],e['new']
        if not old.strip() or not new.strip() or old==new or b.count(old)!=1:raise ValueError('Nonunique, empty or noop replacement')
        if '\n' in new or new!=new.strip():raise ValueError('Newline or outer whitespace in replacement')
        start=b.index(old);end=start+len(old)
        if any(start<z and end>a for a,z in locks):raise ValueError('Protected owner span touched')
        if any(start<z and end>a for a,z,_ in positions):raise ValueError('Overlapping edit intervals')
        positions.append((start,end,new))
    text=b
    for a,z,new in sorted(positions,reverse=True):text=text[:a]+new+text[z:]
    if any(text.count(x)!=b.count(x) for x in c['locked_spans']):raise ValueError('Owner exact retain count changed')
    if c['prohibited_restoration'] and c['prohibited_restoration'] in text:raise ValueError('Exact owner-deleted wording restored')
    if c['id']=='F22' and 'These are just caution signs' not in text:raise ValueError('Specific owner grammar repair lost')
    return text

def writer_prompt(c):
    rules={'known_owner_choice':c['owner_choice'],'target_of_choice':c['target'],
      'owner_words':c['owner_verbatim'],'exact_retained_spans':c['locked_spans'],
      'do_not_restore':c['prohibited_restoration'],'extra_owner_correction':c['mechanical_owner_corrections']}
    return ('The paragraph below already implements the author\'s exact keep/cut decisions. Do NOT reconsider those decisions. '
      'Make it sound more naturally written only where a concrete wording problem remains. '
      'Preserve the author\'s meaning, claims, chronology, certainty, agency, jokes, spiritual view, attribution and practical conditions. '
      'Treat the paragraph as prose, not a list of duties to restate. No fact-checking or added anecdotes, caveats, therapy advice, comfort, examples or slogans. '
      'You may return NO edits if the remaining prose already works. Do not edit just to demonstrate effort. '
      'The surrounding section is reference only, not something to rewrite. '
      'For this bounded experiment, retained spans below are exact byte locks; make changes only outside them. '
      'Return JSON only: {"edits":[{"old":"exact unique contiguous span copied from PARAGRAPH","new":"replacement","why":"specific wording reason"}],"no_change_reason":"if empty"}. '
      'Zero to TWO disjoint replacements, no empty replacement, no new paragraph breaks. Preserve the specific author correction "These are just caution signs" where present. '
      'Each old span must occur verbatim exactly once in PARAGRAPH. Do not return the complete paragraph.\n'
      'AUTHOR INSTRUCTIONS (authority, not a quiz):\n'+json.dumps(rules,ensure_ascii=False)+
      '\nHEADING: '+c['heading']+'\nSURROUNDING SECTION:\n'+c['context']+'\nPARAGRAPH TO EDIT:\n'+c['baseline'])

def write_all():
    rows=[]
    for c in DATA['cases']:
        z=call(c['id'],'WRITE',writer_prompt(c));obj=z.get('parsed')
        try:
            if not isinstance(obj,dict):raise ValueError('No parseable JSON response')
            edits=obj.get('edits');candidate=assemble(c,edits)
            record={'id':c['id'],'status':'ASSEMBLED','baseline_sha256':c['baseline_sha256'],
              'candidate':candidate,'candidate_sha256':SHA(candidate),'changed':candidate!=c['baseline'],
              'edits':edits,'no_change_reason':obj.get('no_change_reason'),'literal_owner_scope_pass':True,
              'semantic_fidelity':'NOT_PROVEN_BY_LITERAL_LOCKS'}
        except ValueError as exc:
            record={'id':c['id'],'status':'ASSEMBLY_REJECTED','error':str(exc),'raw_response_sha256':z['response_sha256'],
                    'candidate':None,'changed':None,'literal_owner_scope_pass':False}
        (OUT/c['id']/'ASSEMBLED.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
        rows.append(record);print('ASSEMBLY',c['id'],record['status'],'changed',record['changed'],flush=True)
    (R/'CANDIDATES.json').write_text(json.dumps({'schema':'owner-bounded-candidates-v1','cases':rows,'new_Pangram_calls':0},ensure_ascii=False,indent=2)+'\n')

def reviews():
    saved=json.loads((R/'CANDIDATES.json').read_text());rows={x['id']:x for x in saved['cases']}
    for c in DATA['cases']:
        r=rows[c['id']]
        if r['status']!='ASSEMBLED' or not r['changed']:
            print('REVIEW_NOT_NEEDED',c['id'],r['status'],r['changed'],flush=True);continue
        versions={'baseline':c['baseline'],'candidate':r['candidate']};m=c['anonymous_style_map']
        sp=STYLE['prefix']+c['heading']+'\nCANDIDATE X:\n'+versions[m['X']]+'\nCANDIDATE Y:\n'+versions[m['Y']]
        call(c['id'],'STYLE',sp)
        dp=('Report only concrete meaning/rhetorical differences between BASELINE and CANDIDATE. '
          'BASELINE already reflects the author\'s explicit decisions; do not vote on whether any retained thought is worth keeping. '
          'Do not require identical sentence architecture, every repeated explanation, or superficial wording. '
          'But independently stated claims, scope, agency, conditions, certainty, causal links, quotations, examples, humor and intended qualifications must not change. '
          'Pay attention to new interpretation even if plausible, lost detail even if the broad gist remains, and synonym restoration of the explicitly deleted function. '
          'Use only the source paragraph and the supplied original section; do not check external truth. '
          'Return JSON: {"differences":[{"baseline_words":"exact support or empty for addition","candidate_words":"exact support or empty for deletion","kind":"ADDITION/LOSS/SHIFT/PROHIBITED_RESTORATION","material":true,"explanation":"why this changes a concrete thought/function"}],"unresolved":[],"summary":"..."}. '
          'If there is no material difference, return an empty differences array. Do not give keep/cut permission or style scores.\n'
          'AUTHOR DECISION: '+c['owner_choice']+'; '+c['owner_verbatim']+'\nSPECIFIC TARGET: '+c['target']+
          '\nSOURCE CONTEXT:\n'+c['context']+'\nBASELINE:\n'+c['baseline']+'\nCANDIDATE:\n'+r['candidate'])
        call(c['id'],'DELTA',dp)
    print('REVIEWS_COMPLETE',flush=True)
if __name__=='__main__':
    if sys.argv[1:] == ['write']:write_all()
    elif sys.argv[1:] == ['review']:reviews()
    else:raise SystemExit('Usage: run_bounded.py write|review')
