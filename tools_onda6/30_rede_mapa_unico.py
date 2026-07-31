# -*- coding: utf-8 -*-
"""
30_rede_mapa_unico.py — onda 9: "Nossa rede" com UM mapa-mundi so.

Uso:  python tools_onda6/30_rede_mapa_unico.py <raiz-que-contem-public>

Substitui o desenho da onda 7 (mapa-mundi + inset ampliado da Europa), que o
Mario rejeitou. Agora e um mapa unico com:

  - um pin por parceiro (6, lidos de src/data/network.json — so leitura);
  - cartao ao passar o mouse no pin, com nome, cidade/pais e link para o site do
    parceiro. O cartao e "hoveravel": encosta na borda do pin, sem vao, entao da
    para levar o mouse do pin ate o link sem ele sumir. Em toque, o tap abre e o
    tap fora fecha;
  - separacao minima entre pins vizinhos (Londres tem DOIS parceiros no mesmo
    endereco): um afastamento iterativo empurra os pins ate ficarem a MIN_SEP
    unidades um do outro — deslocamento de poucos pixels, so o suficiente para
    todos ficarem clicaveis. A identificacao fica por conta do cartao;
  - lista dos parceiros abaixo do mapa; passar o mouse num item destaca o pin.

NENHUMA mencao a escritorio da propria Mirow — nem marcador, nem legenda, nem
nota de rodape do mapa (decisao Mario 30/07). O script 21 (onda 7) desenhava um
marcador da Mirow no Sudeste do Brasil e citava Rio e Sao Paulo na nota; isso sai.

Relacao com o 21_pagina_nossa_rede.py
-------------------------------------
O 21 continua sendo a fonte dos contornos dos continentes (importados aqui por
caminho, porque o nome do modulo comeca com digito). Quanto a PAGINA, o 30
manda: reescreve o <main> inteiro e regrava o bloco de CSS na MESMA chave
("rede"), entao rodar 21 e depois 30 deixa exatamente o resultado do 30.

O "casco" da pagina (head, barra superior, rodape) sai da pagina de
Reconhecimentos do mesmo idioma — mesmo criterio do 21, para herdar o tema antigo.

Idempotente: regera as 3 paginas e o JS por completo; a 2a execucao nao muda nada.
"""
import importlib.util
import io
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import (base_prefix, escrever_bloco_css, garantir_link_css,  # noqa: E402
                        gravar, ler, resolve_public)

AQUI = os.path.dirname(os.path.abspath(__file__))


def _importar_21():
    """Carrega 21_pagina_nossa_rede.py (nome comeca com digito -> import por caminho)."""
    caminho = os.path.join(AQUI, "21_pagina_nossa_rede.py")
    spec = importlib.util.spec_from_file_location("onda7_rede21", caminho)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R21 = _importar_21()
CONTINENTES = R21.CONTINENTES
PARCEIROS_FALLBACK = R21.PARCEIROS_FALLBACK
LOC_DE = R21.LOC_DE
BANNER = R21.BANNER

# nome do parceiro -> (lat, lon). O IMP atua em 4 paises; o pin fica em Viena e
# o cartao lista todos.
COORD = {
    "Akya": (19.43, -99.13),
    "Batten & Company": (51.23, 6.78),
    "IMP Consulting": (48.21, 16.37),
    "Portas Consulting": (51.51, -0.13),
    "PSE Consulting": (51.51, -0.13),
    "Undconsorten": (52.52, 13.40),
}

# ------------------------------------------------------- textos por idioma

