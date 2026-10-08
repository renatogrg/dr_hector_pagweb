const toggle=document.querySelector('.menu-toggle');const nav=document.querySelector('#navigation');toggle?.addEventListener('click',()=>{const open=toggle.getAttribute('aria-expanded')!=='true';toggle.setAttribute('aria-expanded',String(open));nav.classList.toggle('open',open);toggle.setAttribute('aria-label',open?'Cerrar menú':'Abrir menú')});document.addEventListener('keydown',e=>{if(e.key==='Escape'){nav?.classList.remove('open');toggle?.setAttribute('aria-expanded','false')}});let message='';document.querySelector('#appointment-form')?.addEventListener('submit',e=>{e.preventDefault();const form=e.currentTarget;const values=new FormData(form);message=`Hola, soy ${String(values.get('name')).trim()}. Quisiera solicitar una consulta por: ${values.get('reason')}. Mi número de contacto es ${String(values.get('phone')).trim()}. ¿Podrían indicarme la disponibilidad?`;document.querySelector('#request-message').textContent=message;document.querySelector('#form-result').hidden=false;document.querySelector('#form-result').scrollIntoView({behavior:'smooth',block:'nearest'})});document.querySelector('#copy-message')?.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(message);document.querySelector('#copy-status').textContent='Mensaje copiado.'}catch{document.querySelector('#copy-status').textContent='Selecciona el texto para copiarlo manualmente.'}});

// Progressive enhancement: content remains readable without JavaScript.
(()=>{
 const reduce=window.matchMedia('(prefers-reduced-motion: reduce)');
 if(reduce.matches||!('IntersectionObserver' in window))return;
 const targets=[...document.querySelectorAll('.hero-copy,.hero-visual,.mast,.section-heading,.section > .eyebrow,.section > h2,.service-card,.doctor-text,.principles,.steps article,.faq-grid > div,.cta > div,.cta > a,.profile-photo,.profile-grid > div:last-child,.article > h2,.article > p,.treatment-stages article,.appointment-card,.guide-card,.contact-info,.contact-help,.form-card,.info-band')];
 let observer;
 const showAll=()=>{targets.forEach(el=>el.classList.add('reveal-visible'));observer?.disconnect()};
 try{
  observer=new IntersectionObserver(entries=>{entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('reveal-visible');observer.unobserve(entry.target)}})},{threshold:0,rootMargin:'0px 0px -35px 0px'});
  targets.forEach(el=>{const group=el.parentElement;const siblingIndex=[...group.children].indexOf(el);if(group.matches('.service-grid,.steps,.guide-grid'))el.style.setProperty('--reveal-delay',Math.min(siblingIndex*100,200)+'ms');el.classList.add('reveal-ready');observer.observe(el)});
  const onPreference=event=>{if(event.matches)showAll()};reduce.addEventListener?.('change',onPreference);
  document.addEventListener('focusin',event=>{targets.filter(el=>el.contains(event.target)).forEach(el=>el.classList.add('reveal-visible'))});
  window.addEventListener('beforeprint',showAll);
 }catch{showAll()}
})();
