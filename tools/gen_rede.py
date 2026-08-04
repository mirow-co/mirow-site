# -*- coding: utf-8 -*-
"""gen_rede.py — gera a pagina Nossa Rede do arquivo mestre de parceiros (P3).

Uso:
    python tools/gen_rede.py <raiz-que-contem-public> [--mestre=<caminho.json>] [--dry]

Onda 31 — S-111 a S-116 (issues #169 a #174) e fecha a #140.

POR QUE ESTE ARQUIVO EXISTE
---------------------------
Na onda 21 (S-82) os dois mapas eram SVG desenhado a mao e a posicao de cada pin era
um percentual escrito no HTML (`left:43.17%;top:37.40%`). Deu no que deu: o pin da
PSE, que fica em Londres, caiu no mar — e ninguem tinha como saber, porque nao havia
de onde conferir. O Mario viu a olho.

Aqui existe UMA fonte de verdade para tudo desta pagina:

    08_Site/2026-08-04_rede-parceiros-curadoria.json   (repo PRIVADO)

Nome, cidade, lat/lon, link e arquivo de logo de cada parceiro moram la, confirmados
pelo Andreas (#140). O HTML e GERADO deste arquivo — editar a pagina a mao e violacao
de processo.

COMO OS MAPAS SAO FEITOS
------------------------
* Geometria: `tools_onda6/dados/mapas-ne110m.json`, recorte do **Natural Earth 1:110m**
  (dominio publico), preparado por `tools_onda6/_prep_mapas_ne.py`.
* Projecao: **Mercator**, a mesma que o olho espera de um mapa. Cada mapa tem um
  recorte proprio (bbox em lat/lon) e o viewBox sai com a proporcao EXATA do recorte
  projetado — e por isso que o mapa preenche a caixa inteira (S-114) em vez de sobrar
  faixa vazia.
* Pin: a MESMA funcao de projecao converte lat/lon em x/y (S-116). Se o recorte
  mudar, o pin acompanha; nao ha numero escrito a mao. Dois parceiros na mesma cidade
  (CAA Portas e PSE, ambos em Londres) recebem um afastamento lateral deterministico,
  com a agulha de cada chip continuando a apontar o ponto exato da cidade.
"""
import io
import json
import math
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ_TOOLS = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ_TOOLS, "tools_onda6"))
from _onda7_css import escrever_bloco_css, gravar, ler  # noqa: E402

MESTRE_PADRAO = os.path.join(
    os.path.expanduser("~"), "OneDrive - Mirow", "Mirow & Co", "05_Marketing",
    "05_NovoMarketing", "08_Site", "2026-08-04_rede-parceiros-curadoria.json")
GEOMETRIA = os.path.join(RAIZ_TOOLS, "tools_onda6", "dados", "mapas-ne110m.json")

DIR_LOGOS = "wp-content/uploads/2026/08/rede"

PAGINAS = {
    "pt": "pt/sobre-nos/nossa-rede/index.html",
    "en": "en/about-us/our-network/index.html",
    "de": "de/ueber-uns/unser-netzwerk/index.html",
}

# recortes dos dois mapas (lon_min, lat_min, lon_max, lat_max)
MAPAS = [
    ("americas", (-168.0, -56.0, -33.0, 60.0),
     {"pt": u"Américas", "en": u"Americas", "de": u"Amerika"}),
    ("europa", (-12.0, 34.0, 33.0, 62.0),
     {"pt": u"Europa", "en": u"Europe", "de": u"Europa"}),
]

TEXTOS = {
    "pt": {"titulo": u"Onde estão nossos parceiros",
           "nota": u"Passe o mouse — ou toque, no celular — em cada logo para ver cidade e site",
           "visitar": u"Visitar site &rarr;"},
    "en": {"titulo": u"Where our partners are",
           "nota": u"Hover — or tap, on mobile — each logo to see city and website",
           "visitar": u"Visit website &rarr;"},
    "de": {"titulo": u"Wo unsere Partner sind",
           "nota": u"Fahren Sie mit der Maus über jedes Logo — oder tippen Sie am Handy — "
                   u"für Stadt und Website",
           "visitar": u"Website besuchen &rarr;"},
}

LARGURA_VB = 1000.0        # o viewBox nasce com 1000 de largura; a altura sai do recorte

