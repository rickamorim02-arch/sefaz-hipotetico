#!/usr/bin/env python3
# Orquestrador de 20 auditores artificiais determinísticos.
# Cada auditor recebe uma faixa disjunta do banco e aplica o mesmo critério estrutural.
import json,sys,math
from pathlib import Path
from audit_restructure_questions import assess
N=20

def main(root):
 root=Path(root)
 rows=json.loads((root/'questions.json').read_text(encoding='utf-8'))
 size=math.ceil(len(rows)/N)
 workers=[]; failures=[]; passed=0
 for i in range(N):
  chunk=rows[i*size:min((i+1)*size,len(rows))]
  wf=[]; wp=0
  for q in chunk:
   reasons=assess(q.get('q',q.get('question','')))
   if reasons:
    item={'id':q.get('id'),'subject':q.get('s',q.get('subject')),'question':q.get('q',q.get('question')),'reasons':reasons,'auditor':i+1}
    wf.append(item); failures.append(item)
   else: wp+=1; passed+=1
  workers.append({'auditor':i+1,'inicio':i*size+1 if chunk else None,'fim':i*size+len(chunk) if chunk else None,'analisadas':len(chunk),'passam':wp,'nao_passam':len(wf)})
 report={'total':len(rows),'auditores':N,'passam':passed,'nao_passam':len(failures),'criterio':'oração declarativa autônoma com sujeito identificável, verbo/predicado e complementação suficiente','por_auditor':workers,'falhas':failures}
 (root/'structural-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(f'20 AUDITORES: total={len(rows)} passam={passed} nao_passam={len(failures)}')
 for w in workers: print('AUDITOR',w['auditor'],'analisadas=',w['analisadas'],'passam=',w['passam'],'nao_passam=',w['nao_passam'])
if __name__=='__main__': main(sys.argv[1] if len(sys.argv)>1 else '.')