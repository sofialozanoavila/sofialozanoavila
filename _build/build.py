# -*- coding: utf-8 -*-
"""Genera el sitio estático (HTML + CSS) a partir del contenido extraído del Wix."""
import hashlib, json, os, re, sys, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIX = 'https://sofia771199.wixsite.com/sofialozanoavila'
ESCALON = 860   # ancho a partir del cual se usa la maquetación original

pages = json.load(open(os.path.join(ROOT, '_build', 'content.json'), encoding='utf-8'))


def version(ruta):
    """Huella del contenido de un archivo, para añadirla al enlace.

    Sin esto el navegador puede seguir usando una hoja de estilos vieja
    guardada en su caché, y el diseño se descuadra."""
    with open(os.path.join(ROOT, ruta), 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()[:8]


def ascii_slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9-]+', '-', s.lower()).strip('-')


SLUG = {k: ('index' if k == 'home' else ascii_slug(k)) for k in pages}

# --- menú superior, en el mismo orden que el sitio original -------------------
MENU = [
    ('sofía lozano ávila', ''), ('PROYECTOS', 'proyectos'), ('Antejardín', 'antejardín'),
    ('todo lo que no cabe en una vitrina', 'todo-lo-que-no-cabe-en-una-vitrina'),
    ('TIENDA', 'paisaje-interior'), ('bache', 'bache'),
    ('vasija/ver/vaciar', 'vasija-ver-vaciar'), ('procedimiento fértil', 'procedimiento-fertil'),
    ('de dudosa procedencia', 'de-dudosa-procedencia'), ('semi preciosas', 'semi-preciosas'),
    ('revisitar', 'revisitar'), ('inventario sobre lo que no veo', 'inventario-sobre-lo-que-no-veo'),
    ('señales', 'señales'), ('desmedida', 'desmesura'),
    ('la linea no es recta', 'la-linea-no-es-recta'),
    ('dejar que la forma se haga', 'dejar-que-la-forma-se-haga'),
    ('cuerpo residual', 'cuerpo-residual'), ('otros proyectos', 'otros-proyectos'),
    ('cv', 'cv'), ('Contacto', 'contacto'),
]


def local_href(url):
    """Convierte un enlace del Wix en una ruta de este sitio."""
    if not url:
        return url
    u = url.split('?')[0].rstrip('/')
    if u == WIX:
        return 'index.html'
    if u.startswith(WIX + '/'):
        rest = u[len(WIX) + 1:]
        return (SLUG[rest] if rest in SLUG else ascii_slug(rest)) + '.html'
    return url


def img_file(c):
    mid = re.search(r'/media/([^/~]+)~mv2\.(\w+)', c['src'])
    crop = re.search(r'/v1/fill/w_(\d+),h_(\d+)', c['hi'])
    name = (f"{mid.group(1)}_{crop.group(1)}x{crop.group(2)}.{mid.group(2)}"
            if crop else f"{mid.group(1)}.{mid.group(2)}")
    return 'assets/img/' + name


def px(v, default=None):
    return v if v else default


# --- páginas en modo galería -------------------------------------------------
# La tienda venía de Wix con las fotos superpuestas, con anchos distintos y
# márgenes negativos. Se rehace como una rejilla regular: dos columnas, mismo
# espaciado entre todas, y un pie igual debajo de cada foto.
GALERIA = {
    'paisaje-interior': {
        'encabezado': ['comp-m4wyjom5', 'comp-m2c5vyp7'],   # ↩ volver, y el título
        'omitir': ['comp-m2c5vyph'],                        # pie suelto que sobra
        'pie': 'Cerámica. Dimensiones variables.',
        'volver': 'index.html',   # la flecha roja lleva al inicio
    },
}


