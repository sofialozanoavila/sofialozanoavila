# -*- coding: utf-8 -*-
"""Genera el sitio estático (HTML + CSS) a partir del contenido extraído del Wix."""
import hashlib, json, os, re, sys, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIX = 'https://sofia771199.wixsite.com/sofialozanoavila'
ESCALON = 860   # ancho a partir del cual se usa la maquetación original

pages = json.load(open(os.path.join(ROOT, '_build', 'content.json'), encoding='utf-8'))

# Página heredada de Wix: tenía el título «prótesis» pero dentro el contenido
# de «medir el aire» copiado. La sustituye la página protesis.html.
pages.pop('copia-de-medir-el-aire', None)

# Versiones en inglés de las páginas que no vienen de Wix
PAGINAS_EN = {}


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

# Traducciones al inglés, párrafo a párrafo. Se sustituye solo el texto: las
# etiquetas y los estilos del original se conservan intactos.
TRAD = {}
_ruta_trad = os.path.join(ROOT, '_build', 'textos-en.json')
if os.path.exists(_ruta_trad):
    TRAD = json.load(open(_ruta_trad, encoding='utf-8'))


def html_desescapar(t):
    import html as _h
    return _h.unescape(t)


def escapar(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def traducir_pieza(origen, cid, cuerpo):
    """Cambia el texto de cada párrafo por su versión en inglés.

    Solo toca los nodos de texto: la cadena de etiquetas y estilos que Wix
    generó se queda igual, así la traducción hereda el mismo diseño."""
    tabla = TRAD.get(origen, {}).get(cid)
    if not tabla:
        return cuerpo

    if isinstance(tabla, dict):
        # Traducción trozo a trozo: cada fragmento de texto conserva su propio
        # estilo. Es lo que necesita el CV, donde los títulos de sección van en
        # negrita dentro del mismo párrafo que el resto.
        def un_trozo(mm):
            crudo = mm.group(1)
            clave = ' '.join(html_desescapar(crudo).replace('\u200b', ' ').split())
            if clave in tabla:
                izq = crudo[:len(crudo) - len(crudo.lstrip())]
                der = crudo[len(crudo.rstrip()):]
                return '>' + izq + escapar(tabla[clave]) + der + '<'
            return mm.group(0)

        return re.sub(r'>([^<>]+)<', un_trozo, cuerpo)

    n = [0]

    def un_parrafo(m):
        etiqueta, atributos, interior = m.group(1), m.group(2), m.group(3)
        i = n[0]
        n[0] += 1
        if i >= len(tabla) or not tabla[i]:
            return m.group(0)
        if interior.count('<a ') > 1:
            # varios enlaces en un mismo párrafo: sustituir el texto entero
            # los fundiría en uno. Esos casos se traducen aparte.
            return m.group(0)
        puesto = [False]

        def un_texto(mm):
            txt = mm.group(1)
            if not txt.strip():
                return mm.group(0)          # espacios y separadores, intactos
            if puesto[0]:
                return '><'                  # el resto del párrafo se vacía
            puesto[0] = True
            return '>' + escapar(tabla[i]) + '<'

        interior = re.sub(r'>([^<>]*)<', un_texto, interior)
        return '<%s%s>%s</%s>' % (etiqueta, atributos, interior, etiqueta)

    return re.sub(r'<(p|h1|h2|h3)([^>]*)>(.*?)</\1>', un_parrafo, cuerpo, flags=re.S)


# --- versión en inglés -------------------------------------------------------
# El sitio se genera dos veces: el español en la raíz y el inglés en /en/.
# Los nombres de las obras no se traducen: son títulos propios de las piezas.
# Mientras los textos de proyecto sigan sin traducir, la versión en inglés se
# genera solo en local: no se publica ni aparece el cambio de idioma.
PUBLICAR_EN = True
IDIOMAS = ('es', 'en')

MENU_EN = {
    'PROYECTOS': 'PROJECTS',
    'piezas disponibles': 'available works',
    'Contacto': 'Contact',
}

TITULO_EN = {
    'index': 'sofía lozano ávila | artist',
    'proyectos': 'projects | sofialozanoavila',
    'paisaje-interior': 'available works | sofialozanoavila',
    'contacto': 'contact | sofialozanoavila',
    'cv': 'cv | sofialozanoavila',
}

# Sustituciones de texto visible, por página. Solo cadenas que aparecen
# completas dentro de una misma etiqueta.
TEXTO_EN = {
    'index': [
        ('>proyectos', '>projects'),
        ('>contacto', '>contact'),
        ('>Artista<', '>Artist<'),
    ],
    'proyectos': [
        ('>proyectos', '>projects'),
        ('>contacto', '>contact'),
    ],
    'paisaje-interior': [
        ('>piezas disponibles<', '>available works<'),
        ('Cerámica. Dimensiones variables.', 'Ceramic. Dimensions variable.'),
    ],
}

# Enlaces que aparecen en varias páginas
COMUNES_EN = [
    ('\u27ac piezas disponibles', '\u27ac available works'),
    ('Vista general.', 'General view.'),
    ('Detalle.', 'Detail.'),
]

DESC_EN = 'sofía lozano ávila — artist, Bogotá, Colombia.'


def ruta_idioma(idioma, destino):
    """Enlace a la misma página en el otro idioma."""
    return ('en/' + destino) if idioma == 'es' else ('../' + destino)


# --- menú superior, en el mismo orden que el sitio original -------------------
MENU = [
    ('sofía lozano ávila', ''), ('PROYECTOS', 'proyectos'),
    ('prótesis', 'protesis'), ('Antejardín', 'antejardín'),
    ('todo lo que no cabe en una vitrina', 'todo-lo-que-no-cabe-en-una-vitrina'),
    ('piezas disponibles', 'paisaje-interior'), ('bache', 'bache'),
    ('vasija/ver/vaciar', 'vasija-ver-vaciar'), ('procedimiento fértil', 'procedimiento-fertil'),
    ('de dudosa procedencia', 'de-dudosa-procedencia'), ('semi preciosas', 'semi-preciosas'),
    ('revisitar', 'revisitar'), ('inventario sobre lo que no veo', 'inventario-sobre-lo-que-no-veo'),
    ('señales', 'señales'), ('Nada de lo que se mide es basura', 'desmesura'),
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
    if c.get('archivo'):
        return c['archivo']
    mid = re.search(r'/media/([^/~]+)~mv2\.(\w+)', c['src'])
    crop = re.search(r'/v1/fill/w_(\d+),h_(\d+)', c['hi'])
    name = (f"{mid.group(1)}_{crop.group(1)}x{crop.group(2)}.{mid.group(2)}"
            if crop else f"{mid.group(1)}.{mid.group(2)}")
    return 'assets/img/' + name


def px(v, default=None):
    return v if v else default


# «TIENDA» pasa a llamarse «piezas disponibles» en todo el sitio. El texto
# venía dentro del HTML heredado de Wix, así que se sustituye al generar.
TEXTOS = {
    # El proyecto pasa de llamarse «desmedida» a llevar el título de la serie.
    'desmesura': [('>desmedida<', '>Nada de lo que se mide es basura<')],
    'paisaje-interior': [('>TIENDA<', '>piezas disponibles<')],
    'index': [('\u27ac tienda', '\u27ac piezas disponibles')],
    'proyectos': [('\u27ac tienda', '\u27ac piezas disponibles'),
                  ('2020 / d<a href="desmesura.html">esmedida</a>',
                   '2020 / <a href="desmesura.html">Nada de lo que se mide es basura</a>')],
}

TITULOS = {
    'paisaje-interior': 'piezas disponibles | sofialozanoavila',
    'desmesura': 'Nada de lo que se mide es basura | sofialozanoavila',
}


# Nombres estables para algunas piezas, y así poder darles estilo propio
# (los identificadores comp-… vienen de Wix y no dicen nada por sí solos).
CLASES = {
    'index': {
        'comp-lrjn9lv2': 'enlaces',   # proyectos · contacto · CV · tienda
        'comp-lrfas7qe': 'nombre',    # sofía lozano ávila
        'comp-mtx3uuyd': 'lugar',     # Artista / Bogotá, Colombia
    },
    'proyectos': {
        'comp-m2c3o77q': 'nombre-proyectos',   # sofía lozano ávila
        'comp-mtx4x6u5': 'enlaces-proyectos',  # contacto · CV · tienda
    },
    'cv': {
        'comp-mrr1lget': 'enlaces',            # contacto · CV
    },
}


# Inicio y proyectos no llevan menú superior, así que el cambio de idioma se
# engancha al final de su línea de enlaces.
IDIOMA_EN_LINEA = {'index': 'enlaces', 'proyectos': 'enlaces-proyectos'}


def enganchar_idioma(slug, clase, h, idioma):
    if not PUBLICAR_EN or IDIOMA_EN_LINEA.get(slug) != clase:
        return h
    destino = ruta_idioma(idioma, slug + '.html')
    etiqueta = 'EN' if idioma == 'es' else 'ES'
    enlace = ('<a class="idioma-linea" href="%s" hreflang="%s">&nbsp; &nbsp;%s</a>'
              % (destino, 'en' if idioma == 'es' else 'es', etiqueta))
    i = h.rfind('</p>')
    return h[:i] + enlace + h[i:] if i > 0 else h + enlace


# Entradas del listado de proyectos que aún no eran enlaces
ENLAZAR = {
    'proyectos': [('2026 / pr&oacute;tesis', 'protesis.html')],
}

TITULO_EN['desmesura'] = 'Nada de lo que se mide es basura | sofialozanoavila'


def enlazar(slug, h):
    for etiqueta, destino in ENLAZAR.get(slug, []):
        patron = r'(<span[^>]*>\s*)*<span[^>]*>' + re.escape(etiqueta) + r'</span>(\s*</span>)*'
        m = re.search(patron, h)
        if m:
            h = h[:m.start()] + '<a href="%s">%s</a>' % (destino, m.group(0)) + h[m.end():]
    return h


# --- páginas nuevas (proyectos que no vienen de Wix) -------------------------
# Se maquetan con la misma geometría que las páginas de proyecto existentes:
# columna de texto a la izquierda (ancho 419, en x=0) y columna de imágenes a
# la derecha (ancho 541, en x=439), dentro del lienzo de 980 px.
NUEVAS = {
    'protesis': {
        'titulo': 'Prótesis',
        'volver': 'proyectos',
        'ficha': ['3 de Septiembre - 15 de Octubre 2026',
                  'Emblematic Art Gallery - Bogot\u00e1'],
        'texto': [
            'Habitar las ruinas de lo que alguna vez fue la cocina es el punto de partida para “Prótesis”. Este espacio, que aún conserva vestigios fantasmales de su función original como tubos de gas cercenados, tomas eléctricas mudas y una ventana al patio interior, se activa a través de un profundo deseo de completar lo que falta. Entendiendo la cocina como un archivo doméstico que custodia la memoria de gestos repetidos, la artista fija su mirada en los objetos “secundarios”.',
            'Clavijas, cables y conexiones se materializan sutilmente en cerámica, ocupando el vacío de los circuitos interrumpidos. La propuesta se despliega en piezas que dialogan orgánicamente: serigrafías que actúan como restauraciones ficticias del antiguo papel tapiz; una tubería suspendida y estructuras de estufas que, en su proceso de creación, adquirieron la apariencia de huesos, cual injertos sobre la arquitectura de la casa.',
            'En conjunto, esta propuesta aborda la cocina como un cuerpo fragmentado. A través de estas piezas frágiles y suspendidas, como susurros materiales, la artista crea una vida extraña que nos devuelve, por un instante, la pulsión de un tiempo doméstico ya extinguido.',
        ],
        'firma': 'Andrea Mu\u00f1oz',
        'ficha_en': ['3 September - 15 October 2026',
                     'Emblematic Art Gallery - Bogot\u00e1'],
        'texto_en': [
            'Inhabiting the ruins of what was once the kitchen is the starting point for “Prótesis”. This space, which still holds ghostly vestiges of its original function —severed gas pipes, mute electrical sockets and a window onto the inner courtyard— is activated through a deep desire to complete what is missing. Understanding the kitchen as a domestic archive that guards the memory of repeated gestures, the artist fixes her gaze on the “secondary” objects.',
            'Plugs, cables and connections take subtle material form in ceramic, occupying the void of the interrupted circuits. The proposal unfolds in pieces that speak to one another organically: screen prints acting as fictitious restorations of the old wallpaper; a suspended pipe and stove structures that, in the process of their making, took on the appearance of bones, like grafts upon the architecture of the house.',
            'Taken together, this proposal approaches the kitchen as a fragmented body. Through these fragile, suspended pieces —material whispers— the artist creates a strange life that gives us back, for an instant, the pulse of a domestic time already extinguished.',
        ],
        'pies_en': {
            'Vista general.': 'General view.',
            'Detalle.': 'Detail.',
            'Hornillas, 2026. Cerámica y nylon. 50 x 50 cm.': 'Hornillas, 2026. Ceramic and nylon. 50 x 50 cm.',
            'Fuente, 2026. Cerámica y nylon. 100 x 30 x 40 cm.': 'Fuente, 2026. Ceramic and nylon. 100 x 30 x 40 cm.',
            'Gestos de pared, 2026. Serigrafía sobre papel. Dimensiones variables.': 'Gestos de pared, 2026. Screen print on paper. Dimensions variable.',
            'Filtraciones, 2026. Dibujo. Lápiz sobre papel. 35 x 50 cm.': 'Filtraciones, 2026. Drawing. Pencil on paper. 35 x 50 cm.',
            'Clavija, Cable y Clavija (sola), 2026. Cerámica.': 'Clavija, Cable and Clavija (sola), 2026. Ceramic.',
            'Clavija, 2026. Cerámica sobre acrílico. 28 x 17 cm.': 'Clavija, 2026. Ceramic on acrylic. 28 x 17 cm.',
            'Clavija (sola), 2026. Cerámica. 5 x 3 cm.': 'Clavija (sola), 2026. Ceramic. 5 x 3 cm.',
            'Cable, 2026. Cerámica. 8 x 4 cm.': 'Cable, 2026. Ceramic. 8 x 4 cm.',
        },
        # (archivo, pie) en orden de aparición. Pie vacío = sin texto debajo.
        'fotos': [
            ('protesis-15.jpg', 'Vista general.'),
            ('protesis-14.jpg', 'Vista general.'),
            ('protesis-03.jpg', 'Hornillas, 2026. Cerámica y nylon. 50 x 50 cm.'),
            ('protesis-02.jpg', 'Detalle.'),
            ('protesis-01.jpg', 'Detalle.'),
            ('protesis-04.jpg', 'Fuente, 2026. Cerámica y nylon. 100 x 30 x 40 cm.'),
            ('protesis-07.jpg', 'Detalle.'),
            ('protesis-05.jpg', 'Detalle.'),
            ('protesis-06.jpg', 'Detalle.'),
            ('protesis-13.jpg', 'Gestos de pared, 2026. Serigrafía sobre papel. Dimensiones variables.'),
            ('protesis-09.jpg', 'Filtraciones, 2026. Dibujo. Lápiz sobre papel. 35 x 50 cm.'),
            ('protesis-08.jpg', 'Detalle.'),
            ('protesis-16.jpg', 'Clavija, Cable y Clavija (sola), 2026. Cerámica.'),
            ('protesis-12.jpg', 'Clavija, 2026. Cerámica sobre acrílico. 28 x 17 cm.'),
            ('protesis-10.jpg', 'Clavija (sola), 2026. Cer\u00e1mica. 5 x 3 cm.'),
            ('protesis-11.jpg', 'Cable, 2026. Cerámica. 8 x 4 cm.'),
        ],
    },
}

# El carácter ↩ lo dibujan algunos móviles como emoji (gris, con su propio
# estilo). Se sustituye por un dibujo vectorial: mismo trazo, mismo rojo, y
# se ve igual en todos los dispositivos.
FLECHA = (
    '<svg class="flecha" viewBox="0 0 30 22" role="img" aria-label="Volver">'
    '<path d="M26 3 v6 a5 5 0 0 1 -5 5 H7" fill="none" stroke="#FF0006"'
    ' stroke-width="2.6" stroke-linecap="round"/>'
    '<path d="M13 8 L7 14 L13 20" fill="none" stroke="#FF0006"'
    ' stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>'
    '</svg>'
)


TXT_TITULO = ('<h1 class="font_0" style="font-size:34px;"><span style="color:#000000;">'
              '<span style="font-family:open sans,sans-serif;">'
              '<span style="font-size:34px;">%s</span></span></span></h1>')
TXT_VOLVER = ('<p class="font_8" style="font-size:40px; line-height:normal;">'
              '<a href="%s.html"><span style="color:#FF0006;"><span style="font-size:40px;">'
              '<span style="letter-spacing:normal;">↩</span></span></span></a></p>')
TXT_FICHA = ('<p class="font_8" style="font-size:11px;"><span style="font-size:11px;">'
             '<span style="font-family:madefor-display-bold,helveticaneuew01-65medi,sans-serif;">'
             '<span style="color:#414141;">%s</span></span></span></p>')
TXT_PARRAFO = ('<p class="font_8" style="font-size:14px;"><span style="font-size:14px;">'
               '<span style="font-weight:300;"><span style="font-family:almarai,sans-serif;">'
               '%s</span></span></span></p>')
TXT_VACIO = ('<p class="font_8" style="font-size:14px;">&nbsp;</p>')
TXT_PIE = ('<p class="font_8" style="font-size:12px; line-height:1.4em;">'
           '<span style="color:#414141;"><span style="font-size:12px;">'
           '<span style="letter-spacing:0em;">%s</span></span></span></p>')


def pieza(cid, tipo, fila, left, ancho, abajo, filas=1, **extra):
    geo = {'grid-area': '%d / 1 / %d / 2' % (fila, fila + filas),
           'left': '%dpx' % left,
           'width': '%dpx' % ancho,
           'margin': '0px 0px %dpx 0px' % abajo}
    return dict(extra, id=cid, type=tipo, geo=geo)


def render_nueva(slug, cfg, idioma='es'):
    """Construye una página de proyecto desde cero, con el formato del sitio."""
    hijos, fila = [], 1

    hijos.append(pieza('n-volver', 'text', fila, 0, 310, 0,
                       html=TXT_VOLVER % cfg.get('volver', 'proyectos')))
    fila += 1
    hijos.append(pieza('n-titulo', 'text', fila, -53, 568, 25,
                       html=TXT_TITULO % cfg['titulo']))
    fila += 1
    ficha = cfg.get('ficha_en' if idioma == 'en' else 'ficha')
    if ficha:
        hijos.append(pieza('n-ficha', 'text', fila, 0, 425, 13,
                           html=''.join(TXT_FICHA % l for l in ficha)))
        fila += 1

    cuerpo = []
    for i, par in enumerate(cfg.get('texto_en' if idioma == 'en' else 'texto', [])):
        if i:
            cuerpo.append(TXT_VACIO)
        cuerpo.append(TXT_PARRAFO % par)
    if cfg.get('firma'):
        cuerpo += [TXT_VACIO, TXT_PARRAFO % cfg['firma']]

    # Las fotos y sus pies ocupan una fila cada uno, con el mismo margen entre
    # ellos. El texto se extiende a lo largo de todas esas filas, de modo que
    # no impone la altura de ninguna.
    primera = fila
    for n, (archivo, pie) in enumerate(cfg.get('fotos', [])):
        hijos.append(foto_pieza('n-foto%d' % n, fila, archivo, 13))
        fila += 1
        if idioma == 'en':
            pie = cfg.get('pies_en', {}).get(pie, pie)
        if pie:
            hijos.append(pieza('n-pie%d' % n, 'text', fila, 439, 541, 13,
                               html=TXT_PIE % pie))
            fila += 1
    if cuerpo:
        hijos.append(pieza('n-texto', 'text', primera, 0, 419, 10,
                           filas=max(fila - primera, 1), html=''.join(cuerpo)))

    sec = {'id': 'seccion-' + slug, 'children': hijos, 'lienzo': (-53, 1033),
           'mesh': {'grid-template-rows': 'repeat(%d, min-content) 1fr' % max(fila - 1, 1)}}
    return {'title': '%s | sofialozanoavila' % cfg['titulo'],
            'landing': False, 'sections': [sec]}


def foto_pieza(cid, fila, archivo, abajo):
    """Coloca una foto en la columna derecha, a su proporción real."""
    from struct import unpack
    ruta = os.path.join(ROOT, 'assets', 'img', archivo)
    ancho, alto = medidas(ruta)
    escala = 541.0 / ancho
    p = pieza(cid, 'image', fila, 439, 541, abajo)
    p['geo']['height'] = '%dpx' % round(alto * escala)
    p['archivo'] = 'assets/img/' + archivo
    p['w'], p['h'], p['alt'] = 541, int(round(alto * escala)), ''
    p['href'] = None
    return p


def medidas(ruta):
    """Ancho y alto de un JPEG o PNG, leyendo sus cabeceras."""
    with open(ruta, 'rb') as f:
        datos = f.read()
    if datos[:8] == b'\x89PNG\r\n\x1a\n':
        return int.from_bytes(datos[16:20], 'big'), int.from_bytes(datos[20:24], 'big')
    i = 2
    while i < len(datos):
        if datos[i] != 0xFF:
            i += 1
            continue
        marca = datos[i + 1]
        if marca in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                     0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            alto = int.from_bytes(datos[i + 5:i + 7], 'big')
            ancho = int.from_bytes(datos[i + 7:i + 9], 'big')
            return ancho, alto
        i += 2 + int.from_bytes(datos[i + 2:i + 4], 'big')
    raise SystemExit('no pude leer las medidas de ' + ruta)


# Orden en que deben aparecer las fotografías, cuando el del original no es
# el que corresponde.
ORDEN_FOTOS = {
    'señales': ['comp-lrpdbanw', 'comp-lrpdadw2', 'comp-lrpd2vw1',
                'comp-lrpd2vwe', 'comp-lrpd2vwc', 'comp-lrpd2vwi'],
}

# Párrafos que se retiran de un texto, porque pasan a otro sitio de la página.
QUITAR_PARRAFOS = {
    # 7: el listado de SEÑAL 1, 2 y 3 (ahora son los pies de foto)
    # 9: los créditos (pasan al bloque de cierre)
    'señales': {'comp-lrfe02kk3': [7, 9]},
}

# Bloque de cierre, después de las fotografías.
CIERRE = {
    'señales': {
        'es': ['Fotografía: Juan Camilo Forero.',
               'Colaboración: Maria José Espejo.',
               '',
               'Proyecto apoyado por el Ministerio de Cultura.',
               'Programa Jóvenes en Movimiento / 2021.'],
        'en': ['Photography: Juan Camilo Forero.',
               'Collaboration: Maria José Espejo.',
               '',
               'Project supported by the Ministry of Culture.',
               'Jóvenes en Movimiento programme / 2021.'],
        'sellos': True,
    },
}


# Pies añadidos o corregidos a mano, por proyecto y por fotografía. Sustituyen
# a lo que traía el Wix; en español y en inglés.
PIES = {
    'revisitar': {
        'comp-lrh6m4i8': (['Vista general.'], ['General view.']),
    },
    'desmesura': {
        # 1, 2 y 3: los dibujos de la serie
        'comp-lrfdo8ia': (['\u201cNada de lo que se mide es basura\u201d. 48\u00d733 cms. '
                           'Dibujo. Impresi\u00f3n digital y tinta blanca sobre papel. 50\u00d735 cms c/u. 2020.'],
                          ['\u201cNada de lo que se mide es basura\u201d. 48 x 33 cm. '
                           'Drawing. Digital print and white ink on paper. 50 x 35 cm each. 2020.']),
        'comp-lrfdmanc': (['De la serie \u201cNada de lo que se mide es basura\u201d. 48\u00d733 cms. '
                           'Dibujo. Impresi\u00f3n digital y tinta blanca sobre papel. 50\u00d735 cms c/u. 2020.'],
                          ['From the series \u201cNada de lo que se mide es basura\u201d. 48 x 33 cm. '
                           'Drawing. Digital print and white ink on paper. 50 x 35 cm each. 2020.']),
        'comp-lrfdmana': (['Sin t\u00edtulo. De la serie \u201cNada de lo que se mide es basura\u201d. 48\u00d733 cms. '
                           'Dibujo. Impresi\u00f3n digital y tinta blanca sobre papel. 50\u00d735 cms c/u. 2020.'],
                          ['Untitled. From the series \u201cNada de lo que se mide es basura\u201d. 48 x 33 cm. '
                           'Drawing. Digital print and white ink on paper. 50 x 35 cm each. 2020.']),
        'comp-lrfdo5y8': (['Detalle. Sin t\u00edtulo. 48\u00d733 cms. Impresi\u00f3n digital y tinta blanca '
                           'sobre papel. 50\u00d735 cms. 2020.'],
                          ['Detail. Untitled. 48 x 33 cm. Digital print and white ink on paper. '
                           '50 x 35 cm. 2020.']),
        # 5, 6 y 7: las piezas de Contacto
        'comp-lrfdman7': (['\u201cContacto\u201d. Cer\u00e1mica. Dimensiones variables. 2020.'],
                          ['\u201cContacto\u201d. Ceramic. Dimensions variable. 2020.']),
        'comp-lrfdman3': (['\u201cContacto\u201d. Cer\u00e1mica. Dimensiones variables. 2020.'],
                          ['\u201cContacto\u201d. Ceramic. Dimensions variable. 2020.']),
        'comp-lrfdman5': (['\u201cContacto\u201d. Cer\u00e1mica. Dimensiones variables. 2020.'],
                          ['\u201cContacto\u201d. Ceramic. Dimensions variable. 2020.']),
    },
    'señales': {
        'comp-lrpdbanw': (['SEÑAL 1. Hacer cosas para desaparecer.',
                           '30 noviembre - 3 diciembre.'],
                          ['SIGNAL 1. Making things in order to disappear.',
                           '30 November - 3 December.']),
        'comp-lrpdadw2': (['SEÑAL 2. Juguemos en el bosque.', '2, 7 diciembre.'],
                          ['SIGNAL 2. Let us play in the forest.', '2 and 7 December.']),
    },
}
# Las cuatro cianotipias comparten pie
for _id in ('comp-lrpd2vw1', 'comp-lrpd2vwe', 'comp-lrpd2vwc', 'comp-lrpd2vwi'):
    PIES['señales'][_id] = (
        ['SEÑAL 3. Inventario a través de Cianotipia, impresión análoga.',
         '1 - 4 diciembre.'],
        ['SIGNAL 3. Inventory through cyanotype, analogue printing.',
         '1 - 4 December.'])


# --- páginas de proyecto en lista ---------------------------------------------
# Una obra por fila: su ficha en una columna estrecha a la izquierda y la
# fotografía grande a la derecha, alineadas por arriba. Antes el pie iba
# debajo de cada foto y las fotos eran más pequeñas.
LISTA = {
    'antejardín', 'bache', 'copia-de-antejardín', 'cuerpo-residual',
    'de-dudosa-procedencia', 'dejar-que-la-forma-se-haga', 'desmesura',
    'inventario-sobre-lo-que-no-veo', 'la-linea-no-es-recta', 'otros-proyectos',
    'procedimiento-fertil', 'revisitar', 'semi-preciosas', 'señales',
    'todo-lo-que-no-cabe-en-una-vitrina', 'vasija-ver-vaciar',
}


def render_lista(slug, origen, page, idioma):
    """Reparte la página en una introducción y una lista de obras."""
    piezas = []
    for sec in page['sections']:
        # Las correcciones de maquetación se aplican antes de repartir las
        # piezas: si no, se usa la disposición original de Wix.
        piezas += ordenar(reordenar(slug, sec)['children'])

    def fila(c):
        m = re.match(r'(\d+)', c['geo'].get('grid-area', '999'))
        return int(m.group(1)) if m else 999

    def tramo(c):
        x = num(c['geo'].get('left'))
        w = c['geo'].get('width', '')
        return x, x + (num(w, 980) if w.endswith('px') else 980)

    # Los logos de las entidades que apoyaron el proyecto no son obra: en el
    # original iban pequeños junto a los créditos, no como fotografías.
    sellos = [c for c in piezas if c['type'] == 'image' and 0 < num(c['geo'].get('width')) < 330]
    imagenes = [c for c in piezas if c['type'] == 'image' and c not in sellos]
    primera = fila(imagenes[0]) if imagenes else 10 ** 6

    # Cada pie pertenece a la fotografía que tiene justo encima y con la que
    # comparte franja horizontal. En Wix algunas páginas iban a dos columnas,
    # y emparejar por orden de lectura corría los pies de sitio.
    obras = [{'foto': c, 'pies': []} for c in imagenes]
    por_foto = {id(o['foto']): o for o in obras}
    intro = []
    for c in piezas:
        if c['type'] == 'image':
            continue
        a, b = tramo(c)
        candidatas = []
        for img in imagenes:
            if fila(img) >= fila(c):
                continue
            ia, ib = tramo(img)
            if min(b, ib) - max(a, ia) > 0:      # se solapan en horizontal
                candidatas.append(img)
        if candidatas and fila(c) > primera:
            mejor = max(candidatas, key=lambda i: (fila(i), -abs(num(i['geo'].get('left')) - a)))
            por_foto[id(mejor)]['pies'].append(c)
        else:
            intro.append(c)

    manual = ORDEN_FOTOS.get(origen)
    if manual:
        puesto = {cid: i for i, cid in enumerate(manual)}
        obras.sort(key=lambda o: puesto.get(o['foto']['id'], 10 ** 6))
    else:
        obras.sort(key=lambda o: (fila(o['foto']), num(o['foto']['geo'].get('left'))))

    def texto(c):
        h = re.sub(r'href="([^"]*)"', lambda m: 'href="%s"' % local_href(m.group(1)), c['html'])
        if idioma == 'en':
            h = traducir_pieza(origen, c['id'], h)
        return h.replace(' target="_self"', '')

    # El encabezado (flecha, título, fechas) va entero; el texto largo del
    # proyecto se reparte en dos columnas para que, al ensancharlo, los
    # renglones no queden demasiado largos para leer.
    def es_flecha(c):
        return c.get('text', '').strip() == '\u21a9'

    flechas = [c for c in intro if es_flecha(c)]
    cortos = [c for c in intro if not es_flecha(c) and len(c.get('text', '')) <= 250]
    largos = [c for c in intro if not es_flecha(c) and len(c.get('text', '')) > 250]

    def bloques(lista):
        return ''.join('<div class="rt">%s</div>' % texto(c) for c in lista)

    def sin_mudados(cid, h):
        fuera = QUITAR_PARRAFOS.get(origen, {}).get(cid)
        if not fuera:
            return h
        n = [0]
        def uno(m):
            i = n[0]; n[0] += 1
            return '' if i in fuera else m.group(0)
        return re.sub(r'<p[^>]*>.*?</p>', uno, h, flags=re.S)

    def sin_vacios(h):
        """Quita los párrafos vacíos que Wix usaba para separar.

        El espacio entre párrafos se controla desde la hoja de estilos, así
        el texto respira parejo y no depende de cuántos huecos se dejaran."""
        def vacio(m):
            solo_texto = re.sub(r'<[^>]+>', '', m.group(2))
            solo_texto = solo_texto.replace('\u200b', '').replace('&nbsp;', '')
            solo_texto = solo_texto.replace('\xa0', '').strip()
            return '' if not solo_texto else m.group(0)
        return re.sub(r'<p([^>]*)>(.*?)</p>', vacio, h, flags=re.S)

    # La flecha va en su propia fila, arriba del todo: así el título y el texto
    # del proyecto arrancan a la misma altura.
    marcas = ''
    if sellos:
        marcas = '<div class="sellos">%s</div>' % ''.join(
            '<img src="%s" alt="%s" loading="lazy">' % (img_file(c), c.get('alt', ''))
            for c in sellos)

    # Si los logos van en el bloque de cierre, no se repiten arriba.
    al_cierre = bool(CIERRE.get(origen, {}).get('sellos'))
    cabeza = '<div class="volver-fila">%s</div>' % bloques(flechas) if flechas else ''
    cabeza += '<div class="encabezado">%s%s</div>' % (bloques(cortos),
                                                      '' if al_cierre else marcas)
    if largos:
        cuerpo = ''.join('<div class="rt">%s</div>' % sin_mudados(c['id'], texto(c))
                         for c in largos)
        cabeza += '<div class="cuerpo">%s</div>' % sin_vacios(cuerpo)

    filas = []
    for indice, o in enumerate(obras):
        c = o['foto']
        alt = c.get('alt', '').replace('"', '&quot;')
        img = ('<img src="%s" alt="%s" width="%s" height="%s" loading="lazy">'
               % (img_file(c), alt, c.get('w') or '', c.get('h') or ''))
        if c.get('href'):
            destino = local_href(c['href'])
            fuera = ' target="_blank" rel="noopener"' if destino.startswith('http') else ''
            img = '<a href="%s"%s>%s</a>' % (destino, fuera, img)
        propio = PIES.get(origen, {}).get(c['id'])
        if propio:
            lineas = propio[1 if idioma == 'en' else 0]
            ficha = '<div class="rt">%s</div>' % ''.join(TXT_PIE % l for l in lineas)
        else:
            ficha = ''.join('<div class="rt">%s</div>' % texto(t) for t in o['pies'])
        filas.append('<div class="obra"><div class="foto">%s</div>'
                     '<div class="ficha">%s</div></div>' % (img, ficha))

    pie_pagina = ''
    cfg = CIERRE.get(origen)
    if cfg:
        lineas = ''.join(TXT_PIE % l if l else '<p class="font_8">&nbsp;</p>'
                         for l in cfg['en' if idioma == 'en' else 'es'])
        pie_pagina = ('<div class="cierre"><div class="rt">%s</div>%s</div>'
                      % (lineas, marcas if cfg.get('sellos') else ''))

    return ('<section class="sec sec-obras">\n'
            '<div class="lienzo">\n'
            '<div class="intro">%s</div>\n'
            '<div class="obras">\n%s\n</div>\n'
            '%s'
            '</div>\n'
            '</section>' % (cabeza, '\n'.join(filas), pie_pagina))


# --- catálogo de piezas disponibles ------------------------------------------
# Datos y fotografías tomados del portafolio de obra disponible. Los precios
# llevan ya el aumento de 100.000 pesos acordado.
CORREO = 'sofia771199@gmail.com'

CATALOGO = [
    ('flor-borrachero', 'Flor borrachero', 'Cerámica', '12 x 12 x 12 cm', 2026, 180000, ''),
    ('pocillo', 'Pocillo', 'Cerámica', '8 x 8 x 10 cm', 2022, 150000, ''),
    ('concha', 'Concha', 'Cerámica', '16,5 x 10,5 cm', 2026, 180000, ''),
    ('caja-2', 'Caja 2', 'Cerámica', '16,5 x 11 cm', 2026, 180000, ''),
    ('monos-1', 'De la serie moños', 'Cerámica', '', 2026, 160000, ''),
    ('monos-2', 'De la serie moños', 'Cerámica', '5 x 6 x 4 cm', 2026, 160000, ''),
    ('banda-elastica', 'Banda elástica', 'Cerámica', '12 x 5 x 3 cm', 2026, 160000, ''),
    ('monos-serie', 'Moños', 'Cerámica', '30 x 20 x 6 cm', 2026, 380000, 'Serie completa'),
    ('palas', 'Palas', 'Cerámica', '30 x 25 x 5 cm', 2025, 600000, 'Queda una disponible'),
    ('apariciones-instalacion', 'Apariciones', 'Cerámica y tierra', '50 x 50 x 50 cm', 2025,
     2100000, 'Instalación completa'),
    ('apariciones-piezas', 'Apariciones', 'Cerámica', '10 x 10 x 8 cm', 2025, 170000,
     'Por pieza · serie completa 400.000'),
    # Vendidas: se muestran, pero sin precio.
    ('vertebra', 'Vértebra', 'Cerámica', '20 x 5 x 5 cm', 2024, None, ''),
    ('caja', 'Caja', 'Cerámica', '15 x 8,5 x 4,5 cm', 2026, None, ''),
    ('cuchara', 'Cuchara', 'Cerámica', '16 x 4 x 2 cm', 2025, None, ''),
]


# Técnicas y notas del catálogo en inglés. Los nombres de las piezas no se
# traducen: son títulos propios.
CATALOGO_EN = {
    'Cerámica': 'Ceramic',
    'Cerámica y tierra': 'Ceramic and soil',
    'Serie completa': 'Complete series',
    'Queda una disponible': 'One available',
    'Instalación completa': 'Complete installation',
    'Por pieza · serie completa 400.000': 'Per piece · complete series 400,000',
    # descriptivo, no es un título de obra
    'De la serie moños': 'From the moños series',
}


def pesos(n):
    return '$' + '{:,}'.format(n).replace(',', '.') + ' COP'


def render_catalogo(idioma='es'):
    en = idioma == 'en'
    consultar = 'Enquire' if en else 'Consultar'
    asunto = 'Enquiry about' if en else 'Consulta sobre'
    titulo = 'available works' if en else 'piezas disponibles'

    fichas = []
    for clave, nombre, tecnica, medidas, ano, precio, nota in CATALOGO:
        archivo = 'pieza-%s.jpg' % clave
        if en:
            tecnica = CATALOGO_EN.get(tecnica, tecnica)
            nota = CATALOGO_EN.get(nota, nota)
            nombre = CATALOGO_EN.get(nombre, nombre)
        datos = ' · '.join(x for x in (tecnica, medidas, str(ano)) if x)
        correo = ('mailto:%s?subject=%s %s'
                  % (CORREO, asunto.replace(' ', '%20'), nombre.replace(' ', '%20')))
        if precio is None:
            cierre = '<p class="vendida">%s</p>' % ('Sold' if en else 'Vendida')
        else:
            cierre = ('<p class="precio">%s</p>'
                      '<a class="consultar" href="%s">%s</a>'
                      % (pesos(precio), correo, consultar))
        fichas.append(
            '<li%s>'
            '<div class="marco"><img src="assets/img/%s" alt="%s" width="1000" height="750" loading="lazy"></div>'
            '<h3>%s</h3>'
            '<p class="datos">%s</p>'
            '%s'
            '%s'
            '</li>'
            % (' class="agotada"' if precio is None else '',
               archivo, nombre, nombre, datos,
               ('<p class="nota">%s</p>' % nota) if nota else '',
               cierre))

    return ('<section class="sec sec-catalogo">\n'
            '<div class="lienzo">\n'
            '<div class="cabecera">'
            '<div class="rt volver"><p><a href="index.html">\u21a9</a></p></div>'
            '<div class="rt titulo"><h1>%s</h1></div>'
            '</div>\n'
            '<ul class="catalogo">\n%s\n</ul>\n'
            '</div>\n'
            '</section>' % (titulo, '\n'.join(fichas)))


# --- página de contacto ------------------------------------------------------
# Venía de Wix con dos PNG grandes de sobre y cámara. Se rehace con iconos
# vectoriales de trazo fino, del mismo tamaño que la letra.
ICONO_CORREO = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"'
    ' aria-hidden="true">'
    '<rect x="2.5" y="5" width="19" height="14" rx="2.5"/>'
    '<path d="M3.5 8 L12 13.8 L20.5 8" stroke-linecap="round" stroke-linejoin="round"/>'
    '</svg>'
)
ICONO_INSTAGRAM = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"'
    ' aria-hidden="true">'
    '<rect x="3" y="3" width="18" height="18" rx="5.2"/>'
    '<circle cx="12" cy="12" r="4.1"/>'
    '<circle cx="17.3" cy="6.7" r="1.15" fill="currentColor" stroke="none"/>'
    '</svg>'
)

