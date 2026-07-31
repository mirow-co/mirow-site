# -*- coding: utf-8 -*-
"""
21_pagina_nossa_rede.py — item 7 da lista do Mario (onda 7).

SUPERSEDIDO NA ONDA 9 (2026-07-30): o Mario rejeitou o desenho de dois mapas
(mundi + inset da Europa) descrito abaixo. Quem gera a pagina agora e o
30_rede_mapa_unico.py — um mapa-mundi so, com cartao no hover de cada pin e sem
nenhuma mencao a escritorio da propria Mirow. Este script NAO grava mais nada
(sai logo no inicio do main); continua no repositorio porque o 30 importa daqui
os contornos dos continentes (CONTINENTES), os parceiros de reserva e as
localizacoes em alemao — e porque o historico do desenho antigo tem valor.

Uso:  python tools_onda6/21_pagina_nossa_rede.py <raiz-que-contem-public>

Cria a pagina "Nossa rede" nas 3 linguas, com UM MAPA UNICO mostrando onde estao
os parceiros (decisao Mario 30/07). Ate agora a rede so existia como uma aba do
dropdown "Sobre nos", com links soltos para os sites dos parceiros — nao havia
pagina. O script 17 aponta o menu para estas URLs:

    pt/sobre-nos/nossa-rede/      en/about-us/our-network/      de/ueber-uns/unser-netzwerk/

O mapa e um SVG autocontido, gerado aqui a partir de coordenadas lat/lon
(projecao equirretangular) — sem biblioteca externa, sem tiles, sem requisicao de
rede. Cores do tema: fundo navy, continentes em azul do tema, marcadores em ciano
#00ADEC.

Fonte dos parceiros: src/data/network.json do repositorio (6 parceiros
verificados). O src/ NAO e editado — so lido. Se o arquivo nao existir, cai numa
copia embutida identica.

O "casco" da pagina (head, barra superior, rodape) e copiado da pagina de
Reconhecimentos do MESMO idioma, para herdar exatamente o tema antigo; so o
<main>, o <title>/<canonical>/hreflang/og e as classes do <body> mudam.

Idempotente: regera as 3 paginas por completo a cada execucao.
"""
# Depois da onda 9 este modulo so guarda DADOS e funcoes de desenho (o
# 30_rede_mapa_unico.py importa CONTINENTES, PARCEIROS_FALLBACK, LOC_DE e
# BANNER daqui). Por isso nao ha mais import de _onda7_css nem de re: nada
# aqui grava arquivo.
import io
import json
import os

# ---------------------------------------------------------------- parceiros

PARCEIROS_FALLBACK = [
    {"name": "Akya", "url": "https://akya.com.mx/",
     "location": {"en": "Mexico City, Mexico", "pt": u"Cidade do México, México"}},
    {"name": "Batten & Company", "url": "https://www.batten-company.com/en/",
     "location": {"en": u"Düsseldorf, Germany", "pt": u"Düsseldorf, Alemanha"}},
    {"name": "IMP Consulting", "url": "https://www.impconsulting.com",
     "location": {"en": u"Austria · Germany · Switzerland · Brazil",
                  "pt": u"Áustria · Alemanha · Suíça · Brasil"}},
    {"name": "Portas Consulting", "url": "https://portasconsulting.com/",
     "location": {"en": "London, United Kingdom", "pt": "Londres, Reino Unido"}},
    {"name": "PSE Consulting", "url": "https://pseconsulting.com/",
     "location": {"en": "London, United Kingdom", "pt": "Londres, Reino Unido"}},
    {"name": "Undconsorten", "url": "https://undconsorten.de/",
     "location": {"en": "Berlin, Germany", "pt": "Berlim, Alemanha"}},
]

# nome do parceiro -> (lat, lon) do ponto plotado no mapa
# (o IMP atua em 4 paises; o marcador fica em Viena, e o cartao lista todos)
COORD = {
    "Akya": (19.43, -99.13),
    "Batten & Company": (51.23, 6.78),
    "IMP Consulting": (48.21, 16.37),
    "Portas Consulting": (51.51, -0.13),
    "PSE Consulting": (51.51, -0.13),
    "Undconsorten": (52.52, 13.40),
}

# escritorios da propria Mirow (marcador distinto)
MIROW = [(u"Rio de Janeiro", -22.91, -43.17), (u"São Paulo", -23.55, -46.63)]

