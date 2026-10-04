#!/usr/bin/env python3
# Banco V2: 20.000 itens CERTO baseados diretamente na Compilação Auditada V2.
# Regra conservadora: não inventar negações; cada item preserva uma afirmação textual da fonte.
import json,re,sys,hashlib
from pathlib import Path
TARGET=20000

def clean(s): return re.sub(r'\s+',' ',str(s or '')).strip()
def normalize(s): return re.sub(r'\W+',' ',clean(s).lower(),flags=re.UNICODE).strip()
def candidates(text):
 text=clean(str(text or '').replace('\n',' '))
 # divide por pontuação; também recupera segmentos longos separados por ;
 parts=re.split(r'(?<=[.!?;])\s+',text)
 out=[]
 bad=('fonte:','aula ','questões comentadas','questoes comentadas','sumário','sumario','gabarito','resolução','resolucao')
 for s in parts:
  s=clean(s)
  lo=s.lower()
  if not (45<=len(s)<=520): continue
  if lo.startswith(bad): continue
  if re.match(r'^[\d\W_]+$',s): continue
  if s.count(' ')<7: continue
  # evita enunciados incompletos/ordens de prova sem conteúdo afirmativo
  if re.search(r'\b(julgue|assinale|marque|considere os itens|responda)\b',lo) and len(s)<120: continue
  out.append(s)
 return out

def main(root,out):
 root=Path(root)
 manifest=json.loads((root/'reading-manifest.json').read_text(encoding='utf-8'))
 pool=[]; seen=set()
 for d in manifest:
  rows=json.loads((root/d['file']).read_text(encoding='utf-8'))
  for row in rows:
   for statement in candidates(row.get('text','')):
    key=hashlib.sha1(normalize(statement).encode()).hexdigest()
    if key in seen: continue
    seen.add(key)
    pool.append((row,statement))
 if len(pool)<TARGET:
  raise SystemExit(f'ERRO: somente {len(pool)} afirmações únicas e conservadoras; não serão inventadas questões para atingir {TARGET}.')
 # distribuição round-robin por disciplina para evitar concentração excessiva
 by={}
 for row,st in pool: by.setdefault(row['subject'],[]).append((row,st))
 subjects=sorted(by)
 chosen=[]; i=0
 while len(chosen)<TARGET:
  progressed=False
  for sub in subjects:
   if i<len(by[sub]) and len(chosen)<TARGET:
    chosen.append(by[sub][i]); progressed=True
  if not progressed: break
  i+=1
 if len(chosen)<TARGET:
  # completa com itens restantes, ainda únicos e provenientes da fonte
  used={hashlib.sha1(normalize(st).encode()).hexdigest() for _,st in chosen}
  for row,st in pool:
   k=hashlib.sha1(normalize(st).encode()).hexdigest()
   if k not in used:
    chosen.append((row,st));used.add(k)
    if len(chosen)==TARGET:break
 qs=[]
 for n,(row,statement) in enumerate(chosen,1):
  qs.append({'id':f'V2-{n:05d}','s':row['subject'],'t':row['lesson'],'q':statement,'a':True,'c':'CERTO. Item baseado diretamente em afirmação presente no material auditado desta aula. Fonte: '+row.get('source','Fonte registrada na base V2.'),'source':row.get('source',''),'lesson':row['lesson']})
 Path(out).write_text(json.dumps(qs,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 print('APROVADO:',len(qs),'questões;',len(set(q['s'] for q in qs)),'disciplinas; enunciados únicos:',len({normalize(q['q']) for q in qs}))
 if len(qs)!=TARGET: raise SystemExit('ERRO: total diferente de 20.000')
 if len({q['id'] for q in qs})!=TARGET: raise SystemExit('ERRO: IDs duplicados')
 if len({normalize(q['q']) for q in qs})!=TARGET: raise SystemExit('ERRO: enunciados duplicados')
 if len({q['s'] for q in qs})!=19: raise SystemExit('ERRO: cobertura diferente de 19 disciplinas')
if __name__=='__main__': main(sys.argv[1] if len(sys.argv)>1 else '.',sys.argv[2] if len(sys.argv)>2 else 'questions.json')