#!/usr/bin/env python3
import json,sys
from pathlib import Path
from audit_restructure_questions import assess

src=Path(sys.argv[1] if len(sys.argv)>1 else 'questions.json')
out=Path(sys.argv[2] if len(sys.argv)>2 else 'questions-approved.json')
rows=json.loads(src.read_text(encoding='utf-8'))
approved=[]; dropped=[]
for q in rows:
    reasons=assess(q.get('q',q.get('question','')))
    if reasons:
        dropped.append({'id':q.get('id'),'question':q.get('q',q.get('question')),'reasons':reasons})
    else:
        approved.append(q)
assert len(approved)+len(dropped)==len(rows)
assert all(not assess(q.get('q',q.get('question',''))) for q in approved)
out.write_text(json.dumps(approved,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
Path('structural-dropped.json').write_text(json.dumps({'total_original':len(rows),'aprovadas':len(approved),'dispensadas':len(dropped),'itens':dropped},ensure_ascii=False,indent=2),encoding='utf-8')
print('ORIGINAL=',len(rows),'APROVADAS=',len(approved),'DISPENSADAS=',len(dropped),'FALHAS_NO_APROVADO=',sum(bool(assess(q.get('q',''))) for q in approved))
