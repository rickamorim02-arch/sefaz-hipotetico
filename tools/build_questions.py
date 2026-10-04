#!/usr/bin/env python3
# Banco V11 — recuperação conservadora: corrige somente erros factuais já confirmados,
# elimina frases contextuais e mantém itens de risco separados para auditoria factual posterior.
import json,re,sys,hashlib
from pathlib import Path
TARGET_INITIAL=50000

def clean(s): return re.sub(r'\s+',' ',str(s or '')).strip()
def norm(s): return re.sub(r'\W+',' ',clean(s).lower(),flags=re.UNICODE).strip()
def key(s): return hashlib.sha1(norm(s).encode()).hexdigest()
def original_candidates(text):
 text=clean(str(text or '').replace('\n',' ')); out=[]
 for s in re.split(r'(?<=[.!?;])\s+',text):
  s=clean(s)
  if 45<=len(s)<=520 and s.count(' ')>=7 and not re.match(r'^[\d\W_]+$',s): out.append(s)
 return out
QUESTION=re.compile(r'\b(cebraspe|cespe|fcc|fgv|vunesp|quadrix|cesgranrio|banca|prova|concurso|quest[aã]o|julgue|assinale|marque|alternativa|gabarito|resolu[cç][aã]o|coment[aá]rios?)\b',re.I)
META=re.compile(r'\b(?:é correto afirmar que|é incorreto afirmar que|correto afirmar que|incorreto afirmar que|podemos afirmar que|pode-se afirmar que)\b',re.I)
CLASSROOM=re.compile(r'^(?:pessoal|galera|caros alunos|aten[cç][aã]o|veja|vejamos|observe|notem|vamos|lembre-se|perceba)[,:]?\s*',re.I)
CONTEXT_PREFIX=re.compile(r'^(?:portanto|assim|logo|contudo|todavia|entretanto|por[eé]m|de fato|al[eé]m disso|justamente)[,:]?\s*',re.I)
CONTEXT=re.compile(r'\b(?:nessa situa[cç][aã]o|nesta situa[cç][aã]o|nesse caso|neste caso|desse áudio|deste áudio|acima|abaixo|anteriormente|a seguir|na figura|na tabela|no quadro|no exemplo|exemplos citados|ideia central)\b',re.I)
ANAPHORA=re.compile(r'^(?:esse|essa|esses|essas|este|esta|estes|estas|isso|isto|aquilo|aquele|aquela|aqueles|aquelas|seu|sua|seus|suas|dele|dela|deles|delas|o mesmo|a mesma)\b',re.I)
OPTION=re.compile(r'(?:^|\s)[a-eA-E][.)]\s|[•▪◦]')
TRUNCATED=re.compile(r'(?:\b(?:art|arts|inc|incs|al[ií]nea|item|itens|fig|p[aá]g|p[aá]gina|cap|se[cç][aã]o)\.?|\b(?:conforme|segundo|nos termos de|de acordo com)|\b(?:afirmar que|concluir que))\s*\.?$',re.I)
RISKY=re.compile(r'\b(?:não|nem|sem|sempre|nunca|jamais|somente|apenas|exclusivamente|necessariamente|obrigatoriamente|todos|todas|nenhum|nenhuma|única|único|irrevog[aá]vel|irrestrit[oa]s?|consenso total|sem exceção)\b',re.I)
CONCEPT=re.compile(r'\b(?:é|são|consiste|consistem|constitui|constituem|define|definem|significa|significam|corresponde|correspondem|compreende|compreendem|abrange|abrangem|inclui|incluem|possui|possuem|tem|têm|caracteriza-se|caracterizam-se|permite|permitem|exige|exigem|estabelece|estabelecem|determina|determinam|prevê|preveem|aplica|aplicam|utiliza|utilizam|protege|protegem|organiza|organizam|classifica|classificam|identifica|identificam|garante|garantem|veda|vedam|incide|incidem|decorre|decorrem|depende|dependem)\b',re.I)
# Correções somente para erros que já foram identificados e confirmados durante a auditoria.
CORRECTIONS=[
 (re.compile(r'.*cadeia de valor de servi[cç]o do ITIL v4 é formada pelas práticas.*',re.I),'A cadeia de valor de serviço do ITIL 4 é composta por seis atividades interconectadas.'),
 (re.compile(r'.*pseudocódigo é considerado uma linguagem de programação formal e executável.*',re.I),'O pseudocódigo é uma forma textual estruturada de representar algoritmos e não constitui, por si só, uma linguagem de programação executável.'),
 (re.compile(r'.*metadados EXIF ficam em arquivos separados.*',re.I),'Metadados EXIF podem ser incorporados ao próprio arquivo de imagem e armazenar informações sobre sua captura.'),
 (re.compile(r'.*normas constitucionais de eficácia plena e de eficácia contida têm aplicabilidade imediata, são irrevogáveis e não admitem restrições.*',re.I),'As normas constitucionais de eficácia plena e de eficácia contida têm aplicabilidade imediata; as de eficácia contida podem sofrer restrições nos casos constitucionalmente admitidos.')]