def render_galeria(cfg, page):
    """Dibuja la página como cabecera + rejilla de fotos con pie."""
    piezas = [c for sec in page['sections'] for c in sec['children']]
    porid = {c['id']: c for c in piezas}

    cabecera = []
    for pos, cid in enumerate(cfg['encabezado']):
        c = porid[cid]
        h = re.sub(r'href="([^"]*)"', lambda m: 'href="%s"' % local_href(m.group(1)), c['html'])
        h = h.replace(' target="_self"', '')
        clase = 'rt volver' if pos == 0 else 'rt titulo'
        if pos == 0 and cfg.get('volver'):
            h = re.sub(r'href="[^"]*"', 'href="%s"' % cfg['volver'], h)
        cabecera.append('<div class="%s">%s</div>' % (clase, h))

    saltar = set(cfg['encabezado']) | set(cfg.get('omitir', []))
    fotos = [c for c in ordenar(piezas) if c['type'] == 'image' and c['id'] not in saltar]

    celdas = []
    for c in fotos:
        celdas.append(
            '<figure>'
            '<div class="marco">'
            '<img src="%s" alt="%s" width="%s" height="%s" loading="lazy">'
            '</div>'
            '<figcaption>%s</figcaption>'
            '</figure>' % (img_file(c), c['alt'].replace('"', '&quot;'),
                           c['w'] or '', c['h'] or '', cfg['pie']))

    return ('<section class="sec sec-galeria" data-ancho="1033">\n'
            '<div class="lienzo">\n'
            '<div class="cabecera">%s</div>\n'
            '<div class="galeria">\n%s\n</div>\n'
            '</div>\n'
            '</section>' % ('\n'.join(cabecera), '\n'.join(celdas)))


def ordenar(piezas):
    """Orden de lectura del diseño original: por fila y, dentro de ella, por posición."""
    def clave(c):
        fila = re.match(r'(\d+)', c['geo'].get('grid-area', '999'))
        return (int(fila.group(1)) if fila else 999, num(c['geo'].get('left')))
    return sorted(piezas, key=clave)


# --- correcciones de maquetación ---------------------------------------------
# «medir el aire» venía desordenado desde Wix: tres fotos caían en la columna
# izquierda, encima del texto, y una estaba repetida. Aquí se recoloca con el
# mismo esquema que el resto de proyectos: texto a la izquierda, imágenes a la
# derecha, y cada pie debajo de su foto.
#   (id de la pieza, fila, left, ancho, margen inferior)
REORDENAR = {
    'copia-de-antejardin': [   # el archivo se llama copia-de-antejardin.html
        ('comp-m7mr6giq',  1,   0, 310,  0),   # ↩ volver
        ('comp-m7mr6gij',  2, -53, 568, 25),   # título
        ('comp-mh0tn16s',  3,   0, 425, 13),   # fechas y lugar
        ('comp-m7mr6giv',  4,   0, 419, 10),   # texto del proyecto
        ('comp-m7mr6gix1', 4, 439, 541, 13),   # tejido, vista plana
        ('comp-mh0ua0t6',  5, 439, 541,  9),   # pie: tejido caña flecha
        ('comp-mh0u50b1',  6, 439, 541, 13),   # tejido, detalle
        ('comp-mn4wyksp',  7, 439, 541, 13),   # tejido, instalado
        ('comp-mn4x0274',  8, 494, 430, 11),   # dibujo a lápiz negro
        ('comp-mh0uclf6',  9, 439, 541,  9),   # pie: lápiz negro
        ('comp-mh0u6ow8', 10, 494, 430, 13),   # dibujo a lápiz de color
        ('comp-mh0udob2', 11, 439, 541,  9),   # pie: lápiz de color
    ],
}


