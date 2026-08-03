/* onda17 (S-49 / #107) — hero "Horizonte 2050": grade em perspectiva + aurora
 * + cometas descendo + convite ao scroll. Substitui o video de 22,8 MB.
 *
 * Dois canvases de proposito:
 *  - .hero-horizonte__cena: anima ~10s (fade-in 1,2s -> pleno -> desacelera 2s)
 *    e ENTAO o rAF desliga — o ultimo quadro fica como imagem estatica, zero
 *    CPU (padrao decidido na #73). Re-toca quando o hero volta a viewport.
 *  - .hero-horizonte__convite: canvas pequeno (48x72) no centro-base com a
 *    seta + pontinho descendo, em loop PERMANENTE — e o convite ao scroll
 *    pedido pelo Mario (03/08); custo ~zero por ser minusculo.
 * prefers-reduced-motion: cena e convite desenhados estaticos, nenhum loop.
 */
(function () {
  var cena = document.querySelector('.hero-horizonte__cena');
  var conv = document.querySelector('.hero-horizonte__convite');
  if (!cena || !conv) return;
  var DUR = 10000, FADE = 1200, FREIO = 2000;
  var reduz = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function rgba(a) { return 'rgba(0,173,236,' + a + ')'; }

  /* ------------------------------- cena ------------------------------- */
  var ctx = cena.getContext('2d'), W, H, cometas = [];
  function semear() {
    cometas = [];
    for (var i = 0; i < 7; i++) {
      cometas.push({ v: (Math.random() * 22 - 11) | 0, p: Math.random(),
                     vel: .25 + Math.random() * .4 });
    }
  }
  function medir() {
    var r = cena.parentNode.getBoundingClientRect();
    var d = Math.min(window.devicePixelRatio || 1, 2);
    W = r.width; H = r.height;
    cena.width = W * d; cena.height = H * d;
    ctx.setTransform(d, 0, 0, d, 0, 0);
    semear();
  }
  function vLinha(v, hor) {
    var cx = W * .5;
    return { x0: cx + v * 38, y0: hor, x1: cx + v * W * .12, y1: H };
  }
  function desenhar(t, alpha, vel) {
    var hor = H * .62, f, x, y, g, i, v, c, co, L, p;
    ctx.clearRect(0, 0, W, H);
    for (f = 0; f < 3; f++) { /* aurora */
      ctx.beginPath();
      for (x = 0; x <= W; x += 8) {
        y = hor - 40 - f * 34 + Math.sin(x * .004 + t * (.5 - f * .12) + f * 2) * (16 + f * 10);
        if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      g = ctx.createLinearGradient(0, hor - 140, 0, hor);
      g.addColorStop(0, rgba(0)); g.addColorStop(1, rgba(alpha * (.16 - f * .04)));
      ctx.strokeStyle = rgba(alpha * (.35 - f * .09)); ctx.lineWidth = 2.4 - f * .6; ctx.stroke();
      ctx.lineTo(W, hor); ctx.lineTo(0, hor); ctx.closePath(); ctx.fillStyle = g; ctx.fill();
    }
    g = ctx.createLinearGradient(0, hor - 8, 0, hor + 70); /* glow */
    g.addColorStop(0, rgba(alpha * .32)); g.addColorStop(1, rgba(0));
    ctx.fillStyle = g; ctx.fillRect(0, hor - 8, W, 78);
    ctx.lineWidth = 1; /* grade horizontal fluindo PARA o leitor */
    var desloc = (t * .55) % 1;
    for (i = 0; i < 16; i++) {
      var f2 = i + desloc, yy = hor + Math.pow(f2, 1.9) * 7;
      if (yy > H) break;
      ctx.strokeStyle = rgba(alpha * (.10 + .16 * (f2 / 16)));
      ctx.beginPath(); ctx.moveTo(0, yy); ctx.lineTo(W, yy); ctx.stroke();
    }
    for (v = -14; v <= 14; v++) {
      L = vLinha(v, hor);
      ctx.strokeStyle = rgba(alpha * .14);
      ctx.beginPath(); ctx.moveTo(L.x0, L.y0); ctx.lineTo(L.x1, L.y1); ctx.stroke();
    }
    for (c = 0; c < cometas.length; c++) { /* cometas descendo */
      co = cometas[c];
      co.p += co.vel * .011 * vel;
      if (co.p > 1.15) { co.p = 0; co.v = (Math.random() * 22 - 11) | 0; }
      L = vLinha(co.v, hor); p = Math.min(co.p, 1);
      x = L.x0 + (L.x1 - L.x0) * p; y = L.y0 + (L.y1 - L.y0) * p;
      var tx = L.x0 + (L.x1 - L.x0) * Math.max(0, p - .12);
      var ty = L.y0 + (L.y1 - L.y0) * Math.max(0, p - .12);
      g = ctx.createLinearGradient(tx, ty, x, y);
      g.addColorStop(0, rgba(0)); g.addColorStop(1, rgba(alpha * .8 * (1 - p * .4)));
      ctx.strokeStyle = g; ctx.lineWidth = 2.2;
      ctx.beginPath(); ctx.moveTo(tx, ty); ctx.lineTo(x, y); ctx.stroke();
      ctx.fillStyle = rgba(alpha * .9 * (1 - p * .3));
      ctx.beginPath(); ctx.arc(x, y, 2.4, 0, 7); ctx.fill();
    }
  }
  var ini = null, rodando = false;
  function quadro(agora) {
    if (ini === null) ini = agora;
    var ms = agora - ini;
    var alpha = Math.min(1, ms / FADE);
    var vel = 1;
    if (ms > DUR - FREIO) vel = Math.max(0, (DUR - ms) / FREIO);
    desenhar(ms / 1000, alpha, vel);
    if (ms < DUR && rodando) { requestAnimationFrame(quadro); }
    else { rodando = false; } /* ultimo quadro fica na tela; zero CPU */
  }
  function tocar() {
    ini = null;
    if (reduz) { desenhar(9, 1, 0); return; }
    if (!rodando) { rodando = true; requestAnimationFrame(quadro); }
  }

  /* ------------------------- convite ao scroll ------------------------- */
  var cvx = conv.getContext('2d'), CW = 48, CH = 72;
  (function () {
    var d = Math.min(window.devicePixelRatio || 1, 2);
    conv.width = CW * d; conv.height = CH * d;
    cvx.setTransform(d, 0, 0, d, 0, 0);
  })();
  function conviteQuadro(t) {
    var cx = CW / 2, base = CH - 22;
    var ciclo = (t % 2.2) / 2.2;
    var sobe = Math.min(1, ciclo * 4);
    var some = ciclo > .75 ? 1 - (ciclo - .75) * 4 : 1;
    cvx.clearRect(0, 0, CW, CH);
    cvx.strokeStyle = rgba(.25); cvx.lineWidth = 1.5;
    cvx.beginPath(); cvx.moveTo(cx, base - 34); cvx.lineTo(cx, base); cvx.stroke();
    cvx.fillStyle = rgba(.85 * sobe * some);
    cvx.beginPath(); cvx.arc(cx, base - 34 + 34 * ciclo, 2.6, 0, 7); cvx.fill();
    cvx.strokeStyle = rgba(.35 + .45 * some * sobe); cvx.lineWidth = 2.2;
    cvx.lineCap = 'round'; cvx.lineJoin = 'round';
    cvx.beginPath(); cvx.moveTo(cx - 9, base + 8); cvx.lineTo(cx, base + 16);
    cvx.lineTo(cx + 9, base + 8); cvx.stroke();
  }
  if (reduz) { conviteQuadro(1.1); }
  else {
    (function loop(agora) { conviteQuadro(agora / 1000); requestAnimationFrame(loop); })(0);
  }

  /* ----------------------------- arranque ----------------------------- */
  medir(); window.addEventListener('resize', medir);
  tocar();
  if (!reduz && 'IntersectionObserver' in window) {
    /* re-toca a cada volta do hero a viewport (mesmo padrao da #73) */
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) tocar(); });
    }, { threshold: .35 });
    io.observe(cena.parentNode);
  }
})();
