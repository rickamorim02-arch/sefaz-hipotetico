// Banco fragmentado: evita baixar/parsear 50 mil questões na abertura.
(()=>{
let manifest=null,nextPart=0,loading=false,done=false;
async function getManifest(){if(manifest)return manifest;const r=await fetch('questions-manifest.json',{cache:'no-store'});if(!r.ok)throw new Error('manifest');manifest=await r.json();return manifest}
async function loadNext(count=1){if(loading||done)return;loading=true;try{const m=await getManifest();for(let k=0;k<count&&nextPart<m.parts.length;k++,nextPart++){const r=await fetch(m.parts[nextPart].file,{cache:'default'});if(!r.ok)throw new Error(m.parts[nextPart].file);const a=await r.json();window.Q.push(...a)}done=nextPart>=m.parts.length;window.render?.(false);window.subjects?.();window.stats?.();const i=document.getElementById('bankInfo');if(i)i.textContent=`${m.total} questões no banco • ${window.Q.length} carregadas agora.`}catch(e){console.error(e)}finally{loading=false}}
window.loadBank=async function(){window.Q=[];Q=window.Q;try{const m=await getManifest();const i=document.getElementById('bankInfo');if(i)i.textContent=`${m.total} questões no banco • carregamento progressivo.`;await loadNext(1)}catch(e){console.error(e);const i=document.getElementById('bankInfo');if(i)i.textContent='Falha ao carregar índice do banco.'}};
window.loadMoreQuestionData=()=>loadNext(1);
const feed=document.getElementById('feed');if(feed)feed.addEventListener('scroll',()=>{if(done||loading)return;if(feed.scrollTop+feed.clientHeight>feed.scrollHeight-1800)loadNext(1)},{passive:true});
})();