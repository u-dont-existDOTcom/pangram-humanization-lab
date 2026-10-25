#!/usr/bin/env python3
"""Render exact owner-baseline versus candidate; no invented detector colors."""
from pathlib import Path
import json,html,hashlib
R=Path(__file__).resolve().parent
D=json.loads((R/'READING-DATA.json').read_text());E=html.escape
css='''html{color-scheme:light;background:#f3f5f7;color:#172330}*{box-sizing:border-box}body{margin:0;color:#172330;font:17px/1.65 system-ui,sans-serif}main{max-width:1180px;margin:auto;padding:40px 24px 70px}h1{font-size:34px;line-height:1.2}h2{font-size:24px}h3{font-size:20px}.card{background:#fff;border:1px solid #cbd5df;padding:24px;border-radius:8px;margin:24px 0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:24px}.bodytext{white-space:pre-wrap;font-family:Georgia,serif;font-size:18px}.label{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:#4a5e70}.note{font-size:14px;color:#425364}a,summary{color:#174b7a}summary{cursor:pointer}.failure{border-left:5px solid #a44624}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.6 system-ui,sans-serif}.ruling{padding:12px 18px;background:#f0f3f6}code{overflow-wrap:anywhere}@media(max-width:700px){main{padding:24px 14px}.grid{grid-template-columns:1fr}.card{padding:18px}h1{font-size:27px}}'''
out=['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Owner-bounded writing: full comparisons</title><style>'+css+'</style></head><body><main>',
'<div class="label">25 October 2026 · read-only development evidence</div><h1>Owner-bounded writing: all twelve cases</h1>',
'<p>Known owner decisions are authority, not something this model was asked to vote on. Six passages were unchanged; six received one proposed wording adjustment. One adjustment is rejected for changing meaning. No article was edited and no new Pangram call was made.</p>',
'<p class="note">These are historical research excerpts, not current publication copies or health guidance. The baseline implements the exact owner instruction; the candidate is an unapproved experiment. Highlighting does not represent detector results.</p>',
'<nav>'+ ' · '.join('<a href="#'+x['id']+'">'+x['id']+'</a>' for x in D['cases'])+'</nav>',
'<details><summary>Research report, limitations and interpretation</summary><pre>'+E(D['report'])+'</pre></details>']
for x in D['cases']:
 r=x['result'];failed=r['evidence_disposition']=='FIDELITY_REJECTED';cls='card failure' if failed else 'card'
 out.append('<section id="'+x['id']+'" class="'+cls+'"><div class="label">'+E(x['id'])+'</div><h2>'+E(x['heading'])+'</h2><p><strong>'+E(r['evidence_disposition'].replace('_',' ').title())+'</strong></p>')
 out.append('<div class="ruling"><b>Recorded owner decision: '+E(x['owner_decision'])+'</b><p class="note">'+E(x['owner_words'])+'</p><p class="note">The target was: “'+E(x['owner_target'])+'”</p></div>')
 if r['changed']:
  out.append('<div class="grid"><div><h3>Owner-directed baseline</h3><p class="bodytext">'+E(x['baseline'])+'</p></div><div><h3>Experimental candidate</h3><p class="bodytext">'+E(x['candidate'])+'</p></div></div>')
  for patch in r['edits']:
   out.append('<details><summary>Exact replacement and writer rationale</summary><p>Before: '+E(patch['old'])+'</p><p>After: '+E(patch['new'])+'</p><p class="note">Writer explanation, not a validated fact: '+E(patch['why'])+'</p></details>')
  out.append('<details><summary>Separate reviews, including disagreement</summary><p>Style scores: baseline '+str(r['style_scores']['baseline'])+', candidate '+str(r['style_scores']['candidate'])+'. Verbal preference: '+E(r['style_verbal_preference'])+'.</p><p>'+E(r['style_explanation'])+'</p><p><b>Meaning-difference reader:</b> '+E(r['delta_audit']['summary'])+'</p><pre>'+E(json.dumps(r['delta_audit']['differences'],ensure_ascii=False,indent=2))+'</pre></details>')
 else:
  out.append('<p class="note">The writer proposed no additional change. No redundant reviewer calls were made on identical text.</p><p class="bodytext">'+E(x['baseline'])+'</p>')
 out.append('<details><summary>Original shown in the owner question</summary><p class="bodytext">'+E(x['original'])+'</p></details></section>')
out.append('<footer class="note">All owner-source text, execution prompts, first attempts and review records accompany the full evidence archive. No automatic author-quality approval or new production rule is implied.</footer></main></body></html>')
p=R/'Pangram_Owner_Bounded_Full_Comparisons.html';p.write_text(''.join(out),encoding='utf-8');print('HTML',len(out),'cases',len(D['cases']),'sha256',hashlib.sha256(p.read_bytes()).hexdigest())
