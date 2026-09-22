# sofía lozano ávila — sitio web

Este es tu sitio de Wix convertido a código: **HTML, CSS y un poco de JavaScript**.
No necesitas instalar nada para verlo ni para editarlo.

---

## 1. Ver el sitio en tu computador

Haz **doble clic en `index.html`**. Se abre en tu navegador y funciona todo:
los enlaces, el menú y las imágenes.

---

## 2. Publicarlo (ya es automático)

El sitio está conectado a GitHub y a Vercel:

```
tu computador  →  GitHub  →  Vercel  →  sofialozanoavila.info
```

Cada cambio que se guarde y se envíe a GitHub se publica solo en unos 30 segundos.
No hay que arrastrar carpetas ni configurar nada.

- Repositorio: https://github.com/sofialozanoavila/sofialozanoavila
- Dominio: https://sofialozanoavila.info

Para enviar un cambio, desde la carpeta `web`:

```bash
git add -A
git commit -m "describe aquí el cambio"
git push
```

Si no te manejas con la terminal, pídemelo y lo hago yo.

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

---

## Sobre `vercel.json` y la caché

Ese archivo le dice al navegador cuánto tiempo puede guardarse cada cosa:

- **`/assets/img/`** se guarda un año. Cada nombre de archivo corresponde a una
  imagen concreta que nunca cambia, así que no hay riesgo.
- **`/assets/css/` y `/assets/js/`** se comprueban siempre. Si se cachearan,
  el navegador seguiría usando la hoja de estilos vieja y el diseño se
  descuadraría.

Además, los enlaces al CSS y al JS llevan una huella del contenido
(`site.css?v=0dcec18c`). Cuando el archivo cambia, la huella cambia y el
navegador está obligado a bajar la versión nueva.

Nota: `vercel.json` **no admite comentarios** ni campos que no estén en su
formato. Si se añade uno, el despliegue falla con un error de validación.
