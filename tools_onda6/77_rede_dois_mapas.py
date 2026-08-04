# -*- coding: utf-8 -*-
"""77 — onda 21, S-82 (issue #140): Nossa Rede com dois mapas, logo no hover e
lista de parceiros mais viva.

Uso:
    python tools_onda6/77_rede_dois_mapas.py <raiz-que-contem-public>
    python tools_onda6/77_rede_dois_mapas.py <raiz> --sem-download

Pedido do Mario: "nossa rede nao ficou nada bom. eu queria os logos de cada
parceiro no mapa, de forma que apareca quando eu passar o mouse em cima. se voce
precisar desconectar os dois mapas para dar mais zoom a cada um deles
separadamente, faca-o. estao faltando parceiros, nao tinha um no chile (Virtus?).
essa lista os parceiros nao ficou boa nao. quero que essa pagina seja mais
dinamica, criativa."

O QUE ESTE SCRIPT FAZ
---------------------
Roda DEPOIS do 30_rede_mapa_unico.py (que gera a pagina inteira) e substitui a
<section class="rede"> por uma versao nova:
  1. DOIS mapas com janela propria (bbox) — Americas e Europa. O mapa-mundi unico
     da onda 9 amontoava 4 dos 6 parceiros num quadrado de ~30x20 px sobre a
     Europa; com bbox por regiao cada um respira, sem precisar afastar pin.
  2. O cartao de hover mostra o LOGO do parceiro. O logo e baixado UMA VEZ do
     dominio do proprio parceiro (favicon 128px) para
     public/wp-content/uploads/2026/08/rede/ — a pagina publicada nao faz nenhuma
     chamada externa.
  3. A lista de parceiros deixa de ser cartao chapado: logo + nome + local, barra
     ciano que cresce no hover, elevacao, e o numero casando com o pin do mapa.

NAO FEITO — depende do Mario (registrado na issue #140)
------------------------------------------------------
(a) PARCEIROS QUE FALTAM. A lista publicada tem 6 e vem de `src/data/network.json`.
    O Mario citou um no Chile ("Virtus?"). A pesquisa aponta **Virtus Partners**,
    de Santiago, fundada em 2007 por Marcelo Larraguibel (ex-socio senior da
    McKinsey), com escritorios em Santiago, Madri, Sao Paulo, Buenos Aires e Lima
    — perfil compativel com a rede. NAO foi publicado: afirmar parceria e fato de
    negocio, nao achismo de busca. Confirmado o nome/cidade/site, entra em 1 linha
    no network.json (o COORD abaixo ja tem Santiago pronto).
(b) AUTORIZACAO DE MARCA. Os logos usados sao o favicon do site de cada parceiro.
    Se a rede tiver kit de marca, o ideal e trocar pelos arquivos oficiais.

Idempotente: substitui a secao entre marcadores; download so se faltar o arquivo.
"""
import importlib.util
import io
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import (escrever_bloco_css, gravar, idioma_da_pagina, ler,  # noqa: E402
                        resolve_public)

AQUI = os.path.dirname(os.path.abspath(__file__))


