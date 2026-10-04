#!/usr/bin/env python3
import json,re,sys
from pathlib import Path
from audit_restructure_questions import assess

# Correções somente quando o sentido pode ser preservado sem adivinhar o referente.
PREFIXES=[r'^Dessa forma,\s*',r'^Desse modo,\s*',r'^Assim,\s*',r'^Portanto,\s*',r'^Logo,\s*']

def conservative(text):
    s=' '.join(str(text or '').split())
    for p in PREFIXES:
        s=re.sub(p,'',s,flags=re.I)
    # Primeira letra maiúscula após retirada de conectivo.
    if s: s=s[0].upper()+s[1:]
    return s

def main(root='.'):
    root=Path(root)
    rows=json.loads((root/'questions.json').read_text(encoding='utf-8'))
    audit=json.loads((root/'structural-audit.json').read_text(encoding='utf-8'))
    bad={x['id']:x for x in audit['falhas']}
    candidate=[]; changed=[]; pending=[]
    for q in rows:
        nq=dict(q)
        if q.get('id') in bad:
            old=q.get('q','')
            new=conservative(old)
            # Só aceita automaticamente se a transformação passar no mesmo auditor.
            if new!=old and not assess(new):
                nq['q']=new
                changed.append({'id':q['id'],'antes':old,'depois':new,'modo':'conservador'})
            else:
                pending.append({'id':q['id'],'subject':q.get('s'),'question':old,'reasons':bad[q['id']]['reasons']})
        candidate.append(nq)
    assert len(candidate)==len(rows)
    assert all(a.get('id')==b.get('id') for a,b in zip(rows,candidate))
    (root/'questions-candidate.json').write_text(json.dumps(candidate,ensure_ascii=False,indent=2),encoding='utf-8')
    report={'total_original':len(rows),'falhas_originais':len(bad),'corrigidas_conservadoramente':len(changed),'pendentes_de_pesquisa_ou_contexto':len(pending),'alteracoes':changed,'pendentes':pending}
    (root/'structural-repair-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['total_original','falhas_originais','corrigidas_conservadoramente','pendentes_de_pesquisa_ou_contexto']},ensure_ascii=False))

if __name__=='__main__': main(sys.argv[1] if len(sys.argv)>1 else '.')
