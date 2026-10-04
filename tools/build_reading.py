#!/usr/bin/env python3
import json,re,sys,unicodedata,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def slug(s):
 s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower();s=re.sub(r'[^a-z0-9]+','-',s).strip('-');return s

def docx_paragraphs(path):
 with zipfile.ZipFile(path) as z: xml=z.read('word/document.xml')
 root=ET.fromstring(xml);out=[]
 for p in root.iter(W+'p'):
  t=''.join(x.text or '' for x in p.iter(W+'t')).strip()
  if t: out.append(t)
 return out

def split_lessons(subject,pars):
 rows=[];lesson='Aula única';buf=[]
 pat=re.compile(r'^(?:AULA|Aula)\s*(?:n[ºo°.]?\s*)?(\d{1,3}|única|unica)\b',re.I)
 def flush():
  nonlocal buf
  text='\n'.join(buf).strip()
  if text: rows.append({'subject':subject,'lesson':lesson,'text':text})
  buf=[]
 for p in pars:
  m=pat.match(p)
  if m and buf:
   flush();lesson='Aula '+m.group(1)
  elif m: lesson='Aula '+m.group(1)
  buf.append(p)
 flush();return rows

def main(src,out):
 src,out=Path(src),Path(out);out.mkdir(parents=True,exist_ok=True)
 work=out/'_source';work.mkdir(exist_ok=True)
 with zipfile.ZipFile(src) as z:z.extractall(work)
 docs=sorted(p for p in work.rglob('*.docx') if 'RELATORIO_DE_AUDITORIA' not in p.name)
 manifest=[]
 for p in docs:
  subject=p.stem;rows=split_lessons(subject,docx_paragraphs(p));name='reading-'+slug(subject)+'.json'
  (out/name).write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
  manifest.append({'subject':subject,'file':name,'lessons':len(rows)})
 (out/'reading-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 print('disciplinas',len(manifest),'unidades',sum(x['lessons'] for x in manifest))
if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('uso: build_reading.py ARQUIVO.zip DIRETORIO_SAIDA')
 main(sys.argv[1],sys.argv[2])