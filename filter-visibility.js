(function(){
  function syncFeedFilter(){
    const filter=document.getElementById('feedFilter');
    const feed=document.getElementById('feed');
    if(!filter||!feed)return;
    const shortsVisible=!feed.classList.contains('hidden');
    filter.classList.toggle('hidden',!shortsVisible);
  }
  function init(){
    const app=document.querySelector('.app');
    if(!app)return false;
    syncFeedFilter();
    new MutationObserver(syncFeedFilter).observe(app,{subtree:true,attributes:true,attributeFilter:['class']});
    document.addEventListener('click',()=>setTimeout(syncFeedFilter,0),true);
    return true;
  }
  let t=setInterval(()=>{if(init())clearInterval(t)},50);
})();