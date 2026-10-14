/* Un puñado de hormigas pasean por el inicio. En el celular no hay cursor que
   seguir, así que son ellas las que dan el movimiento que allí se pierde. */
(function () {
  if (!document.body.classList.contains('p-index')) return;
  var molde = document.getElementById('dibujo-hormiga-recta');
  if (!molde) return;

  var CUANTAS = 12;
  var lento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var campo = document.createElement('div');
  campo.className = 'hormiguero';
  campo.setAttribute('aria-hidden', 'true');
  document.body.appendChild(campo);

  var ancho = 0, alto = 0, factor = 1;
  function medir() {
    ancho = document.documentElement.clientWidth;
    alto = document.documentElement.clientHeight;
    // A la misma velocidad en píxeles, cruzar una pantalla ancha parece mucho
    // más lento que cruzar la de un celular. La velocidad se mide contra los
    // 500 px del celular, que es el paso que se quiere ver en todas partes.
    factor = Math.min(Math.max(ancho / 500, 1), 3);
    if (hormigas) cadencia();
  }
  var hormigas = null;
  medir();
  window.addEventListener('resize', medir);

  hormigas = [];
  for (var i = 0; i < CUANTAS; i++) {
    var e = document.createElement('div');
    e.className = 'hormiga anda';
    e.innerHTML = molde.innerHTML;
    campo.appendChild(e);
    hormigas.push({
      nodo: e,
      x: Math.random() * ancho,
      y: Math.random() * alto,
      // el rumbo en radianes; 0 apunta a la derecha
      rumbo: Math.random() * Math.PI * 2,
      // cada una anda a su paso, para que no parezcan un desfile
      paso: (lento ? 14 : 34) + Math.random() * (lento ? 12 : 36),
      // cada cuánto se detiene, y cuánto rato
      quieta: 0
    });
  }

  // la cadencia de las patas va con la velocidad: la que corre, trota; y
  // ninguna arranca en el mismo punto del paso que su vecina
  function cadencia() {
    hormigas.forEach(function (h) {
      var seg = Math.max(0.1, Math.min(0.5, 11 / (h.paso * factor)));
      h.nodo.style.setProperty('--cadencia', seg.toFixed(3) + 's');
      if (h.desfase === undefined) h.desfase = Math.random();
      h.nodo.querySelectorAll('.h-patas-a, .h-patas-b, .h-antenas')
        .forEach(function (g) {
          g.style.animationDelay = (-h.desfase * seg).toFixed(3) + 's';
        });
    });
  }
  cadencia();

  var antes = 0;
  function cuadro(ahora) {
    var dt = Math.min((ahora - antes) / 1000, 0.05);
    antes = ahora;
    for (var i = 0; i < hormigas.length; i++) {
      var h = hormigas[i];
      if (h.quieta > 0) {
        h.quieta -= dt;
        h.nodo.classList.remove('anda');
      } else {
        h.nodo.classList.add('anda');
        // el rumbo se tuerce un poco en cada paso: de ahí lo errático
        h.rumbo += (Math.random() - 0.5) * 3.2 * dt;
        h.x += Math.cos(h.rumbo) * h.paso * factor * dt;
        h.y += Math.sin(h.rumbo) * h.paso * factor * dt;
        // al salir por un borde, entra por el contrario
        if (h.x < -40) h.x = ancho + 40;
        if (h.x > ancho + 40) h.x = -40;
        if (h.y < -40) h.y = alto + 40;
        if (h.y > alto + 40) h.y = -40;
        if (Math.random() < 0.12 * dt) h.quieta = 0.4 + Math.random() * 2;
      }
      h.nodo.style.transform = 'translate3d(' + h.x.toFixed(1) + 'px,'
        + h.y.toFixed(1) + 'px,0) rotate(' + (h.rumbo * 180 / Math.PI + 90).toFixed(1) + 'deg)';
    }
    requestAnimationFrame(cuadro);
  }
  requestAnimationFrame(function (t) { antes = t; cuadro(t); });
})();