def reordenar(slug, sec):
    """Reescribe filas y posiciones de una sección según REORDENAR."""
    plan = REORDENAR.get(slug)
    if not plan:
        return sec
    porid = {c['id']: c for c in sec['children']}
    hijos = []
    for cid, fila, left, ancho, abajo in plan:
        c = porid.get(cid)
        if not c:
            raise SystemExit('reordenar: no existe la pieza %s en %s' % (cid, slug))
        g = dict(c['geo'])
        g['grid-area'] = '%d / 1 / %d / 2' % (fila, fila + 1)
        g['left'] = '%dpx' % left
        g['margin'] = '0px 0px %dpx 0px' % abajo
        if c['type'] == 'image':
            # conserva la proporción original de la foto al cambiar el ancho
            g['width'] = '%dpx' % ancho
            g['height'] = '%dpx' % round(c['h'] * ancho / c['w'])
        else:
            g['width'] = '%dpx' % ancho
            g.pop('height', None)
        hijos.append(dict(c, geo=g))
    filas = max(f for _, f, _, _, _ in plan)
    return dict(sec, children=hijos,
                mesh={'grid-template-rows': 'repeat(%d, min-content) 1fr' % (filas - 1)})


# --- generación de CSS por componente ----------------------------------------
def num(v, default=0):
    """Lee un valor en px; devuelve `default` si no es un número."""
    m = re.match(r'(-?[\d.]+)px', (v or '').strip())
    return float(m.group(1)) if m else default


def stage_box(children):
    """Caja que ocupa el contenido de una sección: (x mínimo, ancho total).

    En Wix cada pieza se coloca con `left` dentro de una columna de 980 px
    centrada, y algunas se salen de esa columna. Midiendo la caja real
    podemos centrarla sin que se recorte en pantallas medianas."""
    xs = []
    for c in children:
        g = c['geo']
        if 'grid-area' not in g:
            continue
        x = num(g.get('left'))
        w = g.get('width', '')
        xs.append((x, x + (num(w, 980) if w.endswith('px') else 980)))
    if not xs:
        return 0, 980
    left = min(a for a, _ in xs)
    right = max(b for _, b in xs)
    return left, max(right - left, 1)


def comp_css(c, x0):
    g = c['geo']
    area = re.match(r'(\d+)\s*/\s*(\d+)\s*/\s*(\d+)\s*/\s*(\d+)', g.get('grid-area', ''))
    m = re.match(r'(\S+)\s+(\S+)\s+(\S+)\s+', g.get('margin', '0 0 0 ') + ' ')
    top, right, bottom = (m.group(1), m.group(2), m.group(3)) if m else ('0', '0', '0')
    d = [
        'position:relative',
        'margin:%s %s %s 0' % (top, right, bottom),
        'left:%gpx' % (num(g.get('left')) - x0),
        'justify-self:start',
        'align-self:start',
    ]
    if area:
        # la columna es obligatoria: sin ella el navegador crea columnas implícitas
        d.append('grid-area:%s/%s/%s/%s' % area.groups())
    if g.get('width'):
        d.append('width:%s' % g['width'])
    if g.get('height') and g['height'] != 'auto':
        d.append('height:%s' % g['height'])
    return ';'.join(d)


