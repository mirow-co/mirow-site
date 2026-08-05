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
/* onda34 (S-125 / #178): o "m" da Mirow no ponto de fuga, como fonte das linhas.
 * O pedido do Mario: "um logo do M da mirow no meio do campo central, como algo
 * grandioso da onde saem essas linhas dinamicas apontando para fora, o centro de
 * tudo, da inteligencia". As linhas ja convergiam para o centro do horizonte —
 * o logo vai exatamente nesse ponto, e a origem delas foi APERTADA (v*38 -> v*10)
 * para elas lerem como se saissem de dentro dele.
 * O path vem do PRIMEIRO <path> de wp-content/uploads/2024/04/marca-mirow-co.svg
 * (o mesmo glifo do badge do LinkedIn, em vetor). A assercao S125 recompara os
 * dois: se o arquivo da marca mudar, a suite acusa em vez de divergir calada.
 */
(function () {
  var cena = document.querySelector('.hero-horizonte__cena');
  var conv = document.querySelector('.hero-horizonte__convite');
  if (!cena || !conv) return;
  var DUR = 10000, FADE = 1200, FREIO = 2000;
  var reduz = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function rgba(a) { return 'rgba(0,173,236,' + a + ')'; }

  /* o "m" da marca, viewBox 0 0 101 102 */
  var M_PATH = 'M50.3453 11.9887C55.1412 4.19839 62.635 0.000167847 72.8282 0.000167847C81.213 0.000167847 87.9597 3.15018 92.6023 8.24178C99.8011 16.1861 99.8011 26.2261 99.8011 38.3632V100.702H88.7083V38.3632C88.7083 26.9723 88.7083 20.6801 84.5155 15.5869C81.8169 12.2906 77.3183 10.4907 72.0734 10.4907C66.8278 10.4907 62.3385 12.2906 59.639 15.5869C55.4431 20.6801 55.4431 26.9723 55.4431 38.3632V100.702H44.3542V38.3632C44.3542 26.9723 44.3542 20.6801 40.1575 15.5869C37.4635 12.2906 32.9641 10.4907 27.7177 10.4907C22.4744 10.4907 17.9804 12.2906 15.2856 15.5869C11.0843 20.6801 11.0843 26.9723 11.0843 38.3632V100.702H0V38.3632C0 26.2261 -7.38287e-07 15.8834 7.49068 8.24178C12.4352 3.15018 19.4784 0.000167847 28.4663 0.000167847C38.0557 0.000167847 46.1525 4.04433 50.3453 11.9887Z';
  var M_VB = 102;                       /* lado do viewBox usado para escalar */
  var mPath = (typeof Path2D === 'function') ? new Path2D(M_PATH) : null;

  /* Tamanho do logo. A partir da onda 36 ele e SOLIDO e fica NA FRENTE dos cards,
   * e isso muda a matematica: enquanto era translucido e ficava atras, podia passar
   * por tras do texto sem prejuizo. Opaco e na frente, qualquer sobreposicao APAGA
   * o texto — medido: com 300px fixos ele cobria 200px da linha "Focamos em
   * estrategia, compras e go-to-market..." em 992px, e 21px da legenda dos big
   * numbers em 1400px.
   * Entao o tamanho passa a ser derivado do VAO LIVRE entre os dois cards, medido
   * do DOM: nunca maior que o vao (menos uma folga), e no maximo 300px. Assim
   * "nao cobrir texto" e garantido por construcao, e nao por tentativa.
   * Vao menor que MIN_VAO (cards empilhados, <=1200px): o logo NAO aparece — e
   * melhor nao ter logo do que ter a proposta de valor tapada por ele. */
  var MAX_LOGO = 300, FOLGA_VAO = 16, MIN_VAO = 90;
  function tamanhoLogo() {
    var v = vaoEntreCards();
    if (v < MIN_VAO) return 0;                       /* nao cabe: nao mostra */
    return Math.min(MAX_LOGO, Math.floor(v - FOLGA_VAO));
  }

  /* ------------------------------- cena ------------------------------- */
  var ctx = cena.getContext('2d'), W, H, cometas = [], centroX = 0;

  /* onda34: onde fica o "centro de tudo".
   * O canvas mora no fundo, atras dos dois cards do hero (.hero-texto a esquerda,
   * .hero-numeros a direita). O centro geometrico do palco cai DENTRO do card da
   * esquerda: medido em 1400px, um logo de 300px centrado em W/2 fica com 270px
   * atras do card e 30px no azul aberto — sai torto, com cara de acidente.
   * Entao o centro passa a ser o meio do VAO entre os cards (medido do DOM, para
   * valer nos 3 idiomas e em toda largura). Quando os cards empilham (<992px) nao
   * existe vao horizontal e o centro volta a ser o do palco. */
  /* Borda direita do card da esquerda e borda esquerda do card da direita, em
   * coordenadas do palco. UMA fonte de verdade: centro e tamanho do logo saem os
   * dois daqui (valores gemeos e a classe de bug que o P2.1 do CLAUDE.md proibe). */
  var _vao = null;                      /* {esq, dir, largura} ou null */
  function medirVao() {
    _vao = null;
    var a = document.querySelector('.hero-texto');
    var b = document.querySelector('.hero-numeros');
    if (!a || !b) return;
    var ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
    if (!ra.width || !rb.width) return;
    var esq, dir;
    if (rb.left < ra.left) { esq = rb.right; dir = ra.left; }
    else { esq = ra.right; dir = rb.left; }
    var pal = cena.parentNode.getBoundingClientRect();
    _vao = { esq: esq - pal.left, dir: dir - pal.left, largura: dir - esq };
  }
  function vaoEntreCards() { return _vao ? _vao.largura : 0; }
  function medirCentro() {
    /* centro do vao quando ele existe; senao o centro do palco */
    if (_vao && _vao.largura >= MIN_VAO) return (_vao.esq + _vao.dir) / 2;
    return W * .5;
  }
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
    medirVao();
    centroX = medirCentro();
    garantirLogo();
    posicionarLogo(H * .62);
    semear();
  }
  function vLinha(v, hor) {
    var cx = centroX || W * .5;
    /* onda34: era v*38 (origens espalhadas por ~1060px no horizonte, o que nao
     * lia como ponto de origem). Com v*10 as 29 origens caem DENTRO do logo, e as
     * linhas saem de dentro dele abrindo para fora — o efeito que o Mario pediu. */
    return { x0: cx + v * 10, y0: hor, x1: cx + v * W * .12, y1: H };
  }

  /* onda36 (S-127 / #180): o halo continua no canvas (atras de tudo), mas o "m" em
   * si saiu do canvas e virou ELEMENTO SVG, em z-index 10 — na frente dos cards
   * (z=4) e atras do header (z=20). Pedido do Mario: "nao seja transparente, seja
   * branco solido e na frente de tudo que estiver atras".
   * Por que elemento e nao canvas: o canvas mora no .banner__background (z=1) e
   * nada desenhado nele pode passar na frente dos cards — teria de mover o canvas
   * inteiro, o que poria a grade e os cometas por cima do texto. */
  function desenharHalo(alpha, hor) {
    var t = tamanhoLogo(), cx = centroX || W * .5, g;
    if (!t) return;
    g = ctx.createRadialGradient(cx, hor, 0, cx, hor, t * 1.25);
    g.addColorStop(0, rgba(alpha * .30));
    g.addColorStop(.55, rgba(alpha * .10));
    g.addColorStop(1, rgba(0));
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(cx, hor, t * 1.25, 0, 7); ctx.fill();
  }

  /* O "m" solido, em elemento SVG proprio. Criado uma vez; medir() reposiciona. */
  var elLogo = null;
  function garantirLogo() {
    if (elLogo || !document.querySelector('.banner')) return;
    var ns = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('class', 'hero-logo-m');
    svg.setAttribute('viewBox', '0 0 101 102');
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('focusable', 'false');
    var p = document.createElementNS(ns, 'path');
    p.setAttribute('d', M_PATH);
    svg.appendChild(p);
    document.querySelector('.banner').appendChild(svg);
    elLogo = svg;
  }
  function posicionarLogo(hor) {
    if (!elLogo) return;
    var t = tamanhoLogo(), cx = centroX || W * .5;
    if (!t) { elLogo.style.display = 'none'; return; }
    elLogo.style.width = t + 'px';
    elLogo.style.height = t + 'px';
    elLogo.style.left = cx + 'px';
    elLogo.style.top = hor + 'px';
    elLogo.style.display = 'block';
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
    desenharHalo(alpha, hor);            /* onda36: so o halo fica no canvas */
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