def _r21():
    spec = importlib.util.spec_from_file_location(
        "r21", os.path.join(AQUI, "21_pagina_nossa_rede.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R21 = _r21()
CONTINENTES = R21.CONTINENTES
COORD = dict(R21.COORD)
COORD.setdefault("Virtus Partners", (-33.45, -70.67))   # Santiago, se for confirmado
MIROW = R21.MIROW

MARK_INI = "<!-- onda21:rede-v2 -->"
MARK_FIM = "<!-- /onda21:rede-v2 -->"
LOGO_REL = "wp-content/uploads/2026/08/rede"

# (chave, lon_min, lon_max, lat_min, lat_max, largura, altura)
REGIOES = [
    ("americas", -118.0, -34.0, -40.0, 32.0, 620.0, 530.0),
    ("europa", -22.0, 34.0, 34.0, 62.0, 620.0, 330.0),
]
MIN_SEP = 30.0   # px entre dois pins no mesmo mapa

TXT = {
    "pt": {"americas": u"Américas", "europa": u"Europa",
           "mapa": u"Onde estão nossos parceiros",
           "nota": u"Passe o mouse — ou toque, no celular — em cada marcador para ver o parceiro",
           "lista": u"Os parceiros", "visitar": u"Visitar site",
           "mirow": u"Escritórios Mirow & Co.", "parceiros": u"Parceiros da rede"},
    "en": {"americas": u"Americas", "europa": u"Europe",
           "mapa": u"Where our partners are",
           "nota": u"Hover — or tap, on mobile — each marker to see the partner",
           "lista": u"The partners", "visitar": u"Visit site",
           "mirow": u"Mirow & Co. offices", "parceiros": u"Network partners"},
    "de": {"americas": u"Amerika", "europa": u"Europa",
           "mapa": u"Wo unsere Partner sind",
           "nota": u"Fahren Sie über jeden Marker — oder tippen Sie am Handy — für den Partner",
           "lista": u"Die Partner", "visitar": u"Website besuchen",
           "mirow": u"Büros von Mirow & Co.", "parceiros": u"Netzwerkpartner"},
}

CSS = """/* ---- S-82 (#140): Nossa Rede v2 — dois mapas, logo no hover, lista viva -
   O mapa-mundi unico da onda 9 amontoava 4 dos 6 parceiros sobre a Europa. Aqui
   cada regiao tem janela propria (bbox), o que da zoom sem precisar empurrar pin.
   Tudo no tema da pagina: fundo navy da secao, texto claro, acento ciano. */
.onda21-rede{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin:0 0 44px}
.onda21-mapa{position:relative;background:rgba(255,255,255,.04);
  border:1px solid rgba(170,213,232,.20);padding:14px 14px 10px}
.onda21-mapa__nome{display:block;color:#00ADEC;font-size:13px;font-weight:700;
  letter-spacing:.10em;text-transform:uppercase;margin:0 0 10px}
.onda21-mapa__palco{position:relative}
.onda21-mapa__svg{display:block;width:100%;height:auto}
.onda21-mapa__terra{fill:#12307F;stroke:#AAD5E8;stroke-opacity:.55;stroke-width:.8}
.onda21-mapa__grade{stroke:#AAD5E8;stroke-opacity:.12;stroke-width:.6}
.onda21-mapa__pins{position:absolute;inset:0}

/* o pin */
.onda21-pin{position:absolute;transform:translate(-50%,-50%)}
.onda21-pin__botao{width:26px;height:26px;border-radius:50%;border:2px solid #fff;
  background:#00ADEC;color:#020E66;font-size:12px;font-weight:700;cursor:pointer;
  display:flex;align-items:center;justify-content:center;padding:0;
  box-shadow:0 0 0 4px rgba(0,173,236,.25);transition:transform 180ms ease}
.onda21-pin--mirow .onda21-pin__botao{background:#fff;color:#020E66;
  border-color:#00ADEC;box-shadow:0 0 0 4px rgba(255,255,255,.22)}
.onda21-pin:hover .onda21-pin__botao,
.onda21-pin__botao:focus-visible{transform:scale(1.18)}

/* o cartao com o LOGO do parceiro */
.onda21-pin__card{position:absolute;left:50%;bottom:34px;transform:translateX(-50%);
  width:236px;background:#fff;color:#071C25;padding:14px;text-align:left;
  box-shadow:0 18px 40px rgba(2,14,102,.35);border-bottom:3px solid #00ADEC;
  opacity:0;visibility:hidden;pointer-events:none;transition:opacity 180ms ease;
  z-index:5}
.onda21-pin:hover .onda21-pin__card,
.onda21-pin:focus-within .onda21-pin__card{opacity:1;visibility:visible;
  pointer-events:auto}
.onda21-pin__logo{display:block;max-width:120px;max-height:34px;width:auto;
  height:auto;margin:0 0 10px}
.onda21-pin__nome{color:#020E66;font-size:16px;font-weight:700;margin:0 0 2px}
.onda21-pin__local{color:#7F7F7F;font-size:13px;margin:0 0 8px}
.onda21-pin__link{color:#0A79B8;font-size:13px;font-weight:700;text-decoration:none}
.onda21-pin__link:hover{color:#020E66}
/* pin junto da borda: o cartao encosta para dentro */
.onda21-pin--esq .onda21-pin__card{left:0;transform:none}
.onda21-pin--dir .onda21-pin__card{left:auto;right:0;transform:none}

.onda21-legenda{display:flex;flex-wrap:wrap;gap:8px 22px;list-style:none;
  margin:14px 0 6px;padding:0;color:#AAD5E8;font-size:14px}
.onda21-legenda li{display:flex;align-items:center;gap:8px}
.onda21-legenda__chave{width:11px;height:11px;border-radius:50%;background:#00ADEC;
  display:inline-block}
.onda21-legenda__chave--mirow{background:#fff}
.onda21-nota{color:#AAD5E8;font-size:14px;opacity:.8;margin:0 0 8px}

/* a lista de parceiros — barra que cresce, elevacao, logo */
.onda21-lista{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;
  list-style:none;margin:0;padding:0}
.onda21-lista__item{position:relative;background:rgba(255,255,255,.05);
  border:1px solid rgba(170,213,232,.18);padding:20px 20px 22px;overflow:hidden;
  transition:transform 220ms ease,background 220ms ease}
.onda21-lista__item::before{content:"";position:absolute;left:0;top:0;bottom:0;
  width:3px;background:#00ADEC;transform:scaleY(0);transform-origin:top;
  transition:transform 260ms ease}
.onda21-lista__item:hover{transform:translateY(-4px);background:rgba(255,255,255,.09)}
.onda21-lista__item:hover::before{transform:scaleY(1)}
.onda21-lista__topo{display:flex;align-items:center;justify-content:space-between;
  gap:12px;margin:0 0 12px}
.onda21-lista__logo{max-width:118px;max-height:32px;width:auto;height:auto;
  display:block;background:#fff;padding:4px;border-radius:3px}
.onda21-lista__num{width:26px;height:26px;border-radius:50%;background:#00ADEC;
  color:#020E66;font-size:13px;font-weight:700;display:flex;align-items:center;
  justify-content:center;flex:none}
.onda21-lista__nome{color:#fff;font-size:19px;font-weight:700;margin:0 0 2px}
.onda21-lista__local{color:#AAD5E8;font-size:14px;margin:0 0 12px}
.onda21-lista__link{color:#00ADEC;font-size:14px;font-weight:700;
  text-decoration:none}
.onda21-lista__link:hover{color:#fff}

@media only screen and (max-width: 1200px){
  .onda21-lista{grid-template-columns:repeat(2,1fr)}
}
@media only screen and (max-width: 991px){
  .onda21-rede{grid-template-columns:1fr}
  .onda21-lista{grid-template-columns:1fr}
  .onda21-pin__card{width:200px}
}"""


def proj(lat, lon, reg):
    _k, lo0, lo1, la0, la1, w, hh = reg
    x = (lon - lo0) / (lo1 - lo0) * w
    y = (la1 - lat) / (la1 - la0) * hh
    return x, y


def afastar(pts):
    """Separa pins a menos de MIN_SEP, metade para cada lado, iterativamente."""
    p = [[x, y] for x, y in pts]
    for _passo in range(300):
        moveu = False
        for i in range(len(p)):
            for j in range(i + 1, len(p)):
                dx, dy = p[j][0] - p[i][0], p[j][1] - p[i][1]
                d = (dx * dx + dy * dy) ** 0.5
                if d >= MIN_SEP:
                    continue
                if d < 1e-6:
                    dx, dy, d = 1.0, 0.0, 1.0
                e = (MIN_SEP - d) / 2.0
                ux, uy = dx / d, dy / d
                p[i][0] -= ux * e
                p[i][1] -= uy * e
                p[j][0] += ux * e
                p[j][1] += uy * e
                moveu = True
        if not moveu:
            break
    return [(x, y) for x, y in p]


def dentro(lat, lon, reg):
    _k, lo0, lo1, la0, la1, _w, _h = reg
    return lo0 <= lon <= lo1 and la0 <= lat <= la1


def svg_regiao(reg, aria):
    _k, lo0, lo1, la0, la1, w, hh = reg
    p = ['<svg class="onda21-mapa__svg" viewBox="0 0 %d %d" '
         'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="%s">'
         % (w, hh, aria)]
    passo_lat = 10 if (la1 - la0) <= 40 else 20
    for lat in range(int(la0) - int(la0) % passo_lat, int(la1) + 1, passo_lat):
        _x, y = proj(lat, lo0, reg)
        p.append('<line class="onda21-mapa__grade" x1="0" y1="%.1f" x2="%d" y2="%.1f"/>'
                 % (y, w, y))
    passo_lon = 10 if (lo1 - lo0) <= 60 else 20
    for lon in range(int(lo0) - int(lo0) % passo_lon, int(lo1) + 1, passo_lon):
        x, _y = proj(la0, lon, reg)
        p.append('<line class="onda21-mapa__grade" x1="%.1f" y1="0" x2="%.1f" y2="%d"/>'
                 % (x, x, hh))
    for _nome, pts in CONTINENTES.items():
        pol = " ".join("%.1f,%.1f" % proj(la, lo, reg) for la, lo in pts)
        p.append('<polygon class="onda21-mapa__terra" points="%s"/>' % pol)
    p.append("</svg>")
    return "".join(p)


def dominio(url):
    m = re.match(r'https?://([^/]+)', url)
    return m.group(1).lower() if m else ""


def baixar_logo(pub, dom, baixar=True):
    d = os.path.join(pub, LOGO_REL.replace("/", os.sep))
    nome = dom.replace(":", "_") + ".png"
    p = os.path.join(d, nome)
    if os.path.exists(p) and os.path.getsize(p) > 200:
        return nome
    if not baixar:
        return None
    os.makedirs(d, exist_ok=True)
    url = "https://www.google.com/s2/favicons?domain=%s&sz=128" % dom
    try:
        r = subprocess.run(["curl", "-sSL", "--max-time", "20", "-o", p, url],
                           capture_output=True, text=True)
    except Exception as e:
        print("    erro no curl de %s: %s" % (dom, e))
        return None
    if r.returncode != 0 or not os.path.exists(p) or os.path.getsize(p) < 200:
        if os.path.exists(p):
            os.unlink(p)
        print("    sem logo para %s" % dom)
        return None
    print("    logo baixado: %s" % nome)
    return nome


def secao(pub, idioma, parceiros, prefix, baixar):
    t = TXT.get(idioma, TXT["pt"])
    numero = {p["name"]: i + 1 for i, p in enumerate(parceiros)}
    logos = {}
    for p in parceiros:
        logos[p["name"]] = baixar_logo(pub, dominio(p["url"]), baixar)

    mapas = []
    for reg in REGIOES:
        chave, _lo0, _lo1, _la0, _la1, w, _h = reg
        pins = []
        aqui = [p for p in parceiros
                if dentro(*(COORD.get(p["name"], (0.0, 0.0)) + (reg,)))]
        posic = afastar([proj(*(COORD.get(p["name"], (0.0, 0.0)) + (reg,)))
                         for p in aqui])
        for p, (x, y) in zip(aqui, posic):
            borda = ""
            if x < 130:
                borda = " onda21-pin--esq"
            elif x > w - 130:
                borda = " onda21-pin--dir"
            arq = logos.get(p["name"])
            logo = ('<img class="onda21-pin__logo" src="%s%s/%s" alt="%s">'
                    % (prefix, LOGO_REL, arq, R21.esc(p["name"]) if hasattr(R21, "esc")
                       else p["name"])) if arq else ""
            pins.append(
                '<div class="onda21-pin%s" style="left:%.2f%%;top:%.2f%%">'
                '<button class="onda21-pin__botao" type="button" aria-label="%s">%d</button>'
                '<div class="onda21-pin__card">%s'
                '<p class="onda21-pin__nome">%s</p>'
                '<p class="onda21-pin__local">%s</p>'
                '<a class="onda21-pin__link" href="%s" target="_blank" rel="noopener">'
                '%s &rarr;</a></div></div>'
                % (borda, x / w * 100.0, y / reg[6] * 100.0, p["name"],
                   numero[p["name"]], logo, p["name"],
                   R21.local(p, idioma), p["url"], t["visitar"]))
        for nome, lat, lon in MIROW:
            if not dentro(lat, lon, reg):
                continue
            x, y = proj(lat, lon, reg)
            pins.append(
                '<div class="onda21-pin onda21-pin--mirow" '
                'style="left:%.2f%%;top:%.2f%%">'
                '<button class="onda21-pin__botao" type="button" aria-label="%s">M</button>'
                '<div class="onda21-pin__card">'
                '<p class="onda21-pin__nome">Mirow &amp; Co.</p>'
                '<p class="onda21-pin__local">%s</p></div></div>'
                % (x / w * 100.0, y / reg[6] * 100.0, nome, nome))
        mapas.append('<div class="onda21-mapa" data-aos="fade-up">'
                     '<span class="onda21-mapa__nome">%s</span>'
                     '<div class="onda21-mapa__palco">%s'
                     '<div class="onda21-mapa__pins">%s</div></div></div>'
                     % (t[chave], svg_regiao(reg, t[chave]), "".join(pins)))

    itens = []
    for p in parceiros:
        arq = logos.get(p["name"])
        logo = ('<img class="onda21-lista__logo" src="%s%s/%s" alt="%s">'
                % (prefix, LOGO_REL, arq, p["name"])) if arq else "<span></span>"
        itens.append(
            '<li class="onda21-lista__item" data-aos="fade-up">'
            '<div class="onda21-lista__topo">%s'
            '<span class="onda21-lista__num">%d</span></div>'
            '<h3 class="onda21-lista__nome">%s</h3>'
            '<p class="onda21-lista__local">%s</p>'
            '<a class="onda21-lista__link" href="%s" target="_blank" rel="noopener">'
            '%s &rarr;</a></li>'
            % (logo, numero[p["name"]], p["name"], R21.local(p, idioma),
               p["url"], t["visitar"]))

    return ('%s<section class="rede" id="mainContent"><div class="container">'
            '<div class="row"><div class="col">'
            '<h2 class="rede__titulo">%s</h2>'
            '<p class="onda21-nota">%s</p>'
            '<div class="onda21-rede">%s</div>'
            '<ul class="onda21-legenda">'
            '<li><span class="onda21-legenda__chave"></span>%s</li>'
            '<li><span class="onda21-legenda__chave onda21-legenda__chave--mirow">'
            '</span>%s</li></ul>'
            '<h2 class="rede__titulo">%s</h2>'
            '<ul class="onda21-lista">%s</ul>'
            '</div></div></div></section>%s'
            % (MARK_INI, t["mapa"], t["nota"], "".join(mapas), t["parceiros"],
               t["mirow"], t["lista"], "".join(itens), MARK_FIM))


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    baixar = "--sem-download" not in sys.argv
    raiz = os.path.dirname(pub)

    mudou = escrever_bloco_css(pub, "rede-v2", CSS, onda="onda21")
    print("bloco onda21:rede-v2 %s" % ("gravado" if mudou else "ja estava igual"))

    parceiros, fonte = R21.carregar_parceiros(raiz)
    print("parceiros: %d (fonte: %s)" % (len(parceiros), fonte))
    faltando = [p["name"] for p in parceiros if p["name"] not in COORD]
    if faltando:
        print("  AVISO: sem coordenada, nao entram no mapa: %s" % ", ".join(faltando))

    tocadas = 0
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if n != "index.html":
                continue
            p = os.path.join(dp, n)
            h = ler(p)
            if 'class="page-our-network"' not in h:
                continue
            rel = os.path.relpath(p, pub).replace(os.sep, "/")
            idioma = idioma_da_pagina(h)
            prefix = "/mirow-site/" if "/mirow-site/wp-content/" in h else "/"
            nova = secao(pub, idioma, parceiros, prefix, baixar)

            if MARK_INI in h:
                velha = h[h.index(MARK_INI):h.index(MARK_FIM) + len(MARK_FIM)]
                novo = h.replace(velha, nova, 1)
            else:
                ini = h.find('<section class="rede"')
                if ini < 0:
                    print("  %s: nao achei a secao .rede — NAO alterada" % rel)
                    continue
                fim = h.find("</section>", ini) + len("</section>")
                novo = h[:ini] + nova + h[fim:]
            if novo != h:
                gravar(p, novo)
                tocadas += 1
                print("  %s (%s)" % (rel, idioma))
    print("resumo: %d pagina(s) da rede com os 2 mapas" % tocadas)


if __name__ == "__main__":
    main()
