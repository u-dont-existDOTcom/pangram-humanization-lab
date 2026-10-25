"""Fail closed when an owner-feedback HTML delivery is merely a static report.

This structural check does not replace browser interaction/contrast tests.
"""
from __future__ import annotations
import argparse,json
from html.parser import HTMLParser
from pathlib import Path
class ReviewParser(HTMLParser):
    def __init__(self):
        super().__init__();self.tags={};self.comment_buttons=0;self.cells=0;self.meta=[];self.in_meta=False
    def handle_starttag(self,tag,attrs):
        d=dict(attrs);ident=d.get('id');classes=d.get('class','').split()
        if ident:self.tags[ident]=tag
        if tag=='button' and 'comment-btn' in classes:self.comment_buttons+=1
        if 'diff-cell' in classes and d.get('data-cell-key'):self.cells+=1
        if tag=='script' and ident=='review-data':self.in_meta=True
    def handle_data(self,data):
        if self.in_meta:self.meta.append(data)
    def handle_endtag(self,tag):
        if tag=='script':self.in_meta=False

def check_review_html(text:str,expected_items:int|None=None)->dict:
    p=ReviewParser();p.feed(text);errors=[]
    required={'commentText':'textarea','saveComment':'button','cancelComment':'button','exportJson':'button','exportMd':'button','copyJson':'button','copyMd':'button','search':'input'}
    for key,tag in required.items():
        if p.tags.get(key)!=tag:errors.append('Missing actual '+tag+': '+key)
    if not p.cells or p.comment_buttons<p.cells:errors.append('Every review cell needs an actual comment button')
    try:meta=json.loads(''.join(p.meta))
    except (ValueError,TypeError):meta={};errors.append('Missing parseable review-data identity')
    if meta.get('interface_format')!='joel-commentable-diff-review-v4':errors.append('Wrong or absent comment export contract')
    rows=meta.get('rows',{})
    if expected_items is not None and len(rows)!=expected_items:errors.append('Wrong number of review items')
    for marker in ('selectionSnapshots','rememberSelection','localStorage','review-form-controls-v1','-webkit-text-fill-color:#1f2937'):
        if marker not in text:errors.append('Missing interaction/readability implementation: '+marker)
    return {'ok':not errors,'errors':errors,'review_rows':len(rows),'commentable_cells':p.cells,'comment_buttons':p.comment_buttons,'scope':'static contract only; browser test still required'}

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('html',type=Path);ap.add_argument('--expected-items',type=int);a=ap.parse_args()
    result=check_review_html(a.html.read_text(encoding='utf-8'),a.expected_items);print(json.dumps(result,indent=2));return 0 if result['ok'] else 1
if __name__=='__main__':raise SystemExit(main())
