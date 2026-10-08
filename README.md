# Dr. Hector Rodríguez Aquiño — Cirugía Integral

Proyecto original recuperado de Sites y adaptado para ejecutarse en Windows y publicarse en GitHub Pages. Incluye inicio, doctor, tratamientos, vesícula, hernias, laparoscopia, guía del paciente y contacto.

Repositorio: https://github.com/renatogrg/dr_hector_pagweb

El repositorio se creó privado. GitHub Pages está preparado, pero todavía no activado. Para usar Pages con GitHub Free será necesario autorizar que el repositorio sea público; los planes compatibles también permiten Pages desde repositorios privados.

Para subir cambios a este repositorio desde esta PC:

```powershell
git add .
git commit -m "Actualizar sitio"
git push
```

## Abrir en tu PC

Desde una terminal situada en esta carpeta:

```powershell
npm.cmd run dev
```

Abre http://localhost:5173. Detén el servidor con Ctrl+C. Si el puerto está ocupado, usa `$env:PORT=5174` antes de arrancarlo. No hace falta instalar paquetes: el servidor usa Node.js y la generación usa Python 3, ambos ya instalados en esta PC. En otras computadoras se requiere Node.js 22 o superior y Python 3 disponible como `python`.

## Editar y comprobar

- Textos y estructura de las páginas: `generate.py`.
- Diseño: `dist/style.css`.
- Menú, animaciones y formulario: `dist/app.js`.
- Fotografías: `dist/assets/`.

Después de editar textos o estructura, ejecuta:

```powershell
npm.cmd run build
npm.cmd run check
```

La generación escribe los HTML de `dist/` en UTF-8 y mantiene los archivos de estilos, JavaScript e imágenes. Evita editar los HTML generados directamente porque la siguiente generación los reemplaza. Los enlaces son relativos, por lo que funcionan en una ruta de repositorio como `https://USUARIO.github.io/REPOSITORIO/` y también en un dominio propio. Para trabajar localmente usa el servidor, en lugar de abrir los HTML con doble clic.

## Publicar en GitHub Pages

El archivo `.github/workflows/pages.yml` genera, verifica y publica exclusivamente `dist/` cuando se suben cambios a `main`.

1. Crea un repositorio vacío en GitHub, sin README ni licencia inicial. GitHub Free permite Pages en repositorios públicos.
2. Desde esta carpeta, conecta el repositorio y sube el proyecto (reemplaza USUARIO y REPOSITORIO):

```powershell
git add .
git commit -m "Configurar proyecto local y GitHub Pages"
git remote add origin https://github.com/USUARIO/REPOSITORIO.git
git push -u origin main
```

3. En GitHub abre **Settings → Pages → Build and deployment → Source → GitHub Actions**.
4. Si la primera ejecución falló antes de activar Pages, vuelve a ejecutarla en **Actions → Publicar en GitHub Pages → Run workflow**.
5. La URL publicada aparece en **Settings → Pages** y en la ejecución de Actions.

Guía oficial: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages

## Estado del contenido

Se conservó el diseño y comportamiento original. CMP, RNE, formación, dirección, horarios, teléfono y correo todavía contienen datos por completar. El formulario prepara un mensaje y permite copiarlo; no envía solicitudes ni guarda información en un servidor. También se conserva `noindex,nofollow` y `robots.txt` bloqueando la indexación, como en la propuesta original. Cambia estas opciones cuando el contenido definitivo esté listo.

La configuración `.openai/hosting.json` conserva la referencia al sitio original. GitHub Pages no depende de ella ni de la sesión de ChatGPT, y el flujo publica únicamente el contenido de `dist/`.
