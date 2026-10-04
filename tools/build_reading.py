#!/usr/bin/env python3
# build revision: audit-255-v2
import json,re,sys,unicodedata,zipfile,shutil
from pathlib import Path
from xml.etree import ElementTree as ET
W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
def repair(s):
 try:
  if any(x in s for x in ('├','┬','┼','╬')): return s.encode('cp437').decode('utf-8')
 except Exception: pass
 return s
def slug(s):
 s=unicodedata.normalize('NFKD',repair(s)).encode('ascii','ignore').decode().lower();return re.sub(r'[^a-z0-9]+','-',s).strip('-')
def docx_paragraphs(path):
 with zipfile.ZipFile(path) as z: root=ET.fromstring(z.read('word/document.xml'))
 out=[]
 for p in root.iter(W+'p'):
  t=''.join(x.text or '' for x in p.iter(W+'t')).strip()
  if t: out.append(t)
 return out
def split_sources(subject,pars):
 starts=[]
 for i,p in enumerate(pars[:-1]):
  if re.match(r'^Aula\s+(?:\d{1,3}|única|unica)\b',p,re.I) and pars[i+1].startswith('Fonte:'):
   starts.append(i)
 rows=[]
 for n,i in enumerate(starts):
  j=starts[n+1] if n+1<len(starts) else len(pars)
  title=pars[i].strip(); source=pars[i+1].strip(); text='\n'.join(pars[i:j]).strip()
  rows.append({'subject':subject,'lesson':title,'source':source,'text':text})
 return rows
def main(src,out):
 src,out=Path(src),Path(out);shutil.rmtree(out,ignore_errors=True);out.mkdir(parents=True)
 work=out/'_source';work.mkdir()
 with zipfile.ZipFile(src) as z:z.extractall(work)
 docs=sorted(p for p in work.rglob('*.docx') if 'RELATORIO_DE_AUDITORIA' not in p.name)
 manifest=[]
 for p in docs:
  subject=repair(p.stem);rows=split_sources(subject,docx_paragraphs(p))
  if not rows: raise RuntimeError('Nenhuma fonte identificada em '+subject)
  name='reading-'+slug(subject)+'.json';(out/name).write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
  manifest.append({'subject':subject,'file':name,'lessons':len(rows)})
 (out/'reading-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 shutil.rmtree(work,ignore_errors=True)
 print('disciplinas',len(manifest),'fontes',sum(x['lessons'] for x in manifest))
if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('uso: build_reading.py ARQUIVO.zip DIRETORIO_SAIDA')
 main(sys.argv[1],sys.argv[2])