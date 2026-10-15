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
    n.style.setProperty('--sube', (-15 - Math.random() * 11).toFixed(0) + 'px');
    n.style.setProperty('--lado', ((Math.random() - 0.5) * 15).toFixed(0) + 'px');
    var cuantos = 3 + Math.floor(Math.random() * 2);
    for (var i = 0; i < cuantos; i++) {
      var b = document.createElement('i');
      var tam = 5 + Math.random() * 7;
      b.style.width = b.style.height = tam.toFixed(1) + 'px';
      b.style.left = ((Math.random() - 0.5) * 14 - tam / 2).toFixed(1) + 'px';
      b.style.top = ((Math.random() - 0.5) * 9 - tam / 2).toFixed(1) + 'px';
      b.style.setProperty('--crece', (1.7 + Math.random() * 0.8).toFixed(2));
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
