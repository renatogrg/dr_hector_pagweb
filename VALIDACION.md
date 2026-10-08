# Informe de implementación y validación

Fecha: 8 de octubre de 2026. Estado: cambios locales listos para revisión y publicación en GitHub Pages; no se ha realizado push ni se ha verificado esta nueva versión en producción.

## Implementado

- Diez páginas estáticas con contenido en HTML inicial, URLs de directorio, enlaces rastreables y navegación nativa en móvil sin JavaScript.
- Títulos y descripciones específicos, canonical absoluta, español, viewport, un H1, estructura semántica, Open Graph y breadcrumbs.
- Sitemap XML sin fechas inventadas; robots permite búsqueda; 404 independiente y ausencia de fallback a portada.
- Configuración de dominio raíz/subdirectorio, Search Console y política separada de rastreadores de búsqueda/entrenamiento.
- JSON-LD de WebSite, WebPage, BreadcrumbList e IndividualPhysician. MedicalClinic independiente y relacionado se activa únicamente al configurar identidad y dirección reales. Article y revisión estructurada se activan tras revisión médica documentada.
- Preguntas con respuestas directas y guías educativas con fuentes, autoría editorial asistida por IA, fecha real del borrador y aviso de revisión pendiente. No se atribuyen textos al médico sin aprobación.
- Perfil y contacto sin CMP/RNE, formación, teléfonos, horarios, dirección o experiencia ficticios. Se retiró la ubicación Huancayo al no estar confirmada. Vesícula y hernias son guías, sin anunciar su disponibilidad como servicios confirmados.
- Fuente única de datos locales y botones condicionales de llamada, WhatsApp y Maps; solicitud genérica de disponibilidad sin recoger datos personales ni médicos. Sin mapa pesado.
- GA4 preparado, desactivado sin identificador y aceptación; eventos manuales limitados, sin diagnósticos, valores de formulario ni parámetros personales. La configuración externa de GA4 sigue pendiente.
- WebP responsive: 28.910 B y 47.702 B, frente al retrato PNG original de 1.009.985 B. Imagen de inicio prioritaria; retrato secundario con lazy loading y dimensiones. Fuentes del sistema, JavaScript pequeño y ninguna dependencia de cliente.
- Efectos de aparición sin ocultar el contenido mientras se espera JavaScript, movimiento reducido, foco visible, salto al contenido y menú móvil nativo por teclado.

## Comprobado

| Comprobación | Resultado |
| --- | --- |
| Generación y sintaxis de JavaScript | Correctas |
| Páginas y enlaces/recursos locales | 10 páginas, 244 referencias comprobadas |
| Títulos/descripciones/canónicas/OG/H1/idioma/imágenes | Correctos; títulos y descripciones únicos |
| Sitemap, JSON-LD y propiedades utilizadas | Sintaxis y coherencia correctas; validación local con lista de propiedades y rangos |
| Rastreo de búsqueda | Permitido para Googlebot, Bingbot, OAI-SearchBot y PerplexityBot |
| Rutas HTTP locales en raíz y `/dr_hector_pagweb` | Todas: GET, recarga y HEAD 200; directorio sin barra: 301 |
| URL inexistente | HTTP 404 real, con contenido de error |
| Configuraciones de consultorio, revisión, Maps, teléfono, WhatsApp, Search Console y GA4 | Probadas en archivos temporales; datos de prueba excluidos de la entrega |
| Chrome, móvil 390 px y escritorio 1440 px | Las diez rutas abren y recargan; sin desbordamiento horizontal ni imágenes rotas |
| JavaScript activado y desactivado | Cuatro combinaciones, 40 comprobaciones de página; contenido principal y navegación accesibles |
| Teclado y menú móvil | Enlace de salto, apertura nativa y cierre con Escape comprobados |
| Revisión visual | Capturas móvil y escritorio revisadas; capturas y resultados guardados en `validation/`, fuera del despliegue |

Comandos repetibles: `npm run build`, `npm run check`, `npm run check:browser`. La prueba de navegador requiere Playwright/Chrome en el entorno de pruebas. Su transporte intercepta archivos locales; las pruebas de estado HTTP usan servidores reales aparte. No confundir esos resultados con GitHub Pages publicado.

## Rendimiento y límites de la medición

En una muestra de laboratorio de Chrome headless móvil, con archivos servidos por interceptación local y sin limitación de CPU/red: LCP 120 ms y CLS 0. El primer muestreo detectó CLS 0,135 causado por ocultar el menú después de cargar JavaScript; se corrigió con un menú nativo de estado inicial estable.

Esta muestra verifica una condición local, no un percentil 75 ni rendimiento de usuarios de GitHub Pages. No hay datos de campo de INP, LCP o CLS disponibles. Tras publicar, evaluar PageSpeed Insights y Search Console/CrUX; objetivos p75: LCP ≤ 2,5 s, INP ≤ 200 ms, CLS ≤ 0,1. No se afirma cumplimiento en campo ni se presenta una interacción simulada como INP real.

## Pendiente por decisión del usuario

`medical.config.json` concentra CMP, RNE, formación, experiencia, consultorio, dirección, ciudad, teléfono/WhatsApp, Maps y horarios pendientes. No se activan canales ficticios. También faltan token Search Console, ID de medición y revisión médica real. Antes de publicar artículos como material clínico definitivo, el doctor debe aprobar su precisión, autoría y fechas.

Las credenciales, resultados, testimonios y reseñas no se inventaron. IndividualPhysician expresa la identidad y especialidad aportadas por el usuario; no verifica colegiatura ni habilitación.

## Pendiente externo y de producción

- Publicar el commit mediante GitHub Actions; verificar HTTP y canónicas de la versión desplegada, redirecciones, HTTPS, cabeceras y bloqueos del hospedaje.
- Revisar el robots **de la raíz del dominio**. `/dr_hector_pagweb/robots.txt` no controla el rastreo de GitHub Pages bajo subdirectorio. Registrar el sitemap en Search Console; añadir sus reglas al sitio raíz si se administra, o usar dominio propio.
- Ejecutar Schema Markup Validator y Rich Results Test sobre las URLs definitivas. La comprobación local no sustituye estos servicios ni asegura funciones enriquecidas. Article/BreadcrumbList tienen políticas propias; el marcado médico no garantiza resultados especiales ni estrellas.
- Desactivar medición mejorada de GA4, configurar privacidad y comprobar los eventos con el identificador real antes de producción.
- El titular debe reclamar/verificar el Perfil de Empresa de Google, mantener NAP consistente, solicitar reseñas auténticas y obtener referencias legítimas de entidades con vínculos reales.
- Medir datos reales, consultas y conversiones; mejorar el contenido original aprobado por el médico. No se garantiza indexación, posicionamiento, presencia en Maps ni citas en respuestas de IA. Google no exige archivos ni schema especiales para sus funciones de IA: [documentación oficial](https://developers.google.com/search/docs/appearance/ai-features).

Instrucciones completas de configuración y publicación: `README.md`.

