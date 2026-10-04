#!/usr/bin/env python3
# Banco V5 — cada Short deve ser uma oração declarativa autônoma.
# Prioridade: qualidade e autonomia semântica; não completar meta artificialmente.
import json,re,sys,hashlib
from pathlib import Path
TARGET=50000

def clean(s): return re.sub(r'\s+',' ',str(s or '')).strip()
def norm(s): return re.sub(r'\W+',' ',clean(s).lower(),flags=re.UNICODE).strip()

QUESTION=re.compile(r'\b(cebraspe|cespe|fcc|fgv|vunesp|quadrix|cesgranrio|banca|prova|concurso|quest[aã]o|julgue|assinale|marque|alternativa|gabarito|resolu[cç][aã]o|coment[aá]rios?)\b',re.I)
INSTRUCTION=re.compile(r'\b(certo ou errado|correta|incorreta|considere|responda|indique|escolha|analise os itens|com base no texto)\b',re.I)
CLASSROOM=re.compile(r'^(pessoal|galera|caros alunos|aten[cç][aã]o|veja|vejamos|observe|notem|vamos|lembre-se|perceba)\b',re.I)
CONTEXT=re.compile(r'\b(conforme visto|como vimos|acima|abaixo|anteriormente|a seguir|na figura|na tabela|no quadro|no exemplo|neste caso|nesse caso|de fato|al[eé]m disso|justamente)\b',re.I)
ANAPHORA=re.compile(r'^(?:esse|essa|esses|essas|este|esta|estes|estas|isso|isto|aquilo|aquele|aquela|aqueles|aquelas|seu|sua|seus|suas|dele|dela|deles|delas|tais?|o mesmo|a mesma|os mesmos|as mesmas)\b',re.I)
OPTION=re.compile(r'(?:^|\s)[a-eA-E][.)]\s|[•▪◦]')
ARTICLE_FRAGMENT=re.compile(r'^(?:art\.?\s*)?\d+[º°]?\s+(?:da|do|de|prev[eê]|disp[oõ]e|estabelece|tem)\b',re.I)
PAREN_HEADER=re.compile(r'^\([^)]*(?:20\d\d|cebraspe|cespe|fcc|fgv|vunesp|cargo|t[eé]cnico|analista)[^)]*\)\s*',re.I)
BAD_START=re.compile(r'^(?:e|ou|mas|porque|pois|que|quando|onde|cujo|cuja|cujos|cujas|tamb[eé]m|portanto|assim|logo|contudo|todavia|entretanto|por[eé]m)\b',re.I)

VERBS=r'(?:é|são|foi|foram|será|serão|tem|têm|possui|possuem|constitui|constituem|representa|representam|define|definem|estabelece|estabelecem|determina|determinam|permite|permitem|exige|exigem|inclui|incluem|compreende|compreendem|abrange|abrangem|corresponde|correspondem|decorre|decorrem|depende|dependem|deve|devem|pode|podem|ocorre|ocorrem|consiste|consistem|aplica|aplicam|utiliza|utilizam|considera|consideram|garante|garantem|veda|vedam|prevê|preveem|dispõe|dispõem|integra|integram|adota|adotam|produz|produzem|gera|geram|reduz|reduzem|aumenta|aumentam|mantém|mantêm|recebe|recebem|realiza|realizam|calcula|calculam|registra|registram|controla|controlam|protege|protegem|organiza|organizam|classifica|classificam|identifica|identificam|avalia|avaliam|analisa|analisam|verifica|verificam|autoriza|autorizam|proíbe|proibem|obriga|obrigam|incide|incidem|alcança|alcançam|envolve|envolvem|resulta|resultam|significa|significam)'

def candidate_sentences(text):
 text=clean(str(text or '').replace('\n',' '))
 for s in re.split(r'(?<=[.!?])\s+',text):
  s=clean(s).strip('•*-–— ')
  if 32<=len(s)<=230 and s.count(' ')>=5: yield s

