/* El nombre del inicio no está escrito: lo dibujan las hormigas. Se mide la
   silueta de las letras en un lienzo oculto, se reparten puntos por dentro y
   cada hormiga camina hasta el suyo. El texto sigue en la página para quien
   no ve la pantalla y para los buscadores: solo se esconde a la vista. */
(function () {
  var bloque = document.querySelector('.p-index .nombre');
  if (!bloque) return;
  var parrafo = bloque.querySelector('p');
  if (!parrafo) return;

  var palabras = (parrafo.textContent || '').replace(/​/g, '').trim();
  if (!palabras) return;

  // El lienzo cubre la ventana entera, no solo la caja del nombre: así las
  // hormigas pueden entrar por cualquier borde de la página en vez de
  // asomarse todas por una franja del ancho del texto.
  var lienzo = document.createElement('canvas');
  lienzo.className = 'nombre-hormigas';
  lienzo.setAttribute('aria-hidden', 'true');
  document.body.appendChild(lienzo);

  var ctx = lienzo.getContext('2d');
  var dpr = Math.min(window.devicePixelRatio || 1, 2);
  var hormigas = [];
  var suave = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function repartir(cuerpo, letra, cabe) {
    // si no cabe de un renglón, se parte por palabras, como lo haría el texto
    var med = document.createElement('canvas').getContext('2d');
    med.font = cuerpo + 'px ' + letra;
    var sueltas = palabras.split(' ');
    var lineas = [], actual = '';
    for (var i = 0; i < sueltas.length; i++) {
      var prueba = actual ? actual + ' ' + sueltas[i] : sueltas[i];
      if (actual && med.measureText(prueba).width > cabe) {
        lineas.push(actual); actual = sueltas[i];
      } else { actual = prueba; }
    }
    if (actual) lineas.push(actual);
    return lineas;
  }

  function puntos(lineas, ancho, alto, cuerpo, letra, salto) {
    // se escribe en un lienzo aparte solo para leer dónde cae la tinta
    var m = document.createElement('canvas');
    m.width = Math.ceil(ancho); m.height = Math.ceil(alto);
    var c = m.getContext('2d');
    c.fillStyle = '#000';
    c.textBaseline = 'top';
    c.font = cuerpo + 'px ' + letra;
    for (var n = 0; n < lineas.length; n++) {
      c.fillText(lineas[n], 0, n * salto);
    }
    var datos = c.getImageData(0, 0, m.width, m.height).data;
    var salida = [];
    // una rejilla fina: un punto por cada hueco con tinta
    var malla = Math.max(3, cuerpo / 15);
    for (var y = 0; y < m.height; y += malla) {
      for (var x = 0; x < m.width; x += malla) {
        var px = Math.round(x), py = Math.round(y);
        if (datos[(py * m.width + px) * 4 + 3] > 128) {
          salida.push({
            x: x + (Math.random() - 0.5) * malla * 0.8,
            y: y + (Math.random() - 0.5) * malla * 0.8
          });
        }
      }
    }
    return salida;
  }

  var vw = 0, vh = 0, origen = { x: 0, y: 0 }, sucio = null;

  function encuadrar() {
    vw = document.documentElement.clientWidth;
    vh = document.documentElement.clientHeight;
    lienzo.style.width = vw + 'px';
    lienzo.style.height = vh + 'px';
    lienzo.width = Math.ceil(vw * dpr);
    lienzo.height = Math.ceil(vh * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    sucio = null;
  }

  // Cada hormiga entra por un borde al azar, a una distancia al azar: no hay
  // dos entradas iguales ni un frente ordenado.
  function afuera() {
    var m = 20 + Math.random() * 90;
    var lado = Math.floor(Math.random() * 4);
    if (lado === 0) return { x: Math.random() * vw, y: -m };
    if (lado === 1) return { x: vw + m, y: Math.random() * vh };
    if (lado === 2) return { x: Math.random() * vw, y: vh + m };
    return { x: -m, y: Math.random() * vh };
  }

  // Si la página se mueve bajo el lienzo, el nombre se corre con ella.
  function reasentar() {
    var caja = bloque.getBoundingClientRect();
    var mx = caja.left - origen.x, my = caja.top - origen.y;
    if (!mx && !my) return;
    origen.x = caja.left; origen.y = caja.top;
    for (var i = 0; i < hormigas.length; i++) {
      var h = hormigas[i];
      h.dx += mx; h.dy += my; h.x += mx; h.y += my;
    }
    quietas = false; sucio = null;
  }

  var antes_medido = '';
  function medir(reinicia) {
    var cs = getComputedStyle(parrafo);
    var cuerpo = parseFloat(cs.fontSize) || 48;
    var letra = cs.fontFamily;
    var cabe = bloque.clientWidth || document.documentElement.clientWidth;
    var lineas = repartir(cuerpo, letra, cabe);
    var salto = parseFloat(cs.lineHeight) || cuerpo * 1.2;
    var prueba = document.createElement('canvas').getContext('2d');
    prueba.font = cuerpo + 'px ' + letra;
    var ancho = 0;
    for (var i = 0; i < lineas.length; i++) {
      ancho = Math.max(ancho, prueba.measureText(lineas[i]).width);
    }
    ancho += cuerpo * 0.15;
    var alto = salto * (lineas.length - 1) + cuerpo * 1.35;

    // Si nada ha cambiado, no se vuelve a empezar: al cargar, el navegador
    // dispara más de un cambio de tamaño y la entrada se veía dos veces.
    encuadrar();
    var firma = [ancho, alto, cuerpo, lineas.join('|')].join(',');
    if (firma === antes_medido) { reasentar(); return; }
    quietas = false;
    var primera = antes_medido === '';
    antes_medido = firma;

    var caja = bloque.getBoundingClientRect();
    origen.x = caja.left; origen.y = caja.top;

    var destinos = puntos(lineas, ancho, alto, cuerpo, letra, salto);
    var viejas = hormigas;
    hormigas = destinos.map(function (d, i) {
      // La primera vez entran desde fuera. Si solo ha cambiado el tamaño de la
      // ventana, cada una sigue donde estaba y camina a su nuevo sitio.
      var v = (!primera && viejas[i]) ? viejas[i] : null;
      var e = v ? null : afuera();
      return {
        x: v ? v.x : e.x,
        y: v ? v.y : e.y,
        dx: d.x + origen.x, dy: d.y + origen.y,
        rumbo: Math.random() * Math.PI * 2,
        prisa: 0.9 + Math.random() * 1.5,
        fase: Math.random() * Math.PI * 2
      };
    });
  }

  // Dibujar cada hormiga con trazos costaba 19 órdenes de lienzo por bicho y
  // por cuadro: con 750, más de ochocientas mil por segundo. Se dibuja una
  // sola vez en pequeño, girada en 36 posiciones y con dos fases del paso, y
  // luego solo se estampa. Pasa de 19 órdenes a una.
  var GIROS = 36, FASES = 2, LADO = 14;
  var cunos = [];

  function tallar() {
    var r = 1.05;
    cunos = [];
    for (var f = 0; f < FASES; f++) {
      for (var g = 0; g < GIROS; g++) {
        var c = document.createElement('canvas');
        c.width = c.height = Math.round(LADO * dpr);
        var p = c.getContext('2d');
        p.setTransform(dpr, 0, 0, dpr, 0, 0);
        p.translate(LADO / 2, LADO / 2);
        p.rotate(g / GIROS * Math.PI * 2);
        var vaiven = (f === 0 ? 0.5 : -0.5);
        p.strokeStyle = '#000';
        p.lineWidth = 0.55;
        p.lineCap = 'round';
        p.beginPath();
        for (var i = -1; i <= 1; i++) {
          var yy = i * r * 0.9;
          p.moveTo(-r * 0.5, yy); p.lineTo(-r * 1.9, yy + vaiven * (i + 2) * 0.4);
          p.moveTo(r * 0.5, yy);  p.lineTo(r * 1.9, yy - vaiven * (i + 2) * 0.4);
        }
        p.stroke();
        p.fillStyle = '#000';
        p.beginPath(); p.ellipse(0, -r * 1.5, r * 0.62, r * 0.55, 0, 0, 6.3); p.fill();
        p.beginPath(); p.ellipse(0, 0, r * 0.52, r * 0.62, 0, 0, 6.3); p.fill();
        p.beginPath(); p.ellipse(0, r * 1.7, r * 0.8, r, 0, 0, 6.3); p.fill();
        cunos.push(c);
      }
    }
  }

  function hormiga(x, y, giro, fase) {
    var g = Math.round(giro / (Math.PI * 2) * GIROS) % GIROS;
    if (g < 0) g += GIROS;
    ctx.drawImage(cunos[fase * GIROS + g], x - LADO / 2, y - LADO / 2, LADO, LADO);
  }

  var t0 = 0, ultimo_dibujo = 0, quietas = false;
  function cuadro(ahora) {
    requestAnimationFrame(cuadro);
    // nunca negativo: si el reloj del navegador da un salto atrás, un dt
    // en negativo las mandaría caminando al revés, lejos de su sitio
    var dt = Math.max(0, Math.min((ahora - t0) / 1000, 0.05));
    t0 = ahora;
    // Mientras caminan hace falta cada cuadro. Una vez puestas solo tiemblan
    // un poco, y con quince veces por segundo no se nota la diferencia: el
    // navegador hace la cuarta parte del trabajo.
    if (quietas && ahora - ultimo_dibujo < 66) return;
    ultimo_dibujo = ahora;
    var lejanas = 0;
    // Solo se borra el trozo de ventana que se ensució en el cuadro anterior:
    // una vez puestas, eso es la caja del nombre y no la pantalla entera.
    if (sucio) ctx.clearRect(sucio[0], sucio[1], sucio[2] - sucio[0], sucio[3] - sucio[1]);
    else ctx.clearRect(0, 0, vw, vh);
    var x1 = Infinity, y1 = Infinity, x2 = -Infinity, y2 = -Infinity;
    for (var i = 0; i < hormigas.length; i++) {
      var h = hormigas[i];
      // tiembla un poco alrededor de su sitio, para que nunca quede inmóvil
      var ox = Math.cos(ahora / 700 + h.fase) * 0.7;
      var oy = Math.sin(ahora / 640 + h.fase) * 0.7;
      var ex = h.dx + ox - h.x, ey = h.dy + oy - h.y;
      var lejos = Math.hypot(ex, ey);
      if (lejos > 1.6) lejanas++;
      // El acercamiento es suave, pero con un tope de velocidad: si no, la
      // que entra desde la esquina opuesta cruzaría la pantalla de un salto.
      var avance = lejos * Math.min(1, (suave ? 1.1 : 2.2) * h.prisa * dt);
      var tope = (suave ? 260 : 520 + 260 * h.prisa) * dt;
      if (avance > tope) avance = tope;
      if (lejos > 0.001) {
        var k = avance / lejos;
        h.x += ex * k; h.y += ey * k;
      }
      if (lejos > 0.4) h.rumbo = Math.atan2(ey, ex);
      // la fase del paso solo cambia mientras camina
      var fase = (lejos > 1) ? (Math.floor(ahora / 110 + h.fase * 3) & 1) : 0;
      hormiga(h.x, h.y, h.rumbo + Math.PI / 2, fase);
      if (h.x < x1) x1 = h.x;
      if (h.y < y1) y1 = h.y;
      if (h.x > x2) x2 = h.x;
      if (h.y > y2) y2 = h.y;
    }
    sucio = (x2 > -Infinity)
      ? [x1 - LADO, y1 - LADO, x2 + LADO, y2 + LADO] : null;
    quietas = lejanas === 0;
  }

  var andando = false;
  function arrancar() {
    if (andando) return;
    andando = true;
    tallar();
    medir();
    requestAnimationFrame(function (t) { t0 = t; ultimo_dibujo = t; cuadro(t); });
  }

  if (document.fonts && document.fonts.ready) document.fonts.ready.then(arrancar);
  else arrancar();

  var espera;
  window.addEventListener('resize', function () {
    clearTimeout(espera);
    espera = setTimeout(medir, 200);
  });
  window.addEventListener('scroll', reasentar, { passive: true });
})();
