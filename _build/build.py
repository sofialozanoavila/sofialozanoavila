# -*- coding: utf-8 -*-
"""Genera el sitio estático (HTML + CSS) a partir del contenido extraído del Wix."""
import hashlib, html as html_mod, json, os, re, sys, unicodedata

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
# La página de la tienda se llamaba «paisaje interior» en Wix; su dirección
# ahora dice lo que es.
if 'paisaje-interior' in SLUG:
    SLUG['paisaje-interior'] = 'tienda'

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

NOMBRES_EN = {
    'nada de lo que se mide es basura': 'nada de lo que se mide es basura',
    'la línea no es recta': 'the line is not straight',
    'dejar que la forma se haga': 'letting the form happen',
    'cuerpo residual': 'residual body',
    'otros proyectos': 'other artworks',
    'inventario sobre lo que no veo': 'inventory of what I cannot see',
    'medir el aire': 'medir el aire',
    'todo lo que no cabe en una vitrina': 'todo lo que no cabe en una vitrina',
}

MENU_EN = {
    'proyectos': 'artworks',
    'talleres': 'workshops',
    'tienda': 'shop',
    'contacto': 'contact',
}

TITULO_EN = {
    'index': 'sofía lozano ávila | artist',
    'proyectos': 'artworks | sofialozanoavila',
    'tienda': 'shop | sofialozanoavila',
    'contacto': 'contact | sofialozanoavila',
    'cv': 'cv | sofialozanoavila',
}

# Sustituciones de texto visible, por página. Solo cadenas que aparecen
# completas dentro de una misma etiqueta.
TEXTO_EN = {
    'index': [
        ('>proyectos', '>artworks'),
        ('>contacto', '>contact'),
        # El inicio en inglés viene ya en inglés desde Wix: no pasa por las
        # sustituciones del castellano, así que se parte de su propio texto.
        ('>Artist<', '>I am an artist.<'),
        ('>Bogotá, Colombia<', '>I live and work in Bogotá, Colombia.<'),
    ],
    'proyectos': [
        ('>proyectos', '>artworks'),
        ('>contacto', '>contact'),
    ],
    'paisaje-interior': [
        ('>tienda<', '>shop<'),
        ('Cerámica. Dimensiones variables.', 'Ceramic. Dimensions variable.'),
    ],
}

# Enlaces que aparecen en varias páginas
COMUNES_EN = [
    ('\u27ac tienda', '\u27ac shop'),
    ('Vista general.', 'General view.'),
    ('Detalle.', 'Detail.'),
]

DESC_EN = 'sofía lozano ávila — artist, Bogotá, Colombia.'


def ruta_idioma(idioma, destino):
    """Enlace a la misma página en el otro idioma."""
    return ('en/' + destino) if idioma == 'es' else ('../' + destino)


