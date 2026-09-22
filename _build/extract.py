# -*- coding: utf-8 -*-
"""Extrae contenido y geometría de las páginas Wix descargadas, agrupado por secciones."""
import re, json, os, sys, html

SRC, OUT = sys.argv[1], sys.argv[2]


def parse_decl(t):
    out = {}
    for part in t.split(';'):
        if ':' in part:
            k, v = part.split(':', 1)
            out[k.strip()] = v.strip()
    return out


def css_geometry(s):
    """comp-id -> propiedades de posición y tamaño, leídas del CSS que emite Wix."""
    geo = {}
    for m in re.finditer(r'>\s*\[id="([^"]+)"\][^{}]*\{([^}]*)\}', s):
        geo.setdefault(m.group(1), {}).update(parse_decl(m.group(2)))
    for m in re.finditer(r'#([A-Za-z0-9_-]+)\s*\{([^}]*)\}', s):
        d = {k: v for k, v in parse_decl(m.group(2)).items()
             if k in ('width', 'height', 'min-height')}
        if d:
            geo.setdefault(m.group(1), {}).update(d)
    return geo


def elem_html(s, start):
    """HTML completo del elemento que empieza en `start`, con etiquetas balanceadas."""
    tag = re.match(r'<([a-zA-Z0-9-]+)', s[start:]).group(1)
    pat = re.compile(r'<(/?)' + re.escape(tag) + r'\b([^>]*)>')
    pos, depth = start, 0
    while True:
        m = pat.search(s, pos)
        if not m:
            return s[start:]
        if m.group(1) == '/':
            depth -= 1
            if depth == 0:
                return s[start:m.end()]
        elif not m.group(2).rstrip().endswith('/'):
            depth += 1
        pos = m.end()


def clean_richtext(h):
    # conserva sólo las clases tipográficas del tema (font_N / color_N)
    def keep(m):
        cls = [c for c in m.group(1).split() if re.fullmatch(r'(font|color)_\d+', c)]
        return ' class="%s"' % ' '.join(cls) if cls else ''
    h = re.sub(r'\sclass="([^"]*)"', keep, h)
    h = re.sub(r'\sdata-[a-z-]+="[^"]*"', '', h)
    h = re.sub(r'\sid="[^"]*"', '', h)
    for _ in range(10):
        h2 = re.sub(r'<span>(.*?)</span>', r'\1', h, flags=re.S)
        if h2 == h:
            break
        h = h2
    return re.sub(r'\s+', ' ', h).strip()


def text_of(h):
    return html.unescape(re.sub(r'<[^>]+>', '', h)).replace('​', '').strip()


def comp_from(frag, cid, geo, opening):
    g = geo.get(cid)
    if not g or 'grid-area' not in g:
        return None                      # anidado: lo coloca su contenedor
    item = {'id': cid, 'geo': g}
    if 'wixui-rich-text' in opening:
        inner = re.sub(r'^<div[^>]*>|</div>$', '', frag)
        item['type'] = 'text'
        item['html'] = clean_richtext(inner)
        item['text'] = text_of(item['html'])
        return item
    img = re.search(r'<img[^>]*>', frag)
    if img and 'wixstatic.com/media' in img.group(0):
        tag = img.group(0)
        src = re.search(r'src="([^"]+)"', tag).group(1)
        hi = src
        ss = re.search(r'srcSet="([^"]+)"', tag)
        if ss:
            m2 = re.search(r'(https://\S+?)\s+2x', ss.group(1))
            if m2:
                hi = m2.group(1)
        w = re.search(r'width="(\d+)"', tag)
        h = re.search(r'height="(\d+)"', tag)
        alt = re.search(r'alt="([^"]*)"', tag)
        link = re.search(r'<a[^>]+href="([^"]+)"', frag)
        return dict(item, type='image',
                    src=re.match(r'(https://static\.wixstatic\.com/media/[^/]+)', src).group(1),
                    hi=hi,
                    w=int(w.group(1)) if w else None,
                    h=int(h.group(1)) if h else None,
                    alt=html.unescape(alt.group(1)) if alt else '',
                    href=link.group(1) if link else None)
    return None


def comps_in(chunk, geo, skip=None):
    out, seen = [], {skip} if skip else set()
    for m in re.finditer(r'<(div|nav)\s(?:[^>]*?\s)?id="([A-Za-z0-9][A-Za-z0-9_-]*)"[^>]*>', chunk):
        cid = m.group(2)
        if cid in seen:
            continue
        c = comp_from(elem_html(chunk, m.start()), cid, geo, m.group(0))
        if c:
            seen.add(cid)
            out.append(c)
    return out


def mesh_css(s, sid):
    """Reglas del contenedor grid (filas y alto mínimo) que Wix genera para la sección."""
    for m in re.finditer(r'\[data-mesh-id=' + re.escape(sid) + r'inlineContent-gridContainer\][^{}]*\{([^}]*)\}', s):
        d = parse_decl(m.group(1))
        if d.get('display') == 'grid':
            return {k: v for k, v in d.items()
                    if k in ('grid-template-rows', 'min-height')}
    return {}


def extract_page(path):
    s = open(path, encoding='utf-8').read()
    geo = css_geometry(s)
    body = s[s.find('id="PAGES_CONTAINER"'):]
    body = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.S)
    body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.S)

    title = html.unescape(re.search(r'<title>(.*?)</title>', s, re.S).group(1).strip())
    landing = 'landingPage' in (re.search(r'id="masterPage" class="([^"]*)"', s) or
                                re.match('', '')).group(1)

    sections = []
    starts = [m.start() for m in re.finditer(r'<section\s[^>]*wixui-section[^>]*>', body)]
    if starts:
        for st in starts:
            frag = elem_html(body, st)
            sid = re.search(r'id="([^"]+)"', frag).group(1)
            sections.append({'id': sid,
                             'geo': geo.get(sid, {}),
                             'mesh': mesh_css(s, sid),
                             'children': comps_in(frag, geo, sid)})
    else:
        sections.append({'id': 'page', 'geo': {}, 'mesh': {}, 'children': comps_in(body, geo)})
    return {'title': title, 'landing': landing, 'sections': sections}


pages = {}
for fn in sorted(os.listdir(SRC)):
    if fn.endswith('.html'):
        pages[fn[:-5]] = extract_page(os.path.join(SRC, fn))

json.dump(pages, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for slug, p in pages.items():
    n = sum(len(sec['children']) for sec in p['sections'])
    print(f"{slug:36} secciones={len(p['sections']):2} piezas={n:3} landing={p['landing']}")
