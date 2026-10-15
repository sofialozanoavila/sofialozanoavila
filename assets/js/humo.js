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
    // Unos pocos granos, no una nube: salen disparados hacia los lados y
    // arriba, y caen un poco más abajo de donde salieron.
    var n = document.createElement('span');
    n.className = 'nube';
    n.style.left = x + 'px';
    n.style.top = y + 'px';
    var cuantos = 4 + Math.floor(Math.random() * 3);
    var rato = 0;
    for (var i = 0; i < cuantos; i++) {
      var g = document.createElement('i');
      var tam = 1.4 + Math.random() * 1.8;
      g.style.width = g.style.height = tam.toFixed(1) + 'px';
      g.style.left = ((Math.random() - 0.5) * 6).toFixed(1) + 'px';
      g.style.top = ((Math.random() - 0.5) * 4).toFixed(1) + 'px';
      // a un lado o al otro, y cuanto más lejos, más rato en el aire
      var lado = (Math.random() < 0.5 ? -1 : 1) * (5 + Math.random() * 13);
      var alto = -(5 + Math.random() * 9);
      g.style.setProperty('--dx', lado.toFixed(1) + 'px');
      g.style.setProperty('--alto', alto.toFixed(1) + 'px');
      g.style.setProperty('--caida', (2 + Math.random() * 5).toFixed(1) + 'px');
      var dura = 0.46 + Math.random() * 0.3;
      g.style.setProperty('--rato', dura.toFixed(2) + 's');
      g.style.animationDelay = (Math.random() * 0.05).toFixed(3) + 's';
      rato = Math.max(rato, dura);
      n.appendChild(g);
    }
    campo.appendChild(n);
    setTimeout(function () { n.remove(); }, (rato + 0.2) * 1000);
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
