#!/usr/bin/env python3
# Banco V4 — prioridade absoluta à confiabilidade, não à quantidade.
# Publica apenas afirmações expositivas autônomas; exclui questões, alternativas, gabaritos e fragmentos.
import json,re,sys,hashlib
from pathlib import Path
TARGET=50000

def clean(s): return re.sub(r'\s+',' ',str(s or '')).strip()
def norm(s): return re.sub(r'\W+',' ',clean(s).lower(),flags=re.UNICODE).strip()

QUESTION_MARKERS=re.compile(r'\b(cebraspe|cespe|fcc|fgv|vunesp|quadrix|cesgranrio|instituto ao cp|banca|prova|concurso|quest[aã]o|item|julgue|assinale|marque|alternativa|gabarito|resolu[cç][aã]o|coment[aá]rios?)\b',re.I)
INSTRUCTION=re.compile(r'\b(certo ou errado|correta|incorreta|considere|responda|indique|escolha|analise os itens|com base no texto)\b',re.I)
CLASSROOM=re.compile(r'^(pessoal|galera|caros alunos|aten[cç][aã]o|veja|vejamos|observe|notem|vamos|lembre-se|perceba)\b',re.I)
BAD_CONTEXT=re.compile(r'\b(conforme visto|como vimos|acima|abaixo|anteriormente|a seguir|na figura|na tabela|no quadro|no exemplo|neste caso|nesse caso)\b',re.I)
OPTION=re.compile(r'(?:^|\s)[a-eA-E]\)\s|(?:^|\s)[a-eA-E]\.\s|\b[a-eA-E]\)\s|[•▪◦]')
ARTICLE_FRAGMENT=re.compile(r'^(?:art\.?\s*)?\d+[º°]?\s+(?:da|do|de|prev[eê]|disp[oõ]e|estabelece|tem)\b',re.I)
PAREN_HEADER=re.compile(r'^\([^)]*(?:20\d\d|cebraspe|cespe|fcc|fgv|vunesp|cargo|t[eé]cnico|analista)[^)]*\)\s*',re.I)

VERBS=r'(?:é|são|foi|foram|será|serão|tem|têm|possui|possuem|constitui|constituem|representa|representam|define|definem|estabelece|estabelecem|determina|determinam|permite|permitem|exige|exigem|inclui|incluem|compreende|compreendem|abrange|abrangem|corresponde|correspondem|decorre|decorrem|depende|dependem|deve|devem|pode|podem|ocorre|ocorrem|consiste|consistem|aplica|aplicam|utiliza|utilizam|considera|consideram|garante|garantem|veda|vedam|prevê|preveem|dispõe|dispõem|integra|integram|adota|adotam|produz|produzem|gera|geram|reduz|reduzem|aumenta|aumentam|mantém|mantêm|recebe|recebem|realiza|realizam|calcula|calculam|registra|registram|controla|controlam|protege|protegem|organiza|organizam|classifica|classificam|identifica|identificam|avalia|avaliam|analisa|analisam|verifica|verificam|autoriza|autorizam|proíbe|proibem|obriga|obrigam|incide|incidem|alcança|alcançam|envolve|envolvem|resulta|resultam|significa|significam)'

def candidate_sentences(text):
 text=clean(str(text or '').replace('\n',' '))
 for s in re.split(r'(?<=[.!?])\s+',text):
  s=clean(s).strip('•*-–— ')
  if 30<=len(s)<=260 and s.count(' ')>=5: yield s

def validate(s):
 # Não tentamos inferir gabarito de questões. Qualquer aparência de questão é descartada.
 if '?' in s or QUESTION_MARKERS.search(s) or INSTRUCTION.search(s): return None
 if CLASSROOM.search(s) or BAD_CONTEXT.search(s) or OPTION.search(s): return None
 if PAREN_HEADER.search(s) or ARTICLE_FRAGMENT.search(s): return None
 if re.match(r'^(e|ou|mas|porque|pois|que|quando|onde|cujo|cuja|este|esta|estes|estas|isso|isto|aquilo)\b',s,re.I): return None
 if re.search(r'\b(?:verdadeiro|falso)\b',s,re.I): return None
 # rejeita enumerações, restos editoriais e excesso de orações
 if s.count(';') or s.count(':') or s.count('•') or len(re.findall(r'\b(?:que|quando|onde|porque|pois)\b',s,re.I))>1: return None
 s=re.sub(r'^(?:portanto|assim|logo|contudo|todavia|entretanto|porém|porem),?\s+','',s,flags=re.I)
 m=re.search(r'\b'+VERBS+r'\b',s,re.I)
 if not m or m.start()<4: return None
 subject=clean(s[:m.start()]).strip(' ,.-')
 pred=clean(s[m.start():]).strip(' ,.-')
 # sujeito precisa começar por palavra, sigla ou artigo; nunca número solto
 if not re.match(r'^(?:[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç/-]*|O|A|Os|As|Um|Uma|No|Na|Nos|Nas)\b',subject): return None
 if re.match(r'^\d',subject) or len(subject.split())>18 or len(pred.split())<2: return None
 clause=clean(subject+' '+pred).rstrip(' ,;:')
 if not (30<=len(clause)<=220): return None
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
 # Não cria versões falsas artificialmente: toda publicação é afirmação expositiva preservada do material.
 # Isso evita transformar exercícios sem gabarito verificável em fatos.
 goal=min(TARGET,len(pool)); by={}
 for row,st in pool: by.setdefault(row['subject'],[]).append((row,st))
 chosen=[]; i=0; subjects=sorted(by)
 while len(chosen)<goal:
  moved=False
  for sub in subjects:
   if i<len(by[sub]) and len(chosen)<goal: chosen.append(by[sub][i]); moved=True
  if not moved: break
  i+=1
 qs=[]
 for n,(row,st) in enumerate(chosen,1):
  qs.append({'id':f'V4-{n:05d}','s':row['subject'],'t':row['lesson'],'q':st,'a':True,'c':'CERTO. Afirmação expositiva preservada do material-fonte; itens de prova e alternativas foram excluídos. Fonte: '+row.get('source','Fonte registrada na base.'),'source':row.get('source',''),'lesson':row['lesson']})
 Path(out).write_text(json.dumps(qs,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 unique=len({norm(q['q']) for q in qs}); covered=len({q['s'] for q in qs})
 print('V4: candidatos=',len(pool),'rejeitados=',rejected,'publicados=',len(qs),'disciplinas=',covered,'únicos=',unique)
 if unique!=len(qs): raise SystemExit('ERRO: duplicatas')
 if len({q['id'] for q in qs})!=len(qs): raise SystemExit('ERRO: IDs duplicados')
 if covered!=19: raise SystemExit('ERRO: cobertura diferente de 19 disciplinas')
 # auditoria automática contra resíduos conhecidos
 forbidden=[QUESTION_MARKERS,INSTRUCTION,CLASSROOM,BAD_CONTEXT,OPTION,ARTICLE_FRAGMENT,PAREN_HEADER]
 bad=[q['id'] for q in qs if '?' in q['q'] or any(rx.search(q['q']) for rx in forbidden)]
 if bad: raise SystemExit('ERRO: resíduos pedagógicos: '+','.join(bad[:20]))
if __name__=='__main__': main(sys.argv[1] if len(sys.argv)>1 else '.',sys.argv[2] if len(sys.argv)>2 else 'questions.json')