CONTACTO = {
    'volver': 'index.html',
    'enlaces': [
        (ICONO_CORREO, 'sofia<i>771199</i>@gmail.com',
         'mailto:sofia771199@gmail.com', False),
        (ICONO_INSTAGRAM, '@sofialozanoaa',
         'https://www.instagram.com/sofialozanoaa/?hl=es-la', True),
    ],
}


def render_contacto(cfg):
    filas = []
    for icono, etiqueta, destino, fuera in cfg['enlaces']:
        extra = ' target="_blank" rel="noopener"' if fuera else ''
        filas.append('<li><a href="%s"%s>%s<span>%s</span></a></li>'
                     % (destino, extra, icono, etiqueta))
    return ('<section class="sec sec-contacto" data-ancho="1033">\n'
            '<div class="lienzo">\n'
            '<div class="rt volver"><p><a href="%s">\u21a9</a></p></div>\n'
            '<ul class="contactos">\n%s\n</ul>\n'
            '</div>\n'
            '</section>' % (cfg['volver'], '\n'.join(filas)))


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


def flecha_en_proyectos(page):
    """Añade la flecha de volver al listado de proyectos.

    Esa página no lleva menú superior, así que la flecha se inserta como una
    fila nueva encima de todo y el resto de las piezas baja un puesto."""
    sec = page['sections'][0]
    hijos = []
    for c in sec['children']:
        c = dict(c, geo=dict(c['geo']))
        m = re.match(r'(\d+)\s*/\s*(\d+)\s*/\s*(\d+)\s*/\s*(\d+)', c['geo'].get('grid-area', ''))
        if m:
            a, b, d, e = (int(x) for x in m.groups())
            c['geo']['grid-area'] = '%d / %d / %d / %d' % (a + 1, b, d + 1, e)
        hijos.append(c)

    flecha = {
        'id': 'volver-proyectos',
        'type': 'text',
        'html': TXT_VOLVER % 'index',
        'geo': {'grid-area': '1 / 1 / 2 / 2', 'left': '-162px',
                'width': '310px', 'margin': '15px 0px 4px 0px'},
    }
    mesh = dict(sec.get('mesh') or {})
    filas = re.match(r'repeat\((\d+),', mesh.get('grid-template-rows', '') or '')
    if filas:
        mesh['grid-template-rows'] = mesh['grid-template-rows'].replace(
            'repeat(%s,' % filas.group(1), 'repeat(%d,' % (int(filas.group(1)) + 1), 1)
    return dict(page, sections=[dict(sec, children=[flecha] + hijos, mesh=mesh)])


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


