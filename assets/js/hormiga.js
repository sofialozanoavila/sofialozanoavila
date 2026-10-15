/* El cursor es una hormiga dibujada en la página, no la imagen fija del
   sistema: así puede mover las patas cuando pasa sobre un enlace.
   Si no hay ratón —un celular, una tableta— no se dibuja nada y el puntero
   sigue siendo el del sistema. */
(function () {
  var fino = window.matchMedia('(pointer: fine)');
  if (!fino.matches) return;
  // En talleres manda el lápiz; en el resto del sitio, la hormiga.
  if (document.body.classList.contains('p-talleres')) return;

  var molde = document.getElementById('dibujo-hormiga');
  if (!molde) return;

  var caja = document.createElement('div');
  caja.className = 'hormiga-cursor';
  caja.setAttribute('aria-hidden', 'true');
  caja.innerHTML = molde.innerHTML;
  document.body.appendChild(caja);
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

  var pintada = true;
  function mover() {
    caja.style.transform = 'translate3d(' + (x - 12) + 'px,' + (y - 8) + 'px,0)';
    pintada = true;
  }
  mover();

  window.addEventListener('pagehide', function () {
    try { sessionStorage.setItem('hormiga', x + ',' + y); } catch (e) {}
  });

  document.addEventListener('mousemove', function (e) {
    x = e.clientX; y = e.clientY;
    if (pintada) { pintada = false; requestAnimationFrame(mover); }
    // ¿hay un enlace debajo? entonces camina
    var sobre = e.target.closest && e.target.closest('a, button');
    caja.classList.toggle('anda', !!sobre);
  }, { passive: true });

  // al salir de la ventana se esconde, para que no quede una hormiga quieta
  document.documentElement.addEventListener('mouseleave', function () {
    caja.style.opacity = '0';
  });
  document.documentElement.addEventListener('mouseenter', function () {
    caja.style.opacity = '';
  });
})();
