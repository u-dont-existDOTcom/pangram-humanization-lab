from pathlib import Path
import json,hashlib,html,importlib.util,sys
STUDY=Path(__file__).resolve().parent.parent
OUT=STUDY/'COMMENTABLE-r02';TOOLS=OUT/'tools'
spec=importlib.util.spec_from_file_location('reviewgen',TOOLS/'interactive_review.py');g=importlib.util.module_from_spec(spec);sys.modules[spec.name]=g;spec.loader.exec_module(g)
inputs=json.loads((STUDY/'INPUTS.json').read_text());drafts=json.loads((OUT/'DRAFTS-r02.json').read_text());owner=json.loads((OUT/'OWNER-CORRECTION.json').read_text())
oldmap={c['id']:c for c in inputs['targets']}
def source_html(side):
 return '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Six paragraph candidates</title></head><body><article>'+''.join('<h2>'+html.escape(c['title'])+'</h2><p>'+html.escape(oldmap[c['id']]['source_text'] if side=='old' else c['candidate_text'])+'</p>' for c in drafts['cases'])+'</article></body></html>'
oldfile=OUT/'Historical_Sources.html';newfile=OUT/'Revised_Candidates_r02.html'
oldfile.write_text(source_html('old'));newfile.write_text(source_html('new'))
oldblocks=[b for b in g.extract_blocks(oldfile.read_text()) if b.kind=='p'];newblocks=[b for b in g.extract_blocks(newfile.read_text()) if b.kind=='p']
assert len(oldblocks)==len(newblocks)==6
rows=[]
for before,after,c in zip(oldblocks,newblocks,drafts['cases']):
 row=g.align_blocks([before],[after])[0];row['id']=c['id'];row['classification']='Provisional wording; owner removal applied' if c['id']=='W01' else 'Provisional wording — awaiting review'
 row['reason']={'summary':c['operation'],'origin':'Current-context research candidate; not an article edit or detector pass.','instructions':[c['remaining_question'],'Use comments to identify awkward writing, missing meaning, or a preferable version. Historical source text remains unchanged as evidence.']}
 rows.append(row)
text=oldmap['W01']['source_text'];quote=owner['corrections'][1]['source_quoted_sentence'];start=text.index(quote)
initial={'W01:old':{'decision':'','decision_history':[],'comment':'OWNER CORRECTION — already implemented in the revised column: '+owner['owner_verbatim'].split('but re the grief para, ',1)[1],
 'scope':'selected-text','quote':quote,'quote_start':start,'quote_end':start+len(quote),'updated':'2026-10-25','humor':2,'technical':2,'length':2,'bluntness':2}}
