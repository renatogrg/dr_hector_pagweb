import { spawn } from 'node:child_process';
import { readFileSync } from 'node:fs';
const xml=readFileSync(new URL('../dist/sitemap.xml',import.meta.url),'utf8');
const canonicalBase=JSON.parse(readFileSync(new URL('../site.config.json',import.meta.url))).url;
const paths=[...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map(match=>match[1].slice(canonicalBase.length));
for(const [index,prefix] of ['', '/dr_hector_pagweb'].entries()){
 const port=5290+index;
 const server=spawn(process.execPath,['scripts/serve.mjs'],{env:{...process.env,PORT:String(port),BASE_PATH:prefix},stdio:['ignore','pipe','pipe']});
 try{
  await new Promise((resolve,reject)=>{server.stdout.once('data',resolve);server.once('error',reject);server.once('exit',code=>reject(new Error('Servidor: '+code)))});
  for(const route of paths){
   const address='http://127.0.0.1:'+port+prefix+'/'+route;
   for(let reload=0;reload<2;reload++){
    const response=await fetch(address);
    if(response.status!==200)throw new Error(address+': '+response.status);
    const html=await response.text();
    if(!html.includes('<h1>')||html.includes('content="noindex'))throw new Error('HTML inicial o robots: '+address);
   }
   const response=await fetch(address,{method:'HEAD'});
   if(response.status!==200)throw new Error('HEAD: '+address);
  }
  const missing=await fetch('http://127.0.0.1:'+port+prefix+'/no-existe/otra/');
  if(missing.status!==404||!(await missing.text()).includes('Página no encontrada'))throw new Error('404 incorrecto');
  const redirect=await fetch('http://127.0.0.1:'+port+prefix+'/doctor',{redirect:'manual'});
  if(redirect.status!==301||redirect.headers.get('location')!==prefix+'/doctor/')throw new Error('Redirección incorrecta');
  console.log('HTTP: '+paths.length+' rutas GET, recarga y HEAD 200; 301 y 404 correctos en '+(prefix||'/'));
 }finally{server.kill()}
}
