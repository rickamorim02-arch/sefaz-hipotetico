#!/usr/bin/env python3
# revision: ensure-shards-v2
import json,sys,shutil
from pathlib import Path
src=Path(sys.argv[1] if len(sys.argv)>1 else 'questions.json'); out=Path(sys.argv[2] if len(sys.argv)>2 else 'questions-data'); size=int(sys.argv[3] if len(sys.argv)>3 else 500)
q=json.loads(src.read_text(encoding='utf-8')); shutil.rmtree(out,ignore_errors=True); out.mkdir(parents=True)
parts=[]
for i in range(0,len(q),size):
 chunk=q[i:i+size]; name=f'part-{i//size+1:03d}.json'; (out/name).write_text(json.dumps(chunk,ensure_ascii=False,separators=(',',':')),encoding='utf-8'); parts.append({'file':'questions-data/'+name,'count':len(chunk),'start':i,'end':i+len(chunk)-1})
subjects={}
for x in q: subjects[x['s']]=subjects.get(x['s'],0)+1
manifest={'total':len(q),'chunkSize':size,'parts':parts,'subjects':subjects}
Path('questions-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print('FRAGMENTADO:',len(q),'questões em',len(parts),'arquivos de até',size)