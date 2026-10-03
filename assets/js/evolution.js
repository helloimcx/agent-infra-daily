(() => {
  const parse=id=>JSON.parse(document.getElementById(id).textContent);
  const nodes=parse('evoNodes'), edges=parse('evoEdges'), topics=parse('evoTopics'), deltas=parse('evoDeltas');
  const coreTypes=new Set(['Project','Capability','Research','Trend','Pattern','Standard']);
  const byId=new Map(nodes.map(n=>[n.id,n]));
  const base=document.body.dataset.baseurl||'';
  const entityHref=n=>base+(n?.page||('/graph/?focus='+encodeURIComponent(n?.id||'')));
  const theme=document.getElementById('evoTheme'), type=document.getElementById('evoType'), view=document.getElementById('evoView');
  const timeline=document.getElementById('evoTimeline'), axis=document.getElementById('evoAxis'), growth=document.getElementById('evoGrowth');
  const eventView=document.getElementById('evoEventView'), growthView=document.getElementById('evoGrowthView');

  const allDates=[...new Set(nodes.map(n=>n.first_seen).filter(Boolean))].sort();
  document.getElementById('evoDates').textContent=allDates.length;
  document.getElementById('evoEvents').textContent=nodes.filter(n=>n.type==='Event').length;
  document.getElementById('evoEntities').textContent=nodes.filter(n=>coreTypes.has(n.type)).length;
  document.getElementById('evoRelations').textContent=edges.length;

  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
  const match=n=>(!theme.value||(n.themes||[]).includes(theme.value))&&(!type.value||n.type===type.value);

  function relatedCoreForEvent(event){
    const ids=new Set();
    edges.forEach(e=>{
      if(e.source===event.id&&e.target)ids.add(e.target);
      if(e.target===event.id&&e.source)ids.add(e.source);
    });
    return [...ids].map(id=>byId.get(id)).filter(n=>n&&coreTypes.has(n.type));
  }

  function renderEvents(){
    const events=nodes.filter(n=>n.type==='Event'&&match(n)).sort((a,b)=>a.first_seen.localeCompare(b.first_seen));
    const groups=new Map();
    events.forEach(e=>{if(!groups.has(e.first_seen))groups.set(e.first_seen,[]);groups.get(e.first_seen).push(e);});
    axis.innerHTML=[...groups.keys()].map(d=>'<button data-date="'+d+'"><span></span><b>'+d.slice(5)+'</b></button>').join('');
    timeline.innerHTML=[...groups.entries()].map(([date,items])=>{
      const cards=items.map(ev=>{
        const linked=relatedCoreForEvent(ev);
        const target=linked[0]||ev;
        const chips=linked.slice(0,3).map(n=>'<span>'+esc(n.label)+'</span>').join('');
        return '<a class="evo-event" href="'+entityHref(target)+'">'+
          '<div class="evo-event-type">'+esc((ev.themes||[])[0]||'event')+'</div>'+
          '<h3>'+esc(ev.label)+'</h3><p>'+esc(ev.summary||'')+'</p>'+
          (chips?'<div class="evo-chips">'+chips+'</div>':'')+
        '</a>';
      }).join('');
      return '<article class="evo-day" id="date-'+date+'"><time>'+date+'</time><div class="evo-day-line"><i></i></div><div class="evo-day-events">'+cards+'</div></article>';
    }).join('')||'<div class="evo-empty">当前过滤条件下没有事件。</div>';
    axis.querySelectorAll('[data-date]').forEach(btn=>btn.addEventListener('click',()=>document.getElementById('date-'+btn.dataset.date)?.scrollIntoView({behavior:'smooth',block:'center'})));
  }

  function renderGrowth(){
    const filtered=nodes.filter(n=>coreTypes.has(n.type)&&match(n));
    const counts=new Map();
    filtered.forEach(n=>counts.set(n.first_seen,(counts.get(n.first_seen)||0)+1));
    const entries=[...counts.entries()].sort((a,b)=>a[0].localeCompare(b[0]));
    const max=Math.max(1,...entries.map(x=>x[1]));
    growth.innerHTML=entries.map(([date,count])=>{
      const labels=filtered.filter(n=>n.first_seen===date).slice(0,5).map(n=>n.label).join(' · ');
      return '<div class="growth-row"><time>'+date+'</time><div class="growth-track"><div class="growth-bar" style="width:'+Math.max(6,(count/max)*100)+'%"><span>'+count+'</span></div></div><p>'+esc(labels)+'</p></div>';
    }).join('')||'<div class="evo-empty">当前过滤条件下没有数据。</div>';
  }

  function render(){renderEvents();renderGrowth();}
  [theme,type].forEach(el=>el.addEventListener('change',render));
  view.addEventListener('change',()=>{
    const isGrowth=view.value==='growth';
    eventView.hidden=isGrowth;growthView.hidden=!isGrowth;
  });
  document.getElementById('evoReset').addEventListener('click',()=>{theme.value='';type.value='';view.value='events';eventView.hidden=false;growthView.hidden=true;render();});
  const params=new URLSearchParams(location.search);
  if(params.get('theme'))theme.value=params.get('theme');
  if(params.get('type'))type.value=params.get('type');
  render();
})();