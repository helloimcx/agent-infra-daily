(() => {
  const q=document.getElementById('entitySearch'), type=document.getElementById('entityType');
  const cards=[...document.querySelectorAll('.entity-directory-card')];
  function apply(){
    const term=q.value.trim().toLowerCase(), t=type.value;
    cards.forEach(c=>{const ok=(!term||c.dataset.search.includes(term))&&(!t||c.dataset.type===t);c.hidden=!ok;});
  }
  q.addEventListener('input',apply);type.addEventListener('change',apply);
})();