template=(TOOLS/'review_interface_template.html').read_text()
needle="  let memoryState = {};\n  try { memoryState = JSON.parse(localStorage.getItem(STORE_KEY) || '{}'); } catch(e) { memoryState = {}; }"
assert template.count(needle)==1
seed=json.dumps(initial,ensure_ascii=False).replace('</','<\\/')
replacement="  const OWNER_SEED = "+seed+";\n  let memoryState = JSON.parse(JSON.stringify(OWNER_SEED));\n  try { const saved = localStorage.getItem(STORE_KEY); if(saved!==null) memoryState=JSON.parse(saved); } catch(e) {}"
template=template.replace(needle,replacement)
needle="  renderAll();\n})();"
assert template.count(needle)==1
extra=r'''
  const importer=document.createElement('input'); importer.type='file';importer.accept='.json,application/json';importer.id='importFeedbackFile';importer.hidden=true;document.body.appendChild(importer);
  const ib=document.createElement('button');ib.type='button';ib.id='importFeedback';ib.textContent='Import saved comments';document.querySelector('.controls').appendChild(ib);
  ib.addEventListener('click',()=>importer.click());
  importer.addEventListener('change',async()=>{try{
    const file=importer.files[0];if(!file)return;const data=JSON.parse(await file.text());
    if(data.format!=='joel-commentable-diff-review-v4'||!data.meta||data.meta.source_sha256!==META.source_sha256||data.meta.revised_sha256!==META.revised_sha256||!Array.isArray(data.items))throw new Error('The comments belong to another source or revision. Nothing was imported.');
    const imported={...memoryState};
    for(const x of data.items){const row=META.rows[x.row_id],side=x.side;
      if(!row||!['old','new'].includes(side)||!row[side]||x.current_text_sha256!==row[side].sha256||typeof x.comment!=='string')throw new Error('A comment has an invalid paragraph identity. Nothing was imported.');
      const quote=x.selected_quote||'';
      if(x.comment_scope==='selected-text' && (row[side].text.slice(x.selected_quote_start,x.selected_quote_end)!==quote))throw new Error('A selected quote does not match. Nothing was imported.');
      const value=(o)=>o&&Number.isInteger(o.value)&&o.value>=0&&o.value<=4?o.value:2;
      imported[x.row_id+':'+side]={decision:['keep','remove','brainstorm',''].includes(x.decision)?x.decision:'',decision_history:Array.isArray(x.decision_history)?x.decision_history:[],comment:x.comment,scope:x.comment_scope||'whole-cell',quote,quote_start:x.selected_quote_start??null,quote_end:x.selected_quote_end??null,humor:value(x.humor),technical:value(x.technical_depth),length:value(x.length),bluntness:value(x.bluntness),updated:x.updated||''};
    }
    memoryState=imported;safeSave();renderAll();renderDrawer();statusLine.textContent='Saved comments imported; unreviewed items remain unreviewed.';
  }catch(e){statusLine.textContent=e.message;alert(e.message);}finally{importer.value='';}});
'''
template=template.replace(needle,extra+needle)
page=g.build_document(template,title='Six paragraph candidates — commentable review',artifact_id='six-thought-candidates-r02-commentable',baseline_type='original-vs-current',row_scope='all-passages',source_label='Historical source — unchanged evidence',new_label='Current proposal — not approved',source_filename=oldfile.name,revised_filename=newfile.name,source_version='saved-model-baseline',new_version='r02-owner-disclaimer-removal',source_sha=g.file_sha(oldfile),revised_sha=g.file_sha(newfile),rows=rows,export_basename='Six_Paragraph_Review_Comments_r02')
oldsub='<div class="sub">Each change is shown inside its article section, with the unchanged passage immediately before and after. Yellow placement labels tell you exactly where an insertion, replacement, or removal occurs. Gray dashed boxes are context only; comments attach to the actual changed boxes.</div>'
assert page.count(oldsub)==1
page=page.replace(oldsub,'<div class="sub">Select any words and press ＋ to comment on them, or press ＋ without a selection to comment on the whole paragraph. Use Review / Export to send your notes back.</div>')
banner='<section class="owner-note" style="max-width:1468px;margin:14px auto;padding:14px 18px;background:#edf6ee;color:#17351d;border:1px solid #86a88b;border-radius:8px"><strong>Your correction is applied.</strong> The unsolicited physiology disclaimer is removed from the current grief candidate. Its historical source remains on the left for provenance, with your objection saved as a selected-text comment. No replacement disclaimer was added. The other five proposals are unchanged; none is treated as approved.<nav aria-label="Paragraphs" style="margin-top:10px">'+ ' · '.join('<a href="#'+c['id']+'" style="color:#17351d">'+html.escape(c['title'])+'</a>' for c in drafts['cases'])+'</nav></section>'
page=page.replace('<main>',banner+'<main>',1)
file=OUT/'Six_Paragraphs_Commentable_r02.html';file.write_text(page)
assert 'physiological mechanism' not in newfile.read_text();assert page.count('data-row-id="W01"')>=2
(OUT/'SOURCE-COMMENT-SEED.json').write_text(json.dumps(initial,ensure_ascii=False,indent=2)+'\n')
(OUT/'ROW-MAP.json').write_text(json.dumps({c['id']:{'title':c['title'],'source_sha256':c['source_sha256'],'candidate_sha256':c['candidate_sha256']} for c in drafts['cases']},ensure_ascii=False,indent=2)+'\n')
print('GENERATED',file,len(page),'SHA256',hashlib.sha256(page.encode()).hexdigest(),'six commentable pairs; selected owner comment seeded')

from tools.review_delivery_check import check_review_html
assert check_review_html(file.read_text(),6)["ok"]
