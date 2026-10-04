// Banco fragmentado: carregamento sob demanda controlado pelo feed virtualizado.
(()=>{let manifest=null,nextPart=0,loading=false,done=false;
async function getManifest(){if(manifest)return manifest;const r=await fetch('questions-manifest.json',{cache:'default'});if(!r.ok)throw new Error('manifest');return manifest=await r.json()}
async function loadNext(){if(loading||done)return false;loading=true;try{const m=await getManifest();if(nextPart>=m.parts.length){done=true;return false}const p=m.parts[nextPart++],r=await fetch(p.file,{cache:'default'});if(!r.ok)throw new Error(p.file);const a=await r.json();window.Q.push(...a);done=nextPart>=m.parts.length;window.render?.(false);const i=document.getElementById('bankInfo');if(i)i.textContent=`${m.total} questões no banco • ${window.Q.length} carregadas nesta sessão.`;return true}catch(e){console.error(e);return false}finally{loading=false}}
window.loadBank=async()=>{window.Q=[];Q=window.Q;try{const m=await getManifest(),i=document.getElementById('bankInfo');if(i)i.textContent=`${m.total} questões no banco • carregamento sob demanda.`;await loadNext()}catch(e){console.error(e)}};
window.loadMoreQuestionData=loadNext;
})();