IDIOMAS = {
    "pt": {
        "slug": "pt/sobre-nos/nossa-rede/",
        "shell": "pt/sobre-nos/reconhecimentos/index.html",
        "title": u"Nossa Rede - Mirow",
        "h1": u"Nossa Rede",
        "sub": u"Somos parte de uma rede internacional de consultorias independentes "
               u"— cada uma referência no seu mercado",
        "mapa_titulo": u"Onde estão nossos parceiros",
        "mapa_nota": u"Passe o mouse — ou toque, no celular — em cada marcador para "
                     u"ver o parceiro e o site dele",
        "legenda_parceiros": u"Parceiros da rede",
        "lista_titulo": u"Os parceiros",
        "visitar": u"Visitar site",
        "aria_mapa": u"Mapa-múndi com a localização dos parceiros da rede",
        "og_locale": "pt_BR",
    },
    "en": {
        "slug": "en/about-us/our-network/",
        "shell": "en/about-us/recognitions/index.html",
        "title": u"Our Network - Mirow",
        "h1": u"Our Network",
        "sub": u"We are part of an international network of independent consulting "
               u"firms — each a reference in its own market",
        "mapa_titulo": u"Where our partners are",
        "mapa_nota": u"Hover over — or tap, on mobile — each marker to see the partner "
                     u"and its website",
        "legenda_parceiros": u"Network partners",
        "lista_titulo": u"The partners",
        "visitar": u"Visit website",
        "aria_mapa": u"World map showing where the network partners are located",
        "og_locale": "en_US",
    },
    "de": {
        "slug": "de/ueber-uns/unser-netzwerk/",
        "shell": "de/ueber-uns/anerkennungen/index.html",
        "title": u"Unser Netzwerk - Mirow",
        "h1": u"Unser Netzwerk",
        "sub": u"Wir sind Teil eines internationalen Netzwerks unabhängiger "
               u"Beratungen — jede eine Referenz in ihrem Markt",
        "mapa_titulo": u"Wo unsere Partner sind",
        "mapa_nota": u"Fahren Sie mit der Maus über einen Marker — oder tippen Sie am "
                     u"Handy darauf —, um den Partner und seine Website zu sehen",
        "legenda_parceiros": u"Netzwerkpartner",
        "lista_titulo": u"Die Partner",
        "visitar": u"Website besuchen",
        "aria_mapa": u"Weltkarte mit den Standorten der Netzwerkpartner",
        "og_locale": "de_DE",
    },
}

# ------------------------------------------------------------------ mapa

MAPA_W, MAPA_H = 1000.0, 460.0
LAT_TOPO, LAT_BASE = 80.0, -58.0
# Distancia minima entre centros de pins, em unidades do viewBox. Calibrada
# olhando o render: a 1400px de tela o mapa sai com ~1160px, ou seja ~1,16px por
# unidade; com o pin de 24px, 28 unidades (~32px) deixam ~8px de folga entre as
# bordas. Menos do que isso e os halos se fundem num borrao unico na Europa.
MIN_SEP = 28.0

JS_REL = "wp-content/uploads/2026/07/onda6/onda9-rede.js"


def proj(lat, lon):
    x = (lon + 180.0) / 360.0 * MAPA_W
    y = (LAT_TOPO - lat) / (LAT_TOPO - LAT_BASE) * MAPA_H
    return x, y


def poligono(pontos):
    return " ".join("%s,%s" % (round(x, 1), round(y, 1))
                    for x, y in (proj(la, lo) for la, lo in pontos))


def afastar(pontos):
    """Empurra pins que ficariam a menos de MIN_SEP um do outro.

    Londres tem dois parceiros no MESMO endereco (Portas e PSE) e Dusseldorf,
    Berlim e Viena caem a ~17-19 unidades de distancia. O afastamento e
    iterativo e simetrico: cada par colidindo se separa metade para cada lado,
    ate ninguem mais colidir. Sai um deslocamento de poucos pixels — o cartao
    de hover e que identifica quem e quem.

    `pontos`: lista de [x, y]. Devolve nova lista, na mesma ordem.
    """
    p = [[x, y] for x, y in pontos]
    for _passo in range(400):
        moveu = False
        for i in range(len(p)):
            for j in range(i + 1, len(p)):
                dx = p[j][0] - p[i][0]
                dy = p[j][1] - p[i][1]
                d = math.hypot(dx, dy)
                if d >= MIN_SEP:
                    continue
                if d < 1e-6:      # exatamente sobrepostos: separa na horizontal
                    dx, dy, d = 1.0, 0.0, 1.0
                empurra = (MIN_SEP - d) / 2.0
                ux, uy = dx / d, dy / d
                p[i][0] -= ux * empurra
                p[i][1] -= uy * empurra
                p[j][0] += ux * empurra
                p[j][1] += uy * empurra
                moveu = True
        if not moveu:
            break
    return [(round(x, 2), round(y, 2)) for x, y in p]


