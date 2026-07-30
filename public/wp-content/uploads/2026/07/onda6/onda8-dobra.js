/* onda8 — mede a faixa de logos e alimenta --onda8-logos-h.
   Sem isso a conta da primeira dobra dependeria de um numero magico, que quebra
   quando muda a quantidade de fileiras de logos (largura da janela) ou o idioma. */
(function () {
  var faixa = document.querySelector('.homepage .clientes-logos');
  if (!faixa) { return; }
  var pendente = null;
  function medir() {
    pendente = null;
    var h = Math.round(faixa.getBoundingClientRect().height);
    if (h > 0) {
      document.documentElement.style.setProperty('--onda8-logos-h', h + 'px');
    }
  }
  function agendar() {
    if (pendente) { return; }
    pendente = window.requestAnimationFrame(medir);
  }
  medir();
  window.addEventListener('load', agendar);
  window.addEventListener('resize', agendar);
  window.addEventListener('orientationchange', agendar);
  if (window.ResizeObserver) { new window.ResizeObserver(agendar).observe(faixa); }
  if (document.fonts && document.fonts.ready) { document.fonts.ready.then(agendar); }
})();
