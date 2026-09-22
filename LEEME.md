# sofía lozano ávila — sitio web

Este es tu sitio de Wix convertido a código: **HTML, CSS y un poco de JavaScript**.
No necesitas instalar nada para verlo ni para editarlo.

---

## 1. Ver el sitio en tu computador

Haz **doble clic en `index.html`**. Se abre en tu navegador y funciona todo:
los enlaces, el menú y las imágenes.

---

## 2. Publicarlo en Vercel

1. Entra a [vercel.com](https://vercel.com) y crea una cuenta (puedes usar tu correo).
2. En el panel, busca la opción de desplegar **arrastrando una carpeta**
   (*Deploy* → *Browse* / arrastrar y soltar).
3. Arrastra **toda la carpeta `web`**.
4. Vercel te da una dirección como `https://sofialozanoavila.vercel.app`.

Para conectar tu propio dominio (por ejemplo `sofialozanoavila.com`), en Vercel
entra a tu proyecto → *Settings* → *Domains*.

Cada vez que cambies algo, vuelve a arrastrar la carpeta y Vercel actualiza el sitio.

---

## 3. Qué hay en cada archivo

| Archivo / carpeta | Qué es |
|---|---|
| `index.html` | La página de inicio |
| `proyectos.html` | El listado de proyectos |
| `cv.html`, `contacto.html` | CV y contacto |
| `antejardin.html`, `bache.html`, … | Una página por proyecto |
| `assets/img/` | Todas tus imágenes (105 archivos) |
| `assets/css/site.css` | Colores, tipografías y comportamiento en celular |
| `assets/js/menu.js` | El menú de arriba y el botón `+` |
| `assets/js/escala.js` | Ajusta el tamaño del diseño en pantallas más pequeñas |
| `vercel.json` | Configuración de Vercel (no hace falta tocarlo) |
| `_build/` | Herramientas con las que se generó el sitio (ver punto 6) |

---

## 4. Cambiar un texto

Abre el archivo `.html` de esa página con cualquier editor de texto
(TextEdit en modo texto plano, o mejor [VS Code](https://code.visualstudio.com), gratis).
Busca la frase que quieres cambiar y escríbela encima. Guarda y recarga el navegador.

Los textos están envueltos en etiquetas así:

```html
<p>Aquí va tu texto</p>
```

Cambia sólo lo que está **entre** las etiquetas, no las etiquetas mismas.

---

## 5. Cambiar o agregar una imagen

1. Copia tu foto nueva dentro de `assets/img/`.
2. En el `.html`, busca la imagen que quieres reemplazar:

```html
<img src="assets/img/9af1ea_....jpg" alt="" width="546" height="750" loading="lazy">
```

3. Cambia el nombre del archivo en `src`. Si la foto tiene otra proporción,
   ajusta también `width` y `height` (son las medidas en píxeles).

**Consejo:** antes de subirla, reduce la foto a máximo 1600 px de ancho para que
el sitio cargue rápido. (Vista previa de Mac → Herramientas → Ajustar tamaño.)

---

## 6. Cómo se hizo (por si algún día hace falta)

La carpeta `_build/` contiene los dos programas en Python que generaron el sitio
a partir del HTML descargado de Wix:

- `extract.py` — lee las páginas de Wix y saca textos, imágenes y posiciones.
- `build.py` — con eso escribe los archivos `.html` finales.
- `content.json` — todo el contenido extraído.

No hace falta para que el sitio funcione: puedes ignorar esa carpeta, o borrarla
si prefieres. Si la borras, el sitio sigue funcionando igual.

---

## Detalles que conviene saber

- **Las tipografías**: el sitio original usaba *Almarai*, *Forum* y *Open Sans*
  (se cargan desde Google Fonts) y *Avenir Light*, que no es libre. En su lugar se
  usa *Nunito Sans*, que es muy parecida.
- **El diseño fijo**: como en Wix, las páginas tienen una maquetación de ancho fijo.
  En pantallas más pequeñas el sitio la reduce proporcionalmente, y por debajo de
  860 px de ancho (celulares) apila todo en una sola columna.
- **Nombres de archivo sin tildes**: `antejardín` quedó como `antejardin.html` y
  `señales` como `senales.html`, porque las tildes dan problemas en las direcciones web.
- **Páginas heredadas de Wix**: `copia-de-antejardin.html` y `copia-de-medir-el-aire.html`
  conservan el nombre que tenían allá. Si quieres, puedes renombrarlas — recuerda
  actualizar los enlaces que apuntan a ellas en `proyectos.html`.
