/* Al pulsar una fotografía del catálogo se abre a pantalla completa.
   Se cierra con otro clic, con Escape o con la cruz. */
(function () {
  var fotos = document.querySelectorAll('[data-ampliar]');
  if (!fotos.length) return;

  var capa = document.createElement('div');
  capa.className = 'ampliada';
  capa.setAttribute('role', 'dialog');
  capa.setAttribute('aria-modal', 'true');
  capa.hidden = true;
  capa.innerHTML = '<button class="cerrar" type="button" aria-label="Cerrar">×</button>'
                 + '<img alt="">';
  document.body.appendChild(capa);
  var grande = capa.querySelector('img');

  function abrir(img) {
    grande.src = img.currentSrc || img.src;
    grande.alt = img.alt || '';
    capa.hidden = false;
    document.body.classList.add('con-ampliada');
    capa.querySelector('.cerrar').focus();
  }
  function cerrar() {
    capa.hidden = true;
    document.body.classList.remove('con-ampliada');
    grande.removeAttribute('src');
  }

  fotos.forEach(function (img) {
    img.addEventListener('click', function () { abrir(img); });
  });
  capa.addEventListener('click', cerrar);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !capa.hidden) cerrar();
  });
})();
