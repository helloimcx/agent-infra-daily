(() => {
  const id=JSON.parse(document.getElementById('entityNodeId').textContent);
  const nodes=JSON.parse(document.getElementById('entityNodes').textContent);
  const edges=JSON.parse(document.getElementById('entityEdges').textContent);
  const architecture=JSON.parse(document.getElementById('entityArchitectureData').textContent);
  const byId=new Map(nodes.map(n=>[n.id,n]));
  const root=byId.get(id);
  const relatedEdges=edges.filter(e=>e.source===id||e.target===id);
  const otherId=e=>e.source===id?e.target:e.source;
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
  const base=document.body.dataset.baseurl||'';
  const href=n=>base+(n.page||('/graph/?focus='+encodeURIComponent(n.id)));

  function relationRows(kind){
    const rows=relatedEdges.filter(e=>e.kind===kind).map(e=>({e,n:byId.get(otherId(e))})).filter(x=>x.n);
    return rows.length?rows.map(({e,n})=>'<a href="'+href(n)+'"><div><span>'+esc(e.type)+' · confidence '+esc(e.confidence)+'</span><strong>'+esc(n.label)+'</strong></div><p>'+esc(n.summary||'')+'</p><b>→</b></a>').join(''):'<div class="topic-empty">当前没有 '+kind+' 关系。</div>';
  }
  document.getElementById('entityFacts').innerHTML=relationRows('fact');
  document.getElementById('entityAnalysis').innerHTML=relationRows('analysis')+(relatedEdges.some(e=>e.kind==='hypothesis')?relationRows('hypothesis'):'');

  const layers=architecture.layers.filter(l=>l.members.includes(id));
  document.getElementById('entityArchitecture').innerHTML=layers.length?layers.map(l=>'<a href="'+base+'/stack/"><span>Layer '+String(l.order).padStart(2,'0')+'</span><strong>'+esc(l.label)+'</strong><p>'+esc(l.description)+'</p></a>').join(''):'<div class="topic-empty">当前 Architecture Stack 没有为该节点建立分析层归属。这不代表它不属于任何架构层，只表示尚未形成足够明确的分析判断。</div>';

  const eventNodes=[];
  relatedEdges.forEach(e=>{
    const n=byId.get(otherId(e));
    if(n?.type==='Event')eventNodes.push(n);
  });
  if(root.type==='Event')eventNodes.push(root);
  const uniqueEvents=[...new Map(eventNodes.map(n=>[n.id,n])).values()].sort((a,b)=>a.first_seen.localeCompare(b.first_seen));
  const timeline=[{date:root.first_seen,label:'First seen in knowledge base',summary:root.summary,type:'entity'}].concat(uniqueEvents.filter(n=>n.id!==root.id).map(n=>({date:n.first_seen,label:n.label,summary:n.summary,type:'event',page:n.page}))).sort((a,b)=>a.date.localeCompare(b.date));
  document.getElementById('entityTimeline').innerHTML=timeline.map(x=>'<div class="entity-time-row"><time>'+esc(x.date)+'</time><i></i><div>'+(x.page?'<a href="'+base+x.page+'">'+esc(x.label)+'</a>':'<strong>'+esc(x.label)+'</strong>')+'<p>'+esc(x.summary||'')+'</p></div></div>').join('');

  const evidenceIds=new Set();
  relatedEdges.forEach(e=>(e.evidence||[]).forEach(x=>evidenceIds.add(x)));
  relatedEdges.forEach(e=>{
    const n=byId.get(otherId(e));
    if(n?.type==='Source')evidenceIds.add(n.id);
  });
  if(root.type==='Source')evidenceIds.add(root.id);
  const ev=[...evidenceIds].map(x=>byId.get(x)).filter(Boolean);
  document.getElementById('entityEvidence').innerHTML=ev.length?ev.map(s=>'<article><div><span>'+esc(s.type)+'</span><strong>'+esc(s.label)+'</strong><p>'+esc(s.summary||'')+'</p></div>'+(s.url?'<a href="'+esc(s.url)+'" target="_blank" rel="noopener">Open primary source ↗</a>':'')+'</article>').join(''):'<div class="topic-empty">当前没有独立 Source 节点。该节点可能是分类/分析节点，或证据仍需补充。</div>';

  const localIds=new Set([id]);
  relatedEdges.forEach(e=>localIds.add(otherId(e)));
  const localNodes=nodes.filter(n=>localIds.has(n.id));
  const localEdges=edges.filter(e=>localIds.has(e.source)&&localIds.has(e.target));
  const colors={Theme:'#17211d',Capability:'#2f8f68',Project:'#3273a8',Research:'#7b5bb5',Trend:'#c1742a',Pattern:'#b24e72',Organization:'#67736d',Standard:'#3c8f8a',Event:'#a5ada9',Source:'#c0c7c3'};
  const cy=cytoscape({
    container:document.getElementById('entityGraph'),
    elements:[...localNodes.map(n=>({data:{...n,label:n.label}})),...localEdges.map(e=>({data:{...e,label:e.type}}))],
    minZoom:.4,maxZoom:2.4,wheelSensitivity:.18,
    style:[
      {selector:'node',style:{'background-color':e=>colors[e.data('type')]||'#89958f','label':'data(label)','font-size':9,'color':'#26332d','text-valign':'bottom','text-margin-y':6,'text-wrap':'wrap','text-max-width':90,'width':26,'height':26,'border-width':3,'border-color':'#fff'}},
      {selector:'node[id = "'+id.replace(/"/g,'\\"')+'"]',style:{'width':40,'height':40,'border-color':'#17211d','border-width':4,'font-size':11}},
      {selector:'edge',style:{'line-color':'#cdd5d1','target-arrow-color':'#aab4af','target-arrow-shape':'triangle','curve-style':'bezier','width':1.2,'arrow-scale':.7}},
      {selector:'edge[kind = "analysis"]',style:{'line-style':'dashed','line-color':'#d2a46e','target-arrow-color':'#d2a46e'}}
    ],
    layout:{name:'cose',animate:false,nodeRepulsion:7000,idealEdgeLength:85,gravity:.25,numIter:900,padding:24}
  });
  cy.on('tap','node',evt=>{
    const n=evt.target.data();
    const conn=localEdges.filter(e=>e.source===n.id||e.target===n.id);
    document.getElementById('entityGraphDetail').innerHTML='<div class="eyebrow">'+esc(n.type)+'</div><h3>'+esc(n.label)+'</h3><p>'+esc(n.summary||'')+'</p><div class="entity-local-links">'+conn.slice(0,8).map(e=>{const o=byId.get(e.source===n.id?e.target:e.source);return o?'<a href="'+href(o)+'"><span>'+esc(e.type)+'</span><strong>'+esc(o.label)+'</strong></a>':'';}).join('')+'</div><a class="entity-detail-open" href="'+href(n)+'">Open detail page →</a>';
  });
  if(cy.elements().length)cy.fit(cy.elements(),36);
})();