def render_page(slug, page, idioma='es', origen=None):
    if slug == 'contacto':
        return render_contacto(CONTACTO), '', 0

    if slug == 'paisaje-interior':
        return render_catalogo(idioma), '', 0

    if origen in LISTA:
        return render_lista(slug, origen, page, idioma), '', 0

    if slug == 'proyectos':
        page = flecha_en_proyectos(page)

    if slug in GALERIA:
        return render_galeria(GALERIA[slug], page), '', 0

    css, body, widest = [], [], 0
    for sec in page['sections']:
        sec = reordenar(slug, sec)
        mesh = sec.get('mesh') or {}
        sid = sec['id']
        x0, stage = stage_box(sec['children'])
        if sec.get('lienzo'):
            x0, stage = sec['lienzo']
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
                if idioma == 'en':
                    h = traducir_pieza(origen, c['id'], h)
                h = enlazar(slug, h.replace(' target="_self"', ''))
                extra = CLASES.get(slug, {}).get(c['id'], '')
                if extra:
                    h = enganchar_idioma(slug, extra, h, idioma)
                parts.append('<div id="%s" class="rt%s">%s</div>'
                             % (c['id'], ' ' + extra if extra else '', h))
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


# Entradas que se quedan siempre en la barra; el resto va dentro del «+».
PRINCIPALES = {'proyectos', 'paisaje-interior', 'cv', 'contacto'}