# --- layout dos chips (S-115/S-116) ---------------------------------------
# O chip nao pode cobrir o chip vizinho: Londres tem DOIS parceiros e Dusseldorf
# fica a um passo. Entao o gerador resolve a colisao aqui, em pixels, sobre uma
# largura de referencia de palco — a mesma proporcao vale em qualquer tela.
PALCO_REF = 580.0          # px: largura tipica do palco no desktop (medida no QA)
CHIP_ALTURA = 42.0         # px: altura do chip (logo de 26px + 8px de padding)
CHIP_LOGO_H = 26.0         # px: altura do logo dentro do chip
CHIP_PAD = 24.0            # px: padding horizontal total do chip
HASTE_BASE = 12.0          # px: haste minima entre o ponto da cidade e o chip
FOLGA = 7.0                # px: respiro exigido entre dois chips
RAIO_MAX = 96.0            # px: o chip nunca fica mais longe que isso do seu ponto


# ------------------------------------------------------------------ projeção

def mercator_y(lat):
    lat = max(min(lat, 84.0), -84.0)
    return math.log(math.tan(math.radians(45.0 + lat / 2.0)))


def projetor(bbox):
    """Devolve (fn, largura, altura) do recorte em Mercator, largura fixa em 1000.

    x e y precisam estar na MESMA unidade (radianos), senao a proporcao do mapa sai
    errada — foi o primeiro bug deste gerador: com x em graus e y em Mercator, a
    altura saiu negativa.
    """
    lon0, lat0, lon1, lat1 = bbox
    x0, x1 = math.radians(lon0), math.radians(lon1)
    y_topo, y_base = mercator_y(lat1), mercator_y(lat0)   # topo = latitude maior
    dx = x1 - x0
    dy = y_topo - y_base                                  # positivo
    escala = LARGURA_VB / dx
    altura = dy * escala

    def fn(lon, lat):
        # y cresce para BAIXO na tela: do topo do recorte para o sul
        return ((math.radians(lon) - x0) * escala,
                (y_topo - mercator_y(lat)) * escala)
    return fn, LARGURA_VB, altura


MIN_PASSO = 1.6      # unidades do viewBox: ponto mais perto que isso nao muda o desenho


def dentro_do_recorte(anel, bbox, folga=8.0):
    """O anel encosta no recorte? Pais totalmente fora nao precisa entrar no arquivo."""
    lon0, lat0, lon1, lat1 = bbox
    xs = [p[0] for p in anel]
    ys = [p[1] for p in anel]
    return not (max(xs) < lon0 - folga or min(xs) > lon1 + folga
                or max(ys) < lat0 - folga or min(ys) > lat1 + folga)


def caminho_svg(geo, fn, altura, bbox):
    """Um <path> unico com os paises que encostam no recorte (subcaminhos); o proprio
    viewBox corta o excedente das bordas. Pontos separados por menos de MIN_PASSO
    unidades sao descartados: na escala de tela nao mudam o contorno."""
    partes = []
    for _nome, aneis in sorted(geo["paises"].items()):
        for anel in aneis:
            if not dentro_do_recorte(anel, bbox):
                continue
            pontos = []
            ux = uy = None
            for lon, lat in anel:
                x, y = fn(lon, lat)
                x = max(min(x, 4 * LARGURA_VB), -3 * LARGURA_VB)
                y = max(min(y, 4 * altura), -3 * altura)
                if ux is not None and abs(x - ux) < MIN_PASSO and abs(y - uy) < MIN_PASSO:
                    continue
                pontos.append("%.1f %.1f" % (x, y))
                ux, uy = x, y
            if len(pontos) < 4:
                continue
            partes.append("M" + "L".join(pontos) + "Z")
    return "".join(partes)


def gravar_svg_do_mapa(pub, chave, w, h, d, dry):
    """O mapa vira ARQUIVO — as 3 linguas usam o mesmo, e o navegador cacheia.
    Inline, os dois paths somavam ~160 KB por pagina."""
    svg = (u'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %.0f %.1f" '
           u'preserveAspectRatio="none" role="img" aria-label="mapa">'
           u'<path d="%s" fill="#AAD5E8" fill-opacity="0.30" stroke="#AAD5E8" '
           u'stroke-opacity="0.55" stroke-width="1.6" stroke-linejoin="round"/></svg>\n'
           % (w, h, d))
    rel = "%s/mapa-%s.svg" % (DIR_LOGOS, chave)
    caminho = os.path.join(pub, rel.replace("/", os.sep))
    atual = ler(caminho) if os.path.exists(caminho) else None
    if atual != svg and not dry:
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with io.open(caminho, "w", encoding="utf-8", newline="\n") as f:
            f.write(svg)
    print("  mapa-%s.svg %s (%.0f KB)"
          % (chave, "igual" if atual == svg else "gravado", len(svg) / 1024.0))
    return rel


