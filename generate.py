"""Genera el sitio estático. Los bloques HTML se unen sin añadir espacios."""

from pathlib import Path
import html, json, re, os, shutil
from urllib.parse import quote, urlsplit
from xml.etree import ElementTree as ET
from site_features import (
    settings,
    doctor,
    clinic,
    editorial,
    adapt,
    identity_graph,
    extra_head,
    nap,
)

# 1. Configuración de salida, dominio e indexación.
root = Path(os.environ.get("DIST_DIR", Path(__file__).parent / "dist"))
root.mkdir(parents=True, exist_ok=True)
# Elimina rutas retiradas para que una compilación nueva no conserve páginas antiguas.
for retired_route in ("articulos",):
    retired_path = root / retired_route
    if retired_path.exists():
        shutil.rmtree(retired_path)
config = json.loads(
    (Path(__file__).parent / "site.config.json").read_text(encoding="utf-8")
)
site_url = os.environ.get("SITE_URL", config["url"]).rstrip("/") + "/"
parsed_url = urlsplit(site_url)
if (
    parsed_url.scheme != "https"
    or not parsed_url.netloc
    or parsed_url.query
    or parsed_url.fragment
    or parsed_url.username
    or parsed_url.password
):
    raise ValueError(
        "SITE_URL debe ser una URL pública HTTPS sin consulta, fragmento ni credenciales."
    )
indexable = config["indexable"]
if not isinstance(indexable, bool):
    raise ValueError("indexable debe ser true o false.")
robots = (
    "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"
    if indexable
    else "noindex,follow"
)
# 2. Navegación y tarjetas compartidas por las páginas.
nav = [
    ("", "Inicio"),
    ("doctor", "El doctor"),
    ("servicios", "Servicios"),
    ("guia-del-paciente", "Guía del paciente"),
    ("contacto", "Contacto"),
]
nav = [
    ("", "Inicio"),
    ("doctor", "El doctor"),
    ("servicios", "Servicios"),
    ("guia-del-paciente", "Guía del paciente"),
    ("preguntas-frecuentes", "Preguntas"),
    ("contacto", "Contacto"),
]
services = [
    (
        "laparoscopia",
        "01",
        "Cirugía laparoscópica",
        "Comprende este abordaje de mínima invasión y cuándo podría ser una opción.",
        "Cirugía laparoscópica",
    ),
    (
        "vesicula",
        "02",
        "Colecistectomía",
        "Extracción de la vesícula por laparoscopia o cirugía abierta, según la evaluación médica.",
        "Colecistectomía",
    ),
    (
        "hernias",
        "03",
        "Reparación de hernias abdominales",
        "Reparación por laparoscopia o cirugía abierta, con el abordaje indicado para cada caso.",
        "Reparación de hernias abdominales",
    ),
]


# 3. Componentes HTML reutilizables.
def url(s):
    return "/" + s + "/" if s else "/"


def cards(current_slug=None, include_pending=False):
    rendered = "".join(
        (
            f'<a class="service-card{" service-card--current" if s == current_slug else ""}" href="{url(s)}"'
            + (' aria-current="page"' if s == current_slug else "")
            + ">"
            f'<span class="card-no">{n}</span>'
            f"<h3>{title}</h3>"
            f"<p>{desc}</p>"
            f'<span class="text-link">Ver información completa</span>'
            f"</a>"
        )
        for s, n, title, desc, t in services
    )
    if include_pending:
        rendered += (
            '<article class="service-card service-card--placeholder">'
            '<span class="card-no">04 · PENDIENTE DE CONFIRMAR</span>'
            '<h3>Servicio adicional 04</h3>'
            '<p>El nombre y los detalles se incorporarán al confirmar la información del doctor.</p>'
            '<span class="text-link service-link-disabled">Próximamente</span>'
            '</article>'
            '<article class="service-card service-card--placeholder">'
            '<span class="card-no">05 · PENDIENTE DE CONFIRMAR</span>'
            '<h3>Servicio adicional 05</h3>'
            '<p>El nombre y los detalles se incorporarán al confirmar la información del doctor.</p>'
            '<span class="text-link service-link-disabled">Próximamente</span>'
            '</article>'
        )
    return rendered


def faq(items):
    return (
        '<div class="faq">'
        + "".join(
            (f"<details>" f"<summary>{q}</summary>" f"<p>{a}</p>" f"</details>")
            for q, a in items
        )
        + "</div>"
    )


def cta():
    return (
        '<section class="wrap consultation-banner">'
        '<div class="consultation-banner-inner">'
        '<div class="consultation-banner-copy">'
        '<span class="eyebrow">EL SIGUIENTE PASO</span>'
        "<h2>Hablemos de tu salud.</h2>"
        "<p>Una consulta para entender tu caso y resolver tus dudas.</p>"
        "</div>"
        '<a class="button light consultation-banner-link" href="/contacto/">Solicitar una consulta <span aria-hidden="true">↗</span></a>'
        "</div></section>"
    )


