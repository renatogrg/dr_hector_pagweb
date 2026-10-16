"""Single source of verified identity and conditional integrations. No invented NAP."""

import html, json, re, os
from datetime import date
from pathlib import Path

settings = json.loads(
    Path(
        os.environ.get("MEDICAL_CONFIG", Path(__file__).parent / "medical.config.json")
    ).read_text(encoding="utf-8")
)
doctor, clinic, editorial = (settings[k] for k in ("doctor", "clinic", "editorial"))
e = lambda value: html.escape(str(value), quote=True)
for key in ("phone", "whatsapp"):
    if clinic[key] and not re.fullmatch(r"\+[1-9]\d{7,14}", clinic[key]):
        raise ValueError(f"clinic.{key}: usar número internacional E.164 (+...).")
if clinic["mapsUrl"] and not clinic["mapsUrl"].startswith(
    (
        "https://www.google.com/maps",
        "https://maps.google.com/",
        "https://maps.app.goo.gl/",
    )
):
    raise ValueError("mapsUrl debe ser un enlace HTTPS de Google Maps verificado.")
if settings["analyticsId"] and not re.fullmatch(
    r"G-[A-Z0-9]+", settings["analyticsId"]
):
    raise ValueError("analyticsId debe ser un identificador GA4 G-... válido.")
if clinic["country"] and not re.fullmatch(r"[A-Z]{2}", clinic["country"]):
    raise ValueError("clinic.country debe ser un código ISO de dos letras.")
if not set(settings["confirmedServices"]) <= {"vesicula", "hernias", "laparoscopia"}:
    raise ValueError(
        "Servicio sin página educativa: agregar su contenido antes de anunciarlo."
    )
if not isinstance(settings["allowAITraining"], bool):
    raise ValueError("allowAITraining debe ser booleano.")
date.fromisoformat(editorial["published"])
if bool(editorial["reviewer"]) != bool(editorial["reviewed"]):
    raise ValueError("El revisor y la fecha real de revisión se completan juntos.")
if editorial["reviewed"] and date.fromisoformat(
    editorial["reviewed"]
) < date.fromisoformat(editorial["published"]):
    raise ValueError("Revisión anterior a publicación.")
for slot in clinic["hours"]:
    assert slot["days"] and all(
        day
        in (
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        )
        for day in slot["days"]
    )
    assert re.fullmatch(r"\d{2}:\d{2}", slot["opens"]) and re.fullmatch(
        r"\d{2}:\d{2}", slot["closes"]
    )
    assert "00:00" <= slot["opens"] < slot["closes"] <= "23:59"


def links():
    result = []
    if clinic["phone"]:
        result.append(
            f'<a class="button" data-event="call_click" href="tel:{e(clinic["phone"])}">Llamar al consultorio</a>'
        )
    if clinic["whatsapp"]:
        result.append(
            f'<a class="button outline" data-event="whatsapp_click" href="https://wa.me/{clinic["whatsapp"][1:]}">Contactar por WhatsApp</a>'
        )
    if clinic["mapsUrl"]:
        result.append(
            f'<a class="text-link" href="{e(clinic["mapsUrl"])}">Abrir ubicación en Google Maps</a>'
        )
    return '<div class="actions">' + "".join(result) + "</div>" if result else ""


def nap():
    names = {
        "Monday": "lunes",
        "Tuesday": "martes",
        "Wednesday": "miércoles",
        "Thursday": "jueves",
        "Friday": "viernes",
        "Saturday": "sábado",
        "Sunday": "domingo",
    }
    address = ", ".join(
        str(clinic[k])
        for k in ("streetAddress", "city", "region", "postalCode", "country")
        if clinic[k]
    )
    hours = "; ".join(
        ", ".join(names[d] for d in s["days"]) + ": " + s["opens"] + "–" + s["closes"]
        for s in clinic["hours"]
    )
    rows = [
        ("Profesional", doctor["name"]),
        ("Consultorio", clinic["name"]),
        ("Dirección", address),
        ("Teléfono", clinic["phone"]),
        ("Horarios", hours),
    ]
    return (
        '<dl class="nap">'
        + "".join(
            (f"<div>" f"<dt>{label}</dt>" f"<dd>{e(value)}</dd>" f"</div>")
            for label, value in rows
            if value
        )
        + "</dl>"
    )


