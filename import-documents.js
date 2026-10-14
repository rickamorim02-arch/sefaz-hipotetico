(()=>{'use strict';
const KEY='roleta-importados-v1';let pending=[],filename='';
const el=id=>document.getElementById(id);
function status(t){if(el('importStatus'))el('importStatus').textContent=t}
function parse(text){const lines=text.replace(/\r\n?/g,'\n').split('\n');const out=[];let current=null,skipped=0,article='',section='',history=false;
const legal=lines.some(line=>/^\s*Art\.\s*\d+[º°o]?(?:-[A-Z])?(?:\s|\.|-)/i.test(line));
if(legal){
const flush=()=>{if(current){current.text=current.text.trimEnd();if(current.text)out.push(current)}current=null};
for(const original of lines){const line=original.trim().replace(/^⟪OLD⟫/,'');if(!line)continue;const old=original.trim().startsWith('⟪OLD⟫');
const art=line.match(/^(Art\.\s*\d+[º°o]?(?:-[A-Z])?\.?)(?:\s+|$)/i);
const paragraph=line.match(/^(§\s*\d+[º°o]?(?:\s*[-–.]|\s+)|Parágrafo único\s*[-–.:]?)/i);
const roman=line.match(/^([IVXLCDM]{1,8})\s*[-–]\s+/);
const letter=line.match(/^([a-z])\)\s+/);
const change=/^\*?\s*(?:Nova redação|Redação dada|Redação do|Incluído|Incluída|Acrescentado|Acrescentada|Revogado|Revogada|Efeitos a partir|Alterado|Alterada)/i.test(line);
const heading=/^(?:CAPÍTULO|SEÇÃO|SUBSEÇÃO|TÍTULO|LIVRO)\s+/i.test(line);
if(heading){flush();section=line;history=false;continue}
if(art){flush();article=art[1];current={num:article,text:(old?'⟪OLD⟫':'')+line,kind:'artigo',article,section};history=false;continue}
if(!article){skipped++;continue}
if(change){if(current){current.text+='\n'+(old?'⟪OLD⟫':'')+line;current.note=true}else skipped++;history=true;continue}
if(paragraph||roman||letter){flush();const marker=paragraph?paragraph[1].trim():roman?roman[1]:' '+letter[1]+')';current={num:article+' '+marker.trim(),text:(old?'⟪OLD⟫':'')+line,kind:paragraph?'paragrafo':roman?'inciso':'alinea',article,section};history=false;continue}
if(current){current.text+='\n'+line}else skipped++;
}
flush();return {items:out,skipped,legal:true}}
for(const line of lines){const m=line.match(/^\s*(\d{1,5})[.)\-:]\s+(.+)$/);if(m){if(current)out.push(current);current={num:m[1],text:m[2]}}else if(current){current.text+='\n'+line}else if(line.trim()){skipped++}}if(current)out.push(current);
return {items:out.map(x=>({num:x.num,text:x.text.trimEnd()})),skipped,legal:false}}
async function lib(url,check){if(check())return;await new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=url;s.onload=resolve;s.onerror=()=>reject(Error('Biblioteca indisponível; conecte à internet.'));document.head.append(s)});if(!check())throw Error('Falha ao carregar leitor')}
async function readFile(file){const ext=file.name.split('.').pop().toLowerCase();if(['txt','text','md'].includes(ext))return file.text();
if(ext==='docx'){await lib('https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js',()=>!!window.JSZip);const zip=await JSZip.loadAsync(file);const xml=await zip.file('word/document.xml')?.async('string');if(!xml)throw Error('DOCX sem texto');const doc=new DOMParser().parseFromString(xml,'application/xml');return Array.from(doc.getElementsByTagName('w:p')).map(p=>Array.from(p.getElementsByTagName('w:t')).map(n=>n.textContent).join('')).join('\n')}
if(ext==='pdf'){await lib('https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js',()=>!!window.pdfjsLib);pdfjsLib.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';const pdf=await pdfjsLib.getDocument({data:new Uint8Array(await file.arrayBuffer())}).promise;let lines=[];for(let i=1;i<=pdf.numPages;i++){const page=await pdf.getPage(i),c=await page.getTextContent();let row='',lastY=null,italic=0,total=0;const push=()=>{if(row.trim())lines.push((italic>total*.65?'⟪OLD⟫':'')+row.trim());row='';italic=0;total=0};for(const x of c.items){const y=x.transform?.[5];if(lastY!==null&&Math.abs(y-lastY)>3)push();row+=x.str+(x.hasEOL?'\n':' ');const font=c.styles?.[x.fontName]?.fontFamily||x.fontName||'';if(/italic|oblique/i.test(font))italic+=x.str.length;total+=x.str.length;lastY=y;if(x.hasEOL)push()}push()}return lines.join('\n')}
throw Error('Formato não suportado. Use TXT, MD, DOCX ou PDF com texto selecionável.')}
function parsedLegal(x){return /^Art\./i.test(x.num)}
function refresh(){const stored=JSON.parse(localStorage.getItem(KEY)||'[]');const n=el('importCount');if(n)n.textContent=stored.length+' declarações locais';}
window.previewImport=async()=>{const file=el('importFile')?.files?.[0];if(!file)return status('Escolha um documento.');pending=[];filename=file.name;status('Lendo documento…');try{const raw=await readFile(file);const parsed=parse(raw);pending=parsed.items;if(!pending.length)throw Error('Nenhuma declaração numerada identificada.');const duplicate=parsed.legal?[]:pending.filter((x,i)=>pending.findIndex(y=>y.num===x.num)!==i);if(duplicate.length)throw Error('Numeração repetida: '+duplicate.slice(0,5).map(x=>x.num).join(', '));el('importPreview').textContent=pending.slice(0,5).map(x=>(parsed.legal?x.text:x.num+'. '+x.text)).join('\n\n');el('importConfirm').disabled=false;status(pending.length+(parsed.legal?' dispositivos legais identificados (revisar redações históricas) em ':' declarações identificadas em ')+filename+'. '+(parsed.skipped?'Ignoradas '+parsed.skipped+' linhas de introdução anteriores à primeira declaração. ':'')+'Confira o início abaixo antes de confirmar.')}catch(e){el('importConfirm').disabled=true;el('importPreview').textContent='';status('Importação não concluída: '+e.message)}};
window.confirmImport=()=>{if(!pending.length)return;const replace=el('importReplace').checked;try{const previous=replace?[]:JSON.parse(localStorage.getItem(KEY)||'[]');const start=previous.length;const records=pending.map((x,i)=>({id:'local-'+Date.now()+'-'+i,s:'Documento importado',t:x.num,q:parsedLegal(x)?x.text:x.num+'. '+x.text,source:filename,kind:x.kind||'declaracao',article:x.article||'',section:x.section||'',historicalReview:!!x.note}));const all=previous.concat(records);localStorage.setItem(KEY,JSON.stringify(all));pending=[];el('importConfirm').disabled=true;el('importPreview').textContent='';refresh();status(records.length+' declarações gravadas localmente. Total: '+all.length+'.');window.loadBank?.().then(()=>{window.setFeedMode?.('all');window.tab?.('feed')})}catch(e){status('Não foi possível salvar: '+e.message+'. O armazenamento do navegador pode estar cheio.')}};
window.clearLocalImports=()=>{if(!confirm('Excluir apenas as declarações importadas neste aparelho?'))return;localStorage.removeItem(KEY);refresh();window.loadBank?.();status('Importações locais excluídas.')};
window.getLocalDeclarations=()=>{try{return JSON.parse(localStorage.getItem(KEY)||'[]')}catch(_){return []}};
document.addEventListener('DOMContentLoaded',refresh);
})();