def steps():
    return (
        '<div class="steps">'
        + "".join(
            (
                f"<article>"
                f"<span>0{i}</span>"
                f"<h3>{t}</h3>"
                f"<p>{d}</p>"
                f"</article>"
            )
            for i, t, d in [
                (1, "Escuchar", "Tus síntomas, antecedentes y lo que te preocupa."),
                (2, "Evaluar", "Revisar los estudios y explicar las opciones."),
                (3, "Decidir", "Acordar un plan de atención para tu caso."),
                (4, "Acompañar", "Preparación, cuidados y seguimiento."),
            ]
        )
        + "</div>"
    )


def mast(k, title, desc):
    return (
        f'<section class="mast wrap">'
        f'<span class="eyebrow">{k}</span>'
        f"<h1>{title}</h1>"
        f'<p class="lead">{desc}</p>'
        f"</section>"
    )


# 4. Contenido base de las páginas.
# Inicio: título principal, descripción, botones, fotografía y secciones.
pages = {}
pages[""] = (
    "Cirugía general y laparoscópica en Huancayo",
    (
        '<section class="hero wrap">'
        '<div class="hero-copy">'
        '<span class="eyebrow">CIRUGÍA GENERAL · HUANCAYO</span>'
        "<h1>Precisión quirúrgica.<br>"
        "<em>Atención humana.</em>"
        "</h1>"
        '<p class="lead">Cirugía general y laparoscópica con una evaluación individual y explicaciones claras en cada etapa.</p>'
        '<div class="actions">'
        '<a class="button" href="/contacto/">Agendar una consulta</a>'
        '<a class="button outline" href="/doctor/">Conoce al doctor</a>'
        "</div>"
        '<div class="hero-note">'
        '<span class="mini-line">'
        "</span>"
        "<p>Una decisión informada comienza<br>con una buena conversación.</p>"
        "</div>"
        "</div>"
        '<div class="hero-visual">'
        '<img src="/assets/hector-rodriguez.png" alt="Dr. Hector Rodríguez Aquiño con bata médica" width="800" height="1000" fetchpriority="high">'
        '<div class="portrait-label">'
        "<span>Dr. Hector Rodríguez Aquiño</span>"
        "<small>Cirugía general y laparoscópica</small>"
        "</div>"
        "</div>"
        "</section>"
        '<section class="credential-strip">'
        '<div class="wrap credential-grid">'
        "<div>"
        "<small>ESPECIALIDAD</small>"
        "<span>Cirugía general</span>"
        "</div>"
        "<div>"
        "<small>ENFOQUE</small>"
        "<span>Cirugía laparoscópica</span>"
        "</div>"
        "<div>"
        "<small>ATENCIÓN</small>"
        "<span>Huancayo, Perú</span>"
        "</div>"
        "<div>"
        "<small>ACOMPAÑAMIENTO</small>"
        "<span>De la consulta al seguimiento</span>"
        "</div>"
        "</div>"
        "</section>"
        '<section class="section wrap">'
        '<div class="section-heading">'
        "<div>"
        '<span class="eyebrow">SERVICIOS</span>'
        "<h2>Comprende tus opciones.</h2>"
        "</div>"
        "</div>"
        '<div class="service-grid">'
    )
    + cards()
    + (
        "</div>"
        "</section>"
        '<section class="doctor-section">'
        '<div class="wrap doctor-grid">'
        '<div class="doctor-text">'
        '<span class="eyebrow">EL ESPECIALISTA</span>'
        "<h2>Conoce a quien<br>cuidará de ti.</h2>"
        "<p>La consulta es un espacio para escucharte, revisar tu historia y explicar las alternativas con un lenguaje que puedas entender.</p>"
        '<a class="button outline" href="/doctor/">Perfil del doctor</a>'
        "</div>"
        '<div class="principles">'
        "<article>"
        "<span>01</span>"
        "<div>"
        "<h3>Evaluación individual</h3>"
        "<p>El tratamiento se adapta a tu diagnóstico y tus circunstancias.</p>"
        "</div>"
        "</article>"
        "<article>"
        "<span>02</span>"
        "<div>"
        "<h3>Información clara</h3>"
        "<p>Beneficios, riesgos y alternativas antes de decidir.</p>"
        "</div>"
        "</article>"
        "<article>"
        "<span>03</span>"
        "<div>"
        "<h3>Seguimiento cercano</h3>"
        "<p>Indicaciones para la preparación y la recuperación.</p>"
        "</div>"
        "</article>"
        "</div>"
        "</div>"
        "</section>"
        '<section class="section wrap">'
        '<span class="eyebrow">TU RECORRIDO</span>'
        "<h2>Claridad en cada etapa.</h2>"
    )
    + steps()
    + (
        "</section>"
        '<section class="faq-section home-faq-section">'
        '<div class="wrap faq-grid">'
        "<div>"
        '<span class="eyebrow">PREGUNTAS FRECUENTES</span>'
        "<h2>Antes de<br>tu consulta.</h2>"
        '<a class="text-link" href="/guia-del-paciente/">Visitar la guía del paciente</a>'
        "</div>"
    )
    + faq(
        [
            (
                "¿Todas las cirugías pueden hacerse por laparoscopia?",
                "La elección depende del diagnóstico, los antecedentes y la evaluación del cirujano. También pueden considerarse otros abordajes.",
            ),
            (
                "¿Qué debo llevar a mi primera consulta?",
                "Documento de identidad, resultados disponibles, informes de cirugías previas y una lista de medicamentos y alergias.",
            ),
            (
                "¿Puedo consultar aunque aún no tenga estudios?",
                "La primera evaluación permite revisar tu situación y determinar si necesitas estudios adicionales.",
            ),
        ]
    )
    + "</div>"
    + cta()
    + "</section>",
)
# Perfil del doctor.
pages["doctor"] = (
    "Conoce al doctor · Cirugía Integral",
    (
        '<section class="wrap doctor-profile-hero">'
        '<span class="eyebrow doctor-section-label">EL DOCTOR</span>'
        '<div class="profile-photo">'
        '<img src="/assets/hector-rodriguez.png" alt="Dr. Hector Rodríguez Aquiño" width="1082" height="1454">'
        "</div>"
        '<div class="doctor-profile-copy">'
        '<span class="doctor-profile-tagline">La persona detrás de tu atención.</span>'
        "<h1>Dr. Hector Rodríguez Aquiño</h1>"
        '<p class="lead">Cirugía general y laparoscópica en Huancayo.</p>'
        '<p class="doctor-trust">Una relación de confianza se construye escuchando y explicando.</p>'
        "<p>Mi enfoque comienza con comprender tu motivo de consulta y revisar las opciones disponibles. La recomendación de una cirugía se conversa después de una evaluación individual.</p>"
        '<div class="credential-box">'
        "<h3>Credenciales profesionales</h3>"
        "<dl>"
        "<div>"
        "<dt>CMP</dt>"
        "<dd>Por completar</dd>"
        "</div>"
        "<div>"
        "<dt>RNE</dt>"
        "<dd>Por completar</dd>"
        "</div>"
        "<div>"
        "<dt>Formación</dt>"
        "<dd>Por completar con datos verificables</dd>"
        "</div>"
        "</dl>"
        "</div>"
        '<a class="button" href="/contacto/">Solicitar consulta</a>'
        "</div>"
        "</section>"
        '<section class="section wrap">'
        '<span class="eyebrow">FORMA DE ATENDER</span>'
        "<h2>Tu caso merece tiempo y claridad.</h2>"
    )
    + steps()
    + """</section>"""
    + cta(),
)
# Página de servicios y datos de las guías educativas.
pages["servicios"] = (
    "Servicios · Cirugía general y laparoscópica",
    mast(
        "SERVICIOS",
        "Información para<br>decidir con claridad.",
        "Conoce las áreas de atención y conversa con el cirujano sobre las opciones para tu caso.",
    )
    + '<section class="wrap"><div class="service-grid">'
    + cards()
    + (
        "</div>"
        '<div class="info-band">'
        "<h3>Una técnica, distintas aplicaciones.</h3>"
        "<p>La laparoscopia es un abordaje quirúrgico, no una enfermedad ni un tratamiento único. Puede utilizarse en diferentes procedimientos cuando la evaluación lo permite.</p>"
        "</div>"
        "</section>"
        '<section class="section wrap">'
        '<div class="section-heading">'
        "<div>"
        '<span class="eyebrow">LA EVALUACIÓN</span>'
        "<h2>El plan comienza contigo.</h2>"
        "</div>"
        "<p>Consulta, revisión de estudios<br>y decisiones compartidas.</p>"
        "</div>"
    )
    + steps()
    + """</section>"""
    + cta(),
)
data = {
    "vesicula": (
        "COLECISTECTOMÍA",
        "Extracción de<br>la vesícula.",
        "Servicio de colecistectomía por abordaje laparoscópico o abierto, según la evaluación médica.",
        "¿Qué se evalúa?",
        "Los cálculos biliares pueden asociarse a dolor y otras complicaciones. La indicación de tratamiento requiere revisar los síntomas, los estudios y los antecedentes.",
        "¿Cómo es el procedimiento?",
        "La colecistectomía consiste en retirar la vesícula. Puede realizarse por laparoscopia, mediante pequeñas incisiones, o por cirugía abierta. El cirujano explicará qué abordaje es adecuado para tu caso y cuándo podría ser necesario cambiar de técnica.",
        [
            (
                "Antes de la cirugía",
                "Evaluación y estudios indicados por el equipo. Sigue sus instrucciones sobre preparación y medicamentos.",
            ),
            (
                "Riesgos y alternativas",
                "Pregunta por los riesgos, otras opciones y la posibilidad de cambiar de abordaje durante la intervención.",
            ),
            (
                "Después del procedimiento",
                "El alta, los cuidados y el retorno a las actividades dependen de la evolución y de las indicaciones del equipo.",
            ),
        ],
    ),
    "hernias": (
        "REPARACIÓN DE HERNIAS",
        "Reparación de hernias<br>abdominales.",
        "Evaluación para la reparación quirúrgica de hernias inguinales, umbilicales e incisionales.",
        "¿Qué es una hernia?",
        "Una hernia ocurre cuando tejido del interior del abdomen protruye por una zona débil de su pared. El tipo, el tamaño y los síntomas orientan la evaluación.",
        "¿Qué opciones se consideran?",
        "La reparación puede realizarse mediante distintos abordajes. La elección entre cirugía abierta o laparoscópica, y el uso de malla, se conversa según las características del caso.",
        [
            (
                "Valoración",
                "Exploración de la zona, antecedentes y estudios cuando sean necesarios.",
            ),
            (
                "Decisión compartida",
                "Conversación sobre las opciones, los riesgos y los objetivos del tratamiento.",
            ),
            (
                "Recuperación",
                "Indicaciones personalizadas sobre cuidado de heridas, esfuerzo físico y seguimiento.",
            ),
        ],
    ),
    "laparoscopia": (
        "CIRUGÍA LAPAROSCÓPICA",
        "Pequeñas incisiones.<br>Una decisión cuidadosa.",
        "Conoce el abordaje mínimamente invasivo y las preguntas que puedes hacer en consulta.",
        "¿En qué consiste?",
        "La laparoscopia permite trabajar en el abdomen con una cámara e instrumentos introducidos a través de pequeñas incisiones. Es una técnica que puede aplicarse a distintos procedimientos.",
        "¿Es adecuada para todos?",
        "No siempre. La elección depende de la enfermedad, los antecedentes y los hallazgos clínicos. En algunas situaciones puede ser necesario un abordaje abierto.",
        [
            (
                "Posibles beneficios",
                "Según el procedimiento, puede favorecer la recuperación y reducir el tamaño de las incisiones.",
            ),
            (
                "Aspectos a conversar",
                "Riesgos, alternativas, preparación y posibilidad de conversión a cirugía abierta.",
            ),
            (
                "Seguimiento",
                "Las indicaciones y el tiempo de recuperación se individualizan según el procedimiento y la evolución.",
            ),
        ],
    ),
}
for slug, (tag, title, desc, q1, a1, q2, a2, items) in data.items():
    pages[slug] = (
        tag.title() + " en Huancayo · Cirugía Integral",
        mast(tag, title.replace('<br>', ' '), desc).replace(
            'class="mast wrap"', 'class="mast wrap compact-mast service-detail-mast"'
        )
        + '<div class="wrap breadcrumb service-detail-breadcrumb"><a href="/servicios/">Servicios</a><span>/</span>'
        + tag.title()
        + "</div>"
        + (
            f"""<section class="wrap treatment-grid">"""
            f"""<div class="article">"""
            f"""<h2>{q1}</h2>"""
            f"""<p>{a1}</p>"""
            f"""<h2>{q2}</h2>"""
            f"""<p>{a2}</p>"""
            f"""<div class="treatment-stages">"""
        )
        + "".join(
            (
                f"<article>"
                f"<span>0{i+1}</span>"
                f"<div>"
                f"<h3>{t}</h3>"
                f"<p>{d}</p>"
                f"</div>"
                f"</article>"
            )
            for i, (t, d) in enumerate(items)
        )
        + (
            "</div>"
            "</div>"
            '<aside class="appointment-card">'
            '<span class="eyebrow">CONSULTA ESPECIALIZADA</span>'
            "<h3>Resuelve tus dudas<br>sobre tu caso.</h3>"
            "<p>Prepara tus estudios y preguntas para conversar con el cirujano.</p>"
            '<a class="button" href="/contacto/">Solicitar consulta</a>'
            "<hr>"
            "<small>Cirugía general y laparoscópica<br>Huancayo, Perú</small>"
            "</aside>"
            "</section>"
            '<section class="section wrap">'
            '<span class="eyebrow">SIGUE EXPLORANDO</span>'
            "<h2>Otros servicios.</h2>"
            '<div class="services-carousel services-carousel--contextual" data-services-carousel>'
            '<div class="services-grid service-grid service-grid--contextual">'
        )
        + cards(slug, include_pending=True)
        + (
            '</div>'
            '<div class="services-carousel-controls" aria-label="Navegación de servicios">'
            '<button type="button" class="carousel-button" data-carousel-prev aria-label="Servicio anterior">←</button>'
            '<button type="button" class="carousel-button" data-carousel-next aria-label="Servicio siguiente">→</button>'
            '</div>'
            '</div></section>'
        ),
    )