def identity_graph(base):
    physician = {
        "@type": "IndividualPhysician",
        "@id": base + "#doctor",
        "name": doctor["name"],
        "url": base + "doctor/",
        "medicalSpecialty": "https://schema.org/Surgical",
    }
    graph = [physician]
    # Emit the physical clinic only with real name and address; keep it separate.
    if (
        clinic["name"]
        and clinic["streetAddress"]
        and clinic["city"]
        and clinic["country"]
    ):
        address = {"@type": "PostalAddress"}
        for source, target in [
            ("streetAddress", "streetAddress"),
            ("city", "addressLocality"),
            ("region", "addressRegion"),
            ("postalCode", "postalCode"),
            ("country", "addressCountry"),
        ]:
            if clinic[source]:
                address[target] = clinic[source]
        office = {
            "@type": "MedicalClinic",
            "@id": base + "#clinic",
            "name": clinic["name"],
            "address": address,
            "url": base + "contacto/",
            "medicalSpecialty": "https://schema.org/Surgical",
        }
        if clinic["phone"]:
            office["telephone"] = clinic["phone"]
        if clinic["mapsUrl"]:
            office["hasMap"] = clinic["mapsUrl"]
        if clinic["hours"]:
            office["openingHoursSpecification"] = [
                {
                    "@type": "OpeningHoursSpecification",
                    "dayOfWeek": ["https://schema.org/" + d for d in s["days"]],
                    "opens": s["opens"],
                    "closes": s["closes"],
                }
                for s in clinic["hours"]
            ]
        graph.append(office)
        physician["practicesAt"] = {"@id": office["@id"]}
    return graph


def extra_head(base, slug, title, description):
    canonical = base + (slug + "/" if slug else "")
    properties = {
        "og:type": "website",
        "og:locale": "es_PE",
        "og:site_name": doctor["name"],
        "og:title": title,
        "og:description": description,
        "og:url": canonical,
        "og:image": base + "assets/hector-rodriguez-960.webp",
        "og:image:alt": doctor["name"],
    }
    result = "".join(
        f'<meta property="{key}" content="{e(value)}">'
        for key, value in properties.items()
    )
    if settings["searchConsoleVerification"]:
        result += f'<meta name="google-site-verification" content="{e(settings["searchConsoleVerification"])}">'
    return result


def editorial_block(sources):
    revision = (
        f'Revisión médica: {e(editorial["reviewer"])} · <time datetime="{editorial["reviewed"]}">{editorial["reviewed"]}</time>.'
        if editorial["reviewer"]
        else "Revisión médica pendiente."
    )
    return (
        (
            f'<section class="medical-note">'
            f"<h2>Autoría y fuentes</h2>"
            f'<p>Autor: {e(editorial["author"])}. Publicación del borrador: <time datetime="{editorial["published"]}">{editorial["published"]}</time>. {revision}</p>'
            f"<ul>"
        )
        + "".join(
            (f"<li>" f'<a class="text-link" href="{e(link)}">{e(label)}</a>' f"</li>")
            for label, link in sources
        )
        + (
            "</ul>"
            "<p>Información general; las indicaciones de preparación y recuperación se individualizan en consulta.</p>"
            "</section>"
        )
    )


