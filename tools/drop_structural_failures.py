#!/usr/bin/env python3
import json,sys
from pathlib import Path
from audit_restructure_questions import assess

def main(path='questions.json'):
 p=Path(path); rows=json.loads(p.read_text(encoding='utf-8'))
 kept=[]; dropped=[]
 for q in rows:
  reasons=assess(q.get('q',q.get('question','')))
  if reasons: dropped.append({'id':q.get('id'),'q':q.get('q'),'reasons':reasons})
  else: kept.append(q)
 # preserva IDs/conteúdo dos aprovados; apenas remove reprovados
 p.write_text(json.dumps(kept,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 Path('structural-dropped.json').write_text(json.dumps({'antes':len(rows),'mantidas':len(kept),'dispensadas':len(dropped),'itens':dropped},ensure_ascii=False,indent=2),encoding='utf-8')
 print('ANTES=',len(rows),'MANTIDAS=',len(kept),'DISPENSADAS=',len(dropped))
 if len(kept)+len(dropped)!=len(rows): raise SystemExit('ERRO de contagem')
 if any(assess(q.get('q','')) for q in kept): raise SystemExit('ERRO: reprovado permaneceu')
if __name__=='__main__': main(sys.argv[1] if len(sys.argv)>1 else 'questions.json')
