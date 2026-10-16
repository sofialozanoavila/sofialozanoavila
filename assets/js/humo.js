/* Tierra removida: al pasar por encima de un enlace saltan unos granos que
   suben, caen y se apagan, como si la hormiga escarbara.

   Es una animación fija, dibujada de antemano. Al cargar la página se arman
   unas pocas secuencias de fotogramas en SVG —tres saltos distintos, cada uno
   con su puñado de granos y sus trayectorias—, se rasterizan una sola vez y
   luego solo se reproducen: cada salto estampa el fotograma que le toca.

   Antes se calculaba cada grano en cada cuadro, y antes de eso cada grano era
   un elemento de la página con su propia animación CSS; medido con los
   contadores del navegador, aquello costaba entre 130 y 210 ms de CPU por
   segundo mientras el ratón se movía, lo más caro de todo el sitio. */
(function () {
  if (!window.matchMedia('(pointer: fine)').matches) return;
  // En talleres no salta tierra: el lápiz deja su trazo (ver trazo.js).
  if (document.body.classList.contains('p-talleres')) return;

  var suave = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var dpr = Math.min(window.devicePixelRatio || 1, 2);
  var LADO = 64;                       // lo que ocupa un salto, de sobra
  var SALTOS = 3;                      // cuántos saltos distintos hay
  var CUADROS = 14;                    // fotogramas de cada uno
  var CADA = suave ? 72 : 46;          // milisegundos por fotograma

  var campo = document.createElement('div');
  campo.className = 'humo';
  campo.setAttribute('aria-hidden', 'true');
  document.body.appendChild(campo);

  /* Un generador de números con semilla: así los tres saltos salen siempre
     iguales, y lo que se dibuja de antemano es exactamente lo que se verá. */
  function dados(semilla) {
    var s = semilla;
    return function () {
      s = (s * 1103515245 + 12345) & 0x7fffffff;
      return s / 0x7fffffff;
    };
  }

  /* La trayectoria de un grano, la misma de siempre: sube deprisa, se frena
     arriba y cae un poco más abajo de donde salió. */
  function donde(g, t) {
    var px, py, escala;
    if (t < 0.42) {
      var k = t / 0.42;
      px = g.dx * 0.55 * k;
      py = g.alto * k;
      escala = 1;
    } else {
      var k2 = (t - 0.42) / 0.58;
      px = g.dx * 0.55 + g.dx * 0.45 * k2;
      py = g.alto + (g.caida - g.alto) * k2;
      escala = 1 - 0.3 * k2;
    }
    var opaco = t < 0.1 ? t / 0.1 : (t < 0.42 ? 1 : 1 - (t - 0.42) / 0.58);
    return { x: g.x0 + px, y: g.y0 + py, r: g.tam * escala / 2, o: opaco };
  }

  // Cada salto es una tira de fotogramas ya rasterizados.
  var tiras = [];
  var listas = 0;

  function armar() {
    for (var s = 0; s < SALTOS; s++) {
      var azar = dados(s * 7919 + 13);
      var granos = [];
      var cuantos = 4 + Math.floor(azar() * 3);
      for (var g = 0; g < cuantos; g++) {
        granos.push({
          tam: 1.4 + azar() * 1.8,
          x0: (azar() - 0.5) * 6,
          y0: (azar() - 0.5) * 4,
          // a un lado o al otro, y cuanto más lejos, más rato en el aire
          dx: (azar() < 0.5 ? -1 : 1) * (5 + azar() * 13),
          alto: -(5 + azar() * 9),
          caida: 2 + azar() * 5,
          // no todos salen a la vez
          espera: azar() * 0.12
        });
      }
      tiras.push(dibujar(granos));
    }
  }

  function dibujar(granos) {
    var tira = { cuadros: [], listos: 0 };
    for (var f = 0; f < CUADROS; f++) {
      (function (f) {
        var t = f / (CUADROS - 1);
        var circulos = '';
        for (var i = 0; i < granos.length; i++) {
          var g = granos[i];
          var tg = (t - g.espera) / (1 - g.espera);
          if (tg <= 0 || tg >= 1) continue;
          var d = donde(g, tg);
          if (d.r <= 0.05) continue;
          circulos += '<circle cx="' + (LADO / 2 + d.x).toFixed(2) +
            '" cy="' + (LADO / 2 + d.y).toFixed(2) +
            '" r="' + d.r.toFixed(2) +
            '" fill="rgb(84,84,84)" fill-opacity="' +
            Math.max(0, Math.min(1, d.o)).toFixed(3) + '"/>';
        }
        var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="' +
          Math.round(LADO * dpr) + '" height="' + Math.round(LADO * dpr) +
          '" viewBox="0 0 ' + LADO + ' ' + LADO + '">' + circulos + '</svg>';
        var img = new Image();
        img.onload = function () {
          var c = document.createElement('canvas');
          c.width = c.height = Math.round(LADO * dpr);
          c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
          tira.cuadros[f] = c;
          tira.listos++;
          if (tira.listos === CUADROS) listas++;
        };
        img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
      })(f);
    }
    return tira;
  }
  armar();

  // Los saltos que se están reproduciendo ahora mismo.
  var vivos = [];
  var andando = false;
  var ultimo = 0;
  var cual = 0;

  function soltar(x, y) {
    if (!listas) return;
    var tira = tiras[cual % tiras.length];
    cual++;
    var lienzo = document.createElement('canvas');
    lienzo.className = 'granos';
    lienzo.width = lienzo.height = Math.round(LADO * dpr);
    lienzo.style.left = (x - LADO / 2) + 'px';
    lienzo.style.top = (y - LADO / 2) + 'px';
    // unos saltan al revés, para que no se repitan a ojo
    if (cual % 2) lienzo.style.transform = 'scaleX(-1)';
    campo.appendChild(lienzo);
    vivos.push({
      lienzo: lienzo,
      ctx: lienzo.getContext('2d'),
      tira: tira,
      t0: 0,
      puesto: -1
    });
    if (!andando) { andando = true; requestAnimationFrame(cuadro); }
  }

  function cuadro(ahora) {
    for (var v = vivos.length - 1; v >= 0; v--) {
      var salto = vivos[v];
      if (!salto.t0) salto.t0 = ahora;
      var f = Math.floor((ahora - salto.t0) / CADA);
      if (f >= CUADROS) {
        salto.lienzo.remove();
        vivos.splice(v, 1);
        continue;
      }
      // solo se vuelve a estampar cuando toca fotograma nuevo
      if (f === salto.puesto) continue;
      salto.puesto = f;
      var cuno = salto.tira.cuadros[f];
      if (!cuno) continue;
      salto.ctx.clearRect(0, 0, salto.lienzo.width, salto.lienzo.height);
      salto.ctx.drawImage(cuno, 0, 0);
    }
    if (vivos.length) requestAnimationFrame(cuadro);
    else andando = false;
  }

  document.addEventListener('mousemove', function (e) {
    var enlace = e.target.closest && e.target.closest('a, button');
    if (!enlace) return;
    var ahora = e.timeStamp;
    if (ahora - ultimo < (suave ? 420 : 170)) return;
    ultimo = ahora;
    soltar(e.clientX, e.clientY);
  }, { passive: true });
})();
