import { readdirSync, readFileSync, existsSync, statSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../dist/', import.meta.url));
const files = readdirSync(root, { recursive: true }).filter(file => file.endsWith('.html'));
let count = 0;
const failures = [];
for (const file of files) {
  const html = readFileSync(path.join(root, file), 'utf8');
  if (!html.includes('charset="utf-8"') || html.includes('\uFFFD')) failures.push(`${file}: codificación inválida`);
  for (const match of html.matchAll(/(?:href|src)="([^"]+)"/g)) {
    const link = match[1];
    if (/^(?:[a-z]+:|#|\/\/)/i.test(link)) continue;
    count++;
    if (link.startsWith('/')) { failures.push(`${file}: ruta absoluta ${link}`); continue; }
    let target = path.resolve(root, path.dirname(file), link.split(/[?#]/)[0]);
    if (existsSync(target) && statSync(target).isDirectory()) target = path.join(target, 'index.html');
    if (!existsSync(target)) failures.push(`${file}: enlace sin destino ${link}`);
  }
}
if (files.length !== 8) failures.push(`Se esperaban 8 páginas, se encontraron ${files.length}`);
if (failures.length) { console.error(failures.join('\n')); process.exitCode = 1; }
else console.log(`${files.length} páginas y ${count} enlaces/recursos locales verificados. Compatibles con rutas de GitHub Pages.`);
