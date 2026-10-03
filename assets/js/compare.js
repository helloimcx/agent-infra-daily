(() => {
  const nodes=JSON.parse(document.getElementById('compareNodes').textContent);
  const edges=JSON.parse(document.getElementById('compareEdges').textContent);
  const topics=JSON.parse(document.getElementById('compareTopics').textContent);
  const byId=new Map(nodes.map(n=>[n.id,n]));
  const topicById=new Map(topics.map(t=>[t.id,t]));
  const base=document.body.dataset.baseurl||'';
  const entityHref=n=>base+(n?.page||('/graph/?focus='+encodeURIComponent(n?.id||'')));
  const comparable=nodes.filter(n=>['Project','Research','Standard','Pattern'].includes(n.type)).sort((a,b)=>a.label.localeCompare(b.label));
  const aSel=document.getElementById('compareA'),bSel=document.getElementById('compareB');
  const capTypes=new Set(['IMPLEMENTS','PROVIDES','USES','DEPENDS_ON','ENABLES']);
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));

  function fill(sel){sel.innerHTML=comparable.map(n=>'<option value="'+esc(n.id)+'">'+esc(n.label)+' · '+esc(n.type)+'</option>').join('');}
  fill(aSel);fill(bSel);

  function linksFor(id){
    const out=new Map();
    edges.forEach(e=>{
      if(!capTypes.has(e.type))return;
      let other=null;
      if(e.source===id&&byId.get(e.target)?.type==='Capability')other=byId.get(e.target);
      if(e.target===id&&byId.get(e.source)?.type==='Capability')other=byId.get(e.source);
      if(!other)return;
      const prev=out.get(other.id);
      if(!prev||prev.edge.kind!=='fact'&&e.kind==='fact')out.set(other.id,{cap:other,edge:e});
    });
    return out;
  }
  function evidenceFor(edge){
    return (edge.evidence||[]).map(id=>byId.get(id)).filter(n=>n?.url);
  }
  function entityCard(n,map){
    const fact=[...map.values()].filter(x=>x.edge.kind==='fact').length;
    const analysis=[...map.values()].filter(x=>x.edge.kind==='analysis').length;
    const themeNames=(n.themes||[]).map(id=>topicById.get(id)?.label).filter(Boolean);
    return '<article><div class="eyebrow">'+esc(n.type)+'</div><h2>'+esc(n.label)+'</h2><p>'+esc(n.summary||'')+'</p>'+
      '<div class="compare-meta"><span>'+esc(n.maturity||'n/a')+'</span><span>'+esc(n.first_seen||'—')+'</span><span>'+map.size+' capability links</span><span>'+fact+' fact / '+analysis+' analysis</span></div>'+
      '<div class="compare-themes">'+themeNames.map(x=>'<span>'+esc(x)+'</span>').join('')+'</div>'+
      '<a href="'+entityHref(n)+'">Open detail page →</a></article>';
  }
  function mark(item){
    if(!item)return '<span class="matrix-none">—</span>';
    const cls=item.edge.kind==='fact'?'matrix-fact':'matrix-analysis';
    return '<span class="'+cls+'" title="'+esc(item.edge.type)+' · confidence '+esc(item.edge.confidence)+'">'+(item.edge.kind==='fact'?'●':'◐')+' '+esc(item.edge.type)+'</span>';
  }
  function render(){
    const a=byId.get(aSel.value),b=byId.get(bSel.value); if(!a||!b)return;
    const am=linksFor(a.id), bm=linksFor(b.id);
    document.getElementById('compareSummary').innerHTML=entityCard(a,am)+entityCard(b,bm);
    const capIds=[...new Set([...am.keys(),...bm.keys()])].sort((x,y)=>byId.get(x).label.localeCompare(byId.get(y).label));
    const table=document.getElementById('compareTable');
    table.innerHTML='<thead><tr><th>Capability</th><th>'+esc(a.label)+'</th><th>'+esc(b.label)+'</th></tr></thead><tbody>'+
      (capIds.length?capIds.map(id=>'<tr><td><a href="../graph/?focus='+encodeURIComponent(id)+'">'+esc(byId.get(id).label)+'</a></td><td>'+mark(am.get(id))+'</td><td>'+mark(bm.get(id))+'</td></tr>').join(''):'<tr><td colspan="3">当前图谱没有显式 Capability 关系。</td></tr>')+'</tbody>';
    const common=capIds.filter(id=>am.has(id)&&bm.has(id));
    document.getElementById('commonCaps').innerHTML=common.length?common.map(id=>'<a href="../graph/?focus='+encodeURIComponent(id)+'"><strong>'+esc(byId.get(id).label)+'</strong><span>'+esc(am.get(id).edge.type)+' / '+esc(bm.get(id).edge.type)+'</span></a>').join(''):'<div class="topic-empty">当前没有显式共同能力。</div>';
    const aOnly=capIds.filter(id=>am.has(id)&&!bm.has(id)),bOnly=capIds.filter(id=>bm.has(id)&&!am.has(id));
    document.getElementById('distinctCaps').innerHTML='<div class="distinct-col"><b>'+esc(a.label)+'</b>'+(aOnly.length?aOnly.map(id=>'<span>'+esc(byId.get(id).label)+'</span>').join(''):'<em>none</em>')+'</div><div class="distinct-col"><b>'+esc(b.label)+'</b>'+(bOnly.length?bOnly.map(id=>'<span>'+esc(byId.get(id).label)+'</span>').join(''):'<em>none</em>')+'</div>';
    const related=[...am.values(),...bm.values()];
    const evidence=[];
    related.forEach(x=>evidenceFor(x.edge).forEach(s=>evidence.push({source:s,edge:x.edge,cap:x.cap})));
    const seen=new Set();
    document.getElementById('compareEvidence').innerHTML=evidence.length?evidence.filter(x=>{const k=x.source.id+'|'+x.edge.id;if(seen.has(k))return false;seen.add(k);return true;}).map(x=>
      '<a class="compare-evidence-row" href="'+esc(x.source.url)+'" target="_blank" rel="noopener"><div><span>'+esc(x.edge.kind)+' · '+esc(x.edge.type)+' · confidence '+esc(x.edge.confidence)+'</span><strong>'+esc(x.cap.label)+'</strong></div><p>'+esc(x.source.label)+'</p><b>↗</b></a>'
    ).join(''):'<div class="topic-empty">当前能力关系没有可展示的一手来源。</div>';
    const url=new URL(location.href);url.searchParams.set('a',a.id);url.searchParams.set('b',b.id);history.replaceState(null,'',url);
  }
  const params=new URLSearchParams(location.search);
  const defaultA=comparable.find(n=>n.id==='project:docker-sandbox-kit')||comparable[0];
  const defaultB=comparable.find(n=>n.id==='project:docker-cloud-sandboxes')||comparable[1]||comparable[0];
  aSel.value=byId.has(params.get('a'))?params.get('a'):defaultA?.id;
  bSel.value=byId.has(params.get('b'))?params.get('b'):defaultB?.id;
  aSel.addEventListener('change',render);bSel.addEventListener('change',render);
  document.getElementById('swapCompare').addEventListener('click',()=>{const x=aSel.value;aSel.value=bSel.value;bSel.value=x;render();});
  render();
})();