# Guía del paciente.
pages["guia-del-paciente"] = (
    "Guía del paciente · Preparación y consulta",
    '<div class="page-entry patient-guide-entry">'
    + mast(
        "GUÍA DEL PACIENTE",
        "Más información. Más tranquilidad.",
        "Una guía práctica para preparar tu consulta y conversar sobre tu atención.",
    ).replace('class="mast wrap"', 'class="mast wrap compact-mast"')
    + (
        '<section class="wrap guide-grid patient-guide-overview">'
        '<article class="guide-card">'
        '<span class="card-no">01 · PRIMERA CONSULTA</span>'
        "<h2>Qué llevar.</h2>"
        "<ul>"
        "<li>Documento de identidad.</li>"
        "<li>Informes y estudios disponibles.</li>"
        "<li>Lista de medicamentos y alergias.</li>"
        "<li>Antecedentes de cirugías o enfermedades.</li>"
        "<li>Tus preguntas y preocupaciones.</li>"
        "</ul>"
        "</article>"
        '<article class="guide-card dark">'
        '<span class="card-no">02 · DECISIONES INFORMADAS</span>'
        "<h2>Qué preguntar.</h2>"
        "<ul>"
        "<li>¿Cuál es mi diagnóstico?</li>"
        "<li>¿Qué alternativas tengo?</li>"
        "<li>¿Por qué se recomienda este abordaje?</li>"
        "<li>¿Qué beneficios y riesgos debo conocer?</li>"
        "<li>¿Cómo será el seguimiento?</li>"
        "</ul>"
        "</article>"
        "</section>"
    )
    + cta()
    + (
        '</div><section class="patient-guide-faq">'
        '<div class="wrap narrow">'
        '<span class="eyebrow">DUDAS HABITUALES</span>'
        "<h2>Tu atención, paso a paso.</h2>"
    )
    + faq(
        [
            (
                "¿La consulta implica que debo operarme?",
                "No. La evaluación permite conocer tu situación y conversar sobre las opciones, que pueden incluir estudios, seguimiento o tratamiento quirúrgico.",
            ),
            (
                "¿Cuánto tarda la recuperación?",
                "Depende del procedimiento, del estado de salud y de la evolución. Solicita indicaciones específicas para tu actividad laboral y tus cuidados.",
            ),
            (
                "¿Debo suspender medicamentos antes de operarme?",
                "No los suspendas por tu cuenta. Informa al equipo qué medicamentos utilizas y sigue sus instrucciones.",
            ),
            (
                "¿Dónde puedo consultar después de una cirugía?",
                "El equipo debe indicar el canal de contacto y la cita de seguimiento. Antes del alta, confirma a quién llamar y qué señales requieren atención.",
            ),
        ]
    )
    + "</div></section>",
)
# Contacto base; site_features.py adapta los canales a la configuración real.
pages["contacto"] = (
    "Contacto y consulta en Huancayo · Cirugía Integral",
    mast(
        "CONTACTO",
        "Tu atención comienza<br>con una conversación.",
        "Deja preparada tu solicitud de consulta. El equipo confirmará la disponibilidad cuando se conecten los canales reales.",
    )
    + (
        '<section class="wrap contact-grid">'
        "<div>"
        '<div class="contact-info">'
        '<span class="eyebrow">CONSULTORIO</span>'
        "<h2>Huancayo, Perú.</h2>"
        "<p>Dirección y nombre del consultorio por confirmar.</p>"
        "<dl>"
        "<div>"
        "<dt>WhatsApp / teléfono</dt>"
        "<dd>Por configurar</dd>"
        "</div>"
        "<div>"
        "<dt>Horario de atención</dt>"
        "<dd>Por confirmar · previa cita</dd>"
        "</div>"
        "<div>"
        "<dt>Correo para consultas</dt>"
        "<dd>Por configurar</dd>"
        "</div>"
        "</dl>"
        "</div>"
        '<div class="contact-help">'
        "<h3>¿No sabes qué consulta necesitas?</h3>"
        "<p>Describe brevemente el motivo. El equipo de atención podrá orientarte sobre cómo reservar.</p>"
        "</div>"
        "</div>"
        '<form id="appointment-form" class="form-card">'
        "<h2>Solicitar una consulta</h2>"
        "<p>Prepara tu mensaje en pocos pasos.</p>"
        '<label for="name">Nombre completo</label>'
        '<input id="name" name="name" autocomplete="name" placeholder="Tu nombre" required maxlength="100">'
        '<label for="phone">Celular</label>'
        '<input id="phone" name="phone" type="tel" autocomplete="tel" placeholder="Tu número de contacto" required maxlength="30">'
        '<label for="reason">Motivo de consulta</label>'
        '<select id="reason" name="reason">'
        "<option>Evaluación de vesícula</option>"
        "<option>Evaluación de hernia</option>"
        "<option>Consulta sobre laparoscopia</option>"
        "<option>Otra consulta de cirugía general</option>"
        "</select>"
        '<button class="button" type="submit">Preparar solicitud</button>'
        '<p class="form-note">Esta versión de muestra no envía ni guarda datos.</p>'
        '<div id="form-result" role="status" hidden>'
        "<h3>Tu mensaje está preparado</h3>"
        '<p id="request-message">'
        "</p>"
        "<p>Falta conectar el teléfono del consultorio para enviarlo y confirmar una cita.</p>"
        '<button type="button" class="button outline" id="copy-message">Copiar mensaje</button>'
        '<span id="copy-status" role="status">'
        "</span>"
        "</div>"
        "</form>"
        "</section>"
    ),
)
# 5. Descripciones para buscadores y ajustes finales de contenido.
descriptions = {
    "": "Cirugía general y laparoscópica en Huancayo con el Dr. Hector Rodríguez Aquiño. Conoce las áreas de atención y prepara tu consulta.",
    "doctor": "Conoce al Dr. Hector Rodríguez Aquiño, cirujano general en Huancayo, y su enfoque de evaluación individual y atención laparoscópica.",
    "servicios": "Información sobre cirugía de vesícula, hernias abdominales y laparoscopia en Huancayo. Conoce qué se evalúa y las opciones para tu caso.",
    "vesicula": "Conoce la evaluación de cálculos biliares y la cirugía de vesícula por laparoscopia en Huancayo: procedimiento, preparación y seguimiento.",
    "hernias": "Información sobre hernias inguinales, umbilicales e incisionales en Huancayo: evaluación, opciones de reparación y recuperación.",
    "laparoscopia": "Conoce en qué consiste la cirugía laparoscópica, cuándo puede considerarse y qué conversar con el cirujano en Huancayo.",
    "guia-del-paciente": "Prepara tu consulta de cirugía general: qué llevar, qué preguntar y cómo conversar sobre preparación, recuperación y seguimiento.",
    "contacto": "Información de contacto del Dr. Hector Rodríguez Aquiño en Huancayo y formulario para preparar una solicitud de consulta.",
}
# La especialidad y las ciudades del encabezado se editan en adapt(),
# dentro de site_features.py, en el bloque hero_intro.
pages, descriptions = adapt(pages, descriptions, mast, faq)


