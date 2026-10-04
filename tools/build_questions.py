#!/usr/bin/env python3
import json,re,sys
from pathlib import Path

def clean(s): return re.sub(r'\s+',' ',str(s or '')).strip()
def sentences(text):
 text=clean(text.replace('\n',' '))
 parts=re.split(r'(?<=[.!?])\s+',text)
 out=[]
 for s in parts:
  s=clean(s)
  if 55<=len(s)<=420 and not s.lower().startswith(('fonte:','aula ')) and not re.match(r'^\d+[.)]\s',s): out.append(s)
 return out

def main(root,out):
 root=Path(root); m=json.loads((root/'reading-manifest.json').read_text(encoding='utf-8')); qs=[]; qid=1
 for d in m:
  rows=json.loads((root/d['file']).read_text(encoding='utf-8'))
  for row in rows:
   cand=sentences(row.get('text',''))
   if not cand: continue
   statement=cand[0]
   qs.append({'id':f'V2-{qid:04d}','s':row['subject'],'t':row['lesson'],'q':statement,'a':True,'c':'CERTO. A afirmação foi extraída do conteúdo da '+row['lesson']+' da Compilação Auditada V2. Fonte rastreável: '+row.get('source','Fonte registrada na base V2.'),'source':row.get('source',''),'lesson':row['lesson']})
   qid+=1
 Path(out).write_text(json.dumps(qs,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 print('questoes',len(qs),'disciplinas',len(set(q['s'] for q in qs)))
 if len(qs)!=255: raise SystemExit(f'ERRO: esperado 255 questões rastreáveis, geradas {len(qs)}')
 if len(set(q['s'] for q in qs))!=19: raise SystemExit('ERRO: esperado cobertura das 19 disciplinas')
if __name__=='__main__': main(sys.argv[1] if len(sys.argv)>1 else '.',sys.argv[2] if len(sys.argv)>2 else 'questions.json')