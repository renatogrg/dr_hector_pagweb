# Web del Dr. Héctor Rodríguez Aquiño

Web estática de cirugía general y laparoscopia, preparada para GitHub Pages. Todo el contenido principal está en el HTML inicial. Los datos pendientes se centralizan en `medical.config.json`; no hay teléfonos, direcciones ni credenciales inventados.

## Trabajar y validar

Se requiere Python 3.12+ y Node.js 22+. No se necesitan paquetes para generar ni para las comprobaciones de código/HTTP.

```powershell
npm.cmd run build
npm.cmd run check
npm.cmd run dev
```

Abre http://localhost:5173. Las rutas públicas son `/`, `/doctor/`, `/tratamientos/`, `/laparoscopia/`, `/vesicula/`, `/hernias/`, `/guia-del-paciente/`, `/preguntas-frecuentes/`, `/articulos/` y `/contacto/`.

`generate.py` conserva el diseño original y genera HTML, sitemap, robots y 404. `site_features.py` adapta contenido, identidad y las integraciones. Los estilos y el JavaScript fuente se encuentran en `dist/style.css` y `dist/app.js`; no edites los HTML generados. Las imágenes WebP responsive están en `dist/assets/`; el retrato original se conserva sin usarse como descarga principal.

`npm run check` verifica recursos, enlaces, codificación, títulos/descripciones únicos, idioma, viewport, imágenes, Open Graph, canónicas, JSON-LD, sitemap, robots, páginas huérfanas y error 404. Además arranca servidores locales para probar GET, HEAD y recarga en la raíz y en el subdirectorio de Pages. Las pruebas de configuración generan datos de prueba en un directorio temporal fuera del sitio publicado y los eliminan al finalizar.

Para repetir la prueba visual, instala Playwright en tu entorno de pruebas y Chrome. Ejecuta `npm run check:browser`; si Playwright está en un entorno compartido, indica su carpeta en `BROWSER_NODE_MODULES`. Guarda capturas y resultados en `validation/`, excluido de Git y del despliegue. Esta prueba usa interceptación local de archivos; la prueba HTTP real es independiente. No usa servicios de analítica externos.

## Datos por configurar

Edita `medical.config.json` solo con información confirmada. `null` y las listas vacías representan pendientes y no se emiten en metadatos ni JSON-LD.

- `doctor`: CMP, RNE, formación (`training`, lista de textos verificados) y experiencia.
- `clinic`: nombre real, dirección, ciudad, región, país de dos letras, teléfono y WhatsApp en formato internacional E.164, URL oficial de Google Maps y horarios.
- `hours`: lista de objetos con `days` (por ejemplo `Monday`), `opens` y `closes` en formato de 24 horas. Divide jornadas partidas en varias entradas.
- `confirmedServices`: se incluye únicamente `laparoscopia`, de acuerdo con la especialidad indicada. Añade `vesicula` o `hernias` solo tras confirmar su disponibilidad con el médico. Estas páginas ya existen como guías educativas, sin anunciarlas como servicios confirmados.
- `editorial`: autor real y fechas. El borrador actual identifica redacción asistida por IA y publicación del borrador el 8 de octubre de 2026. Revisor y revisión médica están pendientes. No atribuye su autoría o aprobación al doctor. Actualiza las fechas al publicar o revisar realmente; no cambian automáticamente en cada build. Si incorporas textos con autores distintos, amplía la configuración por artículo.
- `searchConsoleVerification`: token real de la metaetiqueta proporcionada por Google. Vacío: no se genera ninguna etiqueta ficticia.
- `analyticsId`: ID GA4 real `G-...`. Vacío: no se carga analítica.
- `allowAITraining`: permiso de entrenamiento, independiente del acceso para búsqueda. Se conserva el permiso general existente por defecto.

Al generar, los datos locales reales aparecen en contacto y pie de todas las páginas desde una sola fuente. Se activan `tel:`, WhatsApp y Maps solo con datos presentes. No se descarga ningún mapa en la carga inicial. La solicitud de cita abre WhatsApp con un texto genérico de disponibilidad: no recoge nombre, celular, diagnóstico ni archivos y no equivale a una reserva confirmada.

## Medición y privacidad

Con un ID GA4 real se muestra una opción explícita de aceptar/rechazar/retirar medición durante la visita. No se carga GA antes de aceptar. Se preparan `call_click`, `whatsapp_click` y `appointment_request`; este último mide la apertura de una solicitud, no una cita confirmada. No se envían valores de formulario, diagnósticos, títulos de enfermedades, URL completa ni referencias de navegación. El contexto enviado usa una ubicación genérica del sitio.

En el flujo de datos GA4 desactiva **medición mejorada**, especialmente clics, formularios, búsqueda interna y páginas automáticas; el código envía exclusivamente la lista cerrada de eventos manuales. Desactiva Google Signals y personalización publicitaria. Comprueba los eventos en DebugView antes de activar producción. No añadas etiquetas de seguimiento que lean campos médicos ni parámetros personales. Search Console permite medir consultas, páginas, indexación y Core Web Vitals sin instrumentar datos médicos.

## Publicación en GitHub Pages

Repositorio configurado: https://github.com/renatogrg/dr_hector_pagweb
URL canónica prevista: https://renatogrg.github.io/dr_hector_pagweb/

