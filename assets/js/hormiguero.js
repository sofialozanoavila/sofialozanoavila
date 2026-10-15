/* Un puñado de hormigas pasean por el inicio. En el celular no hay cursor que
   seguir, así que son ellas las que dan el movimiento que allí se pierde. */
(function () {
  if (!document.body.classList.contains('p-index')) return;
  var molde = document.getElementById('dibujo-hormiga-recta');
  if (!molde) return;

  var CUANTAS = 9;
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
      quieta: 0,
      // persiguiendo, cada una apunta a un punto algo distinto del cursor:
      // si no, se amontonan todas encima
      sesgo: { x: (Math.random() - 0.5) * 70, y: (Math.random() - 0.5) * 70 }
    });
  }

  // la cadencia de las patas va con la velocidad: la que corre, trota; y
  // ninguna arranca en el mismo punto del paso que su vecina
  function cadencia() {
    // en el molino todas llevan el mismo paso, porque van a la misma
    // velocidad sobre la rueda
    var vRueda = (Math.PI * 2 / 8) * (Math.min(ancho, alto) * 0.22);
    hormigas.forEach(function (h) {
      var v = (modo === 'molino') ? vRueda : h.paso * factor;
      var seg = Math.max(0.1, Math.min(0.5, 11 / v));
      h.nodo.style.setProperty('--cadencia', seg.toFixed(3) + 's');
      if (h.desfase === undefined) h.desfase = Math.random();
      h.nodo.querySelectorAll('.h-patas-a, .h-patas-b, .h-antenas')
        .forEach(function (g) {
          g.style.animationDelay = (-h.desfase * seg).toFixed(3) + 's';
        });
    });
  }
  cadencia();

  // Maneras de andar, que se turnan al pulsar:
  //   'suelta'   cada una a lo suyo
  //   'persigue' todas detrás del cursor
  //   'molino'   en rueda, todas en el mismo sentido
  //   'fila'     todas hacia el mismo rincón
  // Con ratón la primera pulsación las echa a perseguir; con el dedo no hay
  // cursor que perseguir, así que ese modo se salta.
  // ¿hay ratón? con el dedo no hay cursor que perseguir
  var con_raton = window.matchMedia('(pointer: fine)').matches;
  var RONDA = con_raton
    ? ['suelta', 'persigue', 'molino', 'fila']
    : ['suelta', 'molino', 'fila'];
  var paso_ronda = 0;
  var modo = 'suelta';
  var RUMBO_DIAGONAL = -Math.PI / 4;   // hacia arriba y a la derecha

  var raton = { x: -200, y: -200 };
  document.addEventListener('mousemove', function (e) {
    raton.x = e.clientX; raton.y = e.clientY;
  }, { passive: true });

  document.addEventListener('click', function (e) {
    // los enlaces siguen siendo enlaces
    if (e.target.closest && e.target.closest('a, button')) return;
    paso_ronda = (paso_ronda + 1) % RONDA.length;
    modo = RONDA[paso_ronda];
    if (modo === 'molino') {
      // en el molino cada una ocupa su puesto en la rueda
      hormigas.forEach(function (h, i) {
        h.vuelta = (i / hormigas.length) * Math.PI * 2;
        h.desde = { x: h.x, y: h.y };
        h.entrada = 0;
        h.quieta = 0;
      });
    }
    cadencia();
    if (modo === 'fila') {
      hormigas.forEach(function (h) {
        h.rumbo = RUMBO_DIAGONAL + (Math.random() - 0.5) * 0.12;
        h.quieta = 0;
      });
    }
    if (modo === 'persigue') {
      hormigas.forEach(function (h) { h.quieta = 0; });
    }
  });

  var antes = 0;
  function cuadro(ahora) {
    var dt = Math.min((ahora - antes) / 1000, 0.05);
    antes = ahora;

    if (modo === 'molino') {
      // El molino: todas en rueda, girando en el mismo sentido. La entrada se
      // mide en tiempo, no en «acercarse un poco cada cuadro»: así el anillo
      // queda exacto aunque el dibujo vaya a trompicones.
      var cx = ancho / 2, cy = alto / 2;
      var radio = Math.min(ancho, alto) * 0.22;
      // una vuelta cada ocho segundos, sea cual sea la pantalla: a esa
      // velocidad la rueda avanza al paso al que andan, no deslizándose
      var giro = Math.PI * 2 / 8;
      for (var m = 0; m < hormigas.length; m++) {
        var g = hormigas[m];
        g.vuelta += giro * dt;
        g.entrada = Math.min(1, g.entrada + dt / 0.9);
        var suave = 1 - Math.pow(1 - g.entrada, 3);
        var tx = cx + Math.cos(g.vuelta) * radio;
        var ty = cy + Math.sin(g.vuelta) * radio;
        g.x = g.desde.x + (tx - g.desde.x) * suave;
        g.y = g.desde.y + (ty - g.desde.y) * suave;
        g.rumbo = g.vuelta + Math.PI / 2;
        g.nodo.classList.add('anda');
        g.nodo.style.transform = 'translate3d(' + g.x.toFixed(1) + 'px,'
          + g.y.toFixed(1) + 'px,0) rotate('
          + (g.rumbo * 180 / Math.PI + 90).toFixed(1) + 'deg)';
      }
      requestAnimationFrame(cuadro);
      return;
    }

    for (var i = 0; i < hormigas.length; i++) {
      var h = hormigas[i];
      if (h.quieta > 0) {
        h.quieta -= dt;
        h.nodo.classList.remove('anda');
      } else {
        h.nodo.classList.add('anda');
        // en fila no hay titubeo; a lo suyo, el rumbo se tuerce en cada paso
        if (modo === 'persigue') {
          // gira poco a poco hacia donde está el cursor, sin dar un volantazo
          var quiere = Math.atan2(raton.y + h.sesgo.y - h.y,
                                  raton.x + h.sesgo.x - h.x);
          var giro_h = ((quiere - h.rumbo + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
          h.rumbo += Math.max(-4 * dt, Math.min(4 * dt, giro_h));
        } else if (modo === 'fila') {
          // en fila no hay titubeo
        } else {
          // a lo suyo, el rumbo se tuerce un poco en cada paso
          h.rumbo += (Math.random() - 0.5) * 3.2 * dt;
        }
        var veloz = h.paso * factor * (modo === 'persigue' ? 1.35 : 1);
        h.x += Math.cos(h.rumbo) * veloz * dt;
        h.y += Math.sin(h.rumbo) * veloz * dt;
        // al salir por un borde, entra por el contrario
        if (h.x < -40) h.x = ancho + 40;
        if (h.x > ancho + 40) h.x = -40;
        if (h.y < -40) h.y = alto + 40;
        if (h.y > alto + 40) h.y = -40;
        if (modo === 'suelta' && Math.random() < 0.12 * dt) {
          h.quieta = 0.4 + Math.random() * 2;
        }
      }
      h.nodo.style.transform = 'translate3d(' + h.x.toFixed(1) + 'px,'
        + h.y.toFixed(1) + 'px,0) rotate(' + (h.rumbo * 180 / Math.PI + 90).toFixed(1) + 'deg)';
    }
    requestAnimationFrame(cuadro);
  }
  requestAnimationFrame(function (t) { antes = t; cuadro(t); });
})();
