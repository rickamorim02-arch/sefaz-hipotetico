#!/usr/bin/env python3
# Banco V8 — reconstrói o universo V2, separa os 50.000 originais dos excedentes
# e submete AMBOS ao filtro cumulativo V3→V8. Assim os >30 mil excedentes não ficam de fora.
import json,re,sys,hashlib
from pathlib import Path
TARGET_INITIAL=50000

def clean(s): return re.sub(r'\s+',' ',str(s or '')).strip()
def norm(s): return re.sub(r'\W+',' ',clean(s).lower(),flags=re.UNICODE).strip()
def key(s): return hashlib.sha1(norm(s).encode()).hexdigest()

# Extrator V2 original — necessário para reproduzir exatamente o universo que tinha >80 mil itens.
def original_candidates(text):
 text=clean(str(text or '').replace('\n',' ')); out=[]
 bad=('fonte:','aula ','questões comentadas','questoes comentadas','sumário','sumario','gabarito','resolução','resolucao')
 for s in re.split(r'(?<=[.!?;])\s+',text):
  s=clean(s); lo=s.lower()
  if not (45<=len(s)<=520) or lo.startswith(bad) or re.match(r'^[\d\W_]+$',s) or s.count(' ')<7: continue
  if re.search(r'\b(julgue|assinale|marque|considere os itens|responda)\b',lo) and len(s)<120: continue
  out.append(s)
 return out

QUESTION=re.compile(r'\b(cebraspe|cespe|fcc|fgv|vunesp|quadrix|cesgranrio|banca|prova|concurso|quest[aã]o|julgue|assinale|marque|alternativa|gabarito|resolu[cç][aã]o|coment[aá]rios?)\b',re.I)
INSTRUCTION=re.compile(r'\b(certo ou errado|correta|incorreta|considere|responda|indique|escolha|analise os itens|com base no texto)\b',re.I)
CLASSROOM=re.compile(r'^(pessoal|galera|caros alunos|aten[cç][aã]o|veja|vejamos|observe|notem|vamos|lembre-se|perceba)\b',re.I)
CONTEXT=re.compile(r'\b(conforme visto|como vimos|acima|abaixo|anteriormente|a seguir|na figura|na tabela|no quadro|no exemplo|neste caso|nesse caso|nessa situa[cç][aã]o|nesta situa[cç][aã]o|na situa[cç][aã]o|no caso apresentado|de fato|al[eé]m disso|justamente|respectivamente)\b',re.I)
ANAPHORA=re.compile(r'^(?:esse|essa|esses|essas|este|esta|estes|estas|isso|isto|aquilo|aquele|aquela|aqueles|aquelas|seu|sua|seus|suas|dele|dela|deles|delas|tais?|o mesmo|a mesma|os mesmos|as mesmas)\b',re.I)
SCENARIO=re.compile(r'\b(?:filial|filiais|áudio|audio|personagem|empresa x|empresa y|indivíduo|individuo|fulano|beltrano|situa[cç][aã]o hipot[eé]tica|caso hipot[eé]tico|velocidade\s+\d|\bD minutos\b)\b',re.I)
OPTION=re.compile(r'(?:^|\s)[a-eA-E][.)]\s|[•▪◦]')
TRUNCATED=re.compile(r'(?:\b(?:art|arts|inc|incs|al[ií]nea|item|itens|fig|p[aá]g|p[aá]gina|cap|se[cç][aã]o)\.?|\b(?:conforme|segundo|nos termos de|de acordo com))\s*\.?$',re.I)
RISKY=re.compile(r'\b(?:sempre|nunca|jamais|somente|apenas|exclusivamente|necessariamente|obrigatoriamente|em nenhuma hip[oó]tese|em qualquer hip[oó]tese|todos|todas|nenhum|nenhuma|irrevog[aá]vel|irrestrit[oa]s?|n[aã]o admitem?|n[aã]o admite)\b',re.I)
CONCEPT=re.compile(r'\b(?:é|são|consiste|consistem|constitui|constituem|define|definem|significa|significam|corresponde|correspondem|compreende|compreendem|abrange|abrangem|inclui|incluem|possui|possuem|tem|têm|caracteriza-se|caracterizam-se|permite|permitem|exige|exigem|estabelece|estabelecem|determina|determinam|prevê|preveem|aplica|aplicam|utiliza|utilizam|protege|protegem|organiza|organizam|classifica|classificam|identifica|identificam|garante|garantem|veda|vedam|incide|incidem|decorre|decorrem|depende|dependem)\b',re.I)
BAD_GENERIC=re.compile(r'\b(?:ideia central|exemplos citados|pode-se dizer|podemos dizer|vale destacar|vale lembrar|é importante destacar|é importante lembrar)\b',re.I)
BAD_START=re.compile(r'^(?:e|ou|mas|porque|pois|que|quando|onde|cujo|cuja|cujos|cujas|tamb[eé]m|portanto|assim|logo|contudo|todavia|entretanto|por[eé]m)\b',re.I)