# 6. Metadatos estructurados y plantilla común: cabecera, menú y pie.
def page_metadata(slug, title):
    canonical = site_url + (slug + "/" if slug else "")
    graph = [
        {
            "@type": "WebSite",
            "@id": site_url + "#website",
            "url": site_url,
            "name": "Cirugía Integral · Dr. Hector Rodríguez Aquiño",
            "inLanguage": "es-PE",
        },
        {
            "@type": "WebPage",
            "@id": canonical + "#webpage",
            "url": canonical,
            "name": title,
            "description": descriptions[slug],
            "inLanguage": "es-PE",
            "isPartOf": {"@id": site_url + "#website"},
        },
    ]
    if slug:
        crumbs = [
            {"@type": "ListItem", "position": 1, "name": "Inicio", "item": site_url}
        ]
        if slug in data:
            crumbs.append(
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": "Servicios",
                    "item": site_url + "servicios/",
                }
            )
        crumbs.append(
            {
                "@type": "ListItem",
                "position": len(crumbs) + 1,
                "name": title.split(" · ")[0],
                "item": canonical,
            }
        )
        graph.append(
            {
                "@type": "BreadcrumbList",
                "@id": canonical + "#breadcrumbs",
                "itemListElement": crumbs,
            }
        )
        graph[1]["breadcrumb"] = {"@id": canonical + "#breadcrumbs"}
    graph.extend(identity_graph(site_url))
    graph[1]["about"] = {"@id": site_url + "#doctor"}
    if slug in data and editorial["reviewer"]:
        graph.append(
            {
                "@type": "Article",
                "@id": canonical + "#article",
                "headline": title,
                "mainEntityOfPage": {"@id": canonical + "#webpage"},
                "datePublished": editorial["published"],
                "dateModified": editorial["reviewed"],
                "author": {"@type": "Organization", "name": editorial["author"]},
                "url": canonical,
            }
        )
        graph[1]["reviewedBy"] = {"@type": "Person", "name": editorial["reviewer"]}
        graph[1]["lastReviewed"] = editorial["reviewed"]
    structured = json.dumps(
        {"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False
    ).replace("<", "\\u003c")
    return (
        f'<link rel="canonical" href="{html.escape(canonical,quote=True)}">'
        f'<script type="application/ld+json">{structured}</script>'
    )


brand_symbol = (
    '<span class="brand-mark brand-monogram" aria-hidden="true">'
    '<svg viewBox="0 0 64 64" role="img">'
    '<text class="brand-monogram-letter" x="32" y="53" text-anchor="middle">R</text>'
    '<g class="brand-monogram-instrument">'
    '<circle cx="8" cy="21" r="5.2"/>'
    '<circle cx="8" cy="35" r="5.2"/>'
    '<path d="M12 24l5 3M12 32l5-3"/>'
    '<circle cx="19" cy="28" r="3.1"/>'
    '<path d="M22 29l34 14M53 42l8-3M53 44l7 6"/>'
    "</g>"
    "</svg>"
    "</span>"
)

# El favicon usa el mismo monograma R del encabezado para conservar la identidad
# visual incluso en el reducido espacio de una pestaña del navegador.
favicon_svg = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<text x="32" y="53" text-anchor="middle" fill="#10283d" '
    'font-family="Georgia,serif" font-size="58">R</text>'
    '<g fill="none" stroke="#087e83" stroke-width="2.6" '
    'stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="8" cy="21" r="5.2"/><circle cx="8" cy="35" r="5.2"/>'
    '<path d="M12 24l5 3M12 32l5-3"/><circle cx="19" cy="28" r="3.1"/>'
    '<path d="M22 29l34 14M53 42l8-3M53 44l7 6"/>'
    '</g></svg>'
)
favicon_data = quote(favicon_svg, safe="")


