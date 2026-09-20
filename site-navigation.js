(() => {
 const header=document.querySelector('.site-header'),menu=document.querySelector('.site-menu-toggle'),theme=document.querySelector('.site-theme');
 if(!header)return;
 const setMenu=open=>{header.classList.toggle('menu-open',open);menu.setAttribute('aria-expanded',String(open));};
 menu.addEventListener('click',()=>setMenu(menu.getAttribute('aria-expanded')!=='true'));
 header.addEventListener('keydown',e=>{if(e.key==='Escape'){setMenu(false);menu.focus();}});
 document.addEventListener('click',e=>{if(!header.contains(e.target))setMenu(false);});
 header.querySelectorAll('nav a').forEach(a=>a.addEventListener('click',()=>setMenu(false)));
 const apply=value=>{document.documentElement.dataset.theme=value;theme.setAttribute('aria-label',`Switch to ${value==='dark'?'light':'dark'} theme`);};
 let saved;try{saved=localStorage.getItem('ewf-site-theme');}catch{}
 apply(saved==='dark'||saved==='light'?saved:matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
 theme.addEventListener('click',()=>{const value=document.documentElement.dataset.theme==='dark'?'light':'dark';apply(value);try{localStorage.setItem('ewf-site-theme',value);}catch{}});
})();