# Filtro cumulativo V3→V8: uma oração curta, autônoma, conceitual e sem sinais de exercício/contexto.
def validate(raw):
 # V3: usa uma única oração/sentença e limita tamanho.
 s=clean(raw).strip('•*-–— ')
 s=re.split(r'(?<=[.!?])\s+',s)[0]
 s=re.split(r'\s*[;:]\s*',s)[0]
 if not (35<=len(s)<=200) or not (6<=s.count(' ')<=34): return None
 # V4/V5: remove prova, instrução, linguagem docente, anáfora e dependência contextual.
 if '?' in s or any(rx.search(s) for rx in [QUESTION,INSTRUCTION,CLASSROOM,CONTEXT,ANAPHORA,OPTION,BAD_START]): return None
 # V6: remove cenários, truncamentos e absolutizações de alto risco.
 if SCENARIO.search(s) or RISKY.search(s) or TRUNCATED.search(s.rstrip(' .')): return None
 if re.search(r'\b(?:verdadeiro|falso)\b',s,re.I): return None
 # V7: só conceitos/regras/definições/relações explicativas.
 if BAD_GENERIC.search(s) or not CONCEPT.search(s): return None
 nums=re.findall(r'\b\d+(?:[.,]\d+)?\b',s)
 if len(nums)>=2 and not re.search(r'\b(?:lei|artigo|art\.|constitui[cç][aã]o|cf|ctn|lc|ec|%|percentual|al[ií]quota)\b',s,re.I): return None
 m=CONCEPT.search(s)
 if not m or m.start()<5: return None
 subject=clean(s[:m.start()]).strip(' ,.-'); pred=clean(s[m.start():]).strip(' ,.-')
 if ANAPHORA.search(subject) or re.match(r'^(?:no|na|nos|nas|para|por|com|sem|em|de|do|da|dos|das|se)\b',subject,re.I): return None
 if not re.match(r'^(?:O|A|Os|As|Um|Uma|[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç/-]*)\b',subject): return None
 if re.match(r'^\d',subject) or len(subject.split())>16 or len(pred.split())<2: return None
 if len(re.findall(r'\b(?:que|quando|onde|porque|pois)\b',s,re.I))>1: return None
 # V8: rejeita resíduos de reticências/citações incompletas e exige fechamento declarativo.
 if '[...]' in s or '…' in s or re.search(r'\.{2,}',s): return None
 clause=clean(subject+' '+pred).rstrip(' ,;:')
 if not 35<=len(clause)<=200: return None
 if clause[-1] not in '.!': clause+='.'
 return clause

def choose_original_50k(pool):
 by={}
 for row,st in pool: by.setdefault(row['subject'],[]).append((row,st))
 subjects=sorted(by); chosen=[]; i=0
 while len(chosen)<min(TARGET_INITIAL,len(pool)):
  moved=False
  for sub in subjects:
   if i<len(by[sub]) and len(chosen)<TARGET_INITIAL:
    chosen.append(by[sub][i]); moved=True
  if not moved: break
  i+=1
 if len(chosen)<min(TARGET_INITIAL,len(pool)):
  used={key(st) for _,st in chosen}
  for row,st in pool:
   if key(st) not in used:
    chosen.append((row,st)); used.add(key(st))
    if len(chosen)==TARGET_INITIAL: break
 return chosen

def main(root,out):
 root=Path(root); manifest=json.loads((root/'reading-manifest.json').read_text(encoding='utf-8'))
 universe=[]; seen=set()
 for d in manifest:
  for row in json.loads((root/d['file']).read_text(encoding='utf-8')):
   for st in original_candidates(row.get('text','')):
    k=key(st)
    if k in seen: continue
    seen.add(k); universe.append((row,st))
 first=choose_original_50k(universe); first_keys={key(st) for _,st in first}
 leftovers=[x for x in universe if key(x[1]) not in first_keys]
 def filter_group(group):
  outg=[]; used=set()
  for row,raw in group:
   st=validate(raw)
   if not st: continue
   k=key(st)
   if k in used: continue
   used.add(k); outg.append((row,st))
  return outg
 passed_first=filter_group(first); passed_left=filter_group(leftovers)
 # União dos dois lotes, sem duplicatas. O excedente é explicitamente processado e contabilizado.
 combined=[]; used=set()
 for origin,group in [('50k',passed_first),('excedente',passed_left)]:
  for row,st in group:
   k=key(st)
   if k in used: continue
   used.add(k); combined.append((row,st,origin))
 qs=[]
 for n,(row,st,origin) in enumerate(combined,1):
  qs.append({'id':f'V8-{n:05d}','s':row['subject'],'t':row['lesson'],'q':st,'a':True,'c':'CERTO. Short conceitual selecionado após filtros cumulativos V3–V8. Fonte: '+row.get('source','Fonte registrada na base.'),'source':row.get('source',''),'lesson':row['lesson'],'origin':origin})
 Path(out).write_text(json.dumps(qs,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 covered=len({q['s'] for q in qs}); unique=len({norm(q['q']) for q in qs})
 print('UNIVERSO V2=',len(universe),'PRIMEIROS=',len(first),'EXCEDENTES=',len(leftovers))
 print('APROVADOS DOS 50K=',len(passed_first),'APROVADOS DOS EXCEDENTES=',len(passed_left),'TOTAL V8=',len(qs),'DISCIPLINAS=',covered)
 if unique!=len(qs) or len({q['id'] for q in qs})!=len(qs): raise SystemExit('ERRO: duplicatas')
 if covered!=19: raise SystemExit('ERRO: cobertura diferente de 19 disciplinas')
if __name__=='__main__': main(sys.argv[1] if len(sys.argv)>1 else '.',sys.argv[2] if len(sys.argv)>2 else 'questions.json')