"""Single source of verified identity and conditional integrations. No invented NAP."""
import html, json, re, os
from datetime import date
from pathlib import Path

settings = json.loads(Path(os.environ.get('MEDICAL_CONFIG',Path(__file__).parent / 'medical.config.json')).read_text(encoding='utf-8'))
doctor, clinic, editorial = (settings[k] for k in ('doctor', 'clinic', 'editorial'))
e = lambda value: html.escape(str(value), quote=True)
for key in ('phone', 'whatsapp'):
    if clinic[key] and not re.fullmatch(r'\+[1-9]\d{7,14}', clinic[key]):
        raise ValueError(f'clinic.{key}: usar número internacional E.164 (+...).')
if clinic['mapsUrl'] and not clinic['mapsUrl'].startswith(('https://www.google.com/maps', 'https://maps.google.com/', 'https://maps.app.goo.gl/')):
    raise ValueError('mapsUrl debe ser un enlace HTTPS de Google Maps verificado.')
if settings['analyticsId'] and not re.fullmatch(r'G-[A-Z0-9]+', settings['analyticsId']):
    raise ValueError('analyticsId debe ser un identificador GA4 G-... válido.')
if clinic['country'] and not re.fullmatch(r'[A-Z]{2}',clinic['country']):
    raise ValueError('clinic.country debe ser un código ISO de dos letras.')
if not set(settings['confirmedServices']) <= {'vesicula','hernias','laparoscopia'}:
    raise ValueError('Servicio sin página educativa: agregar su contenido antes de anunciarlo.')
if not isinstance(settings['allowAITraining'], bool):
    raise ValueError('allowAITraining debe ser booleano.')
date.fromisoformat(editorial['published'])
if bool(editorial['reviewer']) != bool(editorial['reviewed']):
    raise ValueError('El revisor y la fecha real de revisión se completan juntos.')
if editorial['reviewed'] and date.fromisoformat(editorial['reviewed']) < date.fromisoformat(editorial['published']):
    raise ValueError('Revisión anterior a publicación.')
