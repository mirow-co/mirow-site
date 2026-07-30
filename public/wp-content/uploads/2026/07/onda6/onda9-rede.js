/* onda9 — pagina "Nossa rede": toque nos pins + realce cruzado com a lista.
   O hover em si e 100% CSS (.rede-pin:hover .rede-pin__card). Este arquivo so
   cobre o que CSS nao faz: abrir/fechar no toque e ligar lista <-> pin. */
(function () {
  'use strict';

  function iniciar() {
    var palco = document.querySelector('.rede-mapa__pins');
    if (!palco) { return; }
    var pins = [].slice.call(palco.querySelectorAll('.rede-pin'));
    if (!pins.length) { return; }

    function fecharTodos(exceto) {
      pins.forEach(function (pin) {
        if (pin === exceto) { return; }
        pin.classList.remove('is-aberto');
        var b = pin.querySelector('.rede-pin__botao');
        if (b) { b.setAttribute('aria-expanded', 'false'); }
      });
    }

    pins.forEach(function (pin) {
      var botao = pin.querySelector('.rede-pin__botao');
      if (!botao) { return; }
      botao.addEventListener('click', function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var abrindo = !pin.classList.contains('is-aberto');
        fecharTodos(pin);
        pin.classList.toggle('is-aberto', abrindo);
        botao.setAttribute('aria-expanded', abrindo ? 'true' : 'false');
      });
    });

    // tap/clique fora fecha; Esc tambem
    document.addEventListener('click', function (ev) {
      if (!ev.target.closest || !ev.target.closest('.rede-pin')) { fecharTodos(null); }
    });
    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape') { fecharTodos(null); }
    });

    // passar o mouse num item da lista destaca o pin correspondente
    [].slice.call(document.querySelectorAll('.rede-lista__item')).forEach(function (item) {
      var alvo = palco.querySelector('.rede-pin[data-parceiro="' +
        item.getAttribute('data-parceiro') + '"]');
      if (!alvo) { return; }
      ['mouseenter', 'focusin'].forEach(function (e) {
        item.addEventListener(e, function () { alvo.classList.add('is-realce'); });
      });
      ['mouseleave', 'focusout'].forEach(function (e) {
        item.addEventListener(e, function () { alvo.classList.remove('is-realce'); });
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar);
  } else {
    iniciar();
  }
})();