# --------------------------------------------------- layout dos chips no mapa

def tamanho_do_logo(pub, arquivo):
    """(largura, altura) do logo, para saber a largura do chip antes de renderizar."""
    caminho = os.path.join(pub, DIR_LOGOS.replace("/", os.sep), arquivo)
    if arquivo.endswith(".svg"):
        t = ler(caminho)
        m = re.search(r'viewBox="([-\d.]+)[ ,]+([-\d.]+)[ ,]+([\d.]+)[ ,]+([\d.]+)"', t)
        if m:
            return float(m.group(3)), float(m.group(4))
        return 100.0, 30.0
    # PNG: le largura/altura do cabecalho IHDR, sem depender de biblioteca
    with io.open(caminho, "rb") as f:
        dados = f.read(33)
    if dados[:8] == b"\x89PNG\r\n\x1a\n":
        import struct
        larg, alt = struct.unpack(">II", dados[16:24])
        return float(larg), float(alt)
    return 100.0, 30.0


def layout_dos_chips(parceiros, fn, w, h, pub):
    """Coloca cada chip no lugar livre mais PROXIMO da sua cidade (S-117).

    A agulha fica sempre na coordenada projetada — o que se move e o chip, ligado
    por uma haste inclinada. A conta e feita em pixels sobre um palco de referencia
    (PALCO_REF) e devolvida em px de deslocamento, entao vale igual em qualquer
    largura de tela. Ordem: de norte para sul, para o resultado ser estavel.

    Por que busca em ANEL e nao escadinha (pedido do Mario em 04/08): a primeira
    versao so tentava posicoes acima do pin e, quando batia, subia um degrau. Com
    quatro parceiros no mesmo canto (Londres x2, Dusseldorf, Berlim) o chip do
    Batten subiu tres degraus e foi parar longe da Alemanha. Agora se testam
    posicoes em volta do ponto, em raio crescente e em 16 direcoes, e vence a
    PRIMEIRA livre — ou seja, a mais perto. O chip pode cair sobre a Franca ou
    sobre o mar; o que importa e a haste apontando a cidade certa.
    """
    palco_w = PALCO_REF
    palco_h = PALCO_REF * (h / w)
    ordenados = sorted(parceiros, key=lambda p: (-p["lat"], p["lon"], p["slug"]))
    postos = []          # retangulos ja ocupados (x0, y0, x1, y1) em px
    saida = []
    for p in ordenados:
        x, y = fn(p["lon"], p["lat"])
        px = palco_w * x / w
        py = palco_h * y / h
        lw, lh = tamanho_do_logo(pub, p["logo"])
        chip_w = CHIP_PAD + CHIP_LOGO_H * (lw / lh)

        # candidatos em anel: raio crescente x 16 direcoes, do mais perto ao mais
        # longe. O primeiro raio ja tira o chip de cima do ponto (senao a agulha
        # fica escondida embaixo do chip).
        candidatos = []
        for raio in [r * 1.0 for r in range(24, int(RAIO_MAX) + 1, 8)]:
            for k in range(16):
                ang = math.radians(90.0 + k * (360.0 / 16))   # comeca para cima
                dx = raio * math.cos(ang)
                dy = -raio * math.sin(ang)                    # dy<0 = acima
                candidatos.append((dx, dy, raio))
        escolhido = None
        for dx, dy, raio in candidatos:
            cx, cy = px + dx, py + dy
            x0, x1 = cx - chip_w / 2, cx + chip_w / 2
            y0, y1 = cy - CHIP_ALTURA / 2, cy + CHIP_ALTURA / 2
            if x0 < 2 or x1 > palco_w - 2 or y0 < 2 or y1 > palco_h - 2:
                continue                                     # nao pode vazar o palco
            bate = any(not (x1 + FOLGA < q[0] or x0 - FOLGA > q[2]
                            or y1 + FOLGA < q[1] or y0 - FOLGA > q[3]) for q in postos)
            if not bate:
                escolhido = (dx, dy, (x0, y0, x1, y1), raio)
                break
        if escolhido is None:      # palco lotado (nao acontece com 6 parceiros)
            dx, dy, raio = 0.0, -(HASTE_BASE + CHIP_ALTURA / 2), HASTE_BASE
            escolhido = (dx, dy, (px - chip_w / 2, py + dy - CHIP_ALTURA / 2,
                                  px + chip_w / 2, py + dy + CHIP_ALTURA / 2), raio)
        dx, dy, rect, raio = escolhido
        postos.append(rect)
        # a haste vai do ponto ate a BORDA do chip (nao ate o centro, senao ela
        # atravessaria o logo)
        comprimento = max(raio - CHIP_ALTURA / 2, 6.0)
        angulo = math.degrees(math.atan2(dx, -dy))   # 0 = para cima
        saida.append((p, {"esq": 100.0 * x / w, "top": 100.0 * y / h,
                          "dx": dx, "dy": dy,
                          "haste": comprimento, "ang": angulo,
                          "raio": raio}))
    return saida