# --- menú superior, en el mismo orden que el sitio original -------------------
MENU = [
    ('sofía lozano ávila', ''), ('proyectos', 'proyectos'),
    ('talleres', 'talleres'),
    ('prótesis', 'protesis'), ('antejardín', 'antejardín'),
    ('todo lo que no cabe en una vitrina', 'todo-lo-que-no-cabe-en-una-vitrina'),
    ('tienda', 'paisaje-interior'), ('bache', 'bache'),
    ('superficies de paso', 'superficies-de-paso'),
    ('doblar una flor', 'doblar-una-flor'),
    ('vasija/ver/vaciar', 'vasija-ver-vaciar'), ('procedimiento fértil', 'procedimiento-fertil'),
    ('de dudosa procedencia', 'de-dudosa-procedencia'), ('semi preciosas', 'semi-preciosas'),
    ('revisitar', 'revisitar'), ('inventario sobre lo que no veo', 'inventario-sobre-lo-que-no-veo'),
    ('señales', 'señales'), ('nada de lo que se mide es basura', 'desmesura'),
    ('la línea no es recta', 'la-linea-no-es-recta'),
    ('dejar que la forma se haga', 'dejar-que-la-forma-se-haga'),
    ('cuerpo residual', 'cuerpo-residual'), ('otros proyectos', 'otros-proyectos'),
    ('CV', 'cv'), ('contacto', 'contacto'),
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


# «TIENDA» pasa a llamarse «cerámica» en todo el sitio. El texto
# venía dentro del HTML heredado de Wix, así que se sustituye al generar.
TEXTOS = {
    # Los nombres propios también van en minúscula, como el resto de los
    # títulos del sitio; «CV» se queda como está.
    'cv': [('Bogot&aacute;, Colombia (1997)', 'bogot&aacute;, colombia (1997)')],
    # Venía del Wix con una mayúscula suelta en medio del nombre.
    'cuerpo-residual': [('cuerpo Residual', 'cuerpo residual')],
    # El proyecto pasa de llamarse «desmedida» a llevar el título de la serie.
    'desmesura': [('>desmedida<', '>nada de lo que se mide es basura<')],
    'paisaje-interior': [('>TIENDA<', '>tienda<')],
    'index': [('<span style="color:#FF0006;">\u27ac tienda</span>',
               '<span>\u27ac tienda</span>'),
              ('>Artista<', '>soy artista.<'),
              ('>Bogot&aacute;, Colombia<',
               '>Vivo y trabajo en Bogot&aacute;, Colombia.<')],
    'proyectos': [('<span style="color:#FF0006;">\u27ac tienda</span>',
                   '<span>\u27ac tienda</span>'),
                  ('2020 / desmedida',
                   '2020 / nada de lo que se mide es basura')],
}

TITULOS = {
    'tienda': 'tienda | sofialozanoavila',
    'desmesura': 'nada de lo que se mide es basura | sofialozanoavila',
}


# Nombres estables para algunas piezas, y así poder darles estilo propio
# (los identificadores comp-… vienen de Wix y no dicen nada por sí solos).
def sin_enlace(h, destino):
    """Retira de la lista el renglón que lleva a esa página.

    «vasija / ver / vaciar» es un taller, y vive en la columna de talleres;
    aparecer también entre los proyectos lo contaría dos veces."""
    return re.sub(r'<p\b[^>]*>(?:(?!</p>).)*?href="%s\.html"'
                  r'(?:(?!</p>).)*?</p>\s*' % re.escape(destino),
                  '', h, flags=re.S)


def unir_enlaces(h):
    """Hace que el renglón entero de cada proyecto sea el enlace.

    Wix dejaba fuera del enlace el año y a veces la primera letra del
    nombre —«2023 / p» quedaba suelto y no se podía pulsar—. Aquí el
    enlace abarca todo el párrafo, así el resalte del cursor cubre la
    entrada completa y no un trozo."""
    def uno(m):
        apertura, dentro = m.group(1), m.group(2)
        enlaces = re.findall(r'<a\b[^>]*href="([^"]+)"[^>]*>', dentro)
        # sin enlace (los años) o con destinos distintos: se deja igual
        if not enlaces or len(set(enlaces)) > 1:
            return m.group(0)
        etiqueta = re.search(r'<a\b[^>]*>', dentro).group(0)
        limpio = re.sub(r'<a\b[^>]*>|</a>', '', dentro)
        return '%s%s%s</a></p>' % (apertura, etiqueta, limpio)

    return re.sub(r'(<p\b[^>]*>)(.*?)</p>', uno, h, flags=re.S)


CLASES = {
    'index': {
        'comp-lrjn9lv2': 'enlaces',   # proyectos · contacto · CV · tienda
        'comp-lrfas7qe': 'nombre',    # sofía lozano ávila
        'comp-mtx3uuyd': 'lugar',     # Artista / Bogotá, Colombia
    },
    'proyectos': {
        'comp-m2c3o77q': 'nombre-proyectos',   # sofía lozano ávila
        'comp-mtx4x6u5': 'enlaces-proyectos',  # contacto · CV · tienda
        'comp-luvkx06n1': 'lista-proyectos',   # los proyectos, por año
        'talleres-lista': 'lista-proyectos',   # los talleres, al lado
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

TITULO_EN['desmesura'] = 'nada de lo que se mide es basura | sofialozanoavila'


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
    'superficies-de-paso': {
        'titulo': 'superficies de paso',
        'volver': 'proyectos',
        'ficha': ['3 de Octubre del 2026',
                  'Emblematic Art Gallery - Bogot\u00e1.',
                  'Primer encuentro nacional de artistas mujeres.',
                  '\u201cDesde sus adentros\u201d. Curadur\u00eda de Andrea Mu\u00f1oz.'],
        'texto': [
            'La celos\u00eda y el sif\u00f3n son superficies caladas que regulan lo que '
            'puede atravesar un umbral. La celos\u00eda, ese tablero calado que cierra '
            'ventanas, balcones o fachadas, deja pasar la luz y el aire mientras '
            'bloquea la mirada directa desde afuera, dosificando la privacidad de lo '
            'dom\u00e9stico. El sif\u00f3n hace lo mismo, pero al rev\u00e9s: ubicado en el '
            'suelo, deja pasar el agua y retiene lo que no debe salir, drenando lo '
            '\u00edntimo de la casa hacia lo p\u00fablico del alcantarillado.',
            'Ambos funcionan como un stencil: existen por y desde el molde. Son '
            'objetos matriz, pensados para repetirse y existir en multiplicidad, y su '
            'forma es la de lo que dejan pasar. Una filtra la mirada; el otro filtra '
            'el desecho. Una est\u00e1 en la pared; el otro, en el piso. Pero los dos '
            'son maneras de decidir qu\u00e9 se deja pasar y qu\u00e9 se retiene en el '
            'l\u00edmite entre lo privado y lo p\u00fablico.',
            'De ah\u00ed parte esta actividad: un juego de sombras a partir de '
            'celos\u00edas y sifones recortados en papel. Al proyectar su sombra, ambos '
            'patrones \u2014flores, rejillas, tramas geom\u00e9tricas\u2014 se vuelven '
            'casi indistinguibles entre s\u00ed. Esa ambig\u00fcedad es el punto de '
            'partida para pensar en un espacio delimitado no por muros, sino por la '
            'sombra misma: algo intocable que, sin embargo, marca un adentro y un '
            'afuera.',
            'Este taller fue impartido por Mar\u00eda Paula Mendoza y Sof\u00eda Lozano '
            'en el marco del Primer encuentro nacional de artistas mujeres en '
            'Emblematic Art Gallery, con la exposici\u00f3n \u201cDesde sus '
            'adentros\u201d, curada por Andrea Mu\u00f1oz.',
        ],
        'ficha_en': ['3 October 2026',
                     'Emblematic Art Gallery - Bogot\u00e1.',
                     'First national gathering of women artists.',
                     '\u201cDesde sus adentros\u201d. Curated by Andrea Mu\u00f1oz.'],
        'texto_en': [
            'The lattice screen and the drain are perforated surfaces that govern '
            'what may cross a threshold. The lattice \u2014that pierced panel closing '
            'windows, balconies or fa\u00e7ades\u2014 lets light and air through while '
            'blocking the direct gaze from outside, metering out the privacy of the '
            'domestic. The drain does the same in reverse: set into the floor, it '
            'lets water through and holds back what should not leave, draining the '
            'intimate of the house towards the public of the sewer.',
            'Both work like a stencil: they exist by and from the mould. They are '
            'matrix objects, meant to repeat and to exist in multiplicity, and their '
            'form is the form of what they let through. One filters the gaze; the '
            'other filters waste. One is on the wall; the other, on the floor. But '
            'both are ways of deciding what is let through and what is held back at '
            'the limit between the private and the public.',
            'This activity starts from there: a play of shadows made with lattices '
            'and drains cut out of paper. Cast as shadow, both patterns \u2014flowers, '
            'grilles, geometric weaves\u2014 become almost indistinguishable from one '
            'another. That ambiguity is the starting point for thinking of a space '
            'bounded not by walls but by the shadow itself: something untouchable '
            'that nonetheless marks an inside and an outside.',
            'This workshop was led by Mar\u00eda Paula Mendoza and Sof\u00eda Lozano '
            'within the First national gathering of women artists at Emblematic Art '
            'Gallery, alongside the exhibition \u201cDesde sus adentros\u201d, curated '
            'by Andrea Mu\u00f1oz.',
        ],
        'pies_en': {},
        'fotos': [
            ('superficies-05.jpg', ''),
            ('superficies-01.jpg', ''),
            ('superficies-02.jpg', ''),
            ('superficies-03.jpg', ''),
            ('superficies-04.jpg', ''),
            ('superficies-06.jpg', ''),
            ('superficies-07.jpg', ''),
        ],
    },
    'doblar-una-flor': {
        'titulo': 'doblar una flor',
        'volver': 'proyectos',
        'ficha': ['30 de Mayo del 2025',
                  'Casa Fern\u00e1ndez - Bogot\u00e1.',
                  'Segunda Jornada de Estudios Abiertos.',
                  'Residencia En Bloque - Idartes.'],
        'texto': [
            'Como parte de la Segunda Jornada de Estudios Abiertos, realizada el '
            '30 de mayo de 2025, se llev\u00f3 a cabo una conversaci\u00f3n con los '
            'asistentes sobre el proyecto \u201cAntejard\u00edn\u201d y se realiz\u00f3 '
            'el taller \u201cDoblar una flor\u201d, desarrollado en Casa Fern\u00e1ndez, '
            'en el marco de la Residencia En Bloque de Idartes.',
            'La conversaci\u00f3n abri\u00f3 con una presentaci\u00f3n del proyecto, que se '
            'interesa por el antejard\u00edn como espacio intermedio entre la calle y '
            'la casa: un lugar ni completamente p\u00fablico ni del todo privado, con '
            'un car\u00e1cter liminal, de umbral. El proyecto trabaja con los objetos '
            'que pueblan ese espacio \u2014regaderas, palas, recipientes, tierra y '
            'fuentes\u2014 y c\u00f3mo, en lugar de reproducir su forma o su uso, los '
            'desajusta para dejar ver su fragilidad. Se habl\u00f3 de las piezas '
            'cer\u00e1micas que resultan de ese proceso, como regaderas sin orificios, '
            'recipientes que escurren y flores de cer\u00e1mica que sobresalen de una '
            'monta\u00f1a de tierra. Estas piezas no buscan resolver una funci\u00f3n, '
            'sino plantear preguntas sobre ella y sobre el orden de lo dom\u00e9stico, '
            'lo decorativo y lo \u00fatil.',
            'A partir de ese marco, el taller propuso trasladar la pregunta por el '
            'jard\u00edn al entorno inmediato: la flora del Parque Nacional. Los '
            'participantes conversaron sobre las plantas que habitan este espacio '
            'p\u00fablico, sus formas, sus nombres y las relaciones que las personas '
            'tienen con ellas, mientras coloreaban l\u00e1minas de tres especies '
            'escogidas. Colorear funcion\u00f3 como una actividad pausada que '
            'acompa\u00f1\u00f3 la charla y favoreci\u00f3 la observaci\u00f3n atenta de '
            'cada flor.',
            'El taller, de car\u00e1cter abierto y participativo, cont\u00f3 con seis '
            'asistentes. As\u00ed, el proyecto se extendi\u00f3 m\u00e1s all\u00e1 de la sala '
            'de exposici\u00f3n, hacia un espacio de intercambio donde las personas '
            'pudieron relacionarse con la flora del parque a trav\u00e9s del dibujo.',
        ],
        'ficha_en': ['30 May 2025',
                     'Casa Fern\u00e1ndez - Bogot\u00e1.',
                     'Second Open Studios Day.',
                     'En Bloque residency - Idartes.'],
        'texto_en': [
            'As part of the Second Open Studios Day, held on 30 May 2025, a '
            'conversation was held with those attending about the project '
            '\u201cAntejard\u00edn\u201d, together with the workshop \u201cDoblar una '
            'flor\u201d, run at Casa Fern\u00e1ndez within the En Bloque residency of '
            'Idartes.',
            'The conversation opened with a presentation of the project, which takes '
            'an interest in the antejard\u00edn \u2014the front garden\u2014 as a space '
            'between the street and the house: a place neither wholly public nor '
            'wholly private, liminal, a threshold. The project works with the objects '
            'that inhabit it \u2014watering cans, spades, containers, soil and '
            'fountains\u2014 and with how, rather than reproducing their shape or '
            'their use, it unsettles them to let their fragility show. We spoke about '
            'the ceramic pieces that come out of that process: watering cans without '
            'holes, containers that leak, ceramic flowers rising out of a mound of '
            'earth. These pieces do not set out to resolve a function but to raise '
            'questions about it, and about the order of the domestic, the decorative '
            'and the useful.',
            'From there, the workshop proposed carrying the question of the garden '
            'into the immediate surroundings: the flora of the Parque Nacional. The '
            'participants talked about the plants that inhabit this public space, '
            'their forms, their names and the relationships people have with them, '
            'while colouring in prints of three chosen species. Colouring worked as '
            'an unhurried activity that accompanied the talk and encouraged close '
            'attention to each flower.',
            'The workshop, open and participatory, was attended by six people. In '
            'this way the project reached beyond the exhibition room, into a space '
            'of exchange where people could relate to the flora of the park through '
            'drawing.',
        ],
        'pies_en': {
            'Taller. Casa Fern\u00e1ndez, Bogot\u00e1. 2025.':
                'Workshop. Casa Fern\u00e1ndez, Bogot\u00e1. 2025.',
            'L\u00e1mina coloreada durante el taller. 2025.':
                'Print coloured in during the workshop. 2025.',
        },
        'fotos': [
            ('doblar-02.jpg', 'Taller. Casa Fern\u00e1ndez, Bogot\u00e1. 2025.'),
            ('doblar-01.jpg', 'Taller. Casa Fern\u00e1ndez, Bogot\u00e1. 2025.'),
            ('doblar-03.jpg', 'L\u00e1mina coloreada durante el taller. 2025.'),
        ],
    },
    'protesis': {
        'titulo': 'prótesis',
        'volver': 'proyectos',
        'ficha': ['3 de Septiembre - 15 de Octubre 2026',
                  'Emblematic Art Gallery - Bogot\u00e1.',
                  'Curadur\u00eda de Andrea Mu\u00f1oz.'],
        'texto': [
            'Habitar las ruinas de lo que alguna vez fue la cocina es el punto de partida para “Prótesis”. Este espacio, que aún conserva vestigios fantasmales de su función original como tubos de gas cercenados, tomas eléctricas mudas y una ventana al patio interior, se activa a través de un profundo deseo de completar lo que falta. Entendiendo la cocina como un archivo doméstico que custodia la memoria de gestos repetidos, la artista fija su mirada en los objetos “secundarios”.',
            'Clavijas, cables y conexiones se materializan sutilmente en cerámica, ocupando el vacío de los circuitos interrumpidos. La propuesta se despliega en piezas que dialogan orgánicamente: serigrafías que actúan como restauraciones ficticias del antiguo papel tapiz; una tubería suspendida y estructuras de estufas que, en su proceso de creación, adquirieron la apariencia de huesos, cual injertos sobre la arquitectura de la casa.',
            'En conjunto, esta propuesta aborda la cocina como un cuerpo fragmentado. A través de estas piezas frágiles y suspendidas, como susurros materiales, la artista crea una vida extraña que nos devuelve, por un instante, la pulsión de un tiempo doméstico ya extinguido.',
        ],
        'firma': 'Andrea Mu\u00f1oz',
        'ficha_en': ['3 September - 15 October 2026',
                     'Emblematic Art Gallery - Bogot\u00e1.',
                     'Curated by Andrea Mu\u00f1oz.'],
        'texto_en': [
            'Inhabiting the ruins of what was once the kitchen is the starting point for “Prótesis”. This space, which still holds ghostly vestiges of its original function —severed gas pipes, mute electrical sockets and a window onto the inner courtyard— is activated through a deep desire to complete what is missing. Understanding the kitchen as a domestic archive that guards the memory of repeated gestures, the artist fixes her gaze on the “secondary” objects.',
            'Plugs, cables and connections take subtle material form in ceramic, occupying the void of the interrupted circuits. The proposal unfolds in pieces that speak to one another organically: screen prints acting as fictitious restorations of the old wallpaper; a suspended pipe and stove structures that, in the process of their making, took on the appearance of bones, like grafts upon the architecture of the house.',
            'Taken together, this proposal approaches the kitchen as a fragmented body. Through these fragile, suspended pieces —material whispers— the artist creates a strange life that gives us back, for an instant, the pulse of a domestic time already extinguished.',
        ],
        'pies_en': {
            'Vista general de la exposición.': 'General view of the exhibition.',
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
            ('protesis-15.jpg', 'Vista general de la exposición.'),
            ('protesis-14.jpg', 'Vista general de la exposición.'),
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
# estilo). Se sustituye por un dibujo vectorial, que se ve igual en todos
# los dispositivos: una recta con la punta pequeña, en negro.
FLECHA = (
    '<svg class="flecha" viewBox="0 0 25 22" role="img" aria-label="Volver"'
    ' fill="none" stroke="#000000" stroke-width="1.15"'
    ' stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M23 11 H3"/><path d="M9 5.6 L3 11 L9 16.4"/>'
    '</svg>'
)


TXT_TITULO = ('<h1 class="font_0" style="font-size:34px;"><span style="color:#000000;">'
              '<span style="font-family:open sans,sans-serif;">'
              '<span style="font-size:34px;">%s</span></span></span></h1>')
TXT_VOLVER = ('<p class="font_8" style="font-size:40px; line-height:normal;">'
              '<a href="%s.html"><span style="color:#000000;"><span style="font-size:40px;">'
              '<span style="letter-spacing:normal;">↩</span></span></span></a></p>')
TXT_FICHA = '<p class="font_8 %s">%s</p>'


def html_ficha(renglones, fecha=True):
    """Arma el bloque de la ficha.

    El primer renglón suele ser la fecha y se compone algo más grande; el
    lugar y la curaduría van debajo, con remates, para que se distingan de
    un vistazo sin necesidad de leerlos."""
    salida = []
    hueco = False
    for i, r in enumerate(renglones):
        # un renglón vacío no se imprime: abre un respiro antes del siguiente
        if not r:
            hueco = True
            continue
        clase = 'fecha' if (fecha and i == 0) else 'sede'
        if hueco:
            clase += ' hueco'
            hueco = False
        # los renglones que ya traen etiquetas (un enlace) pasan tal cual
        cuerpo = r if '<' in r else html_mod.escape(r)
        salida.append(TXT_FICHA % (clase, cuerpo))
    return ''.join(salida)
TXT_PARRAFO = ('<p class="font_8" style="font-size:14px;"><span style="font-size:14px;">'
               '<span style="font-weight:300;"><span style="font-family:almarai,sans-serif;">'
               '%s</span></span></span></p>')
TXT_VACIO = ('<p class="font_8" style="font-size:14px;">&nbsp;</p>')
TXT_PIE = ('<p class="font_8" style="font-size:12px; line-height:1.4em;">'
           '<span style="color:#414141;"><span style="font-size:12px;">'
           '<span style="letter-spacing:0em;">%s</span></span></span></p>')


def pieza(cid, tipo, fila, left, ancho, abajo, filas=1, **extra):
    # El texto plano se guarda junto al html: es lo que distingue el texto del
    # proyecto de un pie de foto cuando se reparte la página.
    if 'html' in extra and 'text' not in extra:
        plano = html_desescapar(re.sub(r'<[^>]+>', ' ', extra['html']))
        extra['text'] = ' '.join(plano.replace('\u200b', ' ').split())
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
                           html=html_ficha(ficha)))
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


# Ficha de cada exposición, reescrita a mano con un orden único:
# fecha (inicio - final, si la hay) / lugar / nombre de la curaduría /
# quién curó. Así todas las entradas se leen igual.
ENLACE_MILLON = ('<a href="https://convocatorias.feriadelmillon.com/es/ferias/feria-del-millon-10-anos/" target="_blank" rel="noreferrer noopener">')

FICHAS = {
    'antejardín': ('comp-md1puf2r', [
        '7 de Junio - 15 de Julio 2025',
        'FLOTANTE - Bogotá.',
    ], [
        '7 June - 15 July 2025',
        'FLOTANTE - Bogotá.',
    ]),
    'bache': ('comp-m2c5vned', [
        '25 - 30 de Septiembre del 2024',
        'Ágora centro de convenciones - Bogotá.',
        'Sección Artecámara - “Una moneda al aire”',
        'Curaduría de Ximena Gama',
    ], [
        '25 - 30 September 2024',
        'Ágora convention centre - Bogotá.',
        'Artecámara section - “Una moneda al aire”',
        'Curated by Ximena Gama',
    ]),
    'copia-de-antejardín': ('comp-mh0tn16s', [
        '25 de Septiembre - 25 de Diciembre 2025',
        'Ágora centro de convenciones - Bogotá.',
        '“Atrapar, calar, tejer mitos”',
        'Curaduría Arte vivo.',
    ], [
        '25 September - 25 December 2025',
        'Ágora convention centre - Bogotá.',
        '“Atrapar, calar, tejer mitos”',
        'Curated by Arte Vivo.',
    ]),
    'cuerpo-residual': ('comp-lrp5kkwe', [
        '2020',
        'Bogotá.',
    ], [
        '2020',
        'Bogotá.',
    ]),
    'dejar-que-la-forma-se-haga': ('comp-lrp67gmh', [
        '2020',
        'Bogotá.',
    ], [
        '2020',
        'Bogotá.',
    ]),
    'de-dudosa-procedencia': ('comp-lrhvtebq1', [
        '1 al 29 de Octubre del 2023',
        'Residencia en No Lugar - Quito, Ecuador.',
    ], [
        '1 - 29 October 2023',
        'Residency at No Lugar - Quito, Ecuador.',
    ]),
    'desmesura': ('comp-lrfdguzx2', [
        'Edición 2020',
        'Feria Barcú - Bogotá. Sección Spotlights.',
    ], [
        '2020 edition',
        'Barcú Fair - Bogotá. Spotlights section.',
    ]),
    'la-linea-no-es-recta': ('comp-lrfc33y8', [
        'Espacio Odeón - Bogotá.',
    ], [
        'Espacio Odeón - Bogotá.',
    ], False),
    'otros-proyectos': ('comp-lrp8h3g7', [
        '2018 - 2022',
    ], [
        '2018 - 2022',
    ]),
    'procedimiento-fertil': ('comp-lrhwsxav2', [
        '28 de Octubre del 2023 - 10 de Febrero del 2024',
        'Espacio El Dorado - Bogotá.',
        'Proyecto ganador de la convocatoria “En Blanco”.',
    ], [
        '28 October 2023 - 10 February 2024',
        'Espacio El Dorado - Bogotá.',
        'Winning project of the “En Blanco” open call.',
    ]),
    'revisitar': ('comp-lrpeu12e', [
        '29 de Septiembre al 2 de Octubre del 2022',
        'Plaza La Santamaría - Bogotá. Feria del Millón.',
        '➝ %sFeria del Millón 10 años - Artistas.</a>' % ENLACE_MILLON,
        '',
        'Serie de 18 dibujos, lápiz de color sobre papel.',
    ], [
        '29 September - 2 October 2022',
        'Plaza La Santamaría - Bogotá. Feria del Millón.',
        '➝ %sFeria del Millón 10 years - Artists.</a>' % ENLACE_MILLON,
        '',
        'Series of 18 drawings, coloured pencil on paper.',
    ]),
    'semi-preciosas': ('comp-lrh7i87c1', [
        '24 de Agosto - 24 de Septiembre 2023',
        'Plural Nodo Cultural - Bogotá.',
        '“Fragmentos Móviles”',
        'Curaduría de Andrea Infante y Paula Leuro.',
    ], [
        '24 August - 24 September 2023',
        'Plural Nodo Cultural - Bogotá.',
        '“Fragmentos Móviles”',
        'Curated by Andrea Infante and Paula Leuro.',
    ]),
    'todo-lo-que-no-cabe-en-una-vitrina': ('comp-m2c5w6yg', [
        '23 de Abril - 23 de Mayo del 2025',
        'Universidad de Los Andes - Bogotá.',
        'Proyecto ganador de la convocatoria “La vitrina”.',
    ], [
        '23 April - 23 May 2025',
        'Universidad de Los Andes - Bogotá.',
        'Winning project of the “La vitrina” open call.',
    ]),
}


# Fotografías propias que se añaden al final de una entrada, después de
# las que venían del Wix.
# Entradas cuyas fotografías propias van detrás de las que vienen del Wix,
# en lugar de abrirlas.
AL_FINAL = {'antejard\u00edn'}

AGREGADAS = {
    'antejard\u00edn': [
        ('antejardin-plantas-montaje.jpg', 1164, 1600,
         'Los dos cuadros de la serie, colgados en la pared'),
        ('antejardin-plantas-01.jpg', 1254, 1600, 'Retrato con eucalipto'),
        ('antejardin-plantas-02.jpg', 1226, 1600, 'Retrato con ramo de flores'),
    ],
    'desmesura': [
        ('desmesura-montaje.jpg', 1600, 976, 'Los tres dibujos enmarcados en la pared'),
    ],
    'vasija-ver-vaciar': [
        ('vasija-01.jpg', 1050, 1400, 'Mesa de trabajo'),
        ('vasija-02.jpg', 1050, 1400, 'Libro de vasijas prehispánicas'),
        ('vasija-03.jpg', 1050, 1400, 'Rollos de barro y cuenco'),
        ('vasija-04.jpg', 1050, 1400, 'Vasija con una mano en relieve'),
        ('vasija-05.jpg', 1050, 1400, 'Pieza con rostro'),
    ],
}


# Ajustes de posición sobre la maqueta heredada de Wix. Las medidas son las
# mismas de las páginas de proyecto: un riel de 420 px a la izquierda, 56 px
# de separación, y el texto largo en la columna de la derecha.
COLOCAR = {
    'proyectos': {
        # venía 5 px más ancha que el lienzo, y al estirarse se salía por
        # la derecha del margen
        'comp-mtx4x6u5': {'width': '639px'},
    },
    'cv': {
        # cabecera —ciudad, año y «CV»— en el riel izquierdo
        'comp-lrp5e671': {'left': '0px', 'width': '420px',
                          'margin': '2px 0px 21px 0px'},
        # el texto, donde va el de los proyectos: misma fila que la
        # cabecera, para que ambos arranquen a la misma altura
        'comp-lrjhvqx41': {'left': '476px', 'width': '636px',
                           'grid-area': '2 / 1 / 3 / 2',
                           'margin': '6.04px 0px 10px 0px'},
    },
}


# La flecha de volver debe caer a la misma altura en todas las páginas:
# 30 px por debajo de la barra del menú. Algunas la traían pegada arriba.
MARGEN_SUPERIOR = {
    'cv': {'comp-m4wyash5': '30px'},
}


# Piezas que se retiran de la página por completo.
OMITIR = {
    # llevaba la dirección web entera pegada al texto, sin espacio
    # los tres dibujos —negro, rojo y verde— se ven ahora en el montaje
    'desmesura': {'comp-lrpeet00', 'comp-lrfdo8ia', 'comp-lrfdmanc',
                  'comp-lrfdmana', 'comp-lrfdrp4t'},
    # el enlace y la técnica pasaron a la ficha, arriba
    'revisitar': {'comp-lrpeujyh'},
}


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
    'vasija-ver-vaciar': {
        'nueva-vasija-01.jpg': (['Proceso. 2024.'], ['Process. 2024.']),
        'nueva-vasija-02.jpg': (['Proceso. 2024.'], ['Process. 2024.']),
        'nueva-vasija-03.jpg': (['Proceso. 2024.'], ['Process. 2024.']),
        'nueva-vasija-04.jpg': (['Proceso. 2024.'], ['Process. 2024.']),
        'nueva-vasija-05.jpg': (['Proceso. 2024.'], ['Process. 2024.']),
    },
    'revisitar': {
        'comp-lrh6m4i8': (['Vista general de la exposición.'],
                          ['General view of the exhibition.']),
    },
    'copia-de-antejardín': {
        'comp-m7mr6gix1': (['Medir el aire. Tejido caña flecha, fibras naturales. 250 x 50 cms. 2025'], ['Medir el aire. Caña flecha weaving, natural fibres. 250 x 50 cm. 2025']),
        'comp-mn4wyksp': (['Medir el aire. Tejido caña flecha, fibras naturales. 250 x 50 cms. 2025'], ['Medir el aire. Caña flecha weaving, natural fibres. 250 x 50 cm. 2025']),
        'comp-mh0u50b1': (['Detalle.'], ['Detail.']),
        'comp-mn4x0274': (['Dibujo. Lápiz negro sobre papel. Dimensiones variables. 2025'], ['Drawing. Black pencil on paper. Dimensions variable. 2025']),
        'comp-mh0u6ow8': (['Dibujo. Lápiz de color sobre papel. Dimensiones variables. 2025'], ['Drawing. Coloured pencil on paper. Dimensions variable. 2025']),
    },
    'antejardín': {
        'nueva-antejardin-plantas-montaje.jpg': (['De la serie \u201cPlantas y poder\u201d. Pintura. \u00d3leo sobre lienzo. 35 x 40 cms. 2026.'], ['From the series \u201cPlantas y poder\u201d. Painting. Oil on canvas. 35 x 40 cm. 2026.']),
        'nueva-antejardin-plantas-01.jpg': (['Detalle. De la serie \u201cPlantas y poder\u201d. Pintura. \u00d3leo sobre lienzo. 35 x 40 cms. 2026.'], ['Detail. From the series \u201cPlantas y poder\u201d. Painting. Oil on canvas. 35 x 40 cm. 2026.']),
        'nueva-antejardin-plantas-02.jpg': (['Detalle. De la serie \u201cPlantas y poder\u201d. Pintura. \u00d3leo sobre lienzo. 35 x 40 cms. 2026.'], ['Detail. From the series \u201cPlantas y poder\u201d. Painting. Oil on canvas. 35 x 40 cm. 2026.']),
        'comp-md1ogjko': (['Vista general de la exposición.'],
                          ['General view of the exhibition.']),
        'comp-md1ogjkk': (['Regadera. Cerámica, tierra. Dimensiones variables. 2025'], ['Watering can. Ceramic, soil. Dimensions variable. 2025']),
        'comp-md1ogjjy': (['Cerámica. Herramientas. 40 x 25 cms. 2025'], ['Ceramic. Tools. 40 x 25 cm. 2025']),
        'comp-md1ogjk3': (['Instalación. Matera plástica, plantas, tierra. 50 x 40 x 25 cms. 2025'], ['Installation. Plastic planter, plants, soil. 50 x 40 x 25 cm. 2025']),
        'comp-md1ogjkg': (['Instalación. Regadera en cerámica, base plástica, agua. 170 x 20 x 30 cms. 2025'], ['Installation. Ceramic watering can, plastic base, water. 170 x 20 x 30 cm. 2025']),
        'comp-md1ogjju': (['Instalación. Cerámica. 80 x 40 x 10 cms. 2025'], ['Installation. Ceramic. 80 x 40 x 10 cm. 2025']),
        'comp-md1ogjka': (['Instalación. Cerámica, tierra. 80 x 40 x 30 cms. 2025'], ['Installation. Ceramic, soil. 80 x 40 x 30 cm. 2025']),
    },
    'bache': {
        'comp-m3eskx37': (['Bache. Instalación. Cerámica, plataforma blanca. 190 x 190 cms. x 70 cms. 2024'], ['Bache. Installation. Ceramic, white platform. 190 x 190 x 70 cm. 2024']),
        'comp-m33ekp53': (['Detalle.'], ['Detail.']),
        'comp-m2c5vner1': (['Bache. Instalación. Cerámica, plataforma blanca. 190 x 190 cms. x 70 cms. 2024'], ['Bache. Installation. Ceramic, white platform. 190 x 190 x 70 cm. 2024']),
    },
    'todo-lo-que-no-cabe-en-una-vitrina': {
        'comp-md1ucubl': (['Todo lo que no cabe en una vitrina. Instalación. Vinilo, plotter de corte, vitrina. Dimensiones variables. 2025'], ['Todo lo que no cabe en una vitrina. Installation. Vinyl, cut plotter, display case. Dimensions variable. 2025']),
        'comp-md1ucubh': (['Todo lo que no cabe en una vitrina. Instalación. Vinilo, plotter de corte, vitrina. Dimensiones variables. 2025'], ['Todo lo que no cabe en una vitrina. Installation. Vinyl, cut plotter, display case. Dimensions variable. 2025']),
        'comp-md1ucubd': (['Texto de sala.'], ['Exhibition text.']),
    },
    'otros-proyectos': {
        # la primera pierde la mencion a las piezas en ceramica
        'comp-lrguzcel': (['Serie de dibujos. Sin t\u00edtulo. Tinta sobre papel. 2022.'],
                          ['Series of drawings. Untitled. Ink on paper. 2022.']),
        'comp-lrpaukwz': (['Sin t\u00edtulo. Dibujo. Tinta sobre papel. Dimensiones variables. 2018.'],
                          ['Untitled. Drawing. Ink on paper. Dimensions variable. 2018.']),
        'comp-lrpaykm5': (['Dibujo.'], ['Drawing.']),
        'comp-lrpaukww': (['Dibujo. Cartograf\u00edas. Tinta sobre papel. 22 \u00d7 28 cms. 2018.'],
                          ['Drawing. Cartograf\u00edas. Ink on paper. 22 \u00d7 28 cm. 2018.']),
        'comp-lrpaukx4': (['Dibujo. Mapa. Tinta sobre papel. 22 \u00d7 28 cms. 2018.'],
                          ['Drawing. Map. Ink on paper. 22 \u00d7 28 cm. 2018.']),
    },
    'de-dudosa-procedencia': {
        'comp-lrhwhalv': (['Vista general de la exposici\u00f3n.'],
                          ['General view of the exhibition.']),
        'comp-lrhwhalh': (['Dudosos. Dibujo. Pared, papel, lápiz. Medidas Variables. 2023'], ['Dudosos. Drawing. Wall, paper, pencil. Dimensions variable. 2023']),
        'comp-lrhwn7fj': (['Detalle'], ['Detail']),
        'comp-lrhwn7fg': (['Dudosos. Dibujo. Pared, papel, lápiz. Medidas Variables. 2023'], ['Dudosos. Drawing. Wall, paper, pencil. Dimensions variable. 2023']),
        'comp-lrhwhals': (['Texto de sala'], ['Exhibition text']),
    },
    'semi-preciosas': {
        'comp-lrpfy9ml': (['Semipreciosas. Escultura. Yeso, hilos. 200 x 200 x 200 cm. 2023'], ['Semipreciosas. Sculpture. Plaster, thread. 200 x 200 x 200 cm. 2023']),
        'comp-lrpfy9m6': (['Semipreciosas. Escultura. Yeso, hilos. 200 x 200 x 200 cm. 2023'], ['Semipreciosas. Sculpture. Plaster, thread. 200 x 200 x 200 cm. 2023']),
        'comp-lrpfy9mc': (['Detalle'], ['Detail']),
    },
    'procedimiento-fertil': {
        'comp-lrph1i5n': (['Vista general de la exposici\u00f3n.'],
                          ['General view of the exhibition.']),
        'comp-lrph1i5d': (['Vista general de la exposici\u00f3n.'],
                          ['General view of the exhibition.']),
        'comp-lrphqa7k': (['Instalaci\u00f3n. Tierra, madera. Medidas variables. 2023.',
                           'Dibujo. \u201cEscala\u201d. Carboncillo sobre papel. 2023.',
                           'Pintura. \u201cVara de la interpretaci\u00f3n\u201d. Pintura acr\u00edlica sobre palo de cedro. 2023.'],
                          ['Installation. Soil, wood. Dimensions variable. 2023.',
                           'Drawing. \u201cEscala\u201d. Charcoal on paper. 2023.',
                           'Painting. \u201cVara de la interpretaci\u00f3n\u201d. Acrylic paint on cedar pole. 2023.']),
        'comp-lrphgsk0': (['Detalle. Escala de damero.'],
                          ['Detail. Chequered scale bar.']),
        'comp-lrph1i5j': (['Detalle de Pintura. \u201cVara de la interpretaci\u00f3n\u201d. '
                           'Pintura acr\u00edlica sobre palo de cedro. 2023.'],
                          ['Detail of painting. \u201cVara de la interpretaci\u00f3n\u201d. '
                           'Acrylic paint on cedar pole. 2023.']),
        'comp-m4wxkg31': (['Vista del entramado de los listones de madera que son el soporte '
                           'de la instalaci\u00f3n.'],
                          ['View of the lattice of wooden battens that supports the installation.']),
        'comp-m4wxhd80': (['Vista desde afuera.'], ['View from outside.']),
    },
    'desmesura': {
        # el montaje reemplaza a los tres dibujos sueltos
        'nueva-desmesura-montaje.jpg': (
            ['\u201cNada de lo que se mide es basura\u201d. Serie de tres dibujos. '
             'Impresi\u00f3n digital y tinta blanca sobre papel. 50\u00d735 cms c/u. 2020.'],
            ['\u201cNada de lo que se mide es basura\u201d. Series of three drawings. '
             'Digital print and white ink on paper. 50 x 35 cm each. 2020.']),
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
    'protesis', 'doblar-una-flor', 'superficies-de-paso',
}


def render_lista(slug, origen, page, idioma):
    """Reparte la página en una introducción y una lista de obras."""
    fuera = OMITIR.get(origen, set())
    piezas = []
    for sec in page['sections']:
        # Las correcciones de maquetación se aplican antes de repartir las
        # piezas: si no, se usa la disposición original de Wix.
        piezas += [c for c in ordenar(reordenar(slug, sec)['children'])
                   if c['id'] not in fuera]

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

    # Las fotografías propias abren la entrada; las que venían del Wix quedan
    # debajo. Se añaden después de ordenar, porque no tienen posición en la
    # cuadrícula original de la que tomar el orden.
    nuevas = [{'pies': [], 'foto': {
        'id': 'nueva-' + archivo, 'type': 'image', 'geo': {},
        'archivo': 'assets/img/' + archivo,
        'w': ancho, 'h': alto, 'alt': alt}}
        for archivo, ancho, alto, alt in AGREGADAS.get(origen, [])]
    obras = obras + nuevas if origen in AL_FINAL else nuevas + obras

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
    # En las páginas escritas a mano el texto del proyecto viene marcado; en
    # las heredadas de Wix se reconoce por su largo.
    def es_cuerpo(c):
        return c['id'] == 'n-texto' or len(c.get('text', '')) > 250

    cortos = [c for c in intro if not es_flecha(c) and not es_cuerpo(c)]
    largos = [c for c in intro if not es_flecha(c) and es_cuerpo(c)]

    ficha = FICHAS.get(origen)

    def texto_pieza(c):
        if ficha and c['id'] == ficha[0]:
            return html_ficha(ficha[2] if idioma == 'en' else ficha[1],
                              fecha=ficha[3] if len(ficha) > 3 else True)
        return texto(c)

    def bloques(lista):
        return ''.join('<div class="rt">%s</div>' % texto_pieza(c) for c in lista)

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


# --- catálogo de cerámica ------------------------------------------
# Datos y fotografías tomados del portafolio de obra disponible. Los precios
# llevan ya el aumento de 100.000 pesos acordado.
CORREO = 'sofia771199@gmail.com'
# El botón «consultar» abre una conversación de WhatsApp con el mensaje ya
# escrito. wa.me pide el número sin signos: indicativo del país y después
# el número, sin el «+» ni espacios.
WHATSAPP = '573223940719'

CATALOGO = [
    ('medir-el-aire', 'Medir el aire', 'Tejido ca\u00f1a flecha, fibras naturales',
     '250 x 50 cm', 2025, 2500000, ''),
    ('filtraciones', 'Filtraciones', 'Dibujo. L\u00e1piz sobre papel',
     '35 x 50 cm', 2026, 1500000, ''),
    ('nada-basura', 'Nada de lo que se mide es basura',
     'Serie de tres dibujos. Impresi\u00f3n digital y tinta blanca sobre papel',
     '50 x 35 cm c/u', 2020, 0, ''),
    ('collar-1', 'Variaciones de un collar', 'Dibujo. L\u00e1piz sobre papel',
     'Medidas variables', 2023, 0, ''),
    ('collar-2', 'Variaciones de un collar', 'Dibujo. L\u00e1piz sobre papel',
     'Medidas variables', 2023, 0, ''),
    ('monos-1', 'De la serie moños', 'Cerámica', '', 2026, 160000, ''),
    ('monos-2', 'De la serie moños', 'Cerámica', '5 x 6 x 4 cm', 2026, 160000, ''),
    ('monos-serie', 'Moños', 'Cerámica', '30 x 20 x 6 cm', 2026, 380000, 'Serie completa'),
    ('palas', 'Palas', 'Cerámica', '30 x 25 x 5 cm', 2025, 600000, 'Queda una disponible'),
    ('apariciones-instalacion', 'Apariciones', 'Cerámica y tierra', '50 x 50 x 50 cm', 2025,
     2100000, 'Instalación completa'),
    ('apariciones-piezas', 'Apariciones', 'Cerámica', '10 x 10 x 8 cm', 2025, 170000,
     'Por pieza · serie completa 400.000'),
    ('banda-elastica', 'Banda elástica', 'Cerámica', '12 x 5 x 3 cm', 2026, 160000, ''),
    ('concha', 'Concha', 'Cerámica', '16,5 x 10,5 cm', 2026, 180000, ''),
    ('caja-2', 'Caja 2', 'Cerámica', '16,5 x 11 cm', 2026, 180000, ''),
    ('pocillo', 'Pocillo', 'Cerámica', '8 x 8 x 10 cm', 2022, 150000, ''),
    ('flor-borrachero', 'Flor borrachero', 'Cerámica', '12 x 12 x 12 cm', 2026, 180000, ''),
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
    'Tejido ca\u00f1a flecha, fibras naturales': 'Ca\u00f1a flecha weaving, natural fibres',
    'Dibujo. L\u00e1piz sobre papel': 'Drawing. Pencil on paper',
    'Medidas variables': 'Dimensions variable',
    'Serie de tres dibujos. Impresi\u00f3n digital y tinta blanca sobre papel':
        'Series of three drawings. Digital print and white ink on paper',
    'Nada de lo que se mide es basura': 'Nada de lo que se mide es basura',
}


def pesos(n):
    return '$' + '{:,}'.format(n).replace(',', '.') + ' COP'


# La tienda se divide por técnica. Cada grupo lleva las claves de sus obras,
# en el orden en que se muestran.
GRUPOS = [
    ('tejido', 'tejido', 'weaving', ['medir-el-aire']),
    ('dibujo', 'dibujo', 'drawing',
     ['nada-basura', 'filtraciones', 'collar-1', 'collar-2']),
    ('ceramica', 'cer\u00e1mica', 'ceramics',
     ['monos-1', 'monos-2', 'monos-serie', 'palas',
      'apariciones-instalacion', 'apariciones-piezas', 'banda-elastica',
      'concha', 'caja-2', 'pocillo', 'flor-borrachero',
      'vertebra', 'caja', 'cuchara']),
]


# El CV, en dos columnas: la fecha a la izquierda y el hecho a la derecha.
# Se escribe aqu\xed y no en el HTML heredado de Wix, para poder darle forma.
CV = [
    ('EDUCACI\xd3N', 'EDUCATION', [
        ('2014-2019', 'Maestra en Artes Pl\xe1sticas. Universidad El Bosque (UEB), Facultad de creaci\xf3n y comunicaci\xf3n, Bogot\xe1 (COL)', 'Fine Arts degree. Universidad El Bosque (UEB), Faculty of creation and communication, Bogot\xe1 (COL)'),
        ('2016', 'Programa de intercambio, Universidad Nacional Aut\xf3noma de M\xe9xico (UNAM). Licenciatura en artes Visuales, Facultad de artes y dise\xf1o (FAD), Ciudad de M\xe9xico', 'Exchange programme, Universidad Nacional Aut\xf3noma de M\xe9xico (UNAM). Visual Arts, Faculty of art and design (FAD), Mexico City'),
    ]),
    ('EXPOSICIONES INDIVIDUALES', 'SOLO EXHIBITIONS', [
        ('2025', 'Antejard\xedn / Flotante, Bogot\xe1 (COL)', ''),
        ('2025', 'La vitrina / Universidad de Los Andes, Bogot\xe1 (COL)', ''),
        ('2023', 'Procedimiento F\xe9rtil / Espacio El Dorado, Bogot\xe1 (COL)', ''),
    ]),
    ('EXPOSICIONES COLECTIVAS / PROYECTOS', 'GROUP EXHIBITIONS / PROJECTS', [
        ('2026', 'Desde sus adentros / Emblematic Art Gallery, Bogot\xe1 (COL)', ''),
        ('2026', 'Atrapar, calar, tejer mitos / Expoartesano, Medell\xedn (COL)', ''),
        ('2026', 'Pausa / Perezoso caf\xe9, Bogot\xe1 (COL)', ''),
        ('2025', 'Atrapar, calar, tejer mitos / ARTBO 2025 / Claustro de las Aguas de Artesan\xedas de Colombia / Sala de la Universidad del Rosario \u2014 Facultad de Artes y Dise\xf1o / Expoartesan\xedas 2025, Bogot\xe1 (COL)', ''),
        ('2025', 'Asuntos de hogar / Casa 73#22, Bogot\xe1 (COL)', ''),
        ('2025', 'Pinturas y dibujos / Galer\xeda Jenny Vil\xe1, Cali (COL)', ''),
        ('2025', 'Todo lo que no cabe en una vitrina / La vitrina - Universidad de Los Andes, Bogot\xe1 (COL)', ''),
        ('2024', 'MEDIO / Bogot\xe1 (COL)', ''),
        ('2024', 'Una moneda al aire / Artec\xe1mara - ARTBO / \xc1gora centro de convenciones (COL)', ''),
        ('2023', 'Open Studio / No Lugar, Arte contempor\xe1neo, Quito (EC)', ''),
        ('2023', 'Fragmentos m\xf3viles / Plural Nodo Cultural, Bogot\xe1 (COL)', ''),
        ('2022', 'Dibujar como pensar / Galer\xeda La Balsa, Medell\xedn (COL)', ''),
        ('2022', 'Festival de arte contempor\xe1neo de Manizales (COL)', ''),
        ('2022', 'SOFA muestra archivo Vestales / Corferias, Bogot\xe1 (COL)', ''),
        ('2022', 'Feria Del Mill\xf3n / Plaza La Santa Mar\xeda, Bogot\xe1 (COL)', ''),
        ('2022', 'La Suya Patria / Origen Magenta, Bogot\xe1 (COL)', ''),
        ('2021', 'SE\xd1ALES / F\xe1brica de instantes. Colectivo Destello / J\xf3venes en Movimiento', ''),
        ('2021', 'Rechazada / Pintura ayer, hoy y ma\xf1ana / Galer\xeda Jenny Vil\xe1, Cali (COL)', ''),
        ('2021', 'ARTBO | Tutor', ''),
        ('2020', 'BARC\xda Spotlights / secci\xf3n artistas emergentes', 'BARC\xda Spotlights / emerging artists section'),
        ('2020', 'ENLUNARTE. Categor\xeda Artes y Oficios. Proyecto: \u201cAlguna Vez Fuimos Oro\u201d', 'ENLUNARTE. Arts and Crafts category. Project: \u201cAlguna Vez Fuimos Oro\u201d'),
        ('2019', 'MUESTRA/SUBASTA, Sal\xf3n Zea Mays. Julio-Agosto', 'MUESTRA/SUBASTA, Sal\xf3n Zea Mays. July-August'),
        ('2018', 'Sal\xf3n de Artistas Bernardo P\xe1ramo, Sal\xf3n Zea Mays, Ch\xeda', ''),
        ('2018', 'La l\xednea no es recta / espacio Ode\xf3n (Tesis Meritoria), Bogot\xe1 (COL)', 'La l\xednea no es recta / espacio Ode\xf3n (Distinguished thesis), Bogot\xe1 (COL)'),
        ('2017', 'Apariciones / Feria 40 x 40. Carta Abierta, Bogot\xe1 (COL)', ''),
        ('2017', 'EXXE-HOMO en Nest Art Center, Bogot\xe1 (COL)', 'EXXE-HOMO at Nest Art Center, Bogot\xe1 (COL)'),
    ]),
    ('BECAS Y EST\xcdMULOS', 'GRANTS AND AWARDS', [
        ('2024', 'Beca de circulaci\xf3n nacional para artistas visuales / IDARTES', 'National circulation grant for visual artists / IDARTES'),
        ('2023', 'J\xf3venes Talentos 2023 / ICETEX', ''),
        ('2023', 'Beca en Circulaci\xf3n nacional para artistas y dem\xe1s agentes de las artes visuales / Ministerio de Cultura de Colombia', 'National circulation grant for artists and other agents of the visual arts / Ministry of Culture of Colombia'),
    ]),
    ('RESIDENCIAS', 'RESIDENCIES', [
        ('2025', 'Residencias de creaci\xf3n art\xedstica del CIC - cer\xe1mica / Universidad de Los Andes, Bogot\xe1 (COL)', 'CIC artistic creation residencies - ceramics / Universidad de Los Andes, Bogot\xe1 (COL)'),
        ('2024', 'Residencias Art\xedsticas En Bloque / IDARTES, Bogot\xe1 (COL)', 'En Bloque artistic residencies / IDARTES, Bogot\xe1 (COL)'),
        ('2023', 'No Lugar, Quito (EC)', ''),
    ]),
    ('PUBLICACIONES', 'PUBLICATIONS', [
        ('2024', 'Cat\xe1logo \u201cUna Moneda al aire\u201d / ARTBO 2024', '\u201cUna Moneda al aire\u201d catalogue / ARTBO 2024'),
        ('2018', 'Peri\xf3dico ARTERIA ED. 64, Julio - Agosto. Art\xedculo: \u201cProyectos de grado sobresalientes en lo que va del a\xf1o\u201d', 'ARTERIA newspaper, ED. 64, July - August. Article: \u201cProyectos de grado sobresalientes en lo que va del a\xf1o\u201d'),
        ('2018', 'Cat\xe1logo \u201cSal\xf3n de Artistas Bernardo P\xe1ramo\u201d, Ch\xeda (COL)', '\u201cSal\xf3n de Artistas Bernardo P\xe1ramo\u201d catalogue, Ch\xeda (COL)'),
    ]),
    ('CHARLAS', 'TALKS', [
        ('2024', 'Objetos en duda / Conferencia con H\xe9ctor Garc\xeda Botero. Evento abierto al p\xfablico. Universidad El Bosque', 'Objetos en duda / Lecture with H\xe9ctor Garc\xeda Botero. Open to the public. Universidad El Bosque'),
        ('2023', 'Un Mundo Sin Hallazgos / Charla con H\xe9ctor Garc\xeda Botero. Evento abierto al p\xfablico. Galer\xeda Espacio El Dorado', 'Un Mundo Sin Hallazgos / Talk with H\xe9ctor Garc\xeda Botero. Open to the public. Galer\xeda Espacio El Dorado'),
    ]),
    ('PRODUCCI\xd3N, DISE\xd1O E INVESTIGACI\xd3N', 'PRODUCTION, DESIGN AND RESEARCH', [
        ('2024', 'Dise\xf1o y producci\xf3n del proyecto \u201cDominio Previo\u201d. Museo de Arte Miguel Urrutia - MAMU, Bogot\xe1 (COL)', 'Design and production of the project \u201cDominio Previo\u201d. Museo de Arte Miguel Urrutia - MAMU, Bogot\xe1 (COL)'),
        ('2020', 'Asistente de producci\xf3n. Proyecto \u201cLa f\xe1bula de Aracne\u201d de Juliana G\xf3ngora. Sal\xf3n Nacional de Artistas 2020 - Universidad Jorge Tadeo Lozano, Bogot\xe1 (COL)', 'Production assistant. Project \u201cLa f\xe1bula de Aracne\u201d by Juliana G\xf3ngora. Sal\xf3n Nacional de Artistas 2020 - Universidad Jorge Tadeo Lozano, Bogot\xe1 (COL)'),
        ('2018-2019', 'Comunicaci\xf3n, gesti\xf3n de medios e investigaci\xf3n. SGR Galer\xeda, Bogot\xe1 (COL)', 'Communications, media management and research. SGR Galer\xeda, Bogot\xe1 (COL)'),
    ]),
    ('EXPERIENCIA PEDAG\xd3GICA', 'TEACHING', [
        ('2024', 'Profesora invitada / Taller de Experimentaci\xf3n con Materiales II. Artes, Facultad de Creaci\xf3n (FACREA), Universidad del Rosario, Bogot\xe1 (COL)', 'Visiting lecturer / Materials Experimentation Workshop II. Arts, Faculty of Creation (FACREA), Universidad del Rosario, Bogot\xe1 (COL)'),
        ('2024', 'Profesora (talleres y actividades acad\xe9micas). Universidad El Bosque, Bogot\xe1. Dise\xf1o y ejecuci\xf3n del taller \u201cMapas y cartograf\xedas\u201d / Dise\xf1o y coordinaci\xf3n de club de dibujo para estudiantes / Dise\xf1o y desarrollo de taller de inmersi\xf3n con arcilla', 'Lecturer (workshops and academic activities). Universidad El Bosque, Bogot\xe1. Design and running of the workshop \u201cMapas y cartograf\xedas\u201d / Design and coordination of a student drawing club / Design and development of a clay immersion workshop'),
        ('2024', 'Docente / Taller independiente de cer\xe1mica, Bogot\xe1. Taller introductorio de cer\xe1mica prehisp\xe1nica: modelado manual, terra sigillata, engobes y pigmentos naturales', 'Teacher / Independent ceramics workshop, Bogot\xe1. Introductory workshop on pre-Hispanic ceramics: hand modelling, terra sigillata, slips and natural pigments'),
    ]),
]


def render_cv(idioma='es'):
    """El CV: una columna de fechas y, al lado, lo que pasó en cada una."""
    en = idioma == 'en'
    filas = []
    for titulo_es, titulo_en, items in CV:
        filas.append('<li class="apartado"><h2>%s</h2></li>'
                     % (titulo_en if en else titulo_es))
        for fecha, texto, texto_en in items:
            filas.append('<li><span class="fecha">%s</span>'
                         '<span class="hecho">%s</span></li>'
                         % (fecha, (texto_en or texto) if en else texto))
    cabecera = ['bogot\u00e1, colombia (1997)', 'CV']
    # La flecha arriba, y debajo dos columnas: a la izquierda quién y dónde,
    # a la derecha todo lo que ha hecho.
    return ('<section class="sec sec-catalogo sec-cv">\n'
            '<div class="lienzo">\n'
            '<div class="cabecera">'
            '<div class="rt volver"><p><a href="index.html">\u21a9</a></p></div>'
            '</div>\n'
            '<div class="fila-cv">'
            '<div class="rt titulo"><h1>%s</h1></div>'
            '<ul class="hoja-vida">%s</ul>'
            '</div>\n'
            '</div>\n'
            '</section>' % ('<br>'.join(cabecera), ''.join(filas)))


# Cada proyecto con una fotograf\xeda que lo represente, su nombre y su a\xf1o.
# Si cambias la portada de una entrada, basta con nombrar otro archivo.
PORTADAS = [
    ('protesis', 'pr\xf3tesis', 2026, 'protesis-15.jpg'),
    ('copia-de-antejardin', 'medir el aire', 2025, '9af1ea_1a65bd022dab40409be95595f9e7f4c6_1082x976.jpg'),
    ('antejardin', 'antejard\xedn', 2025, '9af1ea_6d12b15ef098416eba03dcf9c409752e_1092x1500.jpg'),
    ('todo-lo-que-no-cabe-en-una-vitrina', 'todo lo que no cabe en una vitrina', 2025, '9af1ea_c04d74b80028404f8328a9a4444028f7_1082x820.jpg'),
    ('bache', 'bache', 2024, '9af1ea_9da186028f824e5da954efe2b00699a3_1082x724.jpg'),
    ('procedimiento-fertil', 'procedimiento f\xe9rtil', 2023, '9af1ea_93b00ea0eb6b427b9eddf7caa58e2bff_1082x800.jpg'),
    ('de-dudosa-procedencia', 'de dudosa procedencia', 2023, '9af1ea_17d35f12802c4579bf9095e7377bf4ca_1082x652.jpg'),
    ('semi-preciosas', 'semipreciosas', 2023, '9af1ea_c841ea3fd63a4f73a2bc55f3cf2d1cf7_1082x832.jpg'),
    ('revisitar', 'revisitar', 2022, '9af1ea_793fdb6b16e148eb812dcc86e1e42490_1960x1280.jpg'),
    ('inventario-sobre-lo-que-no-veo', 'inventario sobre lo que no veo', 2022, '9af1ea_7cdb87e871db47d5bdeeb6d73a0ec819_1960x878.jpeg'),
    ('senales', 'se\xf1ales', 2021, '9af1ea_b055e09e46a04752aff7e88dead6631b_1082x1044.jpg'),
    ('desmesura', 'nada de lo que se mide es basura', 2020, 'desmesura-montaje.jpg'),
    ('la-linea-no-es-recta', 'la l\xednea no es recta', '', '9af1ea_7475a082fe61455083a536da1791f1f3_1082x746.jpg'),
    ('dejar-que-la-forma-se-haga', 'dejar que la forma se haga', '', '9af1ea_e19524d96577497bacc40e98876086e4_1082x724.jpg'),
    ('cuerpo-residual', 'cuerpo residual', '', '9af1ea_6db7a7798e7944a5a88b376d60b14832_829x556.jpg'),
    ('otros-proyectos', 'otros proyectos', '', '9af1ea_8e177b9c7883411e8d0ee8979cb12c75_1400x1020.jpg'),
]


def render_proyectos_reticula(idioma='es'):
    """Los proyectos como retícula de imágenes: foto, nombre y año."""
    en = idioma == 'en'
    fichas = []
    for slug, nombre, ano, archivo in PORTADAS:
        if en:
            nombre = NOMBRES_EN.get(nombre, nombre)
        fichas.append(
            '<li><a href="%s.html">'
            '<div class="marco"><img src="assets/img/%s" alt="%s" '
            'loading="lazy"></div>'
            '<h3>%s</h3><p class="ano">%s</p></a></li>'
            % (slug, archivo, nombre, nombre, ano or ''))
    return ('<section class="sec sec-catalogo sec-rejilla">\n'
            '<div class="lienzo">\n'
            '<div class="cabecera">'
            '<div class="rt volver"><p><a href="index.html">\u21a9</a></p></div>'
            '<div class="rt titulo"><h1>%s</h1></div>'
            '</div>\n'
            '<ul class="rejilla">\n%s\n</ul>\n'
            '</div>\n'
            '</section>' % ('artworks' if en else 'proyectos', '\n'.join(fichas)))


def render_talleres(idioma='es'):
    """Los talleres, en la misma retícula que los proyectos."""
    en = idioma == 'en'
    fichas = []
    for ano, nombre, destino, archivo in TALLERES:
        if en:
            nombre = NOMBRES_EN.get(nombre, nombre)
        # Los tres talleres son a la vez proyectos: el «#desde-talleres» le
        # dice a la página de destino que la flecha tiene que volver aquí.
        fichas.append(
            '<li><a href="%s.html#desde-talleres">'
            '<div class="marco"><img src="assets/img/%s" alt="%s" '
            'loading="lazy"></div>'
            '<h3>%s</h3><p class="ano">%d</p></a></li>'
            % (destino, archivo, nombre, nombre, ano))
    return ('<section class="sec sec-catalogo sec-rejilla">\n'
            '<div class="lienzo">\n'
            '<div class="cabecera">'
            '<div class="rt volver"><p><a href="index.html">\u21a9</a></p></div>'
            '<div class="rt titulo"><h1>%s</h1></div>'
            '</div>\n'
            '<ul class="rejilla">\n%s\n</ul>\n'
            '</div>\n'
            '</section>' % ('workshops' if en else 'talleres', '\n'.join(fichas)))


# La obra que hace de portada de cada técnica. Si no se nombra aquí, se usa
# la primera del grupo.
PORTADA_GRUPO = {'dibujo': 'collar-1'}


def render_tienda(idioma='es'):
    """La tienda: una imagen por técnica, sin año. La portada de cada una es
    la primera obra de su grupo, así nunca queda huérfana."""
    en = idioma == 'en'
    fichas = []
    for slug, nom_es, nom_en, claves in GRUPOS:
        nombre = nom_en if en else nom_es
        fichas.append(
            '<li><a href="%s.html">'
            '<div class="marco"><img src="assets/img/pieza-%s.jpg" alt="%s" '
            'loading="lazy"></div>'
            '<h3>%s</h3></a></li>'
            % (slug, PORTADA_GRUPO.get(slug, claves[0]), nombre, nombre))
    return ('<section class="sec sec-catalogo sec-rejilla">\n'
            '<div class="lienzo">\n'
            '<div class="cabecera">'
            '<div class="rt volver"><p><a href="index.html">\u21a9</a></p></div>'
            '<div class="rt titulo"><h1>%s</h1></div>'
            '</div>\n'
            '<ul class="rejilla">\n%s\n</ul>\n'
            '</div>\n'
            '</section>' % ('shop' if en else 'tienda', '\n'.join(fichas)))


def render_catalogo(grupo, idioma='es'):
    en = idioma == 'en'
    consultar = 'Enquire' if en else 'Consultar'
    asunto = 'Hello Sofía, I am writing about' if en else 'Hola Sofía, te escribo por'
    porclave = {o[0]: o for o in CATALOGO}
    sueltas = [c for c in porclave if not any(c in g[3] for g in GRUPOS)]
    if sueltas:
        raise SystemExit('obras sin grupo en la tienda: %s' % ', '.join(sueltas))

    slug, nom_es, nom_en, claves = [g for g in GRUPOS if g[0] == grupo][0]
    titulo = nom_en if en else nom_es
    fichas = []
    for clave in claves:
        obra = porclave.get(clave)
        if not obra:
            raise SystemExit('la tienda nombra una obra que no existe: %s' % clave)
        fichas.append(ficha_pieza(obra, en, consultar, asunto))

    return ('<section class="sec sec-catalogo">\n'
            '<div class="lienzo">\n'
            '<div class="cabecera">'
            '<div class="rt volver"><p><a href="tienda.html">\u21a9</a></p></div>'
            '<div class="rt titulo"><h1>%s</h1></div>'
            '</div>\n'
            '<ul class="catalogo">\n%s\n</ul>\n'
            '</div>\n'
            '</section>' % (titulo, '\n'.join(fichas)))


def ficha_pieza(obra, en, consultar, asunto):
    for clave, nombre, tecnica, medidas, ano, precio, nota in [obra]:
        archivo = 'pieza-%s.jpg' % clave
        if en:
            tecnica = CATALOGO_EN.get(tecnica, tecnica)
            nota = CATALOGO_EN.get(nota, nota)
            nombre = CATALOGO_EN.get(nombre, nombre)
        datos = ' · '.join(x for x in (tecnica, medidas, str(ano)) if x)
        from urllib.parse import quote
        mensaje = '%s \u201c%s\u201d.' % (asunto, nombre)
        chat = 'https://wa.me/%s?text=%s' % (WHATSAPP, quote(mensaje))
        if precio is None:
            cierre = '<p class="vendida">%s</p>' % ('Sold' if en else 'Vendida')
        elif precio == 0:
            cierre = ('<p class="precio">%s</p>'
                      '<a class="consultar" href="%s" target="_blank"'
                      ' rel="noopener">%s</a>'
                      % ('Price on request' if en else 'Precio a consultar',
                         chat, consultar))
        else:
            cierre = ('<p class="precio">%s</p>'
                      '<a class="consultar" href="%s" target="_blank"'
                      ' rel="noopener">%s</a>'
                      % (pesos(precio), chat, consultar))
        return (
            '<li%s>'
            '<div class="marco"><img src="assets/img/%s" alt="%s" width="1000"'
            ' height="750" loading="lazy" data-ampliar></div>'
            '<h3>%s</h3>'
            '<p class="datos">%s</p>'
            '%s'
            '%s'
            '</li>'
            % (' class="agotada"' if precio is None else '',
               archivo, nombre, nombre, datos,
               ('<p class="nota">%s</p>' % nota) if nota else '',
               cierre))


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


def titulo_en_minuscula(html):
    """Baja a minúscula el título de la entrada.

    Es una decisión de la artista: todos los nombres de proyecto empiezan en
    minúscula. Los que venían del Wix en versalitas —«VASIJA / VER / VACIAR»—
    se bajan enteros; en los demás basta la primera letra. Solo se toca el
    título de la página, no el texto ni el menú."""
    m = re.search(r'(<div class="encabezado">.*?<h1\b[^>]*>)(.*?)(</h1>)',
                  html, re.S)
    if not m:
        return html
    dentro = m.group(2)
    visible = re.sub(r'<[^>]+>', '', dentro)
    letras = [c for c in visible if c.isalpha()]
    todo = letras and not any(c.islower() for c in letras)

    def baja(t):
        if todo:
            return t.lower()
        for i, c in enumerate(t):
            if c.isalpha():
                return t[:i] + c.lower() + t[i + 1:]
        return t

    hecho = [False]
    def trozo(x):
        if hecho[0] and not todo:
            return x.group(0)
        texto = x.group(0)
        if texto.strip():
            hecho[0] = True
        return baja(texto)

    nuevo = re.sub(r'(?<=>)[^<]+', trozo, dentro)
    return html[:m.start(2)] + nuevo + html[m.end(2):]


# La presentación de la página de contacto, tal como la escribió Sofía.
SOBRE_MI = [
    'Hola. Soy Sofía y soy artista plástica. Mi práctica ha sido una búsqueda constante acerca de las cosas que están ocultas, las partes o fragmentos de una cosa o imagen, o una excavación constante entre mis recuerdos o las anécdotas que me cuentan mis familiares. El dibujo ha sido, desde que era muy pequeña, un impulso casi frenético por capturar todo lo que me rodeaba. Luego, años después, descubrí la cerámica, un mundo que al día de hoy sigo estudiando y al que me acerco desde una permanente curiosidad.',
    'La obra surge de un encuentro con un objeto, un texto, un recuerdo, un concepto o una imagen. De ahí se desprenden otras preguntas acerca de su ubicación, de su contexto, de su posible continuación, de aquello que no dice y de aquello que revela. En varias ocasiones mi trabajo ha tomado forma de instalación, es decir, de la inmersión en un espacio más allá del objeto.',
    'Esta página ha sido creada con esas mismas inquietudes, que son el motor de mi práctica. He integrado elementos que generan nuevas interacciones. Abajo podrás encontrar los canales a través de los cuales puedes contactarme si algo de lo que aquí se muestra te interesa.',
]

SOBRE_MI_EN = [
    'Hello. I am Sofía and I am a visual artist. My practice has been a constant search into the things that lie hidden, the parts or fragments of a thing or an image, or a constant excavation among my memories and the stories my family tells me. Drawing has been, since I was very small, an almost frantic impulse to capture everything around me. Then, years later, I came upon ceramics, a world I am still studying today and approach with unending curiosity.',
    'The work arises from an encounter with an object, a text, a memory, a concept or an image. From there other questions unfold: about where it is, about its context, about how it might continue, about what it does not say and what it reveals. Several times my work has taken the form of an installation — of immersion in a space beyond the object.',
    'This page was made out of those same preoccupations, which are what drives my practice. I have built into it elements that give rise to new interactions. Below you will find the channels through which you can reach me, if something shown here interests you.',
]


def render_contacto(cfg, idioma='es'):
    """Contacto: el título y la presentación arriba, y debajo por dónde
    escribirle. El título se compone como el de talleres o el del CV."""
    en = idioma == 'en'
    filas = []
    for icono, etiqueta, destino, fuera in cfg['enlaces']:
        extra = ' target="_blank" rel="noopener"' if fuera else ''
        filas.append('<li><a href="@1@"@2@>@3@<span>@4@</span></a></li>'
                     .replace('@1@', destino).replace('@2@', extra)
                     .replace('@3@', icono).replace('@4@', etiqueta))
    parrafos = ''.join('<p>' + t + '</p>'
                       for t in (SOBRE_MI_EN if en else SOBRE_MI))
    return ('<section class="sec sec-contacto">\n'
            '<div class="lienzo">\n'
            '<div class="cabecera">'
            '<div class="rt volver"><p><a href="' + cfg['volver'] + '">\u21a9</a></p></div>'
            '</div>\n'
            '<div class="fila-sobre">'
            '<div class="rt titulo"><h1>'
            + ('about me' if en else 'sobre m\u00ed') + '</h1></div>'
            '<div class="columna">'
            '<div class="sobre-mi">' + parrafos + '</div>'
            '<ul class="contactos">\n' + '\n'.join(filas) + '\n</ul>'
            '</div>'
            '</div>\n'
            '</div>\n'
            '</section>')


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


TXT_TITULO_COL = ('<p class="font_7" style="font-size:34px;">'
                  '<span style="font-weight:bold;">'
                  '<span style="font-size:34px;"><span style="color:#000000;">'
                  '%s</span></span></span></p>')
TXT_ANO_COL = ('<p class="font_8" style="font-size:20px; line-height:1.3em;">'
               '<span style="font-size:20px;"><span style="color:#000000;">'
               '<span style="font-weight:bold;">&nbsp; &nbsp; &nbsp;%s &asymp;'
               '</span></span></span></p>')
TXT_ENLACE_COL = ('<p class="font_8" style="font-size:20px; line-height:1.3em;">'
                  '<a href="%s.html"><span style="font-weight:300;">'
                  '<span style="font-size:20px;"><span style="color:#000000;">'
                  '%s</span></span></span></a></p>')

# Los talleres viven en su propia columna, al lado de los proyectos.
TALLERES = [
    (2026, 'superficies de paso', 'superficies-de-paso', 'superficies-05.jpg'),
    (2025, 'doblar una flor', 'doblar-una-flor', 'doblar-02.jpg'),
    (2024, 'vasija / ver / vaciar', 'vasija-ver-vaciar', 'vasija-01.jpg'),
]


def columna_talleres(idioma):
    """Columna de la derecha en la página de proyectos."""
    titulo = 'workshops' if idioma == 'en' else 'talleres'
    filas = []
    ano = None
    for a, nombre, destino, _ in TALLERES:
        if a != ano:
            if ano is not None:
                filas.append('<p class="font_8" style="font-size:20px; '
                             'line-height:1.3em;">&nbsp;</p>')
            filas.append(TXT_ANO_COL % a)
            ano = a
        filas.append(TXT_ENLACE_COL % (destino, '%d / %s' % (a, nombre)))
    return [
        {'id': 'talleres-titulo', 'type': 'text',
         'html': TXT_TITULO_COL % titulo,
         'geo': {'grid-area': '3 / 1 / 4 / 2', 'left': '730px',
                 'width': '382px', 'margin': '0px 0px 20px 0px'}},
        {'id': 'talleres-lista', 'type': 'text',
         'html': ''.join(filas),
         'geo': {'grid-area': '4 / 1 / 5 / 2', 'left': '730px',
                 'width': '382px', 'margin': '0px 0px 10px 0px'}},
    ]


def flecha_en_proyectos(page, idioma):
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
            # la primera fila —nombre y enlaces— se queda arriba; el resto baja
            # un puesto para dejarle sitio a la flecha debajo
            if a > 1:
                c['geo']['grid-area'] = '%d / %d / %d / %d' % (a + 1, b, d + 1, e)
        # Los proyectos pasan a la columna de la izquierda, bajo la flecha,
        # para dejarle sitio a los talleres a la derecha.
        if c['id'] in ('comp-mh0s4d8j', 'comp-luvkx06n1'):
            c['geo']['left'] = '144px'
            c['geo']['width'] = '510px'
        if c['id'] == 'comp-mh0s4d8j':
            c['geo']['grid-area'] = '3 / 1 / 4 / 2'
            c['geo']['margin'] = '0px 0px 20px 0px'
        hijos.append(c)


    flecha = {
        'id': 'volver-proyectos',
        'type': 'text',
        'html': TXT_VOLVER % 'index',
        'geo': {'grid-area': '2 / 1 / 3 / 2', 'left': '-162px',
                'width': '310px', 'margin': '30px 0px 4px 0px'},
    }
    mesh = dict(sec.get('mesh') or {})
    filas = re.match(r'repeat\((\d+),', mesh.get('grid-template-rows', '') or '')
    if filas:
        mesh['grid-template-rows'] = mesh['grid-template-rows'].replace(
            'repeat(%s,' % filas.group(1), 'repeat(%d,' % (int(filas.group(1)) + 1), 1)
    # El lienzo se ajusta para que la línea de enlaces caiga exactamente en la
    # misma vertical que la del inicio, que es la referencia.
    return dict(page, sections=[dict(sec, children=[flecha] + hijos, mesh=mesh,
                                     lienzo=(-162, 1275))])


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


# Páginas cuya maqueta se estira con la pantalla. Las demás conservan el
# ancho fijo que traían de Wix.
FLUIDAS = {'index', 'proyectos'}


def comp_css(c, x0, arriba=None, escenario=None):
    g = c['geo']
    area = re.match(r'(\d+)\s*/\s*(\d+)\s*/\s*(\d+)\s*/\s*(\d+)', g.get('grid-area', ''))
    m = re.match(r'(\S+)\s+(\S+)\s+(\S+)\s+', g.get('margin', '0 0 0 ') + ' ')
    top, right, bottom = (m.group(1), m.group(2), m.group(3)) if m else ('0', '0', '0')
    if arriba:
        top = arriba
    d = [
        'position:relative',
        'margin:%s %s %s 0' % (top, right, bottom),
        ('left:%.4f%%' % ((num(g.get('left')) - x0) / escenario * 100)
         if escenario else 'left:%gpx' % (num(g.get('left')) - x0)),
        'justify-self:start',
        'align-self:start',
    ]
    if area:
        # la columna es obligatoria: sin ella el navegador crea columnas implícitas
        d.append('grid-area:%s/%s/%s/%s' % area.groups())
    if g.get('width'):
        if escenario and g['width'].endswith('px'):
            d.append('width:%.4f%%' % (num(g['width']) / escenario * 100))
        else:
            d.append('width:%s' % g['width'])
    if g.get('height') and g['height'] != 'auto':
        d.append('height:%s' % g['height'])
    return ';'.join(d)


def render_page(slug, page, idioma='es', origen=None):
    if slug == 'contacto':
        return render_contacto(CONTACTO, idioma), '', 0

    # ojo: aquí «slug» es ya el nombre del archivo, no la clave de Wix
    if slug == 'tienda':
        return render_tienda(idioma), '', 0

    if slug == 'talleres':
        return render_talleres(idioma), '', 0

    if slug == 'cv':
        return render_cv(idioma), '', 0

    if slug == 'proyectos':
        return render_proyectos_reticula(idioma), '', 0

    if slug in [g[0] for g in GRUPOS]:
        return render_catalogo(slug, idioma), '', 0

    if origen in LISTA:
        return render_lista(slug, origen, page, idioma), '', 0

    if slug == 'proyectos':
        page = flecha_en_proyectos(page, idioma)

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
        # El contenido arranca en el mismo sitio que en las páginas de
        # proyecto: un lienzo de 1760 px centrado, con 40 px de margen. Así
        # inicio, proyectos, contacto y cv comparten el borde izquierdo.
        fluida = slug in FLUIDAS
        rules = ['display:grid',
                 'grid-template-columns:%s' % ('minmax(0,1fr)' if fluida
                                               else '%gpx' % stage),
                 'justify-content:start', 'position:static', 'width:100%',
                 'max-width:1760px', 'margin:0 auto', 'padding:0 var(--margen)',
                 'box-sizing:border-box']
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
            ajuste = COLOCAR.get(slug, {}).get(c['id'])
            if ajuste:
                c = dict(c, geo=dict(c['geo'], **ajuste))
            css.append('#%s{%s}' % (c['id'], comp_css(
                c, x0, MARGEN_SUPERIOR.get(slug, {}).get(c['id']),
                stage if fluida else None)))
            if c['type'] == 'text':
                h = re.sub(r'href="([^"]*)"',
                           lambda m: 'href="%s"' % local_href(m.group(1)), c['html'])
                if idioma == 'en':
                    h = traducir_pieza(origen, c['id'], h)
                h = enlazar(slug, h.replace(' target="_self"', ''))
                extra = CLASES.get(slug, {}).get(c['id'], '')
                if extra == 'lista-proyectos':
                    h = unir_enlaces(h)
                    if c['id'] == 'comp-luvkx06n1':
                        h = sin_enlace(h, 'vasija-ver-vaciar')
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
        # una maqueta fluida no necesita encogerse: se adapta sola
        marca = '' if slug in FLUIDAS else ' data-ancho="%d"' % stage
        body.append('<section id="%s" class="sec"%s>%s</section>'
                    % (sid, marca, '\n'.join(parts)))

    # Por debajo de ESCALON se apila todo en una columna. Entre ESCALON y el
    # ancho real del diseño, escala.js reduce el zoom para que quepa completo.
    desktop = '@media (min-width:%dpx){\n%s\n}' % (ESCALON, '\n'.join(css))
    return '\n'.join(body), desktop, int(widest)


# La hormiga del cursor, dibujada con vectores para poder animarle las
# patas. Va escondida en la página y el guion la clona.
HORMIGA_SVG = """<div id="dibujo-hormiga" hidden>
<svg viewBox="0 0 64 64" width="32" height="32" aria-hidden="true">
 <g transform="rotate(-28 32 32)">
  <g class="h-patas-a" fill="none" stroke="#000" stroke-width="2"
     stroke-linecap="round" stroke-linejoin="round">
   <path d="M28 21 L18 15 L12.5 19"/>
   <path d="M28 31 L17 37 L13 45"/>
   <path d="M36 26 L48.5 26 L54.5 32"/>
  </g>
  <g class="h-patas-b" fill="none" stroke="#000" stroke-width="2"
     stroke-linecap="round" stroke-linejoin="round">
   <path d="M28 26 L15.5 26 L9.5 32"/>
   <path d="M36 21 L46 15 L51.5 19"/>
   <path d="M36 31 L47 37 L51 45"/>
  </g>
  <g class="h-antenas" fill="none" stroke="#000" stroke-width="2"
     stroke-linecap="round" stroke-linejoin="round">
   <path d="M29.5 10 L24 4 L19.5 5.5"/>
   <path d="M34.5 10 L40 4 L44.5 5.5"/>
  </g>
  <path d="M32 32.5 L32 37.5" fill="none" stroke="#000" stroke-width="2.4"
        stroke-linecap="round"/>
  <g fill="#000">
   <ellipse cx="32" cy="14" rx="5" ry="4.4"/>
   <ellipse cx="32" cy="26" rx="4.2" ry="6"/>
   <ellipse cx="32" cy="46" rx="6.6" ry="8.2"/>
  </g>
 </g>
</svg>
</div>"""

HORMIGA_RECTA = """<div id="dibujo-hormiga-recta" hidden>
<svg viewBox="0 0 64 64" width="32" height="32" aria-hidden="true">
 <g>
  <g class="h-patas-a" fill="none" stroke="#000" stroke-width="2"
     stroke-linecap="round" stroke-linejoin="round">
   <path d="M28 21 L18 15 L12.5 19"/>
   <path d="M28 31 L17 37 L13 45"/>
   <path d="M36 26 L48.5 26 L54.5 32"/>
  </g>
  <g class="h-patas-b" fill="none" stroke="#000" stroke-width="2"
     stroke-linecap="round" stroke-linejoin="round">
   <path d="M28 26 L15.5 26 L9.5 32"/>
   <path d="M36 21 L46 15 L51.5 19"/>
   <path d="M36 31 L47 37 L51 45"/>
  </g>
  <g class="h-antenas" fill="none" stroke="#000" stroke-width="2"
     stroke-linecap="round" stroke-linejoin="round">
   <path d="M29.5 10 L24 4 L19.5 5.5"/>
   <path d="M34.5 10 L40 4 L44.5 5.5"/>
  </g>
  <path d="M32 32.5 L32 37.5" fill="none" stroke="#000" stroke-width="2.4"
        stroke-linecap="round"/>
  <g fill="#000">
   <ellipse cx="32" cy="14" rx="5" ry="4.4"/>
   <ellipse cx="32" cy="26" rx="4.2" ry="6"/>
   <ellipse cx="32" cy="46" rx="6.6" ry="8.2"/>
  </g>
 </g>
</svg>
</div>"""


# Entradas que se quedan siempre en la barra; el resto va dentro del «+».
PRINCIPALES = {'proyectos', 'talleres', 'paisaje-interior', 'cv', 'contacto'}


def header_html(active, idioma):
    items = []
    for label, target in MENU:
        href = (SLUG.get(target, ascii_slug(target)) if target else 'index') + '.html'
        cur = ' aria-current="page"' if href == active + '.html' else ''
        if idioma == 'en':
            label = MENU_EN.get(label, label)
        # la clase sale de la dirección final, no del nombre heredado de Wix
        clase = (' class="principal m-%s"' % SLUG.get(target, ascii_slug(target))
                 ) if target in PRINCIPALES else ''
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
<link rel="preload" href="{pre}assets/fonts/inter-latin.woff2" as="font"
      type="font/woff2" crossorigin>
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
{hormiga}
<script src="{pre}assets/js/escala.js?v={vesc}" defer></script>
<script src="{pre}assets/js/menu.js?v={vmenu}" defer></script>
<script src="{pre}assets/js/cunos.js?v={vcun}" defer></script>
<script src="{pre}assets/js/hormiga.js?v={vhor}" defer></script>
<script src="{pre}assets/js/ampliar.js?v={vamp}" defer></script>
<script src="{pre}assets/js/hormiguero.js?v={vhgo}" defer></script>
<script src="{pre}assets/js/trazo.js?v={vtrz}" defer></script>
</body>
</html>
"""

os.makedirs(os.path.join(ROOT, 'assets', 'css'), exist_ok=True)
os.makedirs(os.path.join(ROOT, 'assets', 'js'), exist_ok=True)

for slug, cfg in NUEVAS.items():
    pages[slug] = render_nueva(slug, cfg)
    PAGINAS_EN[slug] = render_nueva(slug, cfg, 'en')
    SLUG[slug] = slug

pages['talleres'] = {'title': 'talleres | sofialozanoavila', 'landing': False,
                     'sections': []}
SLUG['talleres'] = 'talleres'
TITULO_EN['talleres'] = 'workshops | sofialozanoavila'

# Las tres técnicas de la tienda son páginas por derecho propio.
for _g, _es, _en, _ in GRUPOS:
    pages[_g] = {'title': '%s | sofialozanoavila' % _es, 'landing': False,
                 'sections': []}
    SLUG[_g] = _g
    TITULO_EN[_g] = '%s | sofialozanoavila' % _en

for slug, page in pages.items():
    out = SLUG[slug]
    desc = ''

    for idioma in IDIOMAS:
        fuente = PAGINAS_EN[slug] if (idioma == 'en' and slug in PAGINAS_EN) else page
        body, css, bp = render_page(out, fuente, idioma, slug)

        # La descripción que ven Google y las vistas previas sale del texto del
        # proyecto ya compuesto, para que recoja las correcciones hechas a
        # mano. Las páginas sin texto largo usan la descripción general.
        desc = ''
        trozo = re.search(r'<div class="cuerpo">(.*?)</div>\s*</div>', body, re.S)
        if trozo:
            plano = html_desescapar(re.sub(r'<[^>]+>', ' ', trozo.group(1)))
            plano = ' '.join(plano.replace('\u200b', ' ').replace('\u21a9', ' ').split())
            if len(plano) > 60:
                desc = plano[:155].replace('"', "'")
        pre = '' if idioma == 'es' else '../'
        html = TEMPLATE.format(
            lang=idioma,
            pre=pre,
            vcss=version('assets/css/site.css'),
            vesc=version('assets/js/escala.js'),
            vmenu=version('assets/js/menu.js'),
            vcun=version('assets/js/cunos.js'),
            vhor=version('assets/js/hormiga.js'),
            vamp=version('assets/js/ampliar.js'),
            vhgo=version('assets/js/hormiguero.js'),
            vtrz=version('assets/js/trazo.js'),
            hormiga=HORMIGA_SVG + HORMIGA_RECTA,
            title=(TITULO_EN.get(out) if idioma == 'en' else None)
                  or TITULOS.get(out, page['title']),
            desc=(DESC_EN if idioma == 'en'
                  else (desc or 'sofía lozano ávila — artista, Bogotá, Colombia.')),
            css=css,
            header=header_html(out, idioma),
            bodyclass=(('landing' if page['landing'] else 'inner') + ' p-' + out
                       + (' con-obras' if slug in LISTA or slug in NUEVAS else '')),
            body=body,
        )
        html = titulo_en_minuscula(html)
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
