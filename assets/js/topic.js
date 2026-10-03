(() => {
  const nodes=JSON.parse(document.getElementById('topicNodes').textContent);
  const edges=JSON.parse(document.getElementById('topicEdges').textContent);
  const topic=JSON.parse(document.getElementById('topicId').textContent);
  const allowed=new Set(['Theme','Capability','Project','Research','Trend','Pattern','Standard']);
  const subset=nodes.filter(n=>(n.themes||[]).includes(topic)&&allowed.has(n.type));
  const ids=new Set(subset.map(n=>n.id));
  const rels=edges.filter(e=>ids.has(e.source)&&ids.has(e.target)&&!['PUBLISHED_BY','EVIDENCED_BY'].includes(e.type));
  const colors={Theme:'#17211d',Capability:'#2f8f68',Project:'#3273a8',Research:'#7b5bb5',Trend:'#c1742a',Pattern:'#b24e72',Standard:'#3c8f8a'};
  const byId=new Map(subset.map(n=>[n.id,n]));
  const base=document.body.dataset.baseurl||'';
  const entityHref=n=>base+(n?.page||('/graph/?focus='+encodeURIComponent(n?.id||'')));
  const panel=document.getElementById('topicMapDetail');
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));

  const cy=cytoscape({
    container:document.getElementById('topicMap'),
    elements:[
      ...subset.map(n=>({data:{...n,label:n.label}})),
      ...rels.map(e=>({data:{...e,label:e.type}}))
    ],
    minZoom:.35,maxZoom:2.2,wheelSensitivity:.18,
    style:[
      {selector:'node',style:{
        'background-color':e=>colors[e.data('type')]||'#809088','label':'data(label)','font-size':9,'color':'#26332d',
        'text-valign':'bottom','text-margin-y':6,'text-wrap':'wrap','text-max-width':90,'width':e=>e.data('type')==='Trend'?32:25,
        'height':e=>e.data('type')==='Trend'?32:25,'border-width':3,'border-color':'#fff'
      }},
      {selector:'edge',style:{'line-color':'#ced6d2','target-arrow-color':'#a7b1ac','target-arrow-shape':'triangle','curve-style':'bezier','width':1.2,'arrow-scale':.7,'opacity':.78}},
      {selector:'edge[kind = "analysis"]',style:{'line-style':'dashed','line-color':'#d3a26a','target-arrow-color':'#d3a26a'}},
      {selector:'.selected',style:{'border-color':'#17211d','border-width':4}}
    ],
    layout:{name:'cose',animate:false,nodeRepulsion:8000,idealEdgeLength:90,gravity:.2,numIter:1000,padding:28}
  });

  cy.on('tap','node',evt=>{
    const n=evt.target.data();
    cy.nodes().removeClass('selected'); evt.target.addClass('selected');
    const connected=rels.filter(e=>e.source===n.id||e.target===n.id);
    const relationHtml=connected.slice(0,10).map(e=>{
      const other=byId.get(e.source===n.id?e.target:e.source);
      if(!other)return '';
      return '<a href="'+entityHref(other)+'"><span>'+esc(e.type)+'</span><strong>'+esc(other.label)+'</strong></a>';
    }).join('');
    panel.innerHTML='<div class="eyebrow">'+esc(n.type)+'</div><h3>'+esc(n.label)+'</h3><p>'+esc(n.summary||'')+'</p>'+
      '<div class="topic-map-meta"><span>'+esc(n.maturity||'')+'</span><span>'+esc(n.first_seen||'')+'</span></div>'+
      (relationHtml?'<h4>Connected in this theme</h4><div class="topic-map-links">'+relationHtml+'</div>':'')+
      '<a class="topic-map-open" href="'+entityHref(n)+'">Open detail page →</a>';
  });

  if(cy.elements().length)cy.fit(cy.elements(),38);
})();