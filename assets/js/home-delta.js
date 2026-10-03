(() => {
  const parse=id=>JSON.parse(document.getElementById(id).textContent);
  const nodes=parse('homeNodes'), edges=parse('homeEdges'), deltas=parse('homeDeltas');
  const byId=new Map(nodes.map(n=>[n.id,n]));
  const base=document.body.dataset.baseurl||'';
  const entityHref=n=>base+(n?.page||('/graph/?focus='+encodeURIComponent(n?.id||'')));
  const keys=Object.keys(deltas||{}).sort();
  if(!keys.length)return;
  const date=keys[keys.length-1], delta=deltas[date];
  const bootstrap=String(delta.mode||'').includes('bootstrap');

  let added=delta.nodes_added||[], updated=delta.nodes_updated||[], addedEdges=delta.edges_added||[];
  if(bootstrap){
    added=added.filter(id=>byId.get(id)?.first_seen===date);
    addedEdges=addedEdges.filter(id=>edges.find(e=>e.id===id)?.first_seen===date);
  }

  const preferred=new Set(['Project','Capability','Research','Trend','Pattern','Standard']);
  const visibleAdded=added.map(id=>byId.get(id)).filter(n=>n&&preferred.has(n.type));
  document.getElementById('deltaDate').textContent=date;
  const stats=document.querySelectorAll('#deltaSummary strong');
  stats[0].textContent=visibleAdded.length;
  stats[1].textContent=updated.length;
  stats[2].textContent=addedEdges.length;

  const cards=document.getElementById('deltaCards');
  if(!visibleAdded.length){
    cards.innerHTML='<div class="delta-empty">今天没有新增核心实体；知识更新主要发生在已有节点或关系上。</div>';
    return;
  }
  cards.innerHTML=visibleAdded.slice(0,8).map(n=>
    '<a class="delta-card" href="'+entityHref(n)+'">'+
      '<div><span>'+n.type+'</span><b>'+escapeHtml(n.label)+'</b></div>'+
      '<p>'+escapeHtml(n.summary||'')+'</p>'+
      '<em>'+escapeHtml(n.maturity||'')+'</em>'+
    '</a>'
  ).join('');

  function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));}
})();