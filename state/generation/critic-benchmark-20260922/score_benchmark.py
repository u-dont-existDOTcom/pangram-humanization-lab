#!/usr/bin/env python3
import json, sys
from pathlib import Path

base=Path(__file__).resolve().parent
results=json.loads((base/"venice-results-frozen.json").read_text())
key=json.loads((base/"gold-key.json").read_text())
gold={x["sample_id"]:x for x in key["items"]}
pred={}
for row in results["results"]:
    parsed=row.get("parsed")
    if isinstance(parsed,dict):
        c=parsed.get("classification")
        if c in {"HUMAN","AI"}:
            pred[row["sample_id"]]=c
ids=sorted(gold)
missing=[i for i in ids if i not in pred]
rows=[]
for i in ids:
    g=gold[i]["label"]
    p=pred.get(i)
    rows.append({"sample_id":i,"gold":g,"predicted":p,"correct":p==g,"internal_id":gold[i]["internal_id"],"provenance_class":gold[i]["provenance_class"]})
correct=sum(x["correct"] for x in rows)
human=[x for x in rows if x["gold"]=="HUMAN"]
ai=[x for x in rows if x["gold"]=="AI"]
out={
 "format":"joel-humanization-critic-benchmark-score-v1",
 "total":len(rows),
 "correct":correct,
 "accuracy":correct/len(rows) if rows else 0,
 "human_correct":sum(x["correct"] for x in human),
 "human_total":len(human),
 "ai_correct":sum(x["correct"] for x in ai),
 "ai_total":len(ai),
 "missing_or_invalid":missing,
 "rows":rows,
}
print(json.dumps(out,indent=2))
