#!/usr/bin/env python3
# Banco V2: até 50.000 itens CERTO baseados diretamente na Compilação Auditada V2.
# Regra conservadora: não inventar negações; cada item preserva uma afirmação textual da fonte.
import json,re,sys,hashlib
from pathlib import Path
TARGET=50000

def clean(s): return re.sub(r'\s+',' ',str(s or '')).strip()
def normalize(s): return re.sub(r'\W+',' ',clean(s).lower(),flags=re.UNICODE).strip()
def candidates(text):
 text=clean(str(text or '').replace('\n',' ')); parts=re.split(r'(?<=[.!?;])\s+',text); out=[]
 bad=('fonte:','aula ','questões comentadas','questoes comentadas','sumário','sumario','gabarito','resolução','resolucao')
 for s in parts:
  s=clean(s); lo=s.lower()
  if not (45<=len(s)<=520) or lo.startswith(bad) or re.match(r'^[\d\W_]+$',s) or s.count(' ')<7: continue
  if re.search(r'\b(julgue|assinale|marque|considere os itens|responda)\b',lo) and len(s)<120: continue
  out.append(s)
 return out

def main(root,out):
 root=Path(root); manifest=json.loads((root/'reading-manifest.json').read_text(encoding='utf-8')); pool=[]; seen=set()
 for d in manifest:
  rows=json.loads((root/d['file']).read_text(encoding='utf-8'))
  for row in rows:
   for statement in candidates(row.get('text','')):
    key=hashlib.sha1(normalize(statement).encode()).hexdigest()
    if key in seen: continue
    seen.add(key); pool.append((row,statement))
 available=len(pool); goal=min(TARGET,available)
 print(f'DISPONÍVEIS: {available} afirmações únicas e conservadoras; meta: {TARGET}; serão publicadas: {goal}.')
 by={}
 for row,st in pool: by.setdefault(row['subject'],[]).append((row,st))
 subjects=sorted(by); chosen=[]; i=0
 while len(chosen)<goal:
  progressed=False
  for sub in subjects:
   if i<len(by[sub]) and len(chosen)<goal: chosen.append(by[sub][i]); progressed=True
  if not progressed: break
  i+=1
 if len(chosen)<goal:
  used={hashlib.sha1(normalize(st).encode()).hexdigest() for _,st in chosen}
  for row,st in pool:
   k=hashlib.sha1(normalize(st).encode()).hexdigest()
   if k not in used:
    chosen.append((row,st)); used.add(k)
    if len(chosen)==goal: break
 qs=[]
 for n,(row,statement) in enumerate(chosen,1):
  qs.append({'id':f'V2-{n:05d}','s':row['subject'],'t':row['lesson'],'q':statement,'a':True,'c':'CERTO. Item baseado diretamente em afirmação presente no material auditado desta aula. Fonte: '+row.get('source','Fonte registrada na base V2.'),'source':row.get('source',''),'lesson':row['lesson']})
 Path(out).write_text(json.dumps(qs,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 print('RESULTADO:',len(qs),'questões;',len(set(q['s'] for q in qs)),'disciplinas; enunciados únicos:',len({normalize(q['q']) for q in qs}))
 if len({q['id'] for q in qs})!=len(qs): raise SystemExit('ERRO: IDs duplicados')
 if len({normalize(q['q']) for q in qs})!=len(qs): raise SystemExit('ERRO: enunciados duplicados')
 if len({q['s'] for q in qs})!=19: raise SystemExit('ERRO: cobertura diferente de 19 disciplinas')
if __name__=='__main__': main(sys.argv[1] if len(sys.argv)>1 else '.',sys.argv[2] if len(sys.argv)>2 else 'questions.json')