def validate(s):
 if '?' in s or QUESTION.search(s) or INSTRUCTION.search(s) or CLASSROOM.search(s): return None
 if CONTEXT.search(s) or OPTION.search(s) or PAREN_HEADER.search(s) or ARTICLE_FRAGMENT.search(s): return None
 if BAD_START.search(s) or ANAPHORA.search(s): return None
 if re.search(r'\b(?:verdadeiro|falso)\b',s,re.I): return None
 if s.count(';') or s.count(':') or len(re.findall(r'\b(?:que|quando|onde|porque|pois)\b',s,re.I))>1: return None
 m=re.search(r'\b'+VERBS+r'\b',s,re.I)
 if not m or m.start()<5: return None
 subject=clean(s[:m.start()]).strip(' ,.-')
 pred=clean(s[m.start():]).strip(' ,.-')
 # sujeito explícito e nominal; elimina locuções iniciais que escondem sujeito inexistente.
 if ANAPHORA.search(subject) or re.match(r'^(?:no|na|nos|nas|para|por|com|sem|em|de|do|da|dos|das)\b',subject,re.I): return None
 if not re.match(r'^(?:O|A|Os|As|Um|Uma|[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç/-]*)\b',subject): return None
 if re.match(r'^\d',subject) or not (1<=len(subject.split())<=16) or len(pred.split())<2: return None
 # evita referências pronominais no início do predicado que dependam de antecedente externo.
 if re.match(r'^(?:é|são)\s+(?:esse|essa|isso|isto|aquele|aquela)\b',pred,re.I): return None
 clause=clean(subject+' '+pred).rstrip(' ,;:')
 if not (32<=len(clause)<=210): return None
 if clause[-1] not in '.!': clause+='.'
 return clause

def main(root,out):
 root=Path(root); manifest=json.loads((root/'reading-manifest.json').read_text(encoding='utf-8'))
 pool=[]; seen=set(); rejected=0
 for d in manifest:
  for row in json.loads((root/d['file']).read_text(encoding='utf-8')):
   for raw in candidate_sentences(row.get('text','')):
    st=validate(raw)
    if not st: rejected+=1; continue
    key=hashlib.sha1(norm(st).encode()).hexdigest()
    if key in seen: continue
    seen.add(key); pool.append((row,st))
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
  qs.append({'id':f'V5-{n:05d}','s':row['subject'],'t':row['lesson'],'q':st,'a':True,'c':'CERTO. O Short reproduz uma afirmação expositiva autônoma selecionada do material-fonte. Fonte: '+row.get('source','Fonte registrada na base.'),'source':row.get('source',''),'lesson':row['lesson']})
 Path(out).write_text(json.dumps(qs,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 unique=len({norm(q['q']) for q in qs}); covered=len({q['s'] for q in qs})
 print('V5 candidatos=',len(pool),'rejeitados=',rejected,'publicados=',len(qs),'disciplinas=',covered,'únicos=',unique)
 if unique!=len(qs): raise SystemExit('ERRO: duplicatas')
 if len({q['id'] for q in qs})!=len(qs): raise SystemExit('ERRO: IDs duplicados')
 if covered!=19: raise SystemExit('ERRO: cobertura diferente de 19 disciplinas')
 forbidden=[QUESTION,INSTRUCTION,CLASSROOM,CONTEXT,OPTION,ARTICLE_FRAGMENT,PAREN_HEADER,BAD_START,ANAPHORA]
 bad=[q['id'] for q in qs if '?' in q['q'] or any(rx.search(q['q']) for rx in forbidden)]
 if bad: raise SystemExit('ERRO: resíduos/contexto dependente: '+','.join(bad[:20]))
if __name__=='__main__': main(sys.argv[1] if len(sys.argv)>1 else '.',sys.argv[2] if len(sys.argv)>2 else 'questions.json')