def header_html(active, idioma):
    items = []
    for label, target in MENU:
        href = (SLUG.get(target, ascii_slug(target)) if target else 'index') + '.html'
        cur = ' aria-current="page"' if href == active + '.html' else ''
        if idioma == 'en':
            label = MENU_EN.get(label, label)
        clase = (' class="principal m-%s"' % ascii_slug(target)) if target in PRINCIPALES else ''
        items.append('<li%s><a href="%s"%s>%s</a></li>' % (clase, href, cur, label))
    if PUBLICAR_EN:
        items.append(selector_idioma(idioma, active + '.html'))
    return ('<header class="site-header">\n'
            '<button class="abrir-menu" type="button" aria-expanded="false" '
            'aria-controls="menu-sitio">menú</button>\n'
            '<nav id="menu-sitio" aria-label="Sitio">\n<ul class="menu">\n%s\n'
            '<li class="more"><button type="button" aria-expanded="false" '
            'aria-label="Más páginas">+</button><ul class="submenu"></ul></li>\n'
            '</ul>\n</nav>\n</header>' % '\n'.join(items))


def selector_idioma(idioma, destino):
    """Enlace al otro idioma, como última entrada del menú."""
    otro = 'EN' if idioma == 'es' else 'ES'
    return ('<li class="idioma"><a href="%s" hreflang="%s">%s</a></li>'
            % (ruta_idioma(idioma, destino), 'en' if idioma == 'es' else 'es', otro))