LOC_DE = {
    "Akya": u"Mexiko-Stadt, Mexiko",
    "Batten & Company": u"Düsseldorf, Deutschland",
    "IMP Consulting": u"Österreich · Deutschland · Schweiz · Brasilien",
    "Portas Consulting": u"London, Vereinigtes Königreich",
    "PSE Consulting": u"London, Vereinigtes Königreich",
    "Undconsorten": u"Berlin, Deutschland",
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
        "mapa_nota": u"Escritórios da Mirow &amp; Co. no Rio de Janeiro e em São Paulo; "
                     u"parceiros na Europa e no México",
        "legenda_mirow": u"Mirow &amp; Co.",
        "legenda_parceiros": u"Parceiros da rede",
        "lista_titulo": u"Os parceiros",
        "inset": u"Europa",
        "visitar": u"Visitar site",
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
        "mapa_nota": u"Mirow &amp; Co. offices in Rio de Janeiro and São Paulo; "
                     u"partners across Europe and Mexico",
        "legenda_mirow": u"Mirow &amp; Co.",
        "legenda_parceiros": u"Network partners",
        "lista_titulo": u"The partners",
        "inset": u"Europe",
        "visitar": u"Visit website",
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
        "mapa_nota": u"Büros von Mirow &amp; Co. in Rio de Janeiro und São Paulo; "
                     u"Partner in Europa und Mexiko",
        "legenda_mirow": u"Mirow &amp; Co.",
        "legenda_parceiros": u"Netzwerkpartner",
        "lista_titulo": u"Die Partner",
        "inset": u"Europa",
        "visitar": u"Website besuchen",
        "og_locale": "de_DE",
    },
}

BANNER = "wp-content/uploads/2023/03/banner-bg-ourhistory.png"

# ------------------------------------------------------------------ mapa

# Contornos simplificados (listas de (lat, lon)). Mapa decorativo: o objetivo e
# reconhecer os continentes e situar os marcadores, nao precisao cartografica.
CONTINENTES = {
    "america-do-norte": [
        (70, -165), (71, -156), (70, -140), (69, -130), (69, -120), (68, -95),
        (66, -85), (63, -78), (58, -78), (62, -72), (60, -64), (55, -58),
        (50, -56), (45, -61), (43, -66), (41, -70), (35, -76), (30, -81),
        (25, -80), (26, -90), (25, -97), (21, -97), (18, -94), (16, -95),
        (13, -88), (9, -83), (8, -77), (12, -84), (16, -90), (20, -96),
        (23, -106), (25, -109), (28, -114), (32, -117), (38, -123), (43, -124),
        (48, -125), (55, -131), (58, -138), (60, -145), (59, -152), (62, -166),
        (65, -168),
    ],
    "groenlandia": [
        (83, -33), (81, -20), (76, -19), (70, -22), (65, -40), (70, -53),
        (76, -60), (80, -65), (83, -45),
    ],
    "america-do-sul": [
        (12, -72), (11, -63), (10, -60), (5, -52), (0, -50), (-1, -44),
        (-5, -35), (-13, -38.5), (-23, -41), (-25, -48), (-33, -53), (-38, -57),
        (-42, -63), (-50, -68), (-55, -68), (-53, -71), (-46, -75), (-40, -74),
        (-33, -72), (-23, -70), (-18, -70), (-14, -76), (-6, -81), (-2, -80),
        (1, -79), (7, -77), (9, -76),
    ],
    "africa": [
        (37, -6), (37, 10), (33, 22), (31, 32), (22, 37), (12, 43), (11, 51),
        (2, 42), (-6, 39), (-17, 36), (-26, 33), (-34, 26), (-34, 18),
        (-29, 16), (-23, 14), (-17, 12), (-10, 13), (-5, 12), (0, 9), (4, 9),
        (4, 5), (6, -2), (5, -8), (9, -14), (15, -17), (21, -17), (28, -13),
        (33, -9),
    ],
    "eurasia": [
        (36, -6), (43, -9), (44, -2), (48, -5), (49, 0), (53, 4), (58, 5),
        (58, 11), (56, 13), (60, 18), (63, 21), (66, 24), (70, 28), (69, 33),
        (67, 41), (66, 45), (69, 54), (73, 70), (76, 90), (74, 100), (72, 110),
        (71, 130), (70, 140), (69, 161), (66, 170), (62, 179), (60, 163),
        (59, 155), (54, 142), (46, 142), (43, 135), (39, 128), (35, 126),
        (31, 122), (23, 117), (21, 110), (10, 107), (8, 100), (15, 96),
        (16, 94), (22, 90), (21, 87), (19, 85), (21, 72), (24, 67), (25, 62),
        (26, 57), (22, 60), (17, 55), (13, 43), (20, 39), (25, 36), (31, 35),
        (36, 36), (41, 29), (40, 23), (42, 19), (45, 13), (44, 8), (43, 3),
        (41, 3), (38, -1),
    ],
    "gra-bretanha": [
        (58, -5), (57, -2), (54, -1), (51, 1), (50, -4), (53, -5), (55, -6),
    ],
    "irlanda": [(55, -8), (53, -6), (52, -6), (51, -10), (54, -10)],
    "islandia": [(66, -23), (66, -14), (64, -14), (63, -19), (65, -24)],
    "japao": [
        (45, 142), (43, 145), (41, 141), (36, 141), (34, 136), (33, 131),
        (31, 130), (34, 133), (35, 138), (38, 140), (41, 140), (43, 141),
    ],
    "australia": [
        (-11, 131), (-12, 137), (-16, 141), (-11, 143), (-15, 146), (-20, 149),
        (-25, 153), (-32, 153), (-37, 150), (-38, 145), (-35, 139), (-32, 134),
        (-34, 123), (-35, 118), (-32, 116), (-26, 113), (-22, 114), (-20, 119),
        (-14, 127),
    ],
    "nova-zelandia": [
        (-35, 173), (-38, 178), (-41, 175), (-46, 167), (-47, 168), (-44, 171),
        (-41, 172), (-37, 174),
    ],
    "madagascar": [(-12, 49), (-16, 50), (-25, 47), (-25, 45), (-19, 44), (-14, 48)],
}