for slug, (title, body) in pages.items():
    navigation = "".join(
        f'<a href="{url(s)}"'
        + (
            ' aria-current="page"'
            if s == slug or s == "servicios" and slug in data
            else ""
        )
        + f">{label}</a>"
        for s, label in nav
    )
    head = (
        f"""<!doctype html>"""
        f"""<html lang="es">"""
        f"""<head>"""
        f"""<meta charset="utf-8">"""
        f"""<meta name="viewport" content="width=device-width, initial-scale=1">"""
        f"""<title>{title}</title>"""
        f"""<meta name="description" content="{html.escape(descriptions[slug],quote=True)}">"""
        f"""<meta name="robots" content="{robots}">{page_metadata(slug,title)}<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,{favicon_data}">"""
        f"""<link rel="stylesheet" href="/style.css?v=20261015-side-arrows">"""
        f"""<script defer src="/app.js?v=20261015-side-arrows">"""
        f"""</script>"""
        f"""</head>"""
        f"""<body>"""
        f"""<a class="skip" href="#main">Ir al contenido</a>"""
        f"""<header>"""
        f"""<div class="wrap header-inner">"""
        f"""<a class="brand" href="/" aria-label="Cirugía Integral, inicio">"""
        f"""{brand_symbol}"""
        f"""<span>Cirugía Integral<small>DR. HECTOR RODRÍGUEZ AQUIÑO</small>"""
        f"""</span>"""
        f"""</a>"""
        f"""<button class="menu-toggle" aria-label="Abrir menú" aria-expanded="false" aria-controls="navigation">Menú</button>"""
        f"""<nav id="navigation" aria-label="Navegación principal">{navigation}</nav>"""
        f"""<a class="button header-cta" href="/contacto/">Agendar consulta</a>"""
        f"""</div>"""
        f"""</header>"""
        f"""<main id="main">{body}</main>"""
        f"""<footer>"""
        f"""<div class="wrap footer-grid">"""
        f"""<div>"""
        f"""<a class="brand" href="/">"""
        f"""{brand_symbol}"""
        f"""<span>Cirugía Integral<small>CIRUGÍA GENERAL Y LAPAROSCÓPICA</small>"""
        f"""</span>"""
        f"""</a>"""
        f"""<p>Atención informada.<br>Acompañamiento en cada etapa.</p>"""
        f"""</div>"""
        f"""<div>"""
        f"""<h3>Explora</h3>"""
        f"""<a href="/doctor/">El doctor</a>"""
        f"""<a href="/servicios/">Servicios</a>"""
        f"""<a href="/guia-del-paciente/">Guía del paciente</a>"""
        f"""</div>"""
        f"""<div>"""
        f"""<h3>Tu consulta</h3>"""
        f"""<p>Huancayo, Perú</p>"""
        f"""<a href="/contacto/">Contacto y ubicación</a>"""
        f"""</div>"""
        f"""</div>"""
        f"""<div class="wrap footer-bottom">"""
        f"""<span>© 2026 Cirugía Integral</span>"""
        f"""<span>Propuesta de diseño · Datos del consultorio por completar</span>"""
        f"""</div>"""
        f"""</footer>"""
        f"""</body>"""
        f"""</html>"""
    )
    head = head.replace(
        "</head>", extra_head(site_url, slug, title, descriptions[slug]) + "</head>"
    )
    head = re.sub(r'<button class="menu-toggle".*?</button>', "", head)
    head = head.replace(
        '<nav id="navigation"', '<nav class="desktop-navigation" id="navigation"'
    )
    head = head.replace(
        '</nav><a class="button header-cta"',
        '</nav><details class="mobile-navigation"><summary>Menú</summary><nav aria-label="Navegación móvil">'
        + navigation
        + '</nav></details><a class="button header-cta"',
    )
    head = (
        head.replace("HECTOR", "HÉCTOR")
        .replace("Hector", "Héctor")
        .replace("Huancayo, Perú", "Ubicación pendiente de confirmar")
    )
    if clinic["city"]:
        head = head.replace(
            "Ubicación pendiente de confirmar", html.escape(clinic["city"])
        )
    else:
        head = head.replace("<p>Ubicación pendiente de confirmar</p>", "")
    head = head.replace(
        "Propuesta de diseño · Datos del consultorio por completar",
        "Datos profesionales y del consultorio sujetos a verificación",
    )
    head = head.replace("</footer>", '<div class="wrap">' + nap() + "</div></footer>")
    if settings["analyticsId"]:
        head = head.replace(
            "</body>",
            (
                f'<aside class="wrap analytics-consent" aria-label="Preferencias de medición">'
                f"<p>Con tu permiso medimos clics de contacto, sin enviar nombres, teléfonos ni información médica.</p>"
                f'<button type="button" id="analytics-accept" data-id="{html.escape(settings["analyticsId"],quote=True)}">Aceptar medición</button> <button type="button" id="analytics-decline">Rechazar o retirar permiso</button>'
                f'<p id="analytics-status" role="status">'
                f"</p>"
                f"</aside>"
                f"</body>"
            ),
        )
    # Relative URLs work at localhost, a GitHub repository path, or a custom domain.
    prefix = "../" if slug else "./"
    head = re.sub(
        r'(href|src)="/(?!/)([^"]*)"',
        lambda match: f'{match[1]}="{prefix}{match[2]}"',
        head,
    )
    head = re.sub(
        r'srcset="([^"]+)"',
        lambda match: 'srcset="'
        + re.sub(r"/(assets/)", prefix + r"\1", match[1])
        + '"',
        head,
    )
    target = root / slug if slug else root
    target.mkdir(parents=True, exist_ok=True)
    (target / "index.html").write_text(head, encoding="utf-8")