TEMPLATE = """<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="format-detection" content="telephone=no">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Almarai:wght@300;400;700;800&family=Forum&family=Nunito+Sans:ital,wght@0,200..900;1,200..900&family=Open+Sans:ital,wght@0,300..800;1,300..800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{pre}assets/css/site.css?v={vcss}">
<style>
{css}
</style>
</head>
<body class="{bodyclass}">
{header}
<main id="contenido">
{body}
</main>
<script src="{pre}assets/js/escala.js?v={vesc}" defer></script>
<script src="{pre}assets/js/menu.js?v={vmenu}" defer></script>
</body>
</html>
"""

os.makedirs(os.path.join(ROOT, 'assets', 'css'), exist_ok=True)
os.makedirs(os.path.join(ROOT, 'assets', 'js'), exist_ok=True)

for slug, cfg in NUEVAS.items():
    pages[slug] = render_nueva(slug, cfg)
    PAGINAS_EN[slug] = render_nueva(slug, cfg, 'en')
    SLUG[slug] = slug

for slug, page in pages.items():
    out = SLUG[slug]
    desc = ''
    for sec in page['sections']:
        for c in sec['children']:
            if c['type'] == 'text' and len(c.get('text', '')) > 60:
                desc = c['text'][:155].replace('"', "'")
                break
        if desc:
            break

    for idioma in IDIOMAS:
        fuente = PAGINAS_EN[slug] if (idioma == 'en' and slug in PAGINAS_EN) else page
        body, css, bp = render_page(out, fuente, idioma, slug)
        pre = '' if idioma == 'es' else '../'
        html = TEMPLATE.format(
            lang=idioma,
            pre=pre,
            vcss=version('assets/css/site.css'),
            vesc=version('assets/js/escala.js'),
            vmenu=version('assets/js/menu.js'),
            title=(TITULO_EN.get(out) if idioma == 'en' else None)
                  or TITULOS.get(out, page['title']),
            desc=(DESC_EN if idioma == 'en'
                  else (desc or 'sofía lozano ávila — artista, Bogotá, Colombia.')),
            css=css,
            header=header_html(out, idioma),
            bodyclass=('landing' if page['landing'] else 'inner') + ' p-' + out,
            body=body,
        )
        html = html.replace('\u21a9', FLECHA)
        for viejo_txt, nuevo_txt in TEXTOS.get(out, []):
            html = html.replace(viejo_txt, nuevo_txt)

        if idioma == 'en':
            for viejo_txt, nuevo_txt in COMUNES_EN + TEXTO_EN.get(out, []):
                html = html.replace(viejo_txt, nuevo_txt)
            # las páginas de /en/ apuntan a los recursos de la carpeta madre
            html = html.replace('"assets/', '"../assets/')
            destino = os.path.join(ROOT, 'en')
            os.makedirs(destino, exist_ok=True)
        else:
            destino = ROOT

        open(os.path.join(destino, out + '.html'), 'w', encoding='utf-8').write(html)
    print('->', out + '.html  (es + en)')
