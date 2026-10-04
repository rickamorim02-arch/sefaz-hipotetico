#!/usr/bin/env python3
# Auditoria estrutural censitária do banco publicado.
# Não usa lista fechada de verbos conceituais. Detecta resíduos/fragmentos e tenta
# reestruturação SOMENTE quando a transformação é semanticamente conservadora.
import json,re,sys
from pathlib import Path

BAD_PREFIX=re.compile(r'^(?:[A-E][.)]\s+|portanto[, ]+|assim[, ]+|logo[, ]+|ent[aã]o[, ]+|diante disso[, ]+|diferente d[oa]s?\b|vimos durante a aula\b)',re.I)
ANAPHORA=re.compile(r'^(?:ele|ela|eles|elas|esse|essa|esses|essas|este|esta|estes|estas|isso|isto|aquilo|desse|dessa|deste|desta|seu|sua|seus|suas|tal|tais)\b',re.I)
INCOMPLETE=re.compile(r'(?:\bpara|\bpor|\bde|\bdo|\bda|\bem|\bcom|\bque|\bcomo|\bquando|\bse|\bou|\be)\s*[.!]?$',re.I)
GAP=re.compile(r'_{2,}|\.{3,}|…|\[\.\.\.\]')
META=re.compile(r'\b(?:é correto afirmar que|é incorreto afirmar que|assinale|julgue|marque|analise os itens|passemos a analisar)\b',re.I)
# Flexões verbais frequentes + auxiliares; serve como detector amplo, não como validador semântico.
VERB=re.compile(r'\b(?:é|são|era|eram|foi|foram|será|serão|seria|seriam|tem|têm|teve|tinham|terá|possui|possuem|consiste|consistem|constitui|constituem|define|definem|significa|significam|corresponde|correspondem|compreende|compreendem|abrange|abrangem|inclui|incluem|permite|permitem|exige|exigem|estabelece|estabelecem|determina|determinam|prevê|preveem|aplica|aplicam|utiliza|utilizam|protege|protegem|organiza|organizam|classifica|classificam|identifica|identificam|garante|garantem|veda|vedam|incide|incidem|decorre|decorrem|depende|dependem|gera|geram|produz|produzem|realiza|realizam|registra|registram|controla|controlam|calcula|calculam|representa|representam|forma|formam|integra|integram|adota|adotam|recebe|recebem|mantém|mantêm|reduz|reduzem|aumenta|aumentam|ocorre|ocorrem|resulta|resultam|apresenta|apresentam|indica|indicam|fornece|fornecem|descreve|descrevem|armazena|armazenam|executa|executam|usa|usam|deve|devem|pode|podem|fica|ficam|faz|fazem|h[aá]|existe|existem)\b',re.I)
NOUN_START=re.compile(r'^(?:O|A|Os|As|Um|Uma|Uns|Umas|[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÁÉÍÓÚÂÊÔÃÕÇáéíóúâêôãõç/-]*)\b')

def clean(s): return re.sub(r'\s+',' ',str(s or '')).strip()
def assess(q):
 s=clean(q)
 reasons=[]
 if not s: reasons.append('vazio')
 if GAP.search(s): reasons.append('lacuna_ou_elipse')
 if META.search(s): reasons.append('residuo_de_questao_aula')
 if BAD_PREFIX.search(s): reasons.append('prefixo_contextual_alternativa')
 if ANAPHORA.search(s): reasons.append('referente_dependente_contexto')
 if INCOMPLETE.search(s): reasons.append('complemento_truncado')
 m=VERB.search(s)
 if not m: reasons.append('sem_verbo_principal_detectavel')
 else:
  before=clean(s[:m.start()]).strip(' ,;:-')
  after=clean(s[m.end():]).strip(' ,;:-.!')
  if not before or not NOUN_START.search(before): reasons.append('sujeito_nao_autonomo')
  if len(after.split())<1: reasons.append('predicacao_incompleta')
 # Interrogações e enumerações não são Shorts declarativos.
 if '?' in s: reasons.append('interrogativa')
 if re.match(r'^[IVXLCDM]+\s*[-–—]',s,re.I): reasons.append('item_de_esquema')
 return sorted(set(reasons))

def main(root):
 root=Path(root); manifest=json.loads((root/'questions-manifest.json').read_text(encoding='utf-8'))
 files=manifest.get('files',manifest) if isinstance(manifest,dict) else manifest
 rows=[]
 for f in files:
  path=f.get('file') if isinstance(f,dict) else f
  if not path: continue
  rows.extend(json.loads((root/path).read_text(encoding='utf-8')))
 failed=[]; passed=[]
 for q in rows:
  reasons=assess(q.get('q',q.get('question','')))
  (failed if reasons else passed).append({'id':q.get('id'),'subject':q.get('s',q.get('subject')),'question':q.get('q',q.get('question')),'reasons':reasons})
 report={'total':len(rows),'passam':len(passed),'nao_passam':len(failed),'criterio':'oração declarativa autônoma com sujeito identificável, verbo/predicado e complementação suficiente','falhas':failed}
 (root/'structural-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print('ESTRUTURA total=',len(rows),'passam=',len(passed),'nao_passam=',len(failed))
 # Falha proposital: este script primeiro mede. A reescrita exige fonte/conteúdo por item e não deve ser inventada.
if __name__=='__main__': main(sys.argv[1] if len(sys.argv)>1 else '.')