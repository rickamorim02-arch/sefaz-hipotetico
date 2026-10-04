#!/usr/bin/env python3
# Recuperação estrutural conservadora. Não altera os 8.250 aprovados.
# Corrige apenas transformações que preservam o conteúdo proposicional; casos que
# exigem descobrir referente/conteúdo permanecem pendentes para revisão humana/factual.
import json,re,sys
from pathlib import Path
from audit_restructure_questions import assess

PREFIXES=[
 (re.compile(r'^Dessa forma,\s*',re.I),''),(re.compile(r'^Desse modo,\s*',re.I),''),
 (re.compile(r'^Portanto,\s*',re.I),''),(re.compile(r'^Assim,\s*',re.I),''),
 (re.compile(r'^Logo,\s*',re.I),''),(re.compile(r'^Então,\s*',re.I),''),
 (re.compile(r'^Ademais,\s*',re.I),''),
 (re.compile(r'^Vimos durante a aula que\s*',re.I),''),
]
# Correções estruturais explícitas de itens observados no relatório; conteúdo mantido.
EXACT={
 'V11-00162':'Somente a quantidade de dados não é suficiente para determinar sua qualidade.',
 'V11-00222':'O DANFE não é uma nota fiscal e não substitui a NF-e; ele serve como documento auxiliar da NF-e.',
 'V11-00297':'As normas programáticas podem ser facultativas, quando estabelecem uma faculdade para o Poder Público, ou impositivas, quando estabelecem uma obrigação.',
 'V11-00315':'O credenciamento é obrigatório para a emissão de NF-e.',
 'V11-00516':'O IPI integra a base de cálculo do ICMS quando a operação não ocorre entre contribuintes do ICMS, observadas as hipóteses legais aplicáveis.',
 'V11-00517':'O IPI não integra a base de cálculo do ICMS quando a operação entre contribuintes se destina à industrialização ou à comercialização, observadas as hipóteses legais aplicáveis.',
 'V11-00518':'Cada Estado pode estipular por lei suas alíquotas internas de ICMS, observadas as limitações constitucionais e legais.',
}

def conservative(text):
 s=text.strip()
 for rx,rep in PREFIXES: s=rx.sub(rep,s)
 # Só aceita a transformação automática se ela passar depois da retirada de conectivo metadiscursivo.
 return s

def main(root='.'):
 root=Path(root)
 qs=json.loads((root/'questions.json').read_text(encoding='utf-8'))
 report=json.loads((root/'structural-audit.json').read_text(encoding='utf-8'))
 bad={x['id'] for x in report['falhas']}
 changed=[]; pending=[]
 for q in qs:
  if q['id'] not in bad: continue
  old=q['q']; new=EXACT.get(q['id'],conservative(old))
  if new!=old and not assess(new):
   q['q']=new; q['structural_repair']='recuperado_conservador'; changed.append(q['id'])
  else:
   pending.append({'id':q['id'],'subject':q.get('s'),'question':old,'reasons':assess(old)})
 (root/'questions.json').write_text(json.dumps(qs,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 (root/'structural-repair-report.json').write_text(json.dumps({'alvo_inicial':len(bad),'recuperados':len(changed),'pendentes':len(pending),'recuperados_ids':changed,'pendentes_itens':pending},ensure_ascii=False,indent=2),encoding='utf-8')
 print('ALVO',len(bad),'RECUPERADOS',len(changed),'PENDENTES',len(pending))
if __name__=='__main__': main(sys.argv[1] if len(sys.argv)>1 else '.')