def render_page(slug, page):
    if slug in GALERIA:
        return render_galeria(GALERIA[slug], page), '', 0

    css, body, widest = [], [], 0
    for sec in page['sections']:
        sec = reordenar(slug, sec)
        mesh = sec.get('mesh') or {}
        sid = sec['id']
        x0, stage = stage_box(sec['children'])
        widest = max(widest, stage)
        rules = ['display:grid', 'grid-template-columns:%gpx' % stage,
                 'justify-content:center', 'position:static', 'width:100%']
        if mesh.get('grid-template-rows'):
            rules.append('grid-template-rows:%s' % mesh['grid-template-rows'])
        if mesh.get('min-height'):
            rules.append('min-height:%s' % mesh['min-height'])
        css.append('#%s{%s}' % (sid, ';'.join(rules)))

        parts = []
        kids = sorted(sec['children'], key=lambda c: (
            int((re.match(r'(\d+)', c['geo'].get('grid-area', '999')) or ['999', '999'])[1]),
            num(c['geo'].get('left'))))
        for c in kids:
            css.append('#%s{%s}' % (c['id'], comp_css(c, x0)))
            if c['type'] == 'text':
                h = re.sub(r'href="([^"]*)"',
                           lambda m: 'href="%s"' % local_href(m.group(1)), c['html'])
                h = h.replace(' target="_self"', '')
                parts.append('<div id="%s" class="rt">%s</div>' % (c['id'], h))
            else:
                f = img_file(c)
                alt = c['alt'].replace('"', '&quot;')
                tag = ('<img src="%s" alt="%s" width="%s" height="%s" loading="lazy">'
                       % (f, alt, c['w'] or '', c['h'] or ''))
                if c.get('href'):
                    href = local_href(c['href'])
                    ext = ' target="_blank" rel="noopener"' if href.startswith('http') else ''
                    tag = '<a href="%s"%s>%s</a>' % (href, ext, tag)
                parts.append('<div id="%s" class="pic">%s</div>' % (c['id'], tag))
        body.append('<section id="%s" class="sec" data-ancho="%d">%s</section>'
                    % (sid, int(stage), '\n'.join(parts)))

    # Por debajo de ESCALON se apila todo en una columna. Entre ESCALON y el
    # ancho real del diseño, escala.js reduce el zoom para que quepa completo.
    desktop = '@media (min-width:%dpx){\n%s\n}' % (ESCALON, '\n'.join(css))
    return '\n'.join(body), desktop, int(widest)


def header_html(active):
    items = []
    for label, target in MENU:
        href = (SLUG.get(target, ascii_slug(target)) if target else 'index') + '.html'
        cur = ' aria-current="page"' if href == active + '.html' else ''
        items.append('<li><a href="%s"%s>%s</a></li>' % (href, cur, label))
    return ('<header class="site-header">\n'
            '<button class="abrir-menu" type="button" aria-expanded="false" '
            'aria-controls="menu-sitio">menú</button>\n'
            '<nav id="menu-sitio" aria-label="Sitio">\n<ul class="menu">\n%s\n'
            '<li class="more"><button type="button" aria-expanded="false" '
            'aria-label="Más páginas">+</button><ul class="submenu"></ul></li>\n'
            '</ul>\n</nav>\n</header>' % '\n'.join(items))


TEMPLATE = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Almarai:wght@300;400;700;800&family=Forum&family=Nunito+Sans:ital,wght@0,200..900;1,200..900&family=Open+Sans:ital,wght@0,300..800;1,300..800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/css/site.css?v={vcss}">
<style>
{css}
</style>
</head>
<body class="{bodyclass}">
{header}
<main id="contenido">
{body}
</main>
<script src="assets/js/escala.js?v={vesc}" defer></script>
<script src="assets/js/menu.js?v={vmenu}" defer></script>
</body>
</html>
"""

os.makedirs(os.path.join(ROOT, 'assets', 'css'), exist_ok=True)
os.makedirs(os.path.join(ROOT, 'assets', 'js'), exist_ok=True)

for slug, page in pages.items():
    out = SLUG[slug]
    body, css, bp = render_page(out, page)
    desc = ''
    for sec in page['sections']:
        for c in sec['children']:
            if c['type'] == 'text' and len(c.get('text', '')) > 60:
                desc = c['text'][:155].replace('"', "'")
                break
        if desc:
            break
    html = TEMPLATE.format(
        vcss=version('assets/css/site.css'),
        vesc=version('assets/js/escala.js'),
        vmenu=version('assets/js/menu.js'),
        title=page['title'],
        desc=desc or 'sofía lozano ávila — artista, Bogotá, Colombia.',
        css=css,
        header='' if page['landing'] else header_html(out),
        bodyclass='landing' if page['landing'] else 'inner',
        body=body,
    )
    open(os.path.join(ROOT, out + '.html'), 'w', encoding='utf-8').write(html)
    print('->', out + '.html')
