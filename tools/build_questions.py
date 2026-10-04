#!/usr/bin/env python3
# Banco V7 — Shorts conceituais: definições, características, regras e relações explicativas autônomas.
# Qualidade > quantidade. Não cria afirmações nem inverte frases para fabricar CERTO/ERRADO.
import json,re,sys,hashlib
from pathlib import Path
TARGET=50000

def clean(s): return re.sub(r'\s+',' ',str(s or '')).strip()
def norm(s): return re.sub(r'\W+',' ',clean(s).lower(),flags=re.UNICODE).strip()
QUESTION=re.compile(r'\b(cebraspe|cespe|fcc|fgv|vunesp|quadrix|cesgranrio|banca|prova|concurso|quest[aã]o|julgue|assinale|marque|alternativa|gabarito|resolu[cç][aã]o|coment[aá]rios?)\b',re.I)
INSTRUCTION=re.compile(r'\b(certo ou errado|correta|incorreta|considere|responda|indique|escolha|analise os itens|com base no texto)\b',re.I)
CLASSROOM=re.compile(r'^(pessoal|galera|caros alunos|aten[cç][aã]o|veja|vejamos|observe|notem|vamos|lembre-se|perceba)\b',re.I)
CONTEXT=re.compile(r'\b(conforme visto|como vimos|acima|abaixo|anteriormente|a seguir|na figura|na tabela|no quadro|no exemplo|neste caso|nesse caso|nessa situa[cç][aã]o|nesta situa[cç][aã]o|na situa[cç][aã]o|no caso apresentado|de fato|al[eé]m disso|justamente|respectivamente)\b',re.I)
ANAPHORA=re.compile(r'^(?:esse|essa|esses|essas|este|esta|estes|estas|isso|isto|aquilo|aquele|aquela|aqueles|aquelas|seu|sua|seus|suas|dele|dela|deles|delas|tais?|o mesmo|a mesma|os mesmos|as mesmas)\b',re.I)
SCENARIO=re.compile(r'\b(?:filial|filiais|áudio|audio|personagem|empresa x|empresa y|indivíduo|individuo|fulano|beltrano|situa[cç][aã]o hipot[eé]tica|caso hipot[eé]tico|velocidade\s+\d|\bD minutos\b)\b',re.I)
OPTION=re.compile(r'(?:^|\s)[a-eA-E][.)]\s|[•▪◦]')
TRUNCATED=re.compile(r'(?:\b(?:art|arts|inc|incs|al[ií]nea|item|itens|fig|p[aá]g|p[aá]gina|cap|se[cç][aã]o)\.?|\b(?:conforme|segundo|nos termos de|de acordo com))\s*\.?$',re.I)
RISKY=re.compile(r'\b(?:sempre|nunca|jamais|somente|apenas|exclusivamente|necessariamente|obrigatoriamente|em nenhuma hip[oó]tese|em qualquer hip[oó]tese|todos|todas|nenhum|nenhuma|irrevog[aá]vel|irrestrit[oa]s?|n[aã]o admitem?|n[aã]o admite)\b',re.I)
# Padrões conceituais positivos: a frase precisa ensinar uma definição, propriedade, composição, finalidade ou regra geral.
CONCEPT=re.compile(r'\b(?:é|são|consiste|consistem|constitui|constituem|define|definem|significa|significam|corresponde|correspondem|compreende|compreendem|abrange|abrangem|inclui|incluem|possui|possuem|tem|têm|caracteriza-se|caracterizam-se|permite|permitem|exige|exigem|estabelece|estabelecem|determina|determinam|prevê|preveem|aplica|aplicam|utiliza|utilizam|protege|protegem|organiza|organizam|classifica|classificam|identifica|identificam|garante|garantem|veda|vedam|incide|incidem|decorre|decorrem|depende|dependem)\b',re.I)
BAD_GENERIC=re.compile(r'\b(?:ideia central|exemplos citados|pode-se dizer|podemos dizer|vale destacar|vale lembrar|é importante destacar|é importante lembrar)\b',re.I)

def candidates(text):
 for s in re.split(r'(?<=[.!?])\s+',clean(str(text or '').replace('\n',' '))):
  s=clean(s).strip('•*-–— ')
  if 35<=len(s)<=205 and 6<=s.count(' ')<=34: yield s