for slot in clinic['hours']:
    assert slot['days'] and all(day in ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday') for day in slot['days'])
    assert re.fullmatch(r'\d{2}:\d{2}', slot['opens']) and re.fullmatch(r'\d{2}:\d{2}', slot['closes'])
    assert '00:00' <= slot['opens'] < slot['closes'] <= '23:59'

def links():
    result = []
    if clinic['phone']:
        result.append(f'<a class="button" data-event="call_click" href="tel:{e(clinic["phone"])}">Llamar al consultorio</a>')
    if clinic['whatsapp']:
        result.append(f'<a class="button outline" data-event="whatsapp_click" href="https://wa.me/{clinic["whatsapp"][1:]}">Contactar por WhatsApp</a>')
    if clinic['mapsUrl']:
        result.append(f'<a class="text-link" href="{e(clinic["mapsUrl"])}">Abrir ubicación en Google Maps</a>')
    return '<div class="actions">' + ''.join(result) + '</div>' if result else ''

def nap():
    names = {'Monday':'lunes','Tuesday':'martes','Wednesday':'miércoles','Thursday':'jueves','Friday':'viernes','Saturday':'sábado','Sunday':'domingo'}
    address = ', '.join(str(clinic[k]) for k in ('streetAddress','city','region','postalCode','country') if clinic[k])
    hours = '; '.join(', '.join(names[d] for d in s['days']) + ': ' + s['opens'] + '–' + s['closes'] for s in clinic['hours'])
    rows = [('Profesional',doctor['name']),('Consultorio',clinic['name']),('Dirección',address),('Teléfono',clinic['phone']),('Horarios',hours)]
    return '<dl class="nap">' + ''.join(f'<div><dt>{label}</dt><dd>{e(value)}</dd></div>' for label,value in rows if value) + '</dl>'

def identity_graph(base):
    physician = {'@type':'IndividualPhysician','@id':base+'#doctor','name':doctor['name'],'url':base+'doctor/','medicalSpecialty':'https://schema.org/Surgical'}
    graph = [physician]
    # Emit the physical clinic only with real name and address; keep it separate.
    if clinic['name'] and clinic['streetAddress'] and clinic['city'] and clinic['country']:
        address = {'@type':'PostalAddress'}
        for source,target in [('streetAddress','streetAddress'),('city','addressLocality'),('region','addressRegion'),('postalCode','postalCode'),('country','addressCountry')]:
            if clinic[source]: address[target] = clinic[source]
        office = {'@type':'MedicalClinic','@id':base+'#clinic','name':clinic['name'],'address':address,'url':base+'contacto/','medicalSpecialty':'https://schema.org/Surgical'}
        if clinic['phone']: office['telephone'] = clinic['phone']
        if clinic['mapsUrl']: office['hasMap'] = clinic['mapsUrl']
        if clinic['hours']: office['openingHoursSpecification'] = [{'@type':'OpeningHoursSpecification','dayOfWeek':['https://schema.org/'+d for d in s['days']], 'opens':s['opens'],'closes':s['closes']} for s in clinic['hours']]
        graph.append(office)
        physician['practicesAt'] = {'@id':office['@id']}
    return graph

def extra_head(base, slug, title, description):
    canonical = base + (slug+'/' if slug else '')
    properties = {'og:type':'website','og:locale':'es_PE','og:site_name':doctor['name'],'og:title':title,'og:description':description,'og:url':canonical,'og:image':base+'assets/hector-rodriguez-960.webp','og:image:alt':doctor['name']}
    result = ''.join(f'<meta property="{key}" content="{e(value)}">' for key,value in properties.items())
    if settings['searchConsoleVerification']:
        result += f'<meta name="google-site-verification" content="{e(settings["searchConsoleVerification"])}">'
    return result

def editorial_block(sources):
    revision = f'Revisión médica: {e(editorial["reviewer"])} · <time datetime="{editorial["reviewed"]}">{editorial["reviewed"]}</time>.' if editorial['reviewer'] else 'Revisión médica pendiente. Borrador educativo: no atribuido al doctor ni aprobado por él.'
    return f'<section class="medical-note"><h2>Autoría y fuentes</h2><p>Autor: {e(editorial["author"])}. Publicación del borrador: <time datetime="{editorial["published"]}">{editorial["published"]}</time>. {revision}</p><ul>'+''.join(f'<li><a class="text-link" href="{e(link)}">{e(label)}</a></li>' for label,link in sources)+'</ul><p>Información general; las indicaciones de preparación y recuperación se individualizan en consulta.</p></section>'

def adapt(pages, descriptions, mast, faq):
    for slug,(title,body) in list(pages.items()):
        title = title.replace(' en Huancayo','').replace('Huancayo · ','')
        body = body.replace('Hector','Héctor').replace(' · HUANCAYO','').replace(' en Huancayo','').replace('Huancayo, Perú','Ubicación de atención pendiente de confirmar')
        body = body.replace('Mi enfoque comienza','La evaluación comienza')
        body = body.replace('Conocer el tratamiento','Leer información').replace('Otros tratamientos.','Más información educativa.')
        body = body.replace('Evaluación de cálculos biliares y opciones de tratamiento laparoscópico.','Información educativa sobre cálculos biliares y opciones de tratamiento.').replace('Valoración de hernias inguinales, umbilicales e incisionales.','Información educativa sobre hernias inguinales, umbilicales e incisionales.')
        body = body.replace('Áreas de atención','Información educativa')
        body = re.sub(r'<div class="credential-box">.*?</div><a class="button"', '<div class="credential-box"><h3>Perfil profesional</h3><p>Especialidad indicada: cirugía general y laparoscopia.</p>'+(''.join(f'<p>{label}: {e(value)}</p>' for label,value in [('CMP',doctor['cmp']),('RNE',doctor['rne']),('Experiencia',doctor['experience'])] if value))+''.join(f'<p>{e(t)}</p>' for t in doctor['training'])+'<p>La formación y los registros profesionales se incorporarán tras su verificación.</p></div><a class="button"', body, flags=re.S) if slug=='doctor' else body
        body = body.replace('src="/assets/hector-rodriguez.png"','src="/assets/hector-rodriguez-960.webp" srcset="/assets/hector-rodriguez-640.webp 640w, /assets/hector-rodriguez-960.webp 960w" sizes="(max-width: 760px) 100vw, 57vw"')
        body=body.replace('width="800" height="1000"','width="960" height="1290"')
        if slug == 'doctor': body=body.replace('height="1290"','height="1290" loading="lazy" decoding="async"')
        pages[slug]=(title,body)
        descriptions[slug]=descriptions[slug].replace(' en Huancayo','').replace('Hector','Héctor')
    pages['']=('Dr. Héctor Rodríguez Aquiño | Cirugía general y laparoscopia',pages[''][1].replace('Precisión quirúrgica.<br><em>Atención humana.</em>','Dr. Héctor Rodríguez Aquiño.<br><em>Cirugía general y laparoscopia.</em>'))
    pages['tratamientos']=('Servicios de cirugía general y laparoscopia',mast('SERVICIOS','Cirugía general y laparoscopia.','La evaluación individual permite conversar sobre alternativas, riesgos y recuperación.')+'<section class="wrap section"><h2>Especialidad y abordaje</h2><p>La especialidad indicada es cirugía general y laparoscopia. La indicación de un procedimiento depende de la evaluación médica.</p><a class="button" href="/laparoscopia/">Conocer la laparoscopia</a><h2>Información sobre procedimientos</h2><p>Las guías de vesícula y hernias son material educativo. La disponibilidad de estos procedimientos con el doctor está pendiente de confirmación.</p><div class="actions"><a class="text-link" href="/vesicula/">Guía sobre vesícula</a><a class="text-link" href="/hernias/">Guía sobre hernias</a></div></section>')
    pages['contacto']=('Contacto | Dr. Héctor Rodríguez Aquiño',mast('CONTACTO','Contacto y atención.','Los canales de atención se incorporarán cuando sus datos estén confirmados.')+'<section class="wrap contact-grid"><div>'+nap()+links()+'<p>La dirección, el teléfono y los horarios que todavía no aparecen están pendientes de configuración.</p></div><div class="form-card"><h2>Solicitar disponibilidad</h2>'+('<form id="appointment-form"><label for="channel">Canal de atención</label><select id="channel" name="channel"><option>WhatsApp del consultorio</option></select><button class="button" type="submit" data-whatsapp="'+clinic['whatsapp'][1:]+'">Abrir solicitud en WhatsApp</button><p>Se prepara un mensaje genérico para consultar disponibilidad. La cita solo se confirma con el consultorio.</p><noscript><p>Usa el enlace directo a WhatsApp para consultar disponibilidad.</p></noscript></form>' if clinic['whatsapp'] else '<p>La solicitud de cita estará disponible al confirmar un canal real de atención.</p>')+'<p>No incluyas diagnósticos, resultados, documentos ni otra información médica en consultas iniciales por la web.</p></div></section>')
    questions=[('¿Qué es la cirugía general?','Es una especialidad quirúrgica que evalúa distintas enfermedades, entre ellas problemas del abdomen. La consulta permite estudiar cada caso y decidir si requiere cirugía.'),('¿Qué es la laparoscopia?','Es un abordaje que utiliza una cámara e instrumentos introducidos mediante pequeñas incisiones. Su idoneidad depende del procedimiento y de la evaluación.'),('¿Debo suspender mis medicamentos?','No los suspendas por tu cuenta. Informa al equipo sobre todos tus medicamentos y sigue las indicaciones individualizadas.'),('¿La consulta confirma una cirugía?','No. Primero se realiza una evaluación y se explican las opciones disponibles.'),('¿Cómo solicito una cita?','Cuando se publiquen los canales verificados de contacto, podrás consultar disponibilidad. Una solicitud no equivale a una cita confirmada.')]
    # Expanded answers are initial HTML, including without JS or user interaction.
    pages['preguntas-frecuentes']=('Preguntas frecuentes sobre consulta y cirugía',mast('PREGUNTAS FRECUENTES','Respuestas para preparar tu consulta.','Información general sobre evaluación, laparoscopia y decisiones médicas.')+'<section class="wrap narrow section">'+''.join(f'<article><h2>{e(q)}</h2><p>{e(a)}</p></article>' for q,a in questions)+'</section>')
    descriptions['preguntas-frecuentes']='Respuestas claras sobre cirugía general, laparoscopia, evaluación, medicamentos y solicitud de consulta con el Dr. Héctor Rodríguez Aquiño.'
    sources = {'vesicula':[('NIDDK: tratamiento de los cálculos biliares','https://www.niddk.nih.gov/health-information/digestive-diseases/gallstones/treatment')], 'hernias':[('NIDDK: hernia inguinal','https://www.niddk.nih.gov/health-information/digestive-diseases/inguinal-hernia')], 'laparoscopia':[('NHS: laparoscopia','https://www.nhs.uk/tests-and-treatments/laparoscopy/')]}
    for slug in sources:
        title,body=pages[slug]
        if slug not in settings['confirmedServices']:
            title = {'vesicula':'Guía educativa sobre cirugía de vesícula', 'hernias':'Guía educativa sobre hernias abdominales'}[slug]
            body='<div class="wrap medical-note">Información educativa. Este procedimiento no se anuncia como un servicio confirmado del doctor.</div>'+body
        body += '<section class="wrap narrow section">'+editorial_block(sources[slug])+'</section>'
        pages[slug]=(title,body)
    pages['articulos']=('Artículos educativos sobre cirugía',mast('ARTÍCULOS EDUCATIVOS','Comprender antes de decidir.','Guías generales con fuentes institucionales. La revisión médica de los borradores está pendiente.')+'<section class="wrap section"><div class="service-grid">'+''.join(f'<a class="service-card" href="/{s}/"><h2>{e(pages[s][0])}</h2><p>Definición, evaluación, preparación y recuperación.</p><span class="text-link">Leer guía</span></a>' for s in sources)+'</div></section>')
    descriptions['articulos']='Guías educativas sobre vesícula, hernias y laparoscopia, con fuentes institucionales y estado explícito de revisión médica.'
    descriptions['contacto']='Consulta los canales de atención verificados del Dr. Héctor Rodríguez Aquiño y cómo solicitar disponibilidad.'
    descriptions['tratamientos']='Cirugía general y laparoscopia: evaluación individual y guías educativas sobre procedimientos quirúrgicos.'
    # Local identity appears only with a supplied verified locality.
    if clinic['city']:
        pages['']=(pages[''][0]+' en '+clinic['city'],pages[''][1].replace('Ubicación de atención pendiente de confirmar',e(clinic['city'])))
        descriptions[''] += ' Atención en '+clinic['city']+'.'
        pages['contacto']=(pages['contacto'][0]+' en '+clinic['city'],pages['contacto'][1])
        descriptions['contacto']+=' Atención en '+clinic['city']+'.'
    return pages, descriptions