def desenhar_mapa(aria):
    """SVG autocontido do mapa-mundi (so o fundo: os pins sao HTML por cima)."""
    p = ['<svg class="rede-mapa__svg" viewBox="0 0 %d %d" '
         'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="%s">'
         % (MAPA_W, MAPA_H, aria)]
    for lat in range(-40, 81, 20):
        _x, y = proj(lat, 0)
        p.append('<line class="rede-mapa__grade" x1="0" y1="%s" x2="%d" y2="%s"/>'
                 % (round(y, 1), MAPA_W, round(y, 1)))
    for lon in range(-150, 181, 30):
        x, _y = proj(0, lon)
        p.append('<line class="rede-mapa__grade" x1="%s" y1="0" x2="%s" y2="%d"/>'
                 % (round(x, 1), round(x, 1), MAPA_H))
    for nome, pts in CONTINENTES.items():
        p.append('<polygon class="rede-mapa__terra" data-terra="%s" points="%s"/>'
                 % (nome, poligono(pts)))
    p.append('</svg>')
    return "".join(p)


# ------------------------------------------------------------------ css

CSS = u"""/* onda9 — pagina "Nossa rede": UM mapa-mundi + pins com cartao no hover */
/* fundo navy proprio: o wrap-gradient do tema clareia ate #A2BAE4 embaixo, e a
   pagina e longa o suficiente para o texto claro sumir na parte de baixo */
.rede{background:#020E66;padding:80px 0 100px}
.rede__titulo{color:var(--whiteColor,#fff);font-family:var(--fontFamily),Arial,sans-serif;
  font-size:30px;font-weight:700;line-height:130%;margin:0 0 24px}
.rede__eyebrow{color:#00ADEC;font-family:var(--fontFamily),Arial,sans-serif;
  font-size:14px;font-weight:800;letter-spacing:.5em;text-transform:uppercase;
  margin:0 0 12px}
.rede-mapa{margin:0 0 70px}
.rede-mapa__box{background:rgba(255,255,255,.05);border:1px solid rgba(170,213,232,.35);
  padding:20px}
/* o palco tem a MESMA proporcao do viewBox (1000x460), entao os pins podem ser
   posicionados em % e acompanham o mapa em qualquer largura de tela */
.rede-mapa__palco{position:relative}
.rede-mapa__svg{display:block;width:100%;height:auto}
.rede-mapa__grade{stroke:rgba(170,213,232,.14);stroke-width:1}
.rede-mapa__terra{fill:#0E41A7;stroke:#AAD5E8;stroke-width:1.2;stroke-linejoin:round;
  fill-opacity:.6}

/* --- pins (HTML por cima do SVG) --- */
.rede-pin{position:absolute;width:0;height:0;z-index:10}
.rede-pin__botao{position:absolute;left:-12px;top:-12px;width:24px;height:24px;
  padding:0;border:1px solid #020E66;border-radius:50%;background:#00ADEC;color:#020E66;
  cursor:pointer;font-family:var(--fontFamily),Arial,sans-serif;font-size:12px;
  font-weight:800;line-height:22px;text-align:center;
  box-shadow:0 0 0 4px rgba(0,173,236,.25);
  transition:transform .15s ease,box-shadow .15s ease,background .15s ease}
.rede-pin__botao:hover,.rede-pin__botao:focus-visible{outline:0;background:#fff;
  box-shadow:0 0 0 7px rgba(0,173,236,.4)}
.rede-pin.is-realce .rede-pin__botao{background:#fff;transform:scale(1.2);
  box-shadow:0 0 0 8px rgba(0,173,236,.45)}
/* o cartao encosta na borda de baixo do botao (top:15px = raio do botao): sem
   vao, o mouse vai do pin ate o link sem o cartao sumir */
.rede-pin__card{position:absolute;left:50%;top:12px;width:270px;
  transform:translateX(-50%);padding:14px 0 0;opacity:0;visibility:hidden;
  pointer-events:none;transition:opacity .15s ease}
.rede-pin__card-corpo{background:#020E66;border:1px solid #00ADEC;
  box-shadow:0 12px 30px rgba(0,0,0,.45);padding:16px 18px}
.rede-pin:hover,.rede-pin:focus-within,.rede-pin.is-aberto{z-index:40}
.rede-pin:hover .rede-pin__card,.rede-pin:focus-within .rede-pin__card,
.rede-pin.is-aberto .rede-pin__card{opacity:1;visibility:visible;pointer-events:auto}
.rede-pin__nome{color:var(--whiteColor,#fff);font-family:var(--fontFamily),Arial,sans-serif;
  font-size:18px;font-weight:700;line-height:130%;margin:0 0 6px}
.rede-pin__local{color:#AAD5E8;font-family:var(--fontFamily),Arial,sans-serif;
  font-size:14px;line-height:140%;margin:0 0 10px}
.rede-pin__desc{color:rgba(255,255,255,.85);font-family:var(--fontFamily),Arial,sans-serif;
  font-size:14px;line-height:140%;margin:0 0 10px}
.rede-pin__link{display:inline-block;color:#00ADEC;
  font-family:var(--fontFamily),Arial,sans-serif;font-size:14px;font-weight:700;
  text-decoration:none}
.rede-pin__link:hover,.rede-pin__link:focus{color:#fff;text-decoration:underline}
/* pins colados na borda direita do mapa jogariam o cartao para fora */
.rede-pin--esq .rede-pin__card{left:0;transform:none}
.rede-pin--dir .rede-pin__card{left:auto;right:0;transform:none}

.rede-mapa__legenda{display:flex;flex-wrap:wrap;gap:24px;margin:18px 0 0;padding:0;
  list-style:none;color:var(--whiteColor,#fff);font-family:var(--fontFamily),Arial,sans-serif;
  font-size:15px}
.rede-mapa__legenda li{display:flex;align-items:center;gap:10px}
.rede-mapa__chave{width:16px;height:16px;border-radius:50%;flex:none;display:inline-block;
  background:#00ADEC}
.rede-mapa__nota{color:#AAD5E8;font-family:var(--fontFamily),Arial,sans-serif;
  font-size:14px;margin:12px 0 0}

.rede-lista{display:flex;flex-wrap:wrap;gap:16px;margin:0;padding:0;list-style:none}
.rede-lista__item{flex:1 1 300px;background:rgba(255,255,255,.06);
  border:1px solid rgba(170,213,232,.3);padding:24px;display:flex;
  flex-direction:column;gap:8px;transition:border-color .15s ease,background .15s ease}
.rede-lista__item:hover{background:rgba(255,255,255,.1);border-color:#00ADEC}
.rede-lista__num{display:inline-flex;align-items:center;justify-content:center;
  width:30px;height:30px;border-radius:50%;background:#00ADEC;color:#020E66;
  font-family:var(--fontFamily),Arial,sans-serif;font-weight:800;font-size:14px}
.rede-lista__nome{color:var(--whiteColor,#fff);font-family:var(--fontFamily),Arial,sans-serif;
  font-size:22px;font-weight:700;margin:0}
.rede-lista__local{color:#AAD5E8;font-family:var(--fontFamily),Arial,sans-serif;
  font-size:15px;margin:0}
.rede-lista__link{color:#00ADEC;font-family:var(--fontFamily),Arial,sans-serif;
  font-size:15px;font-weight:700;text-decoration:none;margin-top:auto}
.rede-lista__link:hover{color:#fff}
@media only screen and (max-width: 991px){
  .rede-mapa__box{padding:10px}
  /* no celular o mapa fica com ~340px de largura: os pins da Europa encostam
     mesmo assim. A lista abaixo do mapa e que cumpre o papel de leitura la. */
  .rede-pin__botao{left:-11px;top:-11px;width:22px;height:22px;line-height:20px;
    font-size:11px;box-shadow:0 0 0 3px rgba(0,173,236,.25)}
  .rede-pin__card{width:230px;top:11px}
  .rede-lista__item{flex:1 1 100%}
}
"""

