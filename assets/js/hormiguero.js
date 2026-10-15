/* Un puñado de hormigas pasean por el inicio. En el celular no hay cursor que
   seguir, así que son ellas las que dan el movimiento que allí se pierde.

   Cada una es un lienzo diminuto, no un SVG. Antes eran <svg> con las patas
   animadas por CSS, y eso le salía caro al navegador: una animación CSS sobre
   un hijo de SVG no la puede llevar el compositor, así que en cada cuadro hay
   que recalcular estilo, rehacer la maqueta y repintar. Medido en el inicio:
   115 ms de CPU por segundo con nueve hormigas, 32 de ellos solo en recalcular
   estilo.

   Un único lienzo del tamaño de la ventana tampoco servía: aunque se dibujen
   cuatro píxeles, el navegador vuelve a subir la textura entera en cada cuadro
   y el gasto apenas bajaba. Con un lienzo por hormiga, del tamaño del bicho,
   moverse es solo una transformación —que lleva el compositor sin repintar— y
   solo hay que volver a dibujar cuando la pata cambia de postura. El dibujo es
   el mismo de antes: se rasteriza ese SVG en unas pocas posturas del paso. */
(function () {
  if (!document.body.classList.contains('p-index')) return;
  var molde = document.getElementById('dibujo-hormiga-recta');
  if (!molde) return;
  var svgMolde = molde.querySelector('svg');
  if (!svgMolde) return;

  var CUANTAS = 9;
  var LADO = 20;              // lo que mide en pantalla
  var POSTURAS = 8;           // cuántos momentos del paso se rasterizan
  var lento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var dpr = Math.min(window.devicePixelRatio || 1, 2);

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
  }

  /* Las posturas: el mismo SVG con las patas giradas, rasterizado una vez.
     Los ángulos salen de los fotogramas clave que tenía en la hoja de estilos
     —±14° las patas, ±7° las antenas, con aceleración suave—, que es lo que
     describe un seno. */
  var cunos = [], listos = 0;
  function tallar() {
    for (var i = 0; i < POSTURAS; i++) {
      (function (i) {
        var onda = Math.sin(i / POSTURAS * Math.PI * 2);
        var copia = svgMolde.cloneNode(true);
        copia.setAttribute('width', Math.round(LADO * dpr));
        copia.setAttribute('height', Math.round(LADO * dpr));
        function girar(clase, grados) {
          var g = copia.querySelector('.' + clase);
          if (g) g.setAttribute('transform',
            'rotate(' + (grados * onda).toFixed(2) + ' 32 26)');
        }
        girar('h-patas-a', 14);
        girar('h-patas-b', -14);
        girar('h-antenas', 7);
        // El trazo del molde va en unidades del dibujo, pensado para los 32 px
        // del cursor. A 20 px adelgaza hasta deshacerse en gris al suavizar los
        // bordes: se engorda en la misma proporción, como hacía la hoja.
        var trazos = copia.querySelectorAll('[stroke-width]');
        for (var t = 0; t < trazos.length; t++) {
          trazos[t].setAttribute('stroke-width',
            (parseFloat(trazos[t].getAttribute('stroke-width')) * 1.5).toFixed(2));
        }
        var img = new Image();
        img.onload = function () {
          var c = document.createElement('canvas');
          c.width = c.height = Math.round(LADO * dpr);
          c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
          cunos[i] = c;
          listos++;
        };
        img.src = 'data:image/svg+xml;charset=utf-8,'
          + encodeURIComponent(new XMLSerializer().serializeToString(copia));
      })(i);
    }
  }

  medir();
  tallar();
  window.addEventListener('resize', medir);

  var hormigas = [];
  for (var i = 0; i < CUANTAS; i++) {
    var c = document.createElement('canvas');
    c.className = 'hormiga';
    c.width = c.height = Math.round(LADO * dpr);
    campo.appendChild(c);
    hormigas.push({
      nodo: c,
      pincel: c.getContext('2d'),
      postura: -1,
      x: Math.random() * ancho,
      y: Math.random() * alto,
      // el rumbo en radianes; 0 apunta a la derecha
      rumbo: Math.random() * Math.PI * 2,
      // cada una anda a su paso, para que no parezcan un desfile
      paso: (lento ? 14 : 34) + Math.random() * (lento ? 12 : 36),
      // cada cuánto se detiene, y cuánto rato
      quieta: 0,
      // ninguna arranca en el mismo punto del paso que su vecina
      desfase: Math.random(),
      anda: true,
      // persiguiendo, cada una apunta a un punto algo distinto del cursor:
      // si no, se amontonan todas encima
      sesgo: { x: (Math.random() - 0.5) * 70, y: (Math.random() - 0.5) * 70 }
    });
  }

  // la cadencia de las patas va con la velocidad: la que corre, trota. En el
  // molino todas llevan el mismo paso, porque van a la misma velocidad.
  function cadencia(h) {
    var vRueda = (Math.PI * 2 / 8) * (Math.min(ancho, alto) * 0.22);
    var v = (modo === 'molino') ? vRueda : h.paso * factor;
    return Math.max(0.1, Math.min(0.5, 11 / v));
  }

  // Maneras de andar, que se turnan al pulsar:
  //   'suelta'   cada una a lo suyo
  //   'persigue' todas detrás del cursor
  //   'molino'   en rueda, todas en el mismo sentido
  //   'fila'     todas hacia el mismo rincón
  // Con ratón la primera pulsación las echa a perseguir; con el dedo no hay
  // cursor que perseguir, así que ese modo se salta.
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

  function estampar(h, ahora) {
    // Moverse es solo una transformación: la lleva el compositor.
    h.nodo.style.transform = 'translate3d(' + h.x.toFixed(1) + 'px,'
      + h.y.toFixed(1) + 'px,0) rotate('
      + ((h.rumbo * 180 / Math.PI) + 90).toFixed(1) + 'deg)';

    // Volver a dibujar, solo cuando la pata cambia de postura.
    var postura = 0;
    if (h.anda) {
      var seg = cadencia(h);
      postura = Math.floor((ahora / 1000 / seg + h.desfase) * POSTURAS) % POSTURAS;
      if (postura < 0) postura += POSTURAS;
    }
    if (postura === h.postura) return;
    var cuno = cunos[postura] || cunos[0];
    if (!cuno) return;
    h.postura = postura;
    h.pincel.clearRect(0, 0, h.nodo.width, h.nodo.height);
    h.pincel.drawImage(cuno, 0, 0);
  }

  var antes = 0;
  function cuadro(ahora) {
    requestAnimationFrame(cuadro);
    var dt = Math.max(0, Math.min((ahora - antes) / 1000, 0.05));
    antes = ahora;
    if (!listos) return;

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
        g.anda = true;
        estampar(g, ahora);
      }
      return;
    }

    for (var i = 0; i < hormigas.length; i++) {
      var h = hormigas[i];
      if (h.quieta > 0) {
        h.quieta -= dt;
        h.anda = false;
      } else {
        h.anda = true;
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
      estampar(h, ahora);
    }
  }
  requestAnimationFrame(function (t) { antes = t; cuadro(t); });
})();
