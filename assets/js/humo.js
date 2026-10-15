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
    // Una nube no es un punto: son varios borrones que se abren a la vez y,
    // desenfocados, se funden en una sola bocanada.
    var n = document.createElement('span');
    n.className = 'nube';
    n.style.left = x + 'px';
    n.style.top = y + 'px';
    n.style.setProperty('--sube', (-26 - Math.random() * 18).toFixed(0) + 'px');
    n.style.setProperty('--lado', ((Math.random() - 0.5) * 26).toFixed(0) + 'px');
    var cuantos = 4 + Math.floor(Math.random() * 3);
    for (var i = 0; i < cuantos; i++) {
      var b = document.createElement('i');
      var tam = 9 + Math.random() * 13;
      b.style.width = b.style.height = tam.toFixed(1) + 'px';
      b.style.left = ((Math.random() - 0.5) * 26 - tam / 2).toFixed(1) + 'px';
      b.style.top = ((Math.random() - 0.5) * 16 - tam / 2).toFixed(1) + 'px';
      b.style.setProperty('--crece', (2.3 + Math.random() * 1.1).toFixed(2));
      b.style.animationDelay = (Math.random() * 0.09).toFixed(3) + 's';
      n.appendChild(b);
    }
    campo.appendChild(n);
    setTimeout(function () { n.remove(); }, 1200);
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
