// Otimização para bancos grandes: renderização incremental, índices e busca O(1).
(()=>{
let pageSize=24, shown=pageSize, qById=new Map(), subjectCounts=new Map(), indexedFor=null, observer=null;
const oldLoad=window.loadBank;
function rebuild(){
 if(indexedFor===window.Q)return;
 const a=window.Q||[]; qById=new Map(); subjectCounts=new Map();
 for(const q of a){qById.set(String(q.id),q);const s=q.s||q.subject||'SEFAZ-Hipotético';subjectCounts.set(s,(subjectCounts.get(s)||0)+1)}
 indexedFor=window.Q;
}
function escapeAttr(s){return String(s||'').replace(/'/g,'').replace(/"/g,'')}
function item(q,s){
 const id=escapeAttr(q.id),sub=window.esc(q.s||q.subject||'SEFAZ-Hipotético'),topic=window.esc(q.t||q.topic||''),text=window.esc(q.q||q.question||'');
 return '<article class="q" data-id="'+id+'"><div class="tag">'+sub+'</div><div class="topic">'+topic+'</div><h1>'+text+'</h1><button class="opt" onclick="answer(\''+id+'\',true,this)">CERTO</button><button class="opt" onclick="answer(\''+id+'\',false,this)">ERRADO</button><div class="feedback hidden"></div><button class="star" onclick="favorite(\''+id+'\')">'+(s.fav[id]?'★':'☆')+' Favoritar</button></article>'
}
function eligible(q,s){const done=!!s.answers[q.id];return window.feedMode==='all'||(window.feedMode==='resolved'?done:!done)}
function collect(limit){const s=window.state(),out=[];for(const q of (window.Q||[])){if(eligible(q,s)){out.push(q);if(out.length>=limit)break}}return {s,out}}
window.render=function(reset=false){
 rebuild(); if(reset)shown=pageSize;
 const box=document.getElementById('feed');if(!box)return;
 const {s,out}=collect(shown+1),more=out.length>shown,list=more?out.slice(0,shown):out;
 box.innerHTML=list.length?list.map(q=>item(q,s)).join('')+(more?'<div id="moreFeed" style="height:2px"></div>'):'<section class="q"><div class="card"><h2>Nenhuma questão nesta lista</h2><p>Altere o filtro para visualizar outras questões.</p></div></section>';
 if(observer)observer.disconnect();
 if(more&&'IntersectionObserver'in window){observer=new IntersectionObserver(es=>{if(es.some(e=>e.isIntersecting)){shown+=pageSize;window.render(false)}},{root:box,rootMargin:'600px'});observer.observe(document.getElementById('moreFeed'))}
};
window.answer=function(id,v,b){rebuild();const q=qById.get(String(id));if(!q)return;const correct=Boolean(q.a??q.answer)===v,s=window.state();s.answers[id]={v,correct};window.save(s);const art=b.closest('.q'),fb=art.querySelector('.feedback');art.querySelectorAll('.opt').forEach(x=>x.disabled=true);b.classList.add(correct?'ok':'no');fb.classList.remove('hidden');fb.innerHTML='<b>'+(correct?'✅ Acertou':'❌ Errou')+'</b><p>'+window.esc(q.c||q.comment||'Comentário ainda não disponível.')+'</p>';window.stats()};
window.favorite=function(id){const s=window.state();s.fav[id]=!s.fav[id];if(!s.fav[id])delete s.fav[id];window.save(s);window.render(false);window.stats()};
window.setFeedMode=function(m){window.feedMode=m;shown=pageSize;['fp','fr','fa'].forEach(x=>document.getElementById(x)?.classList.remove('on'));document.getElementById(m==='pending'?'fp':m==='resolved'?'fr':'fa')?.classList.add('on');window.render(true)};
window.subjects=function(){rebuild();const box=document.getElementById('sl');if(!box)return;const f=(document.getElementById('find')?.value||'').toLowerCase();const a=[...subjectCounts.entries()].filter(([x])=>x.toLowerCase().includes(f)).sort((a,b)=>a[0].localeCompare(b[0]));box.innerHTML=a.length?a.map(([x,n])=>'<div class="card"><b>'+window.esc(x)+'</b><br><small>'+n+' questões</small></div>').join(''):'<div class="card">Nenhuma matéria encontrada.</div>'};
// O código original inicia o fetch antes deste arquivo; após a resposta ele chamará estas versões otimizadas.
})();