def apply_correction(s):
 for rx,new in CORRECTIONS:
  if rx.search(s): return new,True
 return s,False

def shape(s):
 s=clean(s).strip('•*-–— '); s=CLASSROOM.sub('',s); s=CONTEXT_PREFIX.sub('',s); s=META.sub('',s)
 s=re.split(r'(?<=[.!?])\s+',s)[0]; s=re.split(r'\s*[;:]\s*',s)[0]; s=clean(s).strip(' ,.-')
 if s and s[-1] not in '.!?': s+='.'
 return s

def structural(s):
 if not (35<=len(s)<=220) or '?' in s or OPTION.search(s) or TRUNCATED.search(s.rstrip(' .')) or CONTEXT.search(s): return None
 if QUESTION.search(s) or ANAPHORA.search(s): return None
 if '[...]' in s or '…' in s or re.search(r'\.{2,}',s) or not CONCEPT.search(s): return None
 m=CONCEPT.search(s)
 if not m or m.start()<5: return None
 subject=clean(s[:m.start()]).strip(' ,.-'); pred=clean(s[m.start():]).strip(' ,.-')
 if ANAPHORA.search(subject) or re.match(r'^(?:no|na|nos|nas|para|por|com|sem|em|de|do|da|dos|das|se)\b',subject,re.I): return None
 if not re.match(r'^(?:O|A|Os|As|Um|Uma|[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç/-]*)\b',subject): return None
 if len(subject.split())>18 or len(pred.split())<2: return None
 return clean(subject+' '+pred).rstrip(' ,;:')+'.'

def classify(raw):
 s=shape(raw); s,corrected=apply_correction(s); st=structural(s)
 if not st: return None,'reject'
 if corrected: return st,'corrigido_confirmado'
 return st,('resgatado_risco' if RISKY.search(st) else 'seguro')

def choose50(pool):
 by={}
 for row,st in pool: by.setdefault(row['subject'],[]).append((row,st))
 chosen=[]; i=0; subs=sorted(by)
 while len(chosen)<min(TARGET_INITIAL,len(pool)):
  moved=False
  for sub in subs:
   if i<len(by[sub]) and len(chosen)<TARGET_INITIAL: chosen.append(by[sub][i]); moved=True
  if not moved: break
  i+=1
 return chosen

def main(root,out):
 root=Path(root); manifest=json.loads((root/'reading-manifest.json').read_text(encoding='utf-8')); universe=[]; seen=set()
 for d in manifest:
  for row in json.loads((root/d['file']).read_text(encoding='utf-8')):
   for raw in original_candidates(row.get('text','')):
    if key(raw) not in seen: seen.add(key(raw)); universe.append((row,raw))
 first=choose50(universe); fk={key(x[1]) for x in first}; left=[x for x in universe if key(x[1]) not in fk]
 combined=[]; used=set(); stats={'seguro':0,'resgatado_risco':0,'corrigido_confirmado':0,'reject':0}
 for origin,group in [('50k',first),('excedente',left)]:
  for row,raw in group:
   st,status=classify(raw); stats[status]+=1
   if not st or key(st) in used: continue
   used.add(key(st)); combined.append((row,st,origin,status))
 qs=[]
 for n,(row,st,origin,status) in enumerate(combined,1):
  qs.append({'id':f'V11-{n:05d}','s':row['subject'],'t':row['lesson'],'q':st,'a':True,'c':'CERTO. Short preservado após revisão estrutural; correções automáticas são restritas a erros previamente confirmados.','source':row.get('source',''),'lesson':row['lesson'],'origin':origin,'validation':status})
 Path(out).write_text(json.dumps(qs,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 counts={x:sum(q['validation']==x for q in qs) for x in ['seguro','resgatado_risco','corrigido_confirmado']}; covered=len({q['s'] for q in qs})
 print('V11 UNIVERSO=',len(universe),'TOTAL=',len(qs),'SEGUROS=',counts['seguro'],'RISCO_PENDENTE=',counts['resgatado_risco'],'CORRIGIDOS_CONFIRMADOS=',counts['corrigido_confirmado'],'REJEITADOS=',stats['reject'],'DISCIPLINAS=',covered)
 if len({key(q['q']) for q in qs})!=len(qs) or len({q['id'] for q in qs})!=len(qs): raise SystemExit('ERRO duplicatas')
 if covered!=19: raise SystemExit('ERRO cobertura')
if __name__=='__main__': main(sys.argv[1] if len(sys.argv)>1 else '.',sys.argv[2] if len(sys.argv)>2 else 'questions.json')