# Compatibilidad con enlaces guardados antes de estandarizar la ruta Servicios.
legacy_services = root / "tratamientos"
legacy_services.mkdir(parents=True, exist_ok=True)
(legacy_services / "index.html").write_text(
    '<!doctype html><html lang="es"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width, initial-scale=1">'
    '<title>Servicios · Cirugía Integral</title>'
    '<meta name="robots" content="noindex,follow">'
    '<meta http-equiv="refresh" content="0;url=../servicios/">'
    f'<link rel="canonical" href="{html.escape(site_url, quote=True)}servicios/">'
    '</head><body><p>Ir a <a href="../servicios/">Servicios</a>.</p></body></html>',
    encoding="utf-8",
)

# The wildcard group also permits search crawlers such as Googlebot, Bingbot
# and OAI-SearchBot. Search access and AI training are separate policies.
# 7. Archivos públicos auxiliares: robots.txt, sitemap y página 404.
robots_text = "User-agent: *\n" + ("Allow: /\n" if indexable else "Disallow: /\n")
if indexable:
    robots_text += "\nSitemap: " + site_url + "sitemap.xml\n"
if indexable and not settings["allowAITraining"]:
    robots_text += "\n# Training controls; search bots remain allowed.\nUser-agent: GPTBot\nDisallow: /\n\nUser-agent: Google-Extended\nDisallow: /\n"
