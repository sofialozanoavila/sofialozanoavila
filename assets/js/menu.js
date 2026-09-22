/* Menú superior: las páginas que no caben en una línea pasan al botón «+»,
   igual que en el sitio original. */
(function () {
  var menu = document.querySelector('.menu');
  if (!menu) return;

  var more = menu.querySelector('.more');
  var submenu = more.querySelector('.submenu');
  var button = more.querySelector('button');
  var items = Array.prototype.slice.call(menu.children).filter(function (li) {
    return li !== more;
  });

  function reflow() {
    // devuelve todo a la barra antes de volver a medir
    items.forEach(function (li) { menu.insertBefore(li, more); });
    submenu.innerHTML = '';
    more.hidden = true;

    if (window.innerWidth < 860) return;   // en pantallas angostas el menú se despliega en vertical

    var top = menu.getBoundingClientRect().top;
    var overflow = items.filter(function (li) {
      return li.getBoundingClientRect().top > top + 4;
    });
    if (!overflow.length) return;

    more.hidden = false;
    // al mostrar «+» puede desbordarse una pieza más: se recalcula
    overflow = items.filter(function (li) {
      return li.getBoundingClientRect().top > top + 4;
    });
    overflow.forEach(function (li) { submenu.appendChild(li); });
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
