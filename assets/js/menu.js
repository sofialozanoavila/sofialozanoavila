/* Menú superior: las páginas que no caben en una línea pasan al botón «+»,
   igual que en el sitio original. */
(function () {
  var menu = document.querySelector('.menu');
  if (!menu) return;

  var more = menu.querySelector('.more');
  var submenu = more.querySelector('.submenu');
  var button = more.querySelector('button');
  // El selector de idioma no entra nunca en el desbordamiento: debe verse
  // siempre, en cualquier página y a cualquier ancho.
  var idioma = menu.querySelector('.idioma');
  var items = Array.prototype.slice.call(menu.children).filter(function (li) {
    return li !== more && li !== idioma;
  });

  function reflow() {
    // En la barra se quedan siempre las mismas cuatro entradas —proyectos,
    // contacto, cv y piezas disponibles— más el idioma. Los nombres de los
    // proyectos viven dentro del «+», en escritorio y en el celular.
    var tope = idioma || more;
    items.forEach(function (li) { menu.insertBefore(li, tope); });
    submenu.innerHTML = '';

    var guardados = items.filter(function (li) {
      return !li.classList.contains('principal');
    });
    guardados.forEach(function (li) { submenu.appendChild(li); });
    more.hidden = guardados.length === 0;
  }

  function close() {
    more.dataset.open = 'false';
    button.setAttribute('aria-expanded', 'false');
  }

  button.addEventListener('click', function (e) {
    e.stopPropagation();
    var open = more.dataset.open === 'true';
    more.dataset.open = open ? 'false' : 'true';
    button.setAttribute('aria-expanded', open ? 'false' : 'true');
  });
  document.addEventListener('click', close);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') close();
  });

  // en pantallas angostas el menú se despliega con el botón «menú»
  var header = document.querySelector('.site-header');
  var abrir = header && header.querySelector('.abrir-menu');
  if (abrir) {
    abrir.addEventListener('click', function () {
      var abierto = header.dataset.abierto === 'true';
      header.dataset.abierto = abierto ? 'false' : 'true';
      abrir.setAttribute('aria-expanded', abierto ? 'false' : 'true');
    });
  }

  var t;
  window.addEventListener('resize', function () {
    clearTimeout(t);
    t = setTimeout(reflow, 150);
  });
  reflow();
})();
