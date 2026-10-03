(() => {
  const id=JSON.parse(document.getElementById('entityNodeId').textContent);
  const nodes=JSON.parse(document.getElementById('entityNodes').textContent);
  const edges=JSON.parse(document.getElementById('entityEdges').textContent);
  const architecture=JSON.parse(document.getElementById('entityArchitectureData').textContent);
  const byId=new Map(nodes.map(n=>[n.id,n]));
  const root=byId.get(id);
  const relatedEdges=edges.filter(e=>e.source===id||e.target===id);
  const factCount=relatedEdges.filter(e=>e.kind==='fact').length;
  const analysisCount=relatedEdges.filter(e=>e.kind==='analysis'||e.kind==='hypothesis').length;
  const otherId=e=>e.source===id?e.target:e.source;
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
  const base=document.body.dataset.baseurl||'';
  const href=n=>base+(n.page||('/graph/?focus='+encodeURIComponent(n.id)));

  const evidenceIds=new Set();
  relatedEdges.forEach(e=>(e.evidence||[]).forEach(x=>evidenceIds.add(x)));
  relatedEdges.forEach(e=>{const n=byId.get(otherId(e));if(n?.type==='Source')evidenceIds.add(n.id);});
  if(root.type==='Source')evidenceIds.add(root.id);
  const evidence=[...evidenceIds].map(x=>byId.get(x)).filter(Boolean);
  const topStats=document.getElementById('entityTopStats');
  if(topStats)topStats.innerHTML='<span>'+evidence.length+' sources</span><span>'+factCount+' facts</span><span>'+analysisCount+' analyses</span>';

  const layers=architecture.layers.filter(l=>l.members.includes(id));
  const related=relatedEdges.map(e=>({edge:e,node:byId.get(otherId(e))})).filter(x=>x.node&& !['Source','Event'].includes(x.node.type));
  const grouped=new Map();
  related.forEach(x=>{const k=x.node.type;if(!grouped.has(k))grouped.set(k,[]);grouped.get(k).push(x);});
  const context=document.getElementById('entityContext');
  const layerHtml='<div class="context-block"><h3>Architecture</h3><div class="context-links">'+
    (layers.length?layers.map(l=>'<a href="'+base+'/stack/"><b>'+esc(l.label)+'</b><span>Layer '+String(l.order).padStart(2,'0')+'</span></a>').join(''):'<div class="context-empty">No architecture layer assigned yet.</div>')+
    '</div></div>';
  const preferred=['Capability','Project','Research','Pattern','Trend','Standard','Organization'];
  const relHtml='<div class="context-block"><h3>Related knowledge</h3><div class="context-links">'+
    preferred.flatMap(t=>(grouped.get(t)||[]).slice(0,3)).slice(0,10).map(x=>'<a href="'+href(x.node)+'"><b>'+esc(x.node.label)+'</b><span>'+esc(x.edge.type)+' · '+esc(x.edge.kind)+'</span></a>').join('')+
    (!related.length?'<div class="context-empty">No explicit relations yet.</div>':'')+'</div></div>';
  context.innerHTML=layerHtml+relHtml;

  const events=[];
  relatedEdges.forEach(e=>{const n=byId.get(otherId(e));if(n?.type==='Event')events.push(n);});
  if(root.type==='Event')events.push(root);
  const unique=[...new Map(events.map(n=>[n.id,n])).values()].sort((a,b)=>a.first_seen.localeCompare(b.first_seen));
  const timeline=[{date:root.first_seen,label:'First seen in knowledge base',summary:root.summary}].concat(unique.filter(n=>n.id!==root.id).map(n=>({date:n.first_seen,label:n.label,summary:n.summary,page:n.page}))).sort((a,b)=>a.date.localeCompare(b.date));
  document.getElementById('entityTimeline').innerHTML=timeline.map(x=>'<div class="entity-time-row"><time>'+esc(x.date)+'</time><i></i><div>'+(x.page?'<a href="'+base+x.page+'">'+esc(x.label)+'</a>':'<strong>'+esc(x.label)+'</strong>')+'<p>'+esc(x.summary||'')+'</p></div></div>').join('');

  document.getElementById('entityEvidence').innerHTML=evidence.length?evidence.map(s=>'<article><div><span>'+esc(s.type)+'</span><strong>'+esc(s.label)+'</strong><p>'+esc(s.intro||s.summary||'')+'</p></div>'+(s.url?'<a href="'+esc(s.url)+'" target="_blank" rel="noopener">Primary source ↗</a>':'')+'</article>').join(''):'<div class="context-empty">No independent primary source attached yet.</div>';

  let cy=null;
  function initGraph(){
    if(cy)return;
    const localIds=new Set([id]);relatedEdges.forEach(e=>localIds.add(otherId(e)));
    const localNodes=nodes.filter(n=>localIds.has(n.id));
    const localEdges=edges.filter(e=>localIds.has(e.source)&&localIds.has(e.target));
    const colors={Theme:'#17211d',Capability:'#2f8f68',Project:'#3273a8',Research:'#7b5bb5',Trend:'#c1742a',Pattern:'#b24e72',Organization:'#67736d',Standard:'#3c8f8a',Event:'#a5ada9',Source:'#c0c7c3'};
    cy=cytoscape({
      container:document.getElementById('entityGraph'),
      elements:[...localNodes.map(n=>({data:{...n,label:n.label}})),...localEdges.map(e=>({data:{...e,label:e.type}}))],
      minZoom:.4,maxZoom:2.4,wheelSensitivity:.18,
      style:[
        {selector:'node',style:{'background-color':e=>colors[e.data('type')]||'#89958f','label':'data(label)','font-size':9,'color':'#26332d','text-valign':'bottom','text-margin-y':6,'text-wrap':'wrap','text-max-width':90,'width':25,'height':25,'border-width':3,'border-color':'#fff'}},
        {selector:'node[id = "'+id.replace(/"/g,'\\"')+'"]',style:{'width':38,'height':38,'border-color':'#17211d','border-width':4,'font-size':11}},
        {selector:'edge',style:{'line-color':'#cdd5d1','target-arrow-color':'#aab4af','target-arrow-shape':'triangle','curve-style':'bezier','width':1.1,'arrow-scale':.7}},
        {selector:'edge[kind = "analysis"]',style:{'line-style':'dashed','line-color':'#d2a46e','target-arrow-color':'#d2a46e'}}
      ],
      layout:{name:'cose',animate:false,nodeRepulsion:6500,idealEdgeLength:80,gravity:.25,numIter:800,padding:24}
    });
    cy.on('tap','node',evt=>{
      const n=evt.target.data();
      const conn=localEdges.filter(e=>e.source===n.id||e.target===n.id);
      document.getElementById('entityGraphDetail').innerHTML='<div class="article-label">'+esc(n.type)+'</div><h3>'+esc(n.label)+'</h3><p>'+esc(n.summary||'')+'</p><div class="context-links">'+conn.slice(0,7).map(e=>{const o=byId.get(e.source===n.id?e.target:e.source);return o?'<a href="'+href(o)+'"><b>'+esc(o.label)+'</b><span>'+esc(e.type)+'</span></a>':'';}).join('')+'</div>';
    });
    cy.fit(cy.elements(),32);
  }
  const details=document.getElementById('localGraphDetails');
  if(details)details.addEventListener('toggle',()=>{if(details.open)setTimeout(initGraph,20);});
})();