MAPA_W, MAPA_H = 1000.0, 460.0
LAT_TOPO, LAT_BASE = 80.0, -58.0

# janela da Europa ampliada num "inset": 5 dos 6 parceiros ficam num raio de
# ~1.500 km e, no mapa-mundi, os marcadores se sobrepoem. O inset resolve isso
# sem depender de interacao (o card impresso/print continua legivel).
EU_LON1, EU_LON2 = -12.0, 22.0
EU_LAT1, EU_LAT2 = 40.0, 60.0
EU_X, EU_Y, EU_W, EU_H = 285.0, 495.0, 430.0, 215.0
SVG_H = 720.0


def proj(lat, lon):
    x = (lon + 180.0) / 360.0 * MAPA_W
    y = (LAT_TOPO - lat) / (LAT_TOPO - LAT_BASE) * MAPA_H
    return round(x, 1), round(y, 1)


def proj_eu(lat, lon):
    x = EU_X + (lon - EU_LON1) / (EU_LON2 - EU_LON1) * EU_W
    y = EU_Y + (EU_LAT2 - lat) / (EU_LAT2 - EU_LAT1) * EU_H
    return round(x, 1), round(y, 1)


def poligono(pontos, projecao):
    return " ".join("%s,%s" % projecao(la, lo) for la, lo in pontos)


def na_europa(lat, lon):
    return EU_LON1 <= lon <= EU_LON2 and EU_LAT1 <= lat <= EU_LAT2


def separa(pontos, projecao, minimo=30.0):
    """Afasta no eixo x marcadores que cairiam praticamente em cima do outro.

    Londres tem dois parceiros no mesmo endereco (Portas e PSE); sem isto, um
    ficaria escondido debaixo do outro.
    """
    saida = []
    for n, nome, lat, lon in pontos:
        x, y = projecao(lat, lon)
        colide = [s for s in saida if abs(s[2] - x) < minimo and abs(s[3] - y) < minimo]
        if colide:
            x = round(x + minimo * len(colide), 1)
        saida.append((n, nome, x, y))
    return saida


def pin(n, nome, x, y, raio=11.0):
    return ('<g class="rede-mapa__pin"><circle class="rede-mapa__halo" cx="%s" cy="%s" '
            'r="%s"/><circle class="rede-mapa__ponto" cx="%s" cy="%s" r="%s"/>'
            '<text class="rede-mapa__num" x="%s" y="%s" text-anchor="middle">%d</text>'
            '<title>%s</title></g>'
            % (x, y, raio * 1.55, x, y, raio, x, round(y + raio * 0.42, 1), n, nome))