# ------------------------------------------------------------------ HTML

def bloco_rede(mestre, geo, lang, prefixo, pub, dry):
    t = TEXTOS[lang]
    mapas_html = []
    for chave, bbox, nomes in MAPAS:
        fn, w, h = projetor(bbox)
        d = caminho_svg(geo, fn, h, bbox)
        rel_svg = gravar_svg_do_mapa(pub, chave, w, h, d, dry)
        # pins deste mapa, com o chip posicionado SEM colisao (ver layout_dos_chips)
        deste = [p for p in mestre["parceiros"] if p["mapa"] == chave]
        colocados = layout_dos_chips(deste, fn, w, h, pub)
        pins = []
        for p, pos in colocados:
            logo = "%s%s/%s" % (prefixo, DIR_LOGOS, p["logo"])
            if logo.endswith(".svg"):
                logo += "?ver=1"      # sem a query o plugin do tema inlina o SVG
            pins.append(
                u'<div class="onda31-pin" style="left:%.2f%%;top:%.2f%%">'
                u'<span class="onda31-pin__agulha" aria-hidden="true"></span>'
                u'<span class="onda31-pin__haste" aria-hidden="true" '
                u'style="--len:%.1fpx;--ang:%.2fdeg"></span>'
                u'<div class="onda31-pin__corpo" style="--dx:%.1fpx;--dy:%.1fpx">'
                u'<button class="onda31-pin__chip" type="button" aria-label="%s">'
                u'<img src="%s" alt="%s" loading="lazy"></button>'
                u'<div class="onda31-pin__card"><p class="onda31-pin__nome">%s</p>'
                u'<p class="onda31-pin__local">%s</p>'
                u'<a class="onda31-pin__link" href="%s" target="_blank" rel="noopener">%s</a>'
                u'</div></div></div>'
                % (pos["esq"], pos["top"], pos["haste"], pos["ang"], pos["dx"],
                   pos["dy"], p["nome"], logo, p["nome"], p["nome"],
                   p["cidade"][lang], p["site"], t["visitar"]))
        mapas_html.append(
            u'<div class="onda31-mapa" data-aos="fade-up">'
            u'<span class="onda31-mapa__nome">%s</span>'
            u'<div class="onda31-mapa__palco" style="aspect-ratio:%.4f">'
            u'<img class="onda31-mapa__svg" src="%s%s?ver=1" alt="" aria-hidden="true" '
            u'loading="lazy">'
            u'<div class="onda31-mapa__pins">%s</div></div></div>'
            % (nomes[lang], w / h, prefixo, rel_svg, "".join(pins)))

    return (u'<!-- onda31:rede -->'
            u'<section class="rede" id="mainContent"><div class="container"><div class="row">'
            u'<div class="col"><h2 class="rede__titulo">%s</h2>'
            u'<p class="onda31-nota">%s</p>'
            u'<div class="onda31-rede">%s</div>'
            u'</div></div></div></section><!-- /onda31:rede -->'
            % (t["titulo"], t["nota"], "".join(mapas_html)))


