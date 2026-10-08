// Progressive enhancement: content and links exist before this script.
const mobileMenu=document.querySelector('.mobile-navigation');
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&mobileMenu?.open){mobileMenu.open=false;mobileMenu.querySelector('summary').focus()}});
const motion=window.matchMedia('(prefers-reduced-motion: reduce)');
if(!motion.matches&&'IntersectionObserver' in window){
 const observer=new IntersectionObserver(entries=>{for(const entry of entries)if(entry.isIntersecting){entry.target.classList.add('reveal-visible');observer.unobserve(entry.target)}},{threshold:.05});
 document.querySelectorAll('.service-card,.steps article,.mast,.guide-card,.contact-grid,.profile-grid,.section-heading').forEach(el=>observer.observe(el));
}
// Closed event allowlist. No form values, medical topics or queried URLs.
const accept=document.querySelector('#analytics-accept');
const decline=document.querySelector('#analytics-decline');
const status=document.querySelector('#analytics-status');
let analyticsAllowed=false;
accept?.addEventListener('click',()=>{
 if(analyticsAllowed)return;
 analyticsAllowed=true;
 const id=accept.dataset.id;
 window['ga-disable-'+id]=false;
 window.dataLayer=window.dataLayer||[];
 window.gtag=function(){window.dataLayer.push(arguments)};
 window.gtag('consent','default',{analytics_storage:'granted',ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied'});
 window.gtag('js',new Date());
 window.gtag('config',id,{send_page_view:false,allow_google_signals:false,allow_ad_personalization_signals:false,page_location:document.querySelector('link[rel=canonical]').href.split('/').slice(0,3).join('/')+'/',page_referrer:'',page_title:'Sitio médico'});
 if(!document.querySelector('#ga-script')){const script=document.createElement('script');script.id='ga-script';script.async=true;script.src='https://www.googletagmanager.com/gtag/js?id='+encodeURIComponent(id);document.head.append(script)}
 status.textContent='Medición de clics activada durante esta visita.';
});
decline?.addEventListener('click',()=>{analyticsAllowed=false;if(accept)window['ga-disable-'+accept.dataset.id]=true;window.gtag?.('consent','update',{analytics_storage:'denied'});status.textContent='Medición desactivada.'});
function track(name){if(analyticsAllowed&&['call_click','whatsapp_click','appointment_request'].includes(name))window.gtag('event',name,{transport_type:'beacon'})}
document.querySelectorAll('[data-event]').forEach(link=>link.addEventListener('click',()=>track(link.dataset.event)));
document.querySelector('#appointment-form')?.addEventListener('submit',event=>{event.preventDefault();const button=event.currentTarget.querySelector('[data-whatsapp]');track('appointment_request');window.location.href='https://wa.me/'+button.dataset.whatsapp+'?text='+encodeURIComponent('Hola. Quisiera consultar disponibilidad para una cita.')});
