/* En talleres el cursor es un lápiz, así que deja su trazo por donde pasa.
   El trazo no se borra de golpe: se va apagando por la cola, como si la
   mina se fuera yendo, y cuando no queda nada el bucle se detiene solo. */
(function () {
  if (!document.body.classList.contains('p-talleres')) return;
  if (!window.matchMedia('(pointer: fine)').matches) return;

  var lienzo = document.createElement('canvas');
  lienzo.className = 'trazo-lapiz';
  lienzo.setAttribute('aria-hidden', 'true');
  document.body.appendChild(lienzo);

  var ctx = lienzo.getContext('2d');
  var dpr = Math.min(window.devicePixelRatio || 1, 2);
  var vw = 0, vh = 0;

  function encuadrar() {
    vw = document.documentElement.clientWidth;
    vh = document.documentElement.clientHeight;
    lienzo.style.width = vw + 'px';
    lienzo.style.height = vh + 'px';
    lienzo.width = Math.ceil(vw * dpr);
    lienzo.height = Math.ceil(vh * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
  }
  encuadrar();

  var espera;
  window.addEventListener('resize', function () {
    clearTimeout(espera);
    espera = setTimeout(encuadrar, 200);
  });

  var suave = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var VIDA = suave ? 900 : 1800;   // lo que tarda en desaparecer, en ms
  var MINIMO = 2.5;                // no se apunta cada píxel: cada 2,5
  var puntos = [];
  var andando = false;
  var sucio = null;

  document.addEventListener('mousemove', function (e) {
    var x = e.clientX, y = e.clientY;
    var u = puntos[puntos.length - 1];
    if (u && Math.hypot(x - u.x, y - u.y) < MINIMO) return;
    puntos.push({ x: x, y: y, t: performance.now() });
    if (puntos.length > 320) puntos.shift();
    if (!andando) { andando = true; requestAnimationFrame(pintar); }
  }, { passive: true });

  function pintar(ahora) {
    while (puntos.length && ahora - puntos[0].t > VIDA) puntos.shift();

    if (sucio) ctx.clearRect(sucio[0], sucio[1], sucio[2] - sucio[0], sucio[3] - sucio[1]);
    else ctx.clearRect(0, 0, vw, vh);

    if (puntos.length < 2) {
      sucio = null;
      andando = false;
      return;
    }

    var x1 = Infinity, y1 = Infinity, x2 = -Infinity, y2 = -Infinity;
    for (var i = 1; i < puntos.length; i++) {
      var a = puntos[i - 1], b = puntos[i];
      // la edad del tramo manda: el final de la cola es el que se va
      var vida = 1 - (ahora - b.t) / VIDA;
      if (vida <= 0) continue;
      ctx.strokeStyle = 'rgba(46, 46, 46, ' + (vida * 0.85).toFixed(3) + ')';
      ctx.lineWidth = 0.7 + vida * 1.1;
      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.stroke();
      if (a.x < x1) x1 = a.x;
      if (a.y < y1) y1 = a.y;
      if (a.x > x2) x2 = a.x;
      if (a.y > y2) y2 = a.y;
      if (b.x < x1) x1 = b.x;
      if (b.y < y1) y1 = b.y;
      if (b.x > x2) x2 = b.x;
      if (b.y > y2) y2 = b.y;
    }
    sucio = (x2 > -Infinity) ? [x1 - 3, y1 - 3, x2 + 3, y2 + 3] : null;
    requestAnimationFrame(pintar);
  }
})();
