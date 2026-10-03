(() => {
  const parse = id => JSON.parse(document.getElementById(id).textContent);
  const nodes = parse('kgNodes');
  const edges = parse('kgEdges');
  const byId = new Map(nodes.map(n => [n.id, n]));
  const colors = {Theme:'#17211d',Capability:'#2f8f68',Project:'#3273a8',Research:'#7b5bb5',Trend:'#c1742a',Pattern:'#b24e72',Organization:'#67736d',Standard:'#3c8f8a',Event:'#a5ada9',Source:'#c0c7c3'};
  const elements = [
    ...nodes.map(n => ({data:{...n,label:n.label}})),
    ...edges.map(e => ({data:{...e,label:e.type}}))
  ];
  const cy = cytoscape({
    container: document.getElementById('kgCanvas'),
    elements,
    minZoom:0.2,maxZoom:2.4,wheelSensitivity:0.18,
    style:[
      {selector:'node',style:{
        'background-color':ele=>colors[ele.data('type')]||'#8b9590',
        'label':'data(label)','color':'#26332d','font-size':10,'text-wrap':'wrap','text-max-width':100,
        'text-valign':'bottom','text-margin-y':7,
        'width':ele=>ele.data('type')==='Theme'?42:ele.data('type')==='Trend'?34:26,
        'height':ele=>ele.data('type')==='Theme'?42:ele.data('type')==='Trend'?34:26,
        'border-width':3,'border-color':'#fff','overlay-opacity':0
      }},
      {selector:'node[type = "Source"], node[type = "Event"]',style:{'width':16,'height':16,'font-size':8}},
      {selector:'edge',style:{'width':1.25,'line-color':'#c9d1cd','target-arrow-color':'#a5b0aa','target-arrow-shape':'triangle','curve-style':'bezier','arrow-scale':0.75,'opacity':0.72}},
      {selector:'edge[kind = "analysis"]',style:{'line-style':'dashed','line-color':'#d2a46e','target-arrow-color':'#d2a46e'}},
      {selector:'.faded',style:{'opacity':0.08,'text-opacity':0.08}},
      {selector:'.focus',style:{'border-color':'#17211d','border-width':4,'z-index':999}}
    ],
    layout:{name:'cose',animate:false,randomize:true,nodeRepulsion:9000,idealEdgeLength:100,edgeElasticity:120,gravity:0.18,numIter:1200,padding:30}
  });

  const search=document.getElementById('kgSearch');
  const theme=document.getElementById('themeFilter');
  const type=document.getElementById('typeFilter');
  const relation=document.getElementById('relationFilter');
  const detail=document.getElementById('detailFilter');
  const panel=document.getElementById('kgDetail');
  const esc=s=>String(s??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[ch]));

  function renderNode(id){
    const n=byId.get(id); if(!n)return;
    const connected=edges.filter(e=>e.source===id||e.target===id);
    const rels=connected.slice(0,18).map(e=>{
      const otherId=e.source===id?e.target:e.source;
      const other=byId.get(otherId); if(!other)return '';
      const arrow=e.source===id?'→':'←';
      const kind=e.kind==='analysis'?'<em>analysis</em>':'';
      return '<button class="kg-rel" data-node="'+esc(other.id)+'"><span>'+esc(e.type)+' '+arrow+'</span><strong>'+esc(other.label)+'</strong>'+kind+'</button>';
    }).join('');
    const evidenceIds=[...new Set(connected.flatMap(e=>e.evidence||[]))];
    const evidence=evidenceIds.map(x=>byId.get(x)).filter(x=>x&&x.url).map(s=>'<a class="kg-source" href="'+esc(s.url)+'" target="_blank" rel="noopener">'+esc(s.label)+' ↗</a>').join('');
    panel.innerHTML='<div class="eyebrow">'+esc(n.type)+'</div><h2>'+esc(n.label)+'</h2><p>'+esc(n.summary||'')+'</p>'+
      '<div class="kg-meta"><span>'+esc(n.maturity||'n/a')+'</span><span>first seen '+esc(n.first_seen||'—')+'</span><span>verified '+esc(n.last_verified||'—')+'</span></div>'+
      (n.url?'<a href="'+esc(n.url)+'" target="_blank" rel="noopener">Primary link ↗</a>':'')+
      (rels?'<h3>Relationships</h3><div class="kg-rel-list">'+rels+'</div>':'')+
      (evidence?'<h3>Evidence</h3><div class="kg-sources">'+evidence+'</div>':'');
    panel.querySelectorAll('[data-node]').forEach(btn=>btn.addEventListener('click',()=>selectNode(btn.dataset.node)));
  }

  function selectNode(id){
    const node=cy.getElementById(id); if(!node.length)return;
    cy.elements().removeClass('focus'); node.addClass('focus'); renderNode(id);
    cy.animate({center:{eles:node},zoom:Math.max(cy.zoom(),1.05)},{duration:260});
  }

  function applyFilters(){
    const q=search.value.trim().toLowerCase(), themeId=theme.value, typeValue=type.value, relationValue=relation.value, showAll=detail.value==='all';
    cy.batch(()=>{
      cy.elements().removeClass('faded').style('display','element');
      cy.nodes().forEach(n=>{
        const d=n.data(), hay=((d.label||'')+' '+(d.summary||'')+' '+(d.id||'')).toLowerCase();
        const ok=(!q||hay.includes(q))&&(!themeId||(d.themes||[]).includes(themeId))&&(!typeValue||d.type===typeValue)&&(showAll||!['Source','Event'].includes(d.type));
        if(!ok)n.style('display','none');
      });
      cy.edges().forEach(e=>{
        const visible=e.source().style('display')!=='none'&&e.target().style('display')!=='none';
        if(!(visible&&(!relationValue||e.data('type')===relationValue)))e.style('display','none');
      });
    });
    const visible=cy.elements(':visible');
    if(visible.length)cy.fit(visible,48);
    document.getElementById('nodeCount').textContent=cy.nodes(':visible').length;
    document.getElementById('edgeCount').textContent=cy.edges(':visible').length;
  }

  [theme,type,relation,detail].forEach(el=>el.addEventListener('change',applyFilters));
  search.addEventListener('input',applyFilters);
  document.getElementById('fitGraph').addEventListener('click',()=>cy.fit(cy.elements(':visible'),48));
  document.getElementById('resetGraph').addEventListener('click',()=>{search.value='';theme.value='';type.value='';relation.value='';detail.value='core';applyFilters();});
  cy.on('tap','node',evt=>selectNode(evt.target.id()));
  cy.on('dbltap','node',evt=>{const n=evt.target;cy.elements().addClass('faded');n.closedNeighborhood().removeClass('faded');});
  cy.on('tap',evt=>{if(evt.target===cy)cy.elements().removeClass('faded focus');});

  const params=new URLSearchParams(location.search);
  if(params.get('theme'))theme.value=params.get('theme');
  if(params.get('q'))search.value=params.get('q');
  applyFilters();
  setTimeout(()=>selectNode('theme:agent-infrastructure'),250);
})();