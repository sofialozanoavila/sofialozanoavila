/* El cursor es una hormiga dibujada en la página, no la imagen fija del
   sistema: así puede mover las patas cuando pasa sobre un enlace.
   Si no hay ratón —un celular, una tableta— no se dibuja nada y el puntero
   sigue siendo el del sistema.

   Va en un lienzo pequeño, no en SVG. Con las patas animadas por CSS costaba
   entre 100 y 180 ms de CPU por segundo mientras el ratón se movía sobre los
   enlaces, que era lo segundo más caro del sitio: una animación CSS sobre un
   hijo de SVG obliga a recalcular estilo, rehacer la maqueta y repintar en
   cada cuadro. Ahora se estampa una postura ya dibujada (ver cunos.js). */
(function () {
  var fino = window.matchMedia('(pointer: fine)');
  if (!fino.matches) return;
  // En talleres manda el lápiz; en el resto del sitio, la hormiga.
  if (document.body.classList.contains('p-talleres')) return;

  var molde = document.getElementById('dibujo-hormiga');
  if (!molde) return;
  var svgMolde = molde.querySelector('svg');
  if (!svgMolde || !window.cunosHormiga) return;

  var LADO = 32;              // el tamaño natural del dibujo
  // lo que tardaba un paso en la hoja de estilos; más lento para quien pide
  // en su sistema que haya menos movimiento
  var CADENCIA =
    window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0.6 : 0.26;
  var dpr = Math.min(window.devicePixelRatio || 1, 2);
  var juego = window.cunosHormiga(svgMolde, LADO, dpr);

  var lienzo = document.createElement('canvas');
  lienzo.className = 'hormiga-cursor';
  lienzo.setAttribute('aria-hidden', 'true');
  lienzo.width = lienzo.height = Math.round(LADO * dpr);
  document.body.appendChild(lienzo);
  var ctx = lienzo.getContext('2d');
  document.documentElement.classList.add('con-hormiga');

  // Al cambiar de página la hormiga aparecía solo cuando se movía el ratón,
  // y entre tanto no había cursor ninguno. Se guarda la última posición para
  // dibujarla ya puesta, sin que se vea la flecha del sistema por el camino.
  var x = -100, y = -100;
  try {
    var guardado = sessionStorage.getItem('hormiga');
    if (guardado) {
      var par = guardado.split(',');
      x = parseFloat(par[0]); y = parseFloat(par[1]);
    }
  } catch (e) { /* ventana privada: se queda sin recordar */ }

  var anda = false, postura = -1, pedido = false;

  function estampar(ahora) {
    pedido = false;
    lienzo.style.transform = 'translate3d(' + (x - 12) + 'px,' + (y - 8) + 'px,0)';
    var cual = 0;
    if (anda && juego.listos) {
      cual = Math.floor(ahora / 1000 / CADENCIA * juego.posturas) % juego.posturas;
      if (cual < 0) cual += juego.posturas;
    }
    if (cual === postura) return;
    var cuno = juego.cunos[cual] || juego.cunos[0];
    if (!cuno) return;
    postura = cual;
    ctx.clearRect(0, 0, lienzo.width, lienzo.height);
    ctx.drawImage(cuno, 0, 0);
  }

  function pedir() {
    if (pedido) return;
    pedido = true;
    requestAnimationFrame(estampar);
  }
  pedir();

  // Mientras camina hay que repintar aunque el ratón se quede parado encima
  // del enlace: es lo único que mueve las patas.
  function pasos(ahora) {
    if (anda) { estampar(ahora); requestAnimationFrame(pasos); }
  }

  window.addEventListener('pagehide', function () {
    try { sessionStorage.setItem('hormiga', x + ',' + y); } catch (e) {}
  });

  document.addEventListener('mousemove', function (e) {
    x = e.clientX; y = e.clientY;
    // ¿hay un enlace debajo? entonces camina
    var sobre = !!(e.target.closest && e.target.closest('a, button'));
    var antes = anda;
    anda = sobre;
    if (anda && !antes) requestAnimationFrame(pasos);
    pedir();
  }, { passive: true });

  // al salir de la ventana se esconde, para que no quede una hormiga quieta
  document.documentElement.addEventListener('mouseleave', function () {
    lienzo.style.opacity = '0';
  });
  document.documentElement.addEventListener('mouseenter', function () {
    lienzo.style.opacity = '';
  });
})();
