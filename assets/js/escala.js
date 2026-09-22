/* La maquetación original tiene un ancho fijo (el del sitio en Wix).
   En pantallas más estrechas la reducimos proporcionalmente, en vez de
   dejar que aparezca una barra de desplazamiento horizontal.
   Por debajo de 860 px manda el CSS: todo se apila en una columna. */
(function () {
  var secciones = document.querySelectorAll('.sec[data-ancho]');
  if (!secciones.length) return;

  function ajustar() {
    var disponible = document.documentElement.clientWidth - 32;
    secciones.forEach(function (sec) {
      if (disponible < 828) {           // 860 - 32: el CSS ya apila el contenido
        sec.style.zoom = '';
        return;
      }
      var ancho = parseFloat(sec.dataset.ancho) || 980;
      sec.style.zoom = disponible < ancho ? (disponible / ancho).toFixed(4) : '';
    });
  }

  var t;
  window.addEventListener('resize', function () {
    clearTimeout(t);
    t = setTimeout(ajustar, 100);
  });
  ajustar();
})();