# Ajustes finales de cada página: estos bloques se aplican al contenido base
# definido en generate.py antes de escribir los archivos HTML.
def adapt(pages, descriptions, mast, faq):
    for slug, (title, body) in list(pages.items()):
        title = title.replace(" en Huancayo", "").replace("Huancayo · ", "")
        body = (
            body.replace("Hector", "Héctor")
            .replace(" · HUANCAYO", "")
            .replace(" en Huancayo", "")
            .replace("Huancayo, Perú", "Ubicación de atención pendiente de confirmar")
        )
        body = body.replace("Mi enfoque comienza", "La evaluación comienza")
        body = body.replace("Conocer el tratamiento", "Ver información completa").replace(
            "Otros servicios.", "Servicios quirúrgicos."
        )
        body = body.replace(
            "Evaluación de cálculos biliares y opciones de tratamiento laparoscópico.",
            "Información educativa sobre cálculos biliares y opciones de tratamiento.",
        ).replace(
            "Valoración de hernias inguinales, umbilicales e incisionales.",
            "Información educativa sobre hernias inguinales, umbilicales e incisionales.",
        )
        body = body.replace("Áreas de atención", "Servicios quirúrgicos")
        body = (
            re.sub(
                r'<div class="credential-box">.*?</div><a class="button"',
                (
                    '<div class="credential-box">'
                    "<h3>Perfil profesional</h3>"
                    "<p>Especialidad indicada: cirugía general y laparoscopia.</p>"
                )
                + (
                    "".join(
                        f"<p>{label}: {e(value)}</p>"
                        for label, value in [
                            ("CMP", doctor["cmp"]),
                            ("RNE", doctor["rne"]),
                            ("Experiencia", doctor["experience"]),
                        ]
                        if value
                    )
                )
                + "".join(f"<p>{e(t)}</p>" for t in doctor["training"])
                + (
                    "<p>La formación y los registros profesionales se incorporarán tras su verificación.</p>"
                    "</div>"
                    '<a class="button"'
                ),
                body,
                flags=re.S,
            )
            if slug == "doctor"
            else body
        )
        body = body.replace(
            'src="/assets/hector-rodriguez.png"',
            'src="/assets/hector-rodriguez-960.webp" srcset="/assets/hector-rodriguez-640.webp 640w, /assets/hector-rodriguez-960.webp 960w" sizes="(max-width: 760px) 100vw, 57vw"',
        )
        body = body.replace('width="800" height="1000"', 'width="960" height="1290"')
        if slug == "doctor":
            body = body.replace(
                'height="1290"', 'height="1290" loading="lazy" decoding="async"'
            )
        pages[slug] = (title, body)
        descriptions[slug] = (
            descriptions[slug].replace(" en Huancayo", "").replace("Hector", "Héctor")
        )
    hero_intro = (
        '<div class="hero-intro">'
        '<span class="eyebrow hero-specialty">CIRUGIA GENERAL Y LAPAROSCÓPICA</span>'
        '<div class="hero-locations">'
        '<ul aria-label="Lugares de atención">'
        "<li>Huancayo</li>"
        "<li>La Merced</li>"
        "<li>Lima</li>"
        "<li>Junín</li>"
        "</ul>"
        "</div>"
        "</div>"
    )
    pages[""] = (
        "Dr. Héctor Rodríguez Aquiño | Cirugía general y laparoscopia",
        pages[""][1].replace(
            '<span class="eyebrow">CIRUGÍA GENERAL</span>', hero_intro
        ),
    )
    # Un solo carrusel compartido mantiene Inicio y Servicios sincronizados.
    service_carousel = (
            '<div class="services-carousel" data-services-carousel>'
            '<div class="services-grid">'
            '<a class="service-option service-option--featured" href="/laparoscopia/">'
            '<span class="service-status">Servicio quirúrgico</span>'
            "<h2>Cirugía laparoscópica</h2>"
            "<p>Comprende este abordaje de mínima invasión y cuándo podría ser una opción.</p>"
            '<span class="text-link">Ver información completa</span>'
            "</a>"
            '<a class="service-option" href="/vesicula/">'
            '<span class="service-status">Servicio quirúrgico</span>'
            "<h2>Colecistectomía</h2>"
            "<p>Extracción de la vesícula por laparoscopia o cirugía abierta, según la evaluación médica.</p>"
            '<span class="text-link">Ver información completa</span>'
            "</a>"
            '<a class="service-option" href="/hernias/">'
            '<span class="service-status">Servicio quirúrgico</span>'
            "<h2>Reparación de hernias abdominales</h2>"
            "<p>Reparación por laparoscopia o cirugía abierta, con el abordaje indicado para cada caso.</p>"
            '<span class="text-link">Ver información completa</span>'
            "</a>"
            '<article class="service-option service-option--placeholder">'
            '<span class="service-status">Pendiente de confirmar</span>'
            "<h2>Servicio adicional 04</h2>"
            "<p>El nombre y los detalles de este servicio se incorporarán al confirmar la información del doctor.</p>"
            '<span class="text-link service-link-disabled">Próximamente</span>'
            "</article>"
            '<article class="service-option service-option--placeholder">'
            '<span class="service-status">Pendiente de confirmar</span>'
            "<h2>Servicio adicional 05</h2>"
            "<p>El nombre y los detalles de este servicio se incorporarán al confirmar la información del doctor.</p>"
            '<span class="text-link service-link-disabled">Próximamente</span>'
            "</article>"
            "</div>"
            '<div class="services-carousel-controls" aria-label="Navegación de servicios">'
            '<button type="button" class="carousel-button" data-carousel-prev aria-label="Servicio anterior">←</button>'
            '<button type="button" class="carousel-button" data-carousel-next aria-label="Servicio siguiente">→</button>'
            "</div>"
            "</div>"
    )
    pages["servicios"] = (
        "Servicios de cirugía general y laparoscopia",
        '<div class="page-entry">'
        + mast(
            "SERVICIOS",
            "Atención quirúrgica con información clara.",
            "Conoce los servicios quirúrgicos y prepara tus preguntas antes de conversar sobre tu caso.",
        ).replace('class="mast wrap"', 'class="mast wrap compact-mast"')
        + (
            '<section class="wrap services-overview">'
            '<div class="services-heading">'
            '<span class="eyebrow">ÁREAS DE ATENCIÓN</span>'
            "<h2>Información para decidir con claridad.</h2>"
            "<p>La cirugía general y laparoscópica requiere una evaluación individual. Conoce los procedimientos y prepara tus preguntas para la consulta.</p>"
            "</div>"
        )
        + service_carousel
        + (
            "</section></div>"
            '<div class="service-consultation-section">'
            '<section class="wrap services-cta">'
            "<div>"
            '<span class="eyebrow">CONSULTA ESPECIALIZADA</span>'
            "<h2>¿Necesitas una evaluación quirúrgica?</h2>"
            "<p>Conversa sobre tus síntomas, estudios previos y las alternativas que podrían corresponder a tu caso.</p>"
            "</div>"
            '<a class="button light" href="/contacto/">Solicitar una consulta</a>'
            "</section></div>"
        ),
    )
    pages[""] = (
        pages[""][0],
        re.sub(
            r'<div class="service-grid">.*?</div>',
            lambda match: service_carousel,
            pages[""][1],
            count=1,
            flags=re.S,
        ),
    )
    pages["contacto"] = (
        "Contacto | Dr. Héctor Rodríguez Aquiño",
        mast(
            "CONTACTO",
            "Contacto y atención.",
            "Los canales de atención se incorporarán cuando sus datos estén confirmados.",
        )
        + '<section class="wrap contact-grid"><div>'
        + nap()
        + links()
        + (
            "<p>La dirección, el teléfono y los horarios que todavía no aparecen están pendientes de configuración.</p>"
            "</div>"
            '<div class="form-card">'
            "<h2>Solicitar disponibilidad</h2>"
        )
        + (
            (
                '<form id="appointment-form">'
                '<label for="channel">Canal de atención</label>'
                '<select id="channel" name="channel">'
                "<option>WhatsApp del consultorio</option>"
                "</select>"
                '<button class="button" type="submit" data-whatsapp="'
            )
            + clinic["whatsapp"][1:]
            + (
                '">Abrir solicitud en WhatsApp</button>'
                "<p>Se prepara un mensaje genérico para consultar disponibilidad. La cita solo se confirma con el consultorio.</p>"
                "<noscript>"
                "<p>Usa el enlace directo a WhatsApp para consultar disponibilidad.</p>"
                "</noscript>"
                "</form>"
            )
            if clinic["whatsapp"]
            else "<p>La solicitud de cita estará disponible al confirmar un canal real de atención.</p>"
        )
        + (
            "<p>No incluyas diagnósticos, resultados, documentos ni otra información médica en consultas iniciales por la web.</p>"
            "</div>"
            "</section>"
        ),
    )
    questions = [
        (
            "¿Qué es la cirugía general?",
            "Es una especialidad quirúrgica que evalúa distintas enfermedades, entre ellas problemas del abdomen. La consulta permite estudiar cada caso y decidir si requiere cirugía.",
        ),
        (
            "¿Qué es la laparoscopia?",
            "Es un abordaje que utiliza una cámara e instrumentos introducidos mediante pequeñas incisiones. Su idoneidad depende del procedimiento y de la evaluación.",
        ),
        (
            "¿Debo suspender mis medicamentos?",
            "No los suspendas por tu cuenta. Informa al equipo sobre todos tus medicamentos y sigue las indicaciones individualizadas.",
        ),
        (
            "¿La consulta confirma una cirugía?",
            "No. Primero se realiza una evaluación y se explican las opciones disponibles.",
        ),
        (
            "¿Cómo solicito una cita?",
            "Cuando se publiquen los canales verificados de contacto, podrás consultar disponibilidad. Una solicitud no equivale a una cita confirmada.",
        ),
    ]
    # Expanded answers are initial HTML, including without JS or user interaction.
    pages["preguntas-frecuentes"] = (
        "Preguntas frecuentes sobre consulta y cirugía",
        mast(
            "PREGUNTAS FRECUENTES",
            "Respuestas para preparar tu consulta.",
            "Información general sobre evaluación, laparoscopia y decisiones médicas.",
        ).replace('class="mast wrap"', 'class="mast wrap compact-mast"')
        + '<section class="wrap questions-list" aria-label="Preguntas y respuestas">'
        + "".join(
            (f"<article>" f"<h2>{e(q)}</h2>" f"<p>{e(a)}</p>" f"</article>")
            for q, a in questions
        )
        + "</section>",
    )
    descriptions["preguntas-frecuentes"] = (
        "Respuestas claras sobre cirugía general, laparoscopia, evaluación, medicamentos y solicitud de consulta con el Dr. Héctor Rodríguez Aquiño."
    )
    sources = {
        "vesicula": [
            (
                "NIDDK: tratamiento de los cálculos biliares",
                "https://www.niddk.nih.gov/health-information/digestive-diseases/gallstones/treatment",
            )
        ],
        "hernias": [
            (
                "NIDDK: hernia inguinal",
                "https://www.niddk.nih.gov/health-information/digestive-diseases/inguinal-hernia",
            )
        ],
        "laparoscopia": [
            (
                "NHS: laparoscopia",
                "https://www.nhs.uk/tests-and-treatments/laparoscopy/",
            )
        ],
    }
    for slug in sources:
        title, body = pages[slug]
        if slug not in settings["confirmedServices"]:
            title = {
                "vesicula": "Guía educativa sobre cirugía de vesícula",
                "hernias": "Guía educativa sobre hernias abdominales",
            }[slug]
        pages[slug] = (title, body)
    descriptions["contacto"] = (
        "Consulta los canales de atención verificados del Dr. Héctor Rodríguez Aquiño y cómo solicitar disponibilidad."
    )
    descriptions["servicios"] = (
        "Servicios de cirugía general y laparoscópica: colecistectomía, reparación de hernias y abordajes de mínima invasión."
    )
    # Local identity appears only with a supplied verified locality.
    if clinic["city"]:
        pages[""] = (
            pages[""][0] + " en " + clinic["city"],
            pages[""][1].replace(
                "Ubicación de atención pendiente de confirmar", e(clinic["city"])
            ),
        )
        descriptions[""] += " Atención en " + clinic["city"] + "."
        pages["contacto"] = (
            pages["contacto"][0] + " en " + clinic["city"],
            pages["contacto"][1],
        )
        descriptions["contacto"] += " Atención en " + clinic["city"] + "."
    return pages, descriptions