1. Revisa `site.config.json`: `url` debe ser la URL HTTPS definitiva con barra final y `indexable` debe estar en `true` para la web pública.
2. Ejecuta build y check. Revisa contenido y pendientes médicos antes de publicar una versión clínica definitiva.
3. En GitHub selecciona **Settings → Pages → Source → GitHub Actions**.
4. Revisa el diff local, realiza el commit y sube los cambios a `main`. El flujo `.github/workflows/pages.yml` genera, prueba y publica exclusivamente `dist/`.
5. Comprueba en el despliegue las diez URLs, la recarga directa y una URL inexistente. No configures una redirección universal a la portada; las URLs inexistentes deben devolver HTTP 404.
6. Añade la propiedad de Search Console, verifica el token real, envía `sitemap.xml` e inspecciona las URLs.

```powershell
git add .
git commit -m "Preparar web estática SEO local y GEO"
git push origin main
```

Estos comandos son instrucciones; esta entrega no realiza commit, push ni publicación.

Para un dominio propio, cambia `site.config.json.url` a `https://tudominio/`, configura **Custom domain** y DNS según GitHub y activa HTTPS. Si administras CNAME mediante código, crea `dist/CNAME` con el dominio real. No agregues un dominio de ejemplo. Las rutas relativas de recursos y enlaces soportan raíz y subdirectorio; canónicas y sitemap se regeneran con la URL definitiva. Mantén un solo dominio principal y revisa redirecciones del anterior para evitar duplicados. El servidor local redirige los directorios sin barra a su URL con barra; el hospedaje debe comprobarse después de publicar.

### Robots en un repositorio de Pages

Los rastreadores leen **https://renatogrg.github.io/robots.txt**, no `/dr_hector_pagweb/robots.txt`. El archivo dentro del proyecto no controla el dominio. Si administras el repositorio raíz `renatogrg.github.io`, incorpora allí las reglas y `Sitemap: https://renatogrg.github.io/dr_hector_pagweb/sitemap.xml`, respetando los demás proyectos. Con dominio propio en la raíz, el archivo generado sí estará en el lugar efectivo.

Se permiten Googlebot, Bingbot, OAI-SearchBot y otros rastreadores de búsqueda mediante la regla general. `allowAITraining: false` añade restricciones para GPTBot y Google-Extended, sin bloquear búsqueda. Google-Extended también controla usos de Gemini descritos por Google y no es el robot de Google Search. Robots.txt es una preferencia para robots que lo respetan, no un control de acceso. ChatGPT-User y otras solicitudes iniciadas por personas tienen comportamiento distinto; no se garantiza su control mediante estas reglas. No se exige `llms.txt` ni se promete indexación o cita en IA.

## Marcado y contenido médico

Se emiten WebSite, WebPage, BreadcrumbList e IndividualPhysician con datos visibles. El consultorio físico es una entidad separada MedicalClinic y se relaciona mediante `practicesAt` únicamente cuando existen nombre y dirección reales suficientes. No hay valoraciones ni testimonios.

Los artículos pendientes de revisión se presentan como borradores con fuentes institucionales y fechas transparentes. Article y revisión estructurada se activan cuando el revisor y la fecha real se hayan completado; no se inventa aprobación médica. La comprobación local valida sintaxis y una lista de propiedades/rangos utilizados. Tras publicar, contrasta también con [Schema Markup Validator](https://validator.schema.org/) y [Rich Results Test](https://search.google.com/test/rich-results).

La validez de Schema.org no implica elegibilidad para funciones enriquecidas de Google. El perfil médico no tiene una función enriquecida garantizada; Article y BreadcrumbList se interpretan según las políticas y campos exigidos por Google. No se emite FAQPage para prometer resultados especiales, ni aggregateRating para solicitar estrellas. Open Graph sirve para compartir la página, sin presentarlo como señal directa de posicionamiento.

Fuentes: [NIDDK: vesícula](https://www.niddk.nih.gov/health-information/digestive-diseases/gallstones/treatment), [NIDDK: hernia inguinal](https://www.niddk.nih.gov/health-information/digestive-diseases/inguinal-hernia), [NHS: laparoscopia](https://www.nhs.uk/tests-and-treatments/laparoscopy/), [Schema.org: IndividualPhysician](https://schema.org/IndividualPhysician), [OpenAI: rastreadores](https://developers.openai.com/api/docs/bots), [Google: funciones de IA](https://developers.google.com/search/docs/appearance/ai-features), [Google-Extended](https://developers.google.com/search/docs/crawling-indexing/overview-google-crawlers#google-extended), [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

## Acciones externas y seguimiento

El código no verifica un Perfil de Empresa de Google. El titular debe crear o reclamar el perfil, verificarlo, usar categorías y datos reales consistentes con la web, añadir los servicios confirmados y mantener horarios. Solicita reseñas auténticas sin fabricarlas y referencias legítimas desde clínicas, colegios o instituciones donde realmente corresponda. La inscripción y las credenciales requieren comprobación en las fuentes profesionales aplicables.

Tras publicar, usa Search Console y PageSpeed Insights/CrUX para evaluar datos reales. Objetivos al percentil 75: LCP ≤ 2,5 s, INP ≤ 200 ms, CLS ≤ 0,1. Las muestras de laboratorio locales no prueban esos objetivos en usuarios. Consulta `VALIDACION.md` para resultados y limitaciones de esta entrega.
