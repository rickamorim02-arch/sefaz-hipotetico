#!/usr/bin/env python3
import json,re,sys,collections
from pathlib import Path
p=Path(sys.argv[1] if len(sys.argv)>1 else 'questions.json')
q=json.loads(p.read_text(encoding='utf-8'))
flags=collections.Counter(); examples=collections.defaultdict(list)
patterns={
'fragmento_inicio':re.compile(r'^(e|ou|mas|porque|pois|portanto|assim|entretanto|contudo|todavia|logo|além disso|alem disso)\b',re.I),
'referencia_solto':re.compile(r'\b(este|esta|estes|estas|isso|isto|aquilo|acima|abaixo|anterior|seguinte|conforme visto|como vimos)\b',re.I),
'questao_original':re.compile(r'\b(julgue|assinale|marque|responda|alternativa correta|alternativa incorreta|certo ou errado|questão \d+)\b',re.I),
'gabarito_resolucao':re.compile(r'\b(gabarito|resolução|resolucao|comentário do professor|comentario do professor)\b',re.I),
'lista_incompleta':re.compile(r'(^|\s)[a-e]\)|(^|\s)[ivx]+\)|(^|\s)\d+[.)]\s',re.I),
'html_ruido':re.compile(r'https?://|www\.|<[^>]+>|\{\{|\}\}'),
}
for x in q:
 s=str(x.get('q','')).strip()
 tests=[]
 if len(s)<55: tests.append('curta_demais')
 if len(s)>420: tests.append('longa_demais')
 if s and s[-1] not in '.!?;:)”"': tests.append('terminacao_suspeita')
 if s.count('(')!=s.count(')'): tests.append('parenteses_desbalanceados')
 if s.count('“')!=s.count('”'): tests.append('aspas_desbalanceadas')
 for name,pat in patterns.items():
  if pat.search(s): tests.append(name)
 for name in set(tests):
  flags[name]+=1
  if len(examples[name])<8: examples[name].append({'id':x.get('id'),'disciplina':x.get('s'),'texto':s[:500]})
report={'total':len(q),'disciplinas':len({x.get('s') for x in q}),'sinalizadas_total':sum(1 for x in q if any(([len(str(x.get('q','')).strip())<55,len(str(x.get('q','')).strip())>420] + [bool(pat.search(str(x.get('q','')).strip())) for pat in patterns.values()]))),'flags':dict(flags),'exemplos':dict(examples),'nota':'Heurística conservadora: sinalização não significa erro factual; itens sinalizados devem ser revisados ou filtrados antes de uso definitivo.'}
Path('questions-quality-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'total':report['total'],'disciplinas':report['disciplinas'],'flags':report['flags']},ensure_ascii=False))