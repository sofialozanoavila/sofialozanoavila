/* El dibujo de la hormiga, rasterizado en unas cuantas posturas del paso.

   Lo usan el hormiguero del inicio y la hormiga del cursor. Las dos dibujaban
   antes las patas con animaciones CSS sobre los grupos del SVG, y eso es de lo
   más caro que puede pedírsele a un navegador: una animación así no la puede
   llevar el compositor, de modo que cada cuadro exige recalcular estilo,
   rehacer la maqueta y repintar. Estampar una imagen ya hecha no cuesta nada.

   Los ángulos salen de los fotogramas clave que llevaba la hoja de estilos
   —±14° las patas, ±7° las antenas, con aceleración suave—, que es lo que
   describe un seno. */
(function () {
  window.cunosHormiga = function (svgMolde, lado, dpr, opciones) {
    opciones = opciones || {};
    var posturas = opciones.posturas || 8;
    var grosor = opciones.grosor || 1;
    var juego = { cunos: [], listos: 0, posturas: posturas };

    for (var i = 0; i < posturas; i++) {
      (function (i) {
        var onda = Math.sin(i / posturas * Math.PI * 2);
        var copia = svgMolde.cloneNode(true);
        copia.setAttribute('width', Math.round(lado * dpr));
        copia.setAttribute('height', Math.round(lado * dpr));
        function girar(clase, grados) {
          var g = copia.querySelector('.' + clase);
          if (g) g.setAttribute('transform',
            'rotate(' + (grados * onda).toFixed(2) + ' 32 26)');
        }
        girar('h-patas-a', 14);
        girar('h-patas-b', -14);
        girar('h-antenas', 7);
        // El trazo del molde va en unidades del dibujo: al encoger la hormiga
        // adelgaza hasta deshacerse en gris al suavizar los bordes.
        if (grosor !== 1) {
          var trazos = copia.querySelectorAll('[stroke-width]');
          for (var t = 0; t < trazos.length; t++) {
            trazos[t].setAttribute('stroke-width',
              (parseFloat(trazos[t].getAttribute('stroke-width')) * grosor).toFixed(2));
          }
        }
        var img = new Image();
        img.onload = function () {
          var c = document.createElement('canvas');
          c.width = c.height = Math.round(lado * dpr);
          c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
          juego.cunos[i] = c;
          juego.listos++;
        };
        img.src = 'data:image/svg+xml;charset=utf-8,'
          + encodeURIComponent(new XMLSerializer().serializeToString(copia));
      })(i);
    }
    return juego;
  };
})();
