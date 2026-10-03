(() => {
  const nodes=JSON.parse(document.getElementById('stackNodes').textContent);
  const edges=JSON.parse(document.getElementById('stackEdges').textContent);
  const architecture=JSON.parse(document.getElementById('stackArchitecture').textContent);
  const byId=new Map(nodes.map(n=>[n.id,n]));
  const base=document.body.dataset.baseurl||'';
  const entityHref=n=>base+(n?.page||('/graph/?focus='+encodeURIComponent(n?.id||'')));
  const typeSel=document.getElementById('stackType'), evidenceSel=document.getElementById('stackEvidence');
  const core=new Set(['Capability','Project','Research','Pattern','Trend','Standard']);
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));

  function edgeStats(id){
    const rel=edges.filter(e=>e.source===id||e.target===id);
    const fact=rel.filter(e=>e.kind==='fact'&&(e.evidence||[]).length).length;
    const analysis=rel.filter(e=>e.kind==='analysis').length;
    const sources=[...new Set(rel.flatMap(e=>e.evidence||[]))].map(x=>byId.get(x)).filter(n=>n?.url);
    return {rel,fact,analysis,sources};
  }
  function layerMembership(id){return architecture.layers.filter(l=>l.members.includes(id));}
  function passes(n){
    if(typeSel.value&&n.type!==typeSel.value)return false;
    const s=edgeStats(n.id);
    if(evidenceSel.value==='fact'&&!s.fact)return false;
    if(evidenceSel.value==='analysis'&&!s.analysis)return false;
    return true;
  }
  function render(){
    const host=document.getElementById('stackLayers');
    host.innerHTML=architecture.layers.sort((a,b)=>a.order-b.order).map((l,i)=>{
      const members=l.members.map(id=>byId.get(id)).filter(n=>n&&core.has(n.type)&&passes(n));
      return '<section class="stack-layer"><div class="stack-layer-label"><span>0'+(i+1)+'</span><h2>'+esc(l.label)+'</h2><p>'+esc(l.description)+'</p></div><div class="stack-layer-entities">'+
        (members.length?members.map(n=>'<button data-stack-node="'+esc(n.id)+'"><span>'+esc(n.type)+'</span><strong>'+esc(n.label)+'</strong><em>'+esc(n.maturity||'')+'</em></button>').join(''):'<div class="stack-empty">No entities under current filters</div>')+
      '</div></section>';
    }).join('');
    host.querySelectorAll('[data-stack-node]').forEach(b=>b.addEventListener('click',()=>show(b.dataset.stackNode)));
    renderCoverage();
  }
  function show(id){
    const n=byId.get(id), layers=layerMembership(id), s=edgeStats(id); if(!n)return;
    document.getElementById('stackDetail').innerHTML='<div class="eyebrow">'+esc(n.type)+'</div><h2>'+esc(n.label)+'</h2><p>'+esc(n.summary||'')+'</p>'+
      '<div class="stack-detail-meta"><span>'+esc(n.maturity||'n/a')+'</span><span>'+s.fact+' fact-backed relations</span><span>'+s.analysis+' analysis relations</span></div>'+
      '<h3>Architecture layers</h3><div class="stack-layer-tags">'+layers.map(l=>'<span>'+esc(l.label)+'</span>').join('')+'</div>'+
      '<h3>Evidence</h3><div class="stack-sources">'+(s.sources.length?s.sources.slice(0,8).map(x=>'<a href="'+esc(x.url)+'" target="_blank" rel="noopener">'+esc(x.label)+' ↗</a>').join(''):'<span>No direct source attached to current relations.</span>')+'</div>'+
      '<div class="stack-detail-actions"><a href="'+entityHref(n)+'">Open detail →</a><a href="../graph/?focus='+encodeURIComponent(id)+'">Graph →</a>'+(['Project','Research','Standard','Pattern'].includes(n.type)?'<a href="../compare/?a='+encodeURIComponent(id)+'">Compare →</a>':'')+'</div>';
  }
  function renderCoverage(){
    const projects=nodes.filter(n=>n.type==='Project');
    const rows=projects.map(p=>({p,layers:layerMembership(p.id)})).filter(x=>x.layers.length).sort((a,b)=>b.layers.length-a.layers.length||a.p.label.localeCompare(b.p.label));
    document.getElementById('stackCoverage').innerHTML='<div class="coverage-head"><span>Project</span>'+architecture.layers.map(l=>'<span>'+esc(l.label.replace(/ & .*/,''))+'</span>').join('')+'</div>'+
      rows.map(x=>'<a class="coverage-row" href="'+entityHref(x.p)+'"><strong>'+esc(x.p.label)+'</strong>'+architecture.layers.map(l=>'<span class="'+(x.layers.some(y=>y.id===l.id)?'covered':'')+'">'+(x.layers.some(y=>y.id===l.id)?'●':'—')+'</span>').join('')+'</a>').join('');
  }
  typeSel.addEventListener('change',render);evidenceSel.addEventListener('change',render);
  document.getElementById('stackReset').addEventListener('click',()=>{typeSel.value='';evidenceSel.value='';render();});
  render();
})();