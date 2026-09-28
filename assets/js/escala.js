/* La maquetación original tiene un ancho fijo (el del sitio en Wix).
   En pantallas más estrechas la reducimos proporcionalmente, en vez de
   dejar que aparezca una barra de desplazamiento horizontal.
   Por debajo de 860 px manda el CSS: todo se apila en una columna. */
(function () {
  var secciones = document.querySelectorAll('.sec[data-ancho]');
  if (!secciones.length) return;

  function ajustar() {
    // los 80 px son los mismos márgenes del lienzo de las páginas de
    // proyecto, y el tope de 1760 px, su misma anchura máxima
    var margen = parseFloat(getComputedStyle(document.documentElement)
      .getPropertyValue('--margen')) || 40;
    var disponible = Math.min(document.documentElement.clientWidth, 1760) - margen * 2;
    secciones.forEach(function (sec) {
      if (document.documentElement.clientWidth < 860) {   // el CSS ya apila el contenido
        sec.style.zoom = '';
        (sec.querySelector('.lienzo') || sec).style.padding = '';
        return;
      }
      var ancho = parseFloat(sec.dataset.ancho) || 980;
      // el margen puede vivir en la sección o en su lienzo, según la página
      var caja = sec.querySelector('.lienzo') || sec;
      if (disponible < ancho) {
        var z = disponible / ancho;
        sec.style.zoom = z.toFixed(4);
        // el margen izquierdo también se encogería con el resto: se agranda
        // en la misma proporción para que siga midiendo 40 px en pantalla,
        // los mismos que en las páginas de proyecto
        caja.style.padding = '0 ' + (margen / z).toFixed(2) + 'px';
      } else {
        sec.style.zoom = '';
        caja.style.padding = '';
      }
    });
  }

  var t;
  window.addEventListener('resize', function () {
    clearTimeout(t);
    t = setTimeout(ajustar, 100);
  });
  ajustar();
})();
