#!/usr/bin/env python3
# Banco V3: Shorts em orações declarativas simples, preferencialmente Sujeito + Verbo + Objeto/Complemento.
# Conservador: não inventa conteúdo factual; simplifica somente afirmações extraídas da base auditada.
import json,re,sys,hashlib
from pathlib import Path
TARGET=50000

def clean(s): return re.sub(r'\s+',' ',str(s or '')).strip()
def normalize(s): return re.sub(r'\W+',' ',clean(s).lower(),flags=re.UNICODE).strip()

def candidates(text):
 text=clean(str(text or '').replace('\n',' ')); parts=re.split(r'(?<=[.!?;:])\s+',text); out=[]
 bad=('fonte:','aula ','questões comentadas','questoes comentadas','sumário','sumario','gabarito','resolução','resolucao')
 for s in parts:
  s=clean(s).strip('•*-–— '); lo=s.lower()
  if not (35<=len(s)<=520) or lo.startswith(bad) or re.match(r'^[\d\W_]+$',s) or s.count(' ')<5: continue
  if re.search(r'\b(julgue|assinale|marque|considere os itens|responda|alternativa correta|alternativa incorreta)\b',lo): continue
  out.append(s)
 return out

def to_clause(s):
 """Converte conservadoramente uma afirmação em UMA oração curta; rejeita fragmentos em vez de inventar."""
 s=clean(s).strip('•*-–— ')
 # remove rótulos/listas e conectores discursivos que dependem do contexto anterior
 s=re.sub(r'^(?:\(?[a-z0-9ivx]+\)?[.)-]\s+)+','',s,flags=re.I)
 s=re.sub(r'^(?:portanto|assim|logo|contudo|todavia|entretanto|além disso|alem disso|porém|porem|desse modo|dessa forma),?\s+','',s,flags=re.I)
 # escolhe a primeira oração autônoma; não concatena enumerações longas
 s=re.split(r'(?<=[.!?])\s+',s)[0]
 s=re.split(r'\s*[;:]\s*',s)[0]
 s=clean(s)
 # rejeita dependência anafórica/contextual forte
 if re.match(r'^(e|ou|mas|porque|pois|que|quando|onde|cujo|cuja|este|esta|estes|estas|isso|isto|aquilo)\b',s,re.I): return None
 if re.search(r'\b(conforme visto|como vimos|acima|abaixo|anteriormente|a seguir)\b',s,re.I): return None
 # exige aparência de oração declarativa: sujeito antes de forma verbal reconhecível
 verbs=r'(?:é|são|foi|foram|será|serão|tem|têm|possui|possuem|constitui|constituem|representa|representam|define|definem|estabelece|estabelecem|determina|determinam|permite|permitem|exige|exigem|inclui|incluem|compreende|compreendem|abrange|abrangem|corresponde|correspondem|decorre|decorrem|depende|dependem|deve|devem|pode|podem|ocorre|ocorrem|consiste|consistem|aplica|aplicam|utiliza|utilizam|considera|consideram|garante|garantem|veda|vedam|prevê|preveem|prevêem|dispõe|dispõem|integra|integram|adota|adotam|produz|produzem|gera|geram|reduz|reduzem|aumenta|aumentam|mantém|mantêm|recebe|recebem|realiza|realizam|calcula|calculam|registra|registram|controla|controlam|protege|protegem|organiza|organizam|classifica|classificam|identifica|identificam|avalia|avaliam|analisa|analisam|verifica|verificam|autoriza|autorizam|proíbe|proibem|obriga|obrigam|incide|incidem|alcança|alcançam|envolve|envolvem|resulta|resultam|significa|significam)'
 m=re.search(r'\b'+verbs+r'\b',s,re.I)
 if not m or m.start()<3: return None
 subject=clean(s[:m.start()]).strip(' ,')
 predicate=clean(s[m.start():]).strip(' ,')
 if len(subject)<2 or len(predicate.split())<2: return None
 # corta subordinadas/explicações após a oração principal quando possível
 for sep in [', que ', ', o que ', ', sendo ', ', permitindo ', ', garantindo ', ', pois ', ', porque ']:
  i=predicate.lower().find(sep)
  if i>12: predicate=predicate[:i]
 clause=clean(subject+' '+predicate).rstrip(' ,;:')
 if len(clause)<25 or len(clause)>240: return None
 if clause[-1] not in '.!?': clause+='.'
 return clause

def main(root,out):
 root=Path(root); manifest=json.loads((root/'reading-manifest.json').read_text(encoding='utf-8')); pool=[]; seen=set(); rejected=0
 for d in manifest:
  rows=json.loads((root/d['file']).read_text(encoding='utf-8'))
  for row in rows:
   for raw in candidates(row.get('text','')):
    statement=to_clause(raw)
    if not statement: rejected+=1; continue
    key=hashlib.sha1(normalize(statement).encode()).hexdigest()
    if key in seen: continue
    seen.add(key); pool.append((row,statement))
 available=len(pool); goal=min(TARGET,available)
 print(f'ORAÇÕES SVO/SVC APROVEITÁVEIS: {available}; rejeitadas por ambiguidade/fragmentação: {rejected}; meta: {TARGET}; publicação: {goal}.')
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
  used={normalize(st) for _,st in chosen}
  for row,st in pool:
   if normalize(st) not in used:
    chosen.append((row,st)); used.add(normalize(st))
    if len(chosen)==goal: break
 qs=[]
 for n,(row,statement) in enumerate(chosen,1):
  qs.append({'id':f'V3-{n:05d}','s':row['subject'],'t':row['lesson'],'q':statement,'a':True,'c':'CERTO. A oração preserva uma afirmação do material auditado. Fonte: '+row.get('source','Fonte registrada na base.'),'source':row.get('source',''),'lesson':row['lesson']})
 Path(out).write_text(json.dumps(qs,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 print('RESULTADO:',len(qs),'orações;',len(set(q['s'] for q in qs)),'disciplinas; únicas:',len({normalize(q['q']) for q in qs}))
 if len({q['id'] for q in qs})!=len(qs): raise SystemExit('ERRO: IDs duplicados')
 if len({normalize(q['q']) for q in qs})!=len(qs): raise SystemExit('ERRO: orações duplicadas')
 if len({q['s'] for q in qs})!=19: raise SystemExit('ERRO: cobertura diferente de 19 disciplinas')
if __name__=='__main__': main(sys.argv[1] if len(sys.argv)>1 else '.',sys.argv[2] if len(sys.argv)>2 else 'questions.json')