def desenhar_mapa(pontos_parceiros, rotulo_inset, aria):
    """SVG autocontido: mapa-mundi + inset ampliado da Europa."""
    p = ['<svg class="rede-mapa__svg" viewBox="0 0 %d %d" '
         'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="%s">'
         % (MAPA_W, SVG_H, aria),
         '<defs><clipPath id="rede-inset-clip"><rect x="%s" y="%s" width="%s" '
         'height="%s"/></clipPath></defs>' % (EU_X, EU_Y, EU_W, EU_H)]

    for lat in range(-40, 81, 20):
        _x, y = proj(lat, 0)
        p.append('<line class="rede-mapa__grade" x1="0" y1="%s" x2="%d" y2="%s"/>'
                 % (y, MAPA_W, y))
    for lon in range(-150, 181, 30):
        x, _y = proj(0, lon)
        p.append('<line class="rede-mapa__grade" x1="%s" y1="0" x2="%s" y2="%d"/>'
                 % (x, x, MAPA_H))
    for nome, pts in CONTINENTES.items():
        p.append('<polygon class="rede-mapa__terra" data-terra="%s" points="%s"/>'
                 % (nome, poligono(pts, proj)))

    # um unico marcador da Mirow no Sudeste do Brasil (Rio e Sao Paulo ficariam
    # a 4 px um do outro e virariam um borrao)
    mx, my = proj((MIROW[0][1] + MIROW[1][1]) / 2, (MIROW[0][2] + MIROW[1][2]) / 2)
    p.append('<circle class="rede-mapa__mirow" cx="%s" cy="%s" r="9"><title>'
             'Mirow &amp; Co. — %s</title></circle>'
             % (mx, my, " / ".join(n for n, _la, _lo in MIROW)))

    fora = [q for q in pontos_parceiros if not na_europa(q[2], q[3])]
    dentro = [q for q in pontos_parceiros if na_europa(q[2], q[3])]
    for n, nome, x, y in separa(fora, proj):
        p.append(pin(n, nome, x, y))

    # moldura da janela da Europa no mapa-mundi + conector ate o inset
    jx1, jy1 = proj(EU_LAT2, EU_LON1)
    jx2, jy2 = proj(EU_LAT1, EU_LON2)
    p.append('<rect class="rede-mapa__janela" x="%s" y="%s" width="%s" height="%s"/>'
             % (jx1, jy1, round(jx2 - jx1, 1), round(jy2 - jy1, 1)))
    p.append('<line class="rede-mapa__conector" x1="%s" y1="%s" x2="%s" y2="%s"/>'
             % (round((jx1 + jx2) / 2, 1), jy2, round(EU_X + EU_W / 2, 1), EU_Y))

    p.append('<rect class="rede-mapa__inset-bg" x="%s" y="%s" width="%s" height="%s"/>'
             % (EU_X, EU_Y, EU_W, EU_H))
    p.append('<g clip-path="url(#rede-inset-clip)">')
    for nome, pts in CONTINENTES.items():
        p.append('<polygon class="rede-mapa__terra" points="%s"/>'
                 % poligono(pts, proj_eu))
    p.append('</g>')
    p.append('<rect class="rede-mapa__inset-borda" x="%s" y="%s" width="%s" height="%s"/>'
             % (EU_X, EU_Y, EU_W, EU_H))
    p.append('<text class="rede-mapa__inset-rotulo" x="%s" y="%s">%s</text>'
             % (EU_X + 12, EU_Y + 24, rotulo_inset))
    for n, nome, x, y in separa(dentro, proj_eu, 34.0):
        p.append(pin(n, nome, x, y, 13.0))

    p.append('</svg>')
    return "".join(p)


