"""Validate the generated crawl graph, metadata and XML with standard libraries."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from xml.etree import ElementTree as ET
import json
import os
import re
from urllib.robotparser import RobotFileParser

project = Path(__file__).resolve().parent.parent
root = Path(os.environ.get('DIST_DIR', project / 'dist'))
config = json.loads((project / 'site.config.json').read_text(encoding='utf-8'))
base = os.environ.get('SITE_URL', config['url']).rstrip('/') + '/'
indexable = config['indexable']


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.meta, self.links, self.ids, self.jsonld = {}, [], [], []
        self.canonicals, self.title, self.h1 = [], '', 0
        self.in_title = self.in_jsonld = False
        self.images, self.lang = [], None
        self.script = ''
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'html': self.lang = attrs.get('lang')
        if tag == 'img': self.images.append(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'meta':
            self.meta[attrs.get('name',attrs.get('property'))] = attrs.get('content', '')
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonicals.append(attrs.get('href'))
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
        if tag == 'h1':
            self.h1 += 1
        if tag == 'title':
            self.in_title = True
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.in_jsonld = True
            self.script = ''

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_jsonld:
            self.script += data

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        if tag == 'script' and self.in_jsonld:
            self.jsonld.append(json.loads(self.script))
            self.in_jsonld = False


pages = {}
titles, descriptions = set(), set()
for file in root.rglob('index.html'):
    slug = file.parent.relative_to(root).as_posix()
    canonical = base + (slug + '/' if slug != '.' else '')
    page = Page(file.read_text(encoding='utf-8'))
    assert page.canonicals == [canonical], f'{file}: canonical incorrecta'
    assert page.h1 == 1, f'{file}: se requiere un H1'
    assert page.lang == 'es' and page.meta.get('viewport')
    assert page.meta.get('og:url') == canonical
    assert page.meta.get('og:title') == page.title
    assert page.meta.get('og:image','').startswith(base)
    for image in page.images:
        assert 'alt' in image and int(image.get('width',0)) > 0 and int(image.get('height',0)) > 0
    assert page.title and page.title not in titles, f'{file}: título vacío o duplicado'
    description = page.meta.get('description')
    assert description and description not in descriptions, f'{file}: descripción vacía o duplicada'
    titles.add(page.title)
    descriptions.add(description)
    directives = page.meta.get('robots', '').split(',')
    assert ('index' if indexable else 'noindex') in directives and 'follow' in directives, f'{file}: robots incorrecto'
    assert len(page.jsonld) == 1, f'{file}: JSON-LD faltante o duplicado'
    graph = page.jsonld[0]['@graph']
    allowed = {
      'WebSite': {'@type','@id','url','name','inLanguage'},
      'WebPage': {'@type','@id','url','name','description','inLanguage','isPartOf','breadcrumb','about','reviewedBy','lastReviewed'},
      'BreadcrumbList': {'@type','@id','itemListElement'},
      'IndividualPhysician': {'@type','@id','name','url','medicalSpecialty','practicesAt'},
      'MedicalClinic': {'@type','@id','name','address','url','medicalSpecialty','telephone','hasMap','openingHoursSpecification'},
      'Article': {'@type','@id','headline','mainEntityOfPage','datePublished','dateModified','author','url'}
    }
    for entity in graph:
        assert entity['@type'] in allowed and set(entity) <= allowed[entity['@type']], f'Propiedad no validada: {entity}'
        assert 'aggregateRating' not in entity
    physician = next(item for item in graph if item['@type']=='IndividualPhysician')
    assert physician['name'] in file.read_text(encoding='utf-8')
    assert physician['medicalSpecialty']=='https://schema.org/Surgical'
    for office in (item for item in graph if item['@type']=='MedicalClinic'):
        assert office['address']['@type']=='PostalAddress'
        assert set(office['address']) <= {'@type','streetAddress','addressLocality','addressRegion','postalCode','addressCountry'}
        assert len(office['address']['addressCountry'])==2
        assert physician['practicesAt']['@id']==office['@id']
        assert office['address']['streetAddress'] in file.read_text(encoding='utf-8')
        for slot in office.get('openingHoursSpecification',[]):
            assert slot['@type']=='OpeningHoursSpecification'
            assert all(day.startswith('https://schema.org/') for day in slot['dayOfWeek'])
            assert '00:00'<=slot['opens']<slot['closes']<='23:59'
    assert page.jsonld[0]['@context'] == 'https://schema.org'
    webpage = next(item for item in graph if item['@type'] == 'WebPage')
    assert webpage['url'] == canonical and webpage['description'] == description
    pages[canonical] = page

sitemap = ET.parse(root / 'sitemap.xml')
locations = [item.text for item in sitemap.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
assert len(locations) == len(set(locations)), 'URLs duplicadas en sitemap'
assert set(locations) == (set(pages) if indexable else set()), 'Sitemap y páginas no coinciden'
robots = (root / 'robots.txt').read_text(encoding='utf-8')
assert 'User-agent: *' in robots
if indexable:
    policy=RobotFileParser()
    policy.parse(robots.splitlines())
    for agent in ('Googlebot','Bingbot','OAI-SearchBot','PerplexityBot'):
        assert policy.can_fetch(agent,base), f'Rastreo de búsqueda bloqueado: {agent}'
    assert 'Sitemap: ' + base + 'sitemap.xml' in robots
else:
    assert 'Disallow: /' in robots

# Walk ordinary HTML anchors from the homepage, without executing JavaScript.
visited, pending = set(), [base]
while pending:
    current = pending.pop()
    if current in visited:
        continue
    visited.add(current)
    for href in pages[current].links:
        target = urlsplit(urljoin(current, href))
        url = target._replace(query='', fragment='').geturl()
        if url in pages:
            if target.fragment:
                assert target.fragment in pages[url].ids, f'{current}: ancla inexistente {href}'
            pending.append(url)
assert visited == set(pages), 'Hay páginas huérfanas'
error_page = Page((root / '404.html').read_text(encoding='utf-8'))
assert 'noindex' in error_page.meta['robots'] and not error_page.canonicals
assert base in error_page.links
print(f'SEO técnico: {len(pages)} páginas accesibles por enlaces HTML; canonical, robots, sitemap, JSON-LD y 404 verificados.')
