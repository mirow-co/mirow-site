/* onda13 — S-23 (issue #73): camada viva do hero da home (Variante B).
 *
 * A JPG da malha (malha-hero.jpg) fica como base estatica; este canvas acende
 * nos e manda pulsos de luz pelas arestas, por curta duracao (decisao Mario):
 * fade-in 1,2s -> movimento pleno 7s -> desaceleracao 2s -> requestAnimationFrame
 * DESLIGADO — o ultimo quadro fica na tela como imagem estatica (zero CPU).
 * Com prefers-reduced-motion: reduce, vai direto para o quadro parado.
 *
 * Codigo da Variante B do prototipo aprovado em 30/07
 * (mirow-marketing/08_Site/_proto-hero-animado/hero-animado.html).
 */
(function () {
  var MOV = 7000;
  var FREIO = 2000;
  var CYAN = [0, 173, 236];

  function criar(canvas) {
    var ctx = canvas.getContext('2d');
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var W = 0, H = 0, nos = [], pulsos = [], t0 = 0, raf = null;
    var DIST = 0;

    function medir() {
      var r = canvas.getBoundingClientRect();
      W = r.width; H = r.height;
      canvas.width = W * dpr; canvas.height = H * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      DIST = Math.min(190, Math.max(120, W / 9));
    }

    function semear() {
      nos = [];
      var qtd = Math.min(Math.round(W * H / 26000), 260);
      var cristas = [{ x: 0.10, y: 0.72 }, { x: 0.44, y: 0.86 }, { x: 0.72, y: 0.66 }];
      for (var i = 0; i < qtd; i++) {
        var x, y;
        if (Math.random() < 0.62) {
          var c = cristas[(Math.random() * cristas.length) | 0];
          x = (c.x + (Math.random() - 0.5) * 0.42) * W;
          y = (c.y + (Math.random() - 0.5) * 0.44) * H;
        } else {
          x = Math.random() * W;
          y = Math.pow(Math.random(), 0.55) * H;
        }
        nos.push({
          x: Math.max(-20, Math.min(W + 20, x)), y: Math.max(-20, Math.min(H + 20, y)),
          vx: (Math.random() - 0.5) * 0.20,
          vy: (Math.random() - 0.5) * 0.14,
          r: Math.random() < 0.14 ? 2.6 + Math.random() * 1.6 : 1.1 + Math.random() * 0.9,
          f: 0.4 + Math.random() * 1.6,
          b: 0.45 + Math.random() * 0.55
        });
      }
      pulsos = [];
      for (var j = 0; j < 3; j++) pulsos.push({ a: 0, b: 0, p: Math.random(), v: 0.0016 + Math.random() * 0.0022 });
    }

    function rgba(a) { return 'rgba(' + CYAN[0] + ',' + CYAN[1] + ',' + CYAN[2] + ',' + a + ')'; }

    function quadro(agora) {
      var t = agora - t0;
      var vel = t < MOV ? 1 : Math.max(0, 1 - (t - MOV) / FREIO);
      vel = vel * vel * (3 - 2 * vel);
      var entrada = Math.min(1, t / 1200);

      var i, j, n, m;
      for (i = 0; i < nos.length; i++) {
        n = nos[i];
        n.x += n.vx * vel; n.y += n.vy * vel;
        if (n.x < -40) n.x = W + 40; if (n.x > W + 40) n.x = -40;
        if (n.y < -40) n.y = H + 40; if (n.y > H + 40) n.y = -40;
      }

      ctx.clearRect(0, 0, W, H);
      var opGeral = 0.72 * entrada;

      ctx.lineWidth = 1;
      for (i = 0; i < nos.length; i++) {
        n = nos[i];
        for (j = i + 1; j < nos.length; j++) {
          m = nos[j];
          var dx = n.x - m.x, dy = n.y - m.y, d2 = dx * dx + dy * dy;
          if (d2 > DIST * DIST) continue;
          var d = Math.sqrt(d2);
          var a = (1 - d / DIST);
          var prof = 0.22 + 0.78 * Math.pow(((n.y + m.y) / 2) / H, 1.15);
          a = a * a * 0.78 * prof * opGeral;
          if (a < 0.012) continue;
          ctx.strokeStyle = rgba(a);
          ctx.beginPath(); ctx.moveTo(n.x, n.y); ctx.lineTo(m.x, m.y); ctx.stroke();
        }
      }

      var ph = agora / 1000;
      for (i = 0; i < nos.length; i++) {
        n = nos[i];
        var pulso = 0.68 + 0.32 * Math.sin(ph * n.f + i);
        var prof2 = 0.25 + 0.75 * Math.pow(n.y / H, 1.15);
        var a2 = n.b * pulso * prof2 * opGeral;
        ctx.fillStyle = rgba(Math.min(1, a2));
        ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, 6.2832); ctx.fill();
        if (n.r > 2.4) {
          ctx.fillStyle = rgba(a2 * 0.13);
          ctx.beginPath(); ctx.arc(n.x, n.y, n.r * 4.2, 0, 6.2832); ctx.fill();
        }
      }

      if (vel > 0.02) {
        for (var k = 0; k < pulsos.length; k++) {
          var P = pulsos[k];
          var A = nos[P.a % nos.length], B = nos[P.b % nos.length];
          if (!A || !B) continue;
          var dd = Math.hypot(A.x - B.x, A.y - B.y);
          if (dd > DIST * 1.15 || P.p >= 1) {
            P.a = (Math.random() * nos.length) | 0;
            var cand = [];
            for (j = 0; j < nos.length; j++) {
              if (j === P.a) continue;
              if (Math.hypot(nos[P.a].x - nos[j].x, nos[P.a].y - nos[j].y) < DIST) cand.push(j);
            }
            if (!cand.length) continue;
            P.b = cand[(Math.random() * cand.length) | 0]; P.p = 0;
            A = nos[P.a]; B = nos[P.b];
          }
          P.p += P.v * vel * 16;
          var x = A.x + (B.x - A.x) * P.p, y = A.y + (B.y - A.y) * P.p;
          var g = ctx.createRadialGradient(x, y, 0, x, y, 16);
          g.addColorStop(0, rgba(0.85 * vel * entrada)); g.addColorStop(1, rgba(0));
          ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, 16, 0, 6.2832); ctx.fill();
          ctx.fillStyle = 'rgba(255,255,255,' + (0.75 * vel * entrada) + ')';
          ctx.beginPath(); ctx.arc(x, y, 1.9, 0, 6.2832); ctx.fill();
        }
      }

      if (t < MOV + FREIO + 80) raf = requestAnimationFrame(quadro);
      else raf = null;
    }

    function tocar() {
      if (raf) cancelAnimationFrame(raf);
      medir(); semear();
      if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        t0 = performance.now() - (MOV + FREIO); quadro(performance.now()); return;
      }
      t0 = performance.now(); raf = requestAnimationFrame(quadro);
    }
    return { tocar: tocar };
  }

  function iniciar() {
    var canvas = document.querySelector('.hero-malha__canvas');
    if (!canvas) return;
    var inst = criar(canvas);
    inst.tocar();
    var deb;
    window.addEventListener('resize', function () {
      clearTimeout(deb); deb = setTimeout(inst.tocar, 220);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciar);
  } else {
    iniciar();
  }
})();