CSS = u"""/* ---- S-111 a S-116: a Nossa Rede com mapa de verdade ---------------------
   Mapas: SVG gerado do Natural Earth (dominio publico) em projecao Mercator, um
   recorte por mapa. O `aspect-ratio` de cada palco vem do proprio recorte, entao o
   mapa PREENCHE a caixa (S-114) — antes o SVG da Europa tinha proporcao fixa e
   sobrava faixa vazia.
   Pins: chip branco com o logo do parceiro (S-111/S-115, no lugar do favicon de
   128px) e uma AGULHA que marca o ponto exato da cidade (S-116). O chip pode se
   afastar lateralmente (--desvio) quando dois parceiros dividem a cidade — a agulha
   fica onde a projecao mandou. */
.onda31-rede{display:grid;grid-template-columns:repeat(2,1fr);gap:34px;margin:26px 0 0}
.onda31-mapa__nome{display:block;color:#fff;font-size:15px;font-weight:700;
  letter-spacing:.14em;text-transform:uppercase;margin:0 0 10px}
.onda31-mapa__palco{position:relative;width:100%;
  background:rgba(2,14,102,.28);border:1px solid rgba(170,213,232,.30);border-radius:3px;
  overflow:hidden}
.onda31-mapa__svg{position:absolute;inset:0;width:100%;height:100%;display:block}
.onda31-mapa__pins{position:absolute;inset:0}

.onda31-pin{position:absolute;width:0;height:0}
/* a agulha: 8px de ponto no lugar exato + haste subindo ate o chip */
.onda31-pin__agulha{position:absolute;left:-4px;top:-4px;width:8px;height:8px;
  border-radius:50%;background:#00ADEC;box-shadow:0 0 0 3px rgba(0,173,236,.28)}
/* o chip e CENTRADO no deslocamento que o gerador calculou — pode estar acima,
   ao lado ou abaixo do ponto (S-117), o que importa e ser o lugar livre mais
   proximo da cidade */
.onda31-pin__corpo{position:absolute;left:0;top:0;
  transform:translate(calc(-50% + var(--dx,0px)),calc(-50% + var(--dy,-40px)))}
.onda31-pin__chip{display:block;padding:8px 12px;border:0;cursor:pointer;
  background:#fff;border-radius:4px;box-shadow:0 6px 18px rgba(2,14,102,.34);
  transition:transform 200ms ease,box-shadow 200ms ease}
.onda31-pin__chip img{display:block;height:26px;width:auto;max-width:132px;
  object-fit:contain}
.onda31-pin__chip:hover,.onda31-pin__chip:focus-visible{outline:none;
  transform:translateY(-2px);box-shadow:0 10px 24px rgba(0,173,236,.45)}
/* haste ligando o ponto da cidade ao chip: nasce NO ponto e gira o quanto o
   gerador calculou (atan2 do desvio pelo quanto subiu), entao o chip pode sair do
   eixo sem a linha desgrudar dele */
.onda31-pin__haste{position:absolute;left:0;bottom:0;width:1px;
  height:var(--len,12px);transform-origin:bottom center;
  transform:rotate(var(--ang,0deg));background:rgba(0,173,236,.85)}

.onda31-pin__card{position:absolute;left:50%;bottom:calc(100% + 10px);
  transform:translateX(-50%) translateY(6px);width:230px;padding:14px 16px;
  background:#fff;border-radius:4px;box-shadow:0 16px 34px rgba(2,14,102,.34);
  opacity:0;visibility:hidden;transition:all 220ms ease;z-index:6}
.onda31-pin:hover .onda31-pin__card,
.onda31-pin__chip:focus-visible + .onda31-pin__card,
.onda31-pin__card:hover{opacity:1;visibility:visible;transform:translateX(-50%)}
.onda31-pin__nome{color:#020E66;font-size:16px;font-weight:700;margin:0 0 2px}
.onda31-pin__local{color:#4A4A4A;font-size:14px;margin:0 0 8px}
.onda31-pin__link{color:#00ADEC;font-size:14px;font-weight:700;text-decoration:none}
.onda31-pin__link:hover{text-decoration:underline}
/* o pin com hover sobe na pilha, senao o card fica atras do chip vizinho */
.onda31-pin:hover{z-index:7}

.onda31-nota{color:#fff;opacity:.82;font-size:15px;margin:6px 0 0}

@media only screen and (max-width: 991px){
  .onda31-rede{grid-template-columns:1fr;gap:26px}
  .onda31-pin__chip{padding:6px 9px}
  .onda31-pin__chip img{height:20px;max-width:104px}
  .onda31-pin__card{width:200px}
}"""


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    raiz = os.path.abspath(sys.argv[1])
    pub = raiz if os.path.basename(raiz) == "public" else os.path.join(raiz, "public")
    if not os.path.isdir(pub):
        raise SystemExit(u"não achei public/ em %s" % raiz)
    dry = "--dry" in sys.argv
    mestre_path = MESTRE_PADRAO
    for a in sys.argv[2:]:
        if a.startswith("--mestre="):
            mestre_path = a[len("--mestre="):]
    if not os.path.exists(mestre_path):
        raise SystemExit(u"arquivo mestre não encontrado: %s" % mestre_path)

    with io.open(mestre_path, encoding="utf-8") as f:
        mestre = json.load(f)
    with io.open(GEOMETRIA, encoding="utf-8") as f:
        geo = json.load(f)

    # o logo de cada parceiro liberado TEM de existir — senao o gerador falha alto
    faltando = [p["slug"] for p in mestre["parceiros"]
                if not os.path.exists(os.path.join(pub, DIR_LOGOS.replace("/", os.sep),
                                                   p["logo"]))]
    if faltando:
        raise SystemExit(u"parceiro sem arquivo de logo: %s" % ", ".join(faltando))

    if not dry:
        mudou = escrever_bloco_css(pub, "rede", CSS, onda="onda31")
        print("bloco onda31:rede %s" % ("gravado" if mudou else "ja estava igual"))

    for lang, rel in PAGINAS.items():
        p = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(p):
            print("  AVISO: nao achei %s" % rel)
            continue
        h = ler(p)
        m = re.search(r'<!-- onda(?:21:rede-v2|31:rede) -->.*?'
                      r'<!-- /onda(?:21:rede-v2|31:rede) -->', h, re.S)
        if not m:
            print("  AVISO: %s sem o bloco da rede" % rel)
            continue
        prefixo = "/mirow-site/"
        novo = h[:m.start()] + bloco_rede(mestre, geo, lang, prefixo, pub, dry) + h[m.end():]
        if novo == h:
            print("  %s ja estava igual" % rel)
            continue
        if not dry:
            gravar(p, novo)
        print("  %s regenerada (%d parceiros)%s"
              % (rel, len(mestre["parceiros"]), " (dry)" if dry else ""))

    # `tools/rede-publicada.json`: so o que a suite precisa para RECALCULAR a
    # projecao e cobrar o HTML (mesmo padrao do clients-publicados.json). Nada de
    # interno do mestre vaza para o repo publico.
    publicado = {"mapas": {}}
    for chave, bbox, _n in MAPAS:
        fn, w, h = projetor(bbox)
        pins = []
        for p in mestre["parceiros"]:
            if p["mapa"] != chave:
                continue
            x, y = fn(p["lon"], p["lat"])
            pins.append({"nome": p["nome"], "lat": p["lat"], "lon": p["lon"],
                         "esq": round(100.0 * x / w, 2),
                         "top": round(100.0 * y / h, 2)})
        publicado["mapas"][chave] = {"bbox": list(bbox), "pins": pins}
    alvo = os.path.join(AQUI, "rede-publicada.json")
    texto = json.dumps(publicado, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if not dry and (not os.path.exists(alvo) or ler(alvo) != texto):
        with io.open(alvo, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
        print("tools/rede-publicada.json atualizado")

    # relatorio das posicoes, para conferencia humana
    print("\nposicao de cada pin (calculada da lat/lon, nao escrita a mao):")
    for chave, bbox, _n in MAPAS:
        fn, w, h = projetor(bbox)
        print("  mapa %-9s viewBox 0 0 %.0f %.1f  (proporcao %.3f)" % (chave, w, h, w / h))
        for pa in mestre["parceiros"]:
            if pa["mapa"] != chave:
                continue
            x, y = fn(pa["lon"], pa["lat"])
            print("    %-16s lat %7.3f lon %8.3f -> left %5.2f%% top %5.2f%%"
                  % (pa["nome"], pa["lat"], pa["lon"], 100 * x / w, 100 * y / h))


if __name__ == "__main__":
    main()