(root / "robots.txt").write_text(robots_text, encoding="utf-8")
ET.register_namespace("", "http://www.sitemaps.org/schemas/sitemap/0.9")
sitemap = ET.Element("{http://www.sitemaps.org/schemas/sitemap/0.9}urlset")
if indexable:
    for slug in pages:
        entry = ET.SubElement(
            sitemap, "{http://www.sitemaps.org/schemas/sitemap/0.9}url"
        )
        ET.SubElement(
            entry, "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
        ).text = site_url + (slug + "/" if slug else "")
ET.ElementTree(sitemap).write(
    root / "sitemap.xml", encoding="utf-8", xml_declaration=True
)
# GitHub Pages serves this document with HTTP 404 for nonexistent paths.
(root / "404.html").write_text(
    (
        "<!doctype html>"
        '<html lang="es">'
        "<head>"
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>Página no encontrada · Cirugía Integral</title>"
        '<meta name="robots" content="noindex,follow">'
        "</head>"
        "<body>"
        "<main>"
        "<h1>Página no encontrada</h1>"
        "<p>La dirección solicitada no existe.</p>"
        '<a href="'
    )
    + html.escape(site_url, quote=True)
    + '">Volver al inicio</a></main></body></html>',
    encoding="utf-8",
)
(root / ".nojekyll").touch()