# ------------------------------------------------------------------- js

JS = u"""/* onda9 — pagina "Nossa rede": toque nos pins + realce cruzado com a lista.
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
"""


# ------------------------------------------------------------- montagem

def carregar_parceiros(raiz):
    p = os.path.join(raiz, "src", "data", "network.json")
    if os.path.exists(p):
        import json
        with io.open(p, encoding="utf-8") as f:
            return json.load(f), "src/data/network.json"
    return PARCEIROS_FALLBACK, "copia embutida no script"


def local(parceiro, idioma):
    if idioma == "de":
        return LOC_DE.get(parceiro["name"], parceiro["location"].get("en", ""))
    loc = parceiro["location"]
    return loc.get(idioma) or loc.get("en", "")


def descricao(parceiro, idioma):
    """Linha de descricao, se o network.json trouxer uma. Nao inventamos texto."""
    d = parceiro.get("description")
    if isinstance(d, dict):
        return d.get(idioma) or d.get("en") or ""
    return d or ""


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def monta_main(idioma, txt, parceiros, prefix):
    brutos = [proj(*COORD.get(p["name"], (0.0, 0.0))) for p in parceiros]
    posicoes = afastar(brutos)

    pins = []
    itens = []
    for n, (p, (x, y)) in enumerate(zip(parceiros, posicoes), start=1):
        nome = esc(p["name"])
        loc = esc(local(p, idioma))
        desc = esc(descricao(p, idioma))
        borda = ""
        if x < 150:
            borda = " rede-pin--esq"
        elif x > MAPA_W - 150:
            borda = " rede-pin--dir"
        pins.append(
            '<div class="rede-pin%(borda)s" data-parceiro="%(n)d" '
            'style="left:%(px).3f%%;top:%(py).3f%%">'
            '<button class="rede-pin__botao" type="button" aria-expanded="false" '
            'aria-label="%(nome)s — %(loc)s">%(n)d</button>'
            '<div class="rede-pin__card">'
            '<div class="rede-pin__card-corpo">'
            '<p class="rede-pin__nome">%(nome)s</p>'
            '<p class="rede-pin__local">%(loc)s</p>'
            '%(desc)s'
            '<a class="rede-pin__link" href="%(url)s" target="_blank" rel="noopener">'
            '%(visitar)s &rarr;</a>'
            '</div></div></div>'
            % {"borda": borda, "n": n, "px": x / MAPA_W * 100.0,
               "py": y / MAPA_H * 100.0, "nome": nome, "loc": loc,
               "desc": ('<p class="rede-pin__desc">%s</p>' % desc) if desc else "",
               "url": p["url"], "visitar": txt["visitar"]})
        itens.append(
            '<li class="rede-lista__item" data-parceiro="%d" data-aos="fade-up">'
            '<span class="rede-lista__num">%d</span>'
            '<h3 class="rede-lista__nome">%s</h3>'
            '<p class="rede-lista__local">%s</p>'
            '%s'
            '<a class="rede-lista__link" href="%s" target="_blank" rel="noopener">'
            '%s &rarr;</a></li>'
            % (n, n, nome, loc,
               ('<p class="rede-lista__local">%s</p>' % desc) if desc else "",
               p["url"], txt["visitar"]))

    return (
        '<main class=""><div class="page-our-network">\n'
        '<section class="internal-banner" style="background-image:url(\'%(prefix)s%(banner)s\');">\n'
        '    <div class="container">\n        <div class="row">\n'
        '            <div class="col">\n'
        '                <h1 class="internal-banner__title" data-aos="fade-right">%(h1)s</h1>\n'
        '                <h2 class="internal-banner__subtitle" data-aos="fade-right">%(sub)s</h2>\n'
        '                <div class="internal-banner__text"></div>\n'
        '            </div>\n        </div>\n    </div>\n</section>\n'
        '<section class="rede" id="mainContent">\n'
        '    <div class="container">\n'
        '        <div class="row"><div class="col">\n'
        '            <div class="rede-mapa" data-aos="fade-up">\n'
        '              <p class="rede__eyebrow">%(h1)s</p>\n'
        '              <h2 class="rede__titulo">%(mapa_titulo)s</h2>\n'
        '              <div class="rede-mapa__box">\n'
        '                <div class="rede-mapa__palco">%(mapa)s'
        '<div class="rede-mapa__pins">%(pins)s</div></div>\n'
        '              </div>\n'
        '              <ul class="rede-mapa__legenda">'
        '<li><span class="rede-mapa__chave"></span>%(leg_p)s</li></ul>\n'
        '              <p class="rede-mapa__nota">%(nota)s</p>\n'
        '            </div>\n'
        '            <h2 class="rede__titulo" data-aos="fade-up">%(lista_titulo)s</h2>\n'
        '            <ul class="rede-lista">%(itens)s</ul>\n'
        '        </div></div>\n'
        '    </div>\n</section>\n'
        '</div></main>'
        % {"prefix": prefix, "banner": BANNER, "h1": txt["h1"], "sub": txt["sub"],
           "mapa_titulo": txt["mapa_titulo"], "mapa": desenhar_mapa(txt["aria_mapa"]),
           "pins": "".join(pins), "leg_p": txt["legenda_parceiros"],
           "nota": txt["mapa_nota"], "lista_titulo": txt["lista_titulo"],
           "itens": "".join(itens)}
    )


def garantir_script(html, prefix):
    if "onda9-rede" in html:
        return html
    tag = '<script src="%s%s"></script>\n' % (prefix, JS_REL)
    return html.replace("</body>", tag + "</body>", 1)


def preservar_versao(html, antigo):
    """Reaplica o ?v=<N> que o 27_cache_busting.py ja tinha carimbado.

    A pagina e reconstruida a partir do casco (Reconhecimentos), entao o
    <script> do onda9-rede.js entra sem query. Sem isto, a cada rodada o 30
    tiraria o carimbo e o 27 o poria de volta — a sequencia da onda nunca
    convergiria e os dois scripts ficariam brigando pelo mesmo arquivo.
    """
    for asset in (JS_REL, "wp-content/uploads/2026/07/onda6/onda6.css"):
        m = re.search(re.escape(asset) + r"\?v=(\d+)", antigo)
        if not m:
            continue
        html = re.sub(re.escape(asset) + r"(\?v=\d+)?",
                      asset + "?v=" + m.group(1), html)
    return html


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    raiz = os.path.abspath(sys.argv[1])
    pub = resolve_public(raiz)
    if os.path.basename(raiz) == "public":
        raiz = os.path.dirname(raiz)

    parceiros, origem = carregar_parceiros(raiz)
    print("parceiros: %d (fonte: %s)" % (len(parceiros), origem))
    faltando = [p["name"] for p in parceiros if p["name"] not in COORD]
    if faltando:
        print("AVISO: sem coordenada, plotados em (0,0): %s" % faltando)

    # bloco de CSS: MESMA chave "rede" da onda 7, para o 30 substituir o 21
    if escrever_bloco_css(pub, "rede", CSS, onda="onda9"):
        print("css onda9:rede gravado")
    else:
        print("css onda9:rede ja atualizado")
    # o bloco antigo (onda7:rede) fica obsoleto: remover para nao brigar
    css_path = os.path.join(pub, "wp-content", "uploads", "2026", "07", "onda6", "onda6.css")
    if os.path.exists(css_path):
        atual = ler(css_path)
        novo = re.sub(re.escape("/* onda7:rede:ini */") + r".*?"
                      + re.escape("/* onda7:rede:fim */") + r"\n?", "", atual, flags=re.S)
        if novo != atual:
            with io.open(css_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(novo)
            print("bloco onda7:rede removido (substituido pelo onda9:rede)")

    js_path = os.path.join(pub, JS_REL.replace("/", os.sep))
    os.makedirs(os.path.dirname(js_path), exist_ok=True)
    atual_js = ler(js_path) if os.path.exists(js_path) else None
    if atual_js != JS:
        with io.open(js_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(JS)
        print("js gravado: %s" % JS_REL)
    else:
        print("js ja atualizado")

    escritos = 0
    for idioma, txt in IDIOMAS.items():
        shell_path = os.path.join(pub, txt["shell"].replace("/", os.sep))
        if not os.path.exists(shell_path):
            print("AVISO: casco ausente (%s)" % txt["shell"])
            continue
        html = ler(shell_path)
        prefix = base_prefix(html)

        i = html.find("<main")
        j = html.find("</main>") + len("</main>")
        html = html[:i] + monta_main(idioma, txt, parceiros, prefix) + html[j:]

        html = re.sub(r"<title>.*?</title>", "<title>%s</title>" % txt["title"],
                      html, flags=re.S)
        html = re.sub(r'(<meta property="og:title" content=")[^"]*(")',
                      lambda m: m.group(1) + txt["title"] + m.group(2), html)
        url_pt = prefix + IDIOMAS["pt"]["slug"]
        url_en = prefix + IDIOMAS["en"]["slug"]
        url_de = prefix + IDIOMAS["de"]["slug"]
        minha = prefix + txt["slug"]
        html = re.sub(r'<link rel="canonical"[^>]*>',
                      '<link rel="canonical" href="%s" />' % minha, html)
        html = re.sub(r'(<meta property="og:url" content=")[^"]*(")',
                      lambda m: m.group(1) + minha + m.group(2), html)
        html = re.sub(r'<link rel="alternate" href="[^"]*" hreflang="pt" />',
                      '<link rel="alternate" href="%s" hreflang="pt" />' % url_pt, html)
        html = re.sub(r'<link rel="alternate" href="[^"]*" hreflang="en" />',
                      '<link rel="alternate" href="%s" hreflang="en" />' % url_en, html)
        html = re.sub(r'<link rel="alternate" href="[^"]*" hreflang="de" />',
                      '<link rel="alternate" href="%s" hreflang="de" />' % url_de, html)
        html = re.sub(r'<link rel="alternate" title="(?:oEmbed \((?:JSON|XML)\)|JSON)"[^>]*>',
                      "", html)
        html = re.sub(r'(<body[^>]*class=")[^"]*(")',
                      lambda m: m.group(1) + "wp-singular page page-our-network wp-theme-mirow"
                      + m.group(2), html)
        html = garantir_link_css(html, prefix)
        html = garantir_script(html, prefix)

        destino = os.path.join(pub, txt["slug"].replace("/", os.sep), "index.html")
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        antigo = ler(destino) if os.path.exists(destino) else None
        if antigo:
            html = preservar_versao(html, antigo)
        if antigo != html:
            gravar(destino, html)
            escritos += 1
            print("pagina gravada: %s" % (txt["slug"] + "index.html"))
        else:
            print("sem mudanca: %s" % (txt["slug"] + "index.html"))

    print("\nresumo: %d arquivo(s) alterado(s)" % escritos)


if __name__ == "__main__":
    main()
