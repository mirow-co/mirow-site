# -*- coding: utf-8 -*-
"""Onda 17 — S-49 (#107): hero "Horizonte 2050" no lugar do video da lampada.

Decisao do Mario (03/08, prototipo v2 aprovado): fundo dinamico futurista no
tema Mirow — grade em perspectiva + aurora + cometas descendo + convite ao
scroll. Sai o <video> de 22,8 MB das 4 homes; entram 2 canvases + ~6 KB de JS
(onda17-horizonte.js). REVERTE a S-37 (#92) por decisao do dono.

Idempotente: 2a execucao reporta 0 mudancas.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import (resolve_public, escrever_bloco_css, ler, gravar,
                        base_prefix)

HOMES = ["pt/index.html", "en/index.html", "de/index.html",
         "en/homepage/index.html"]

# o bloco do video (onda13/S-37) vira os dois canvases da onda17
RE_VIDEO = re.compile(
    r"<!-- onda13:hero-malha -->.*?<!-- /onda13:hero-malha -->", re.S)
BLOCO_CANVAS = (
    "<!-- onda17:hero-horizonte -->"
    '<canvas class="hero-horizonte__cena" aria-hidden="true"></canvas>'
    '<canvas class="hero-horizonte__convite" aria-hidden="true"></canvas>'
    "<!-- /onda17:hero-horizonte -->")

CSS = """
/* S-49 (#107): hero Horizonte 2050 — cena no tamanho do fundo do banner
   (que a onda14 ja prende a section inteira, sem mascara) e o convite ao
   scroll como canvas pequeno no centro-base, acima do conteudo. As zonas
   do tema: conteudo z-5 (onda14); o convite fica z-4 para nunca roubar
   clique das pills. */
.banner__background .hero-horizonte__cena{
  position:absolute;top:0;left:0;width:100%;height:100%;display:block}
.hero-horizonte__convite{
  position:absolute;left:50%;bottom:18px;transform:translateX(-50%);
  width:48px;height:72px;z-index:4;pointer-events:none}
"""


def main(root):
    pub = resolve_public(root)
    mudancas = 0

    if escrever_bloco_css(pub, "hero-horizonte-s49", CSS, onda="onda17"):
        mudancas += 1
        print("css: onda17:hero-horizonte-s49 gravado")

    for rel in HOMES:
        path = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(path):
            print("AVISO: %s nao existe" % rel)
            continue
        html = ler(path)
        orig = html
        prefix = base_prefix(html)

        # 1) video -> canvases (o convite precisa ficar FORA do
        #    banner__background? nao: o background e full-bleed na section
        #    (onda14), entao bottom:18px do background = bottom do hero)
        if "hero-horizonte__cena" not in html:
            html = RE_VIDEO.sub(BLOCO_CANVAS, html, count=1)

        # 2) script no fim do body (uma vez)
        if "onda17-horizonte.js" not in html:
            tag = ('<script src="%swp-content/uploads/2026/07/onda6/'
                   'onda17-horizonte.js" defer></script>\n' % prefix)
            html = html.replace("</body>", tag + "</body>", 1)

        if html != orig:
            gravar(path, html)
            mudancas += 1
            print("html: %s atualizado" % rel)

    print("total: %d mudancas" % mudancas)
    return mudancas


if __name__ == "__main__":
    raiz = sys.argv[1] if len(sys.argv) > 1 else "."
    main(raiz)
