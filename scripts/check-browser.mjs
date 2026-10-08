import { createRequire } from 'node:module';
import { readFileSync, mkdirSync, writeFileSync, existsSync, statSync } from 'node:fs';
import path from 'node:path';
const require=createRequire(import.meta.url);
const packages=process.env.BROWSER_NODE_MODULES;
const {chromium}=packages?require(packages+'/playwright'):require('playwright');
mkdirSync('validation',{recursive:true});
// Serve the built bytes via Playwright interception to work in restricted networks.
// Real HTTP statuses are independently tested by check-http.mjs.
async function routeFiles(context){
 await context.route('**/*',async route=>{
  const url=new URL(route.request().url());
  if(url.hostname!=='127.0.0.1')throw new Error('Solicitud externa no esperada: '+url.origin);
  let file=path.resolve('dist','.'+decodeURIComponent(url.pathname.replace('/dr_hector_pagweb','')));
  if(existsSync(file)&&statSync(file).isDirectory())file=path.join(file,'index.html');
  const mime={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.webp':'image/webp'};
  await route.fulfill({status:existsSync(file)?200:404,contentType:mime[path.extname(file)]||'application/octet-stream',body:existsSync(file)?readFileSync(file):'No encontrado'});
 });
}
let browser;
try{
 browser=await chromium.launch({headless:true,channel:process.env.BROWSER_CHANNEL||'chrome'});
 const routes=['','doctor/','tratamientos/','vesicula/','hernias/','laparoscopia/','guia-del-paciente/','preguntas-frecuentes/','articulos/','contacto/'];
 const results=[];
 for(const javaScriptEnabled of [true,false])for(const viewport of [{width:390,height:844},{width:1440,height:1000}]){
  const context=await browser.newContext({javaScriptEnabled,viewport,reducedMotion:'reduce'});
  await routeFiles(context);
  const page=await context.newPage();
  const failures=[];
  page.on('pageerror',error=>failures.push(error.message));
  page.on('response',response=>{if(response.status()>=400)failures.push(response.url()+': '+response.status())});
  for(const route of routes){
   const address='http://127.0.0.1:5294/dr_hector_pagweb/'+route;
   const response=await page.goto(address);
   if(response.status()!==200)throw new Error(address);
   await page.reload();
   if(!await page.locator('h1').isVisible())throw new Error('H1 oculto: '+route);
   const width=await page.evaluate(()=>({content:document.documentElement.scrollWidth,viewport:window.innerWidth}));
   if(width.content>width.viewport+1)throw new Error('Desbordamiento: '+route+' '+JSON.stringify(width));
   for(const img of await page.locator('img').all())if(!await img.evaluate(el=>el.complete&&el.naturalWidth>0))throw new Error('Imagen sin cargar');
   if(!javaScriptEnabled&&viewport.width<760){await page.locator('.mobile-navigation summary').click();if(!await page.getByRole('navigation',{name:'Navegación móvil'}).isVisible())throw new Error('Menú inaccesible sin JS')}
   if(route===''&&javaScriptEnabled)await page.screenshot({path:'validation/home-'+viewport.width+'.png',fullPage:true});
   if(route==='contacto/'&&!javaScriptEnabled)await page.screenshot({path:'validation/contact-nojs-'+viewport.width+'.png',fullPage:true});
  }
  await page.goto('http://127.0.0.1:5294/dr_hector_pagweb/');
  await page.keyboard.press('Tab');
  if(await page.locator(':focus').textContent()!=='Ir al contenido')throw new Error('Enlace de salto no recibe foco');
  if(javaScriptEnabled&&viewport.width<760){await page.locator('.mobile-navigation summary').click();if(!await page.getByRole('navigation',{name:'Navegación móvil'}).isVisible())throw new Error('Menú móvil');await page.keyboard.press('Escape');if(await page.getByRole('navigation',{name:'Navegación móvil'}).isVisible())throw new Error('Escape no cierra menú')}
  if(failures.length)throw new Error(failures.join('\n'));
  results.push({javaScriptEnabled,viewport:viewport.width,routes:routes.length,status:'passed'});
  await context.close();
 }
 // Small local lab sample. It is not field data or a p75 result.
 const context=await browser.newContext({viewport:{width:390,height:844}});
 await routeFiles(context);
 const page=await context.newPage();
 await page.addInitScript(()=>{
  window.lab={lcp:0,cls:0};
  new PerformanceObserver(list=>{for(const entry of list.getEntries())window.lab.lcp=entry.startTime}).observe({type:'largest-contentful-paint',buffered:true});
  new PerformanceObserver(list=>{for(const entry of list.getEntries())if(!entry.hadRecentInput)window.lab.cls+=entry.value}).observe({type:'layout-shift',buffered:true});
 });
 await page.goto('http://127.0.0.1:5294/dr_hector_pagweb/');
 await page.locator('.hero img').waitFor({state:'visible'});
 await page.evaluate(()=>document.fonts.ready);
 // Wait for animation frames, not an arbitrary long sleep.
 await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
 const lab=await page.evaluate(()=>({...window.lab,htmlBytes:new TextEncoder().encode(document.documentElement.outerHTML).length}));
 writeFileSync('validation/browser-results.json',JSON.stringify({results,lab,conditions:'Chrome headless, archivos servidos por interceptación local de Playwright, sin limitación de red o CPU; muestra única, no p75. INP requiere datos de campo.'},null,2));
 console.log(JSON.stringify({browserChecks:results,lab}));
 await context.close();
}finally{await browser?.close()}
