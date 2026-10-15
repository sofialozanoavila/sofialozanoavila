/* Una nube de polvo al pasar por encima de un enlace, como si la hormiga
   levantara tierra al caminar. */
(function () {
  if (!window.matchMedia('(pointer: fine)').matches) return;

  var campo = document.createElement('div');
  campo.className = 'humo';
  campo.setAttribute('aria-hidden', 'true');
  document.body.appendChild(campo);

  var suave = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var ultimo = 0;

  function soplo(x, y) {
    var n = document.createElement('span');
    n.className = 'nube';
    // cada nube sale con su tamaño, su ladeo y su deriva
    var tam = 11 + Math.random() * 9;
    n.style.width = n.style.height = tam.toFixed(0) + 'px';
    n.style.left = (x - tam / 2) + 'px';
    n.style.top = (y - tam / 2) + 'px';
    n.style.setProperty('--sube', (-18 - Math.random() * 16).toFixed(0) + 'px');
    n.style.setProperty('--lado', ((Math.random() - 0.5) * 22).toFixed(0) + 'px');
    campo.appendChild(n);
    setTimeout(function () { n.remove(); }, 900);
  }

  document.addEventListener('mousemove', function (e) {
    var enlace = e.target.closest && e.target.closest('a, button');
    if (!enlace) return;
    var ahora = e.timeStamp;
    if (ahora - ultimo < (suave ? 420 : 170)) return;
    ultimo = ahora;
    soplo(e.clientX, e.clientY);
  }, { passive: true });
})();
