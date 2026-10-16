/* Tierra removida: al pasar por encima de un enlace saltan unos granos que
   suben, caen y se apagan, como si la hormiga escarbara.

   Van en un lienzo, no en elementos de la página. Antes cada grano era un
   <i> con su propia animación CSS, y se creaban y destruían unos treinta por
   segundo mientras el ratón se movía: medido con los contadores del navegador,
   entre 130 y 210 ms de CPU por segundo, lo más caro de todo el sitio. Cada
   salto es ahora un lienzo pequeño, del tamaño de lo que ocupa el salto, y
   todos se dibujan desde un mismo bucle. */
(function () {
  if (!window.matchMedia('(pointer: fine)').matches) return;
  // En talleres no salta tierra: el lápiz deja su trazo (ver trazo.js).
  if (document.body.classList.contains('p-talleres')) return;

  var campo = document.createElement('div');
  campo.className = 'humo';
  campo.setAttribute('aria-hidden', 'true');
  document.body.appendChild(campo);

  var suave = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var dpr = Math.min(window.devicePixelRatio || 1, 2);
  var LADO = 80;                 // lo que cabe un salto, de sobra
  var ultimo = 0;
  var saltos = [];
  var andando = false;

  // La misma curva que llevaba la hoja de estilos: cubic-bezier(.33,.05,.55,1).
  function curva(t) {
    // Newton sobre la x de la bézier; con cuatro vueltas sobra para esto.
    var x = t;
    for (var i = 0; i < 4; i++) {
      var u = 1 - x;
      var fx = 3 * u * u * x * 0.33 + 3 * u * x * x * 0.55 + x * x * x - t;
      var dx = 3 * u * u * 0.33 + 6 * u * x * (0.55 - 0.33) + 3 * x * x * (1 - 0.55);
      if (Math.abs(dx) < 1e-6) break;
      x -= fx / dx;
    }
    var v = 1 - x;
    return 3 * v * v * x * 0.05 + 3 * v * x * x + x * x * x;
  }

  function soplo(x, y) {
    // Unos pocos granos, no una nube: salen disparados hacia los lados y
    // arriba, y caen un poco más abajo de donde salieron.
    var lienzo = document.createElement('canvas');
    lienzo.className = 'granos';
    lienzo.width = lienzo.height = Math.round(LADO * dpr);
    lienzo.style.left = (x - LADO / 2) + 'px';
    lienzo.style.top = (y - LADO / 2) + 'px';
    campo.appendChild(lienzo);
    var ctx = lienzo.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = 'rgb(84, 84, 84)';

    var granos = [];
    var cuantos = 4 + Math.floor(Math.random() * 3);
    var rato = 0;
    for (var i = 0; i < cuantos; i++) {
      var g = {
        tam: 1.4 + Math.random() * 1.8,
        x0: (Math.random() - 0.5) * 6,
        y0: (Math.random() - 0.5) * 4,
        // a un lado o al otro, y cuanto más lejos, más rato en el aire
        dx: (Math.random() < 0.5 ? -1 : 1) * (5 + Math.random() * 13),
        alto: -(5 + Math.random() * 9),
        caida: 2 + Math.random() * 5,
        dura: (suave ? 1 : 0.46 + Math.random() * 0.3) * 1000,
        espera: Math.random() * 50
      };
      rato = Math.max(rato, g.dura + g.espera);
      granos.push(g);
    }
    saltos.push({ lienzo: lienzo, ctx: ctx, granos: granos, t0: 0, fin: rato });
    if (!andando) { andando = true; requestAnimationFrame(cuadro); }
  }

  function cuadro(ahora) {
    var vivos = 0;
    for (var s = saltos.length - 1; s >= 0; s--) {
      var salto = saltos[s];
      if (!salto.t0) salto.t0 = ahora;
      var edad = ahora - salto.t0;
      if (edad > salto.fin) {
        salto.lienzo.remove();
        saltos.splice(s, 1);
        continue;
      }
      vivos++;
      salto.ctx.clearRect(0, 0, LADO, LADO);
      for (var i = 0; i < salto.granos.length; i++) {
        var g = salto.granos[i];
        var t = (edad - g.espera) / g.dura;
        if (t <= 0 || t >= 1) continue;
        var e = curva(t);
        // sube deprisa, se frena arriba y cae: el salto de un grano de tierra
        var px, py, escala, opaco;
        if (e < 0.42) {
          var k = e / 0.42;
          px = g.dx * 0.55 * k;
          py = g.alto * k;
          escala = 1;
        } else {
          var k2 = (e - 0.42) / 0.58;
          px = g.dx * 0.55 + (g.dx - g.dx * 0.55) * k2;
          py = g.alto + (g.caida - g.alto) * k2;
          escala = 1 - 0.3 * k2;
        }
        opaco = t < 0.1 ? t / 0.1 : (e < 0.42 ? 1 : 1 - (e - 0.42) / 0.58);
        salto.ctx.globalAlpha = Math.max(0, Math.min(1, opaco));
        var r = g.tam * escala / 2;
        salto.ctx.beginPath();
        salto.ctx.arc(LADO / 2 + g.x0 + px, LADO / 2 + g.y0 + py, r, 0, 6.2832);
        salto.ctx.fill();
      }
    }
    if (vivos) requestAnimationFrame(cuadro);
    else andando = false;
  }

  document.addEventListener('mousemove', function (e) {
    var enlace = e.target.closest && e.target.closest('a, button');
    if (!enlace) return;
    var ahora = e.timeStamp;
    if (ahora - ultimo < (suave ? 420 : 170)) return;
    ultimo = ahora;
    soplo(e.clientX, e.clientY);
  }, { passive: true });
})();