def validate(s):
 if '?' in s or any(rx.search(s) for rx in [QUESTION,INSTRUCTION,CLASSROOM,CONTEXT,ANAPHORA,SCENARIO,OPTION,RISKY,BAD_GENERIC]): return None
 if s.count(';') or s.count(':') or TRUNCATED.search(s.rstrip(' .')): return None
 if re.search(r'\b(?:verdadeiro|falso)\b',s,re.I): return None
 # cálculos e exercícios numéricos contextualizados ficam fora; números só passam quando parecem referência normativa/percentual/data conceitual.
 nums=re.findall(r'\b\d+(?:[.,]\d+)?\b',s)
 if len(nums)>=2 and not re.search(r'\b(?:lei|artigo|art\.|constitui[cç][aã]o|cf|ctn|lc|ec|%|percentual|al[ií]quota)\b',s,re.I): return None
 if not CONCEPT.search(s): return None
 # exige sujeito nominal explícito antes do primeiro verbo conceitual.
 m=CONCEPT.search(s)
 if not m or m.start()<5: return None
 subject=clean(s[:m.start()]).strip(' ,.-'); pred=clean(s[m.start():]).strip(' ,.-')
 if ANAPHORA.search(subject) or re.match(r'^(?:no|na|nos|nas|para|por|com|sem|em|de|do|da|dos|das|se)\b',subject,re.I): return None
 if not re.match(r'^(?:O|A|Os|As|Um|Uma|[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç/-]*)\b',subject): return None
 if re.match(r'^\d',subject) or len(subject.split())>16 or len(pred.split())<2: return None
 if len(re.findall(r'\b(?:que|quando|onde|porque|pois)\b',s,re.I))>1: return None
 clause=clean(subject+' '+pred).rstrip(' ,;:')
 if not 35<=len(clause)<=200: return None
 if clause[-1] not in '.!': clause+='.'
 return clause

def main(root,out):
 root=Path(root); manifest=json.loads((root/'reading-manifest.json').read_text(encoding='utf-8')); pool=[]; seen=set(); rejected=0
 for d in manifest:
  for row in json.loads((root/d['file']).read_text(encoding='utf-8')):
   for raw in candidates(row.get('text','')):
    st=validate(raw)
    if not st: rejected+=1; continue
    k=hashlib.sha1(norm(st).encode()).hexdigest()
    if k in seen: continue
    seen.add(k); pool.append((row,st))
 by={}
 for row,st in pool: by.setdefault(row['subject'],[]).append((row,st))
 subjects=sorted(by); chosen=[]; i=0
 while len(chosen)<min(TARGET,len(pool)):
  moved=False
  for sub in subjects:
   if i<len(by[sub]) and len(chosen)<TARGET: chosen.append(by[sub][i]); moved=True
  if not moved: break
  i+=1
 qs=[]
 for n,(row,st) in enumerate(chosen,1):
  qs.append({'id':f'V7-{n:05d}','s':row['subject'],'t':row['lesson'],'q':st,'a':True,'c':'CERTO. Short conceitual extraído do material-fonte após filtros de autonomia, contexto e risco. Fonte: '+row.get('source','Fonte registrada na base.'),'source':row.get('source',''),'lesson':row['lesson']})
 Path(out).write_text(json.dumps(qs,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 unique=len({norm(q['q']) for q in qs}); covered=len({q['s'] for q in qs})
 print('V7 candidatos=',len(pool),'rejeitados=',rejected,'publicados=',len(qs),'disciplinas=',covered,'únicos=',unique)
 if unique!=len(qs) or len({q['id'] for q in qs})!=len(qs): raise SystemExit('ERRO: duplicatas')
 if covered!=19: raise SystemExit('ERRO: cobertura diferente de 19 disciplinas')
 forbidden=[QUESTION,INSTRUCTION,CLASSROOM,CONTEXT,ANAPHORA,SCENARIO,OPTION,RISKY,BAD_GENERIC]
 bad=[q['id'] for q in qs if '?' in q['q'] or any(rx.search(q['q']) for rx in forbidden) or not CONCEPT.search(q['q'])]
 if bad: raise SystemExit('ERRO: item V7 inválido: '+','.join(bad[:20]))
if __name__=='__main__': main(sys.argv[1] if len(sys.argv)>1 else '.',sys.argv[2] if len(sys.argv)>2 else 'questions.json')