CSS = u"""/* onda7 — pagina "Nossa rede": mapa unico + lista de parceiros */
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
.rede-mapa__svg{display:block;width:100%;height:auto}
.rede-mapa__grade{stroke:rgba(170,213,232,.14);stroke-width:1}
.rede-mapa__terra{fill:#0E41A7;stroke:#AAD5E8;stroke-width:1.2;stroke-linejoin:round;
  fill-opacity:.6}
.rede-mapa__mirow{fill:#fff;stroke:#00ADEC;stroke-width:3}
.rede-mapa__halo{fill:#00ADEC;fill-opacity:.22}
.rede-mapa__ponto{fill:#00ADEC}
.rede-mapa__num{fill:#020E66;font-family:var(--fontFamily),Arial,sans-serif;
  font-size:12px;font-weight:800}
.rede-mapa__janela{fill:none;stroke:#00ADEC;stroke-width:1.5;stroke-dasharray:5 4}
.rede-mapa__conector{stroke:#00ADEC;stroke-width:1;stroke-dasharray:5 4;opacity:.6}
.rede-mapa__inset-bg{fill:#020E66;fill-opacity:.92}
.rede-mapa__inset-borda{fill:none;stroke:#00ADEC;stroke-width:1.5}
.rede-mapa__inset-rotulo{fill:#AAD5E8;font-family:var(--fontFamily),Arial,sans-serif;
  font-size:14px;font-weight:800;letter-spacing:.3em;text-transform:uppercase}
.rede-mapa__legenda{display:flex;flex-wrap:wrap;gap:24px;margin:18px 0 0;padding:0;
  list-style:none;color:var(--whiteColor,#fff);font-family:var(--fontFamily),Arial,sans-serif;
  font-size:15px}
.rede-mapa__legenda li{display:flex;align-items:center;gap:10px}
.rede-mapa__chave{width:16px;height:16px;border-radius:50%;flex:none;display:inline-block}
.rede-mapa__chave--mirow{background:#fff;box-shadow:0 0 0 3px #00ADEC inset}
.rede-mapa__chave--parceiro{background:#00ADEC}
.rede-mapa__nota{color:#AAD5E8;font-family:var(--fontFamily),Arial,sans-serif;
  font-size:14px;margin:12px 0 0}

.rede-lista{display:flex;flex-wrap:wrap;gap:16px;margin:0;padding:0;list-style:none}
.rede-lista__item{flex:1 1 300px;background:rgba(255,255,255,.06);
  border:1px solid rgba(170,213,232,.3);padding:24px;display:flex;
  flex-direction:column;gap:8px}
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
  .rede-lista__item{flex:1 1 100%}
}
"""


def carregar_parceiros(raiz):
    p = os.path.join(raiz, "src", "data", "network.json")
    if os.path.exists(p):
        with io.open(p, encoding="utf-8") as f:
            return json.load(f), "src/data/network.json"
    return PARCEIROS_FALLBACK, "copia embutida no script"


def local(parceiro, idioma):
    if idioma == "de":
        return LOC_DE.get(parceiro["name"], parceiro["location"].get("en", ""))
    loc = parceiro["location"]
    return loc.get(idioma) or loc.get("en", "")


def monta_main(idioma, txt, parceiros, prefix):
    pontos = []
    itens = []
    for n, p in enumerate(parceiros, start=1):
        lat, lon = COORD.get(p["name"], (0.0, 0.0))
        pontos.append((n, p["name"], lat, lon))
        itens.append(
            '<li class="rede-lista__item" data-aos="fade-up">'
            '<span class="rede-lista__num">%d</span>'
            '<h3 class="rede-lista__nome">%s</h3>'
            '<p class="rede-lista__local">%s</p>'
            '<a class="rede-lista__link" href="%s" target="_blank" rel="noopener">'
            '%s &rarr;</a></li>'
            % (n, p["name"].replace("&", "&amp;"), local(p, idioma), p["url"],
               txt["visitar"]))

    mapa = desenhar_mapa(pontos, txt["inset"], txt["mapa_titulo"])

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
        '              <div class="rede-mapa__box">%(mapa)s</div>\n'
        '              <ul class="rede-mapa__legenda">'
        '<li><span class="rede-mapa__chave rede-mapa__chave--mirow"></span>%(leg_m)s</li>'
        '<li><span class="rede-mapa__chave rede-mapa__chave--parceiro"></span>%(leg_p)s</li>'
        '</ul>\n'
        '              <p class="rede-mapa__nota">%(nota)s</p>\n'
        '            </div>\n'
        '            <h2 class="rede__titulo" data-aos="fade-up">%(lista_titulo)s</h2>\n'
        '            <ul class="rede-lista">%(itens)s</ul>\n'
        '        </div></div>\n'
        '    </div>\n</section>\n'
        '</div></main>'
        % {"prefix": prefix, "banner": BANNER, "h1": txt["h1"], "sub": txt["sub"],
           "mapa_titulo": txt["mapa_titulo"], "mapa": mapa,
           "leg_m": txt["legenda_mirow"], "leg_p": txt["legenda_parceiros"],
           "nota": txt["mapa_nota"], "lista_titulo": txt["lista_titulo"],
           "itens": "".join(itens)}
    )


def main():
    # Onda 9: a pagina passou a ser gerada pelo 30_rede_mapa_unico.py. Rodar os
    # dois em sequencia faria um sobrescrever o outro a cada execucao — a
    # sequencia da onda nunca convergiria. O corpo antigo (montagem do <main>
    # com o inset da Europa e o marcador dos escritorios) saiu daqui; esta no
    # historico do git, no commit anterior a este.
    print("21_pagina_nossa_rede.py: SUPERSEDIDO pelo 30_rede_mapa_unico.py "
          "(onda 9) - nada a fazer")


if __name__ == "__main__":
    main()
