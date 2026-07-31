# -*- coding: utf-8 -*-
"""48 — S-30 (issue #82): malha do hero de ponta a ponta (sem a borda esmaecida).

Uso:
    python tools_onda6/48_hero_malha_cheia.py <raiz-que-contem-public>

O PROBLEMA
----------
O tema aplica em .banner__background uma mascara vertical
(transparent 5% -> opaco 49% -> transparent 95%). Com o video escuro isso era
invisivel; com a malha clara vira uma "moldura" esmaecida — a imagem parece
menor que o quadro azul (reclamacao do Mario ao vivo, 31/07).

O QUE FAZ
---------
1. Adiciona a classe extra `banner__background--malha` no div do hero das 4
   homes (so onde a malha esta — as outras paginas com .banner__background
   continuam com a mascara do tema).
2. MOVE o div para filho direto de <section class="banner"> (era filho do
   .container, que e position:relative — os top:0/bottom:0 do tema prendiam
   o fundo a um box de ~373px no meio do hero, nao ao hero inteiro; com o
   video escuro + mascara isso passava despercebido, com a malha clara vira
   a "imagem menor que o quadro azul" que o Mario apontou).
   A section ganha a classe `banner--malha`.
3. CSS em bloco marcado (onda14:hero-malha-cheia): desliga a mascara nessa
   classe, prende o fundo as 4 bordas do banner e mantem o conteudo do
   .container acima (z-index).

A parte "animar quando visivel" da S-30 e do onda13-hero-plexus.js
(IntersectionObserver), nao deste script.

Idempotente.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, gravar, ler, resolve_public  # noqa: E402

HOMES = ["pt/index.html", "en/index.html", "de/index.html", "en/homepage/index.html"]

REX_DIV = re.compile(
    r'\s*<div class="banner__background(?: banner__background--malha)?">\s*'
    r'<!-- onda13:hero-malha -->.*?<!-- /onda13:hero-malha -->\s*</div>\s*', re.S)

CSS = """/* S-30 (#82): a malha preenche o hero inteiro. (a) sem a mascara vertical do
   tema (virava moldura esmaecida na imagem clara); (b) o div do fundo agora e
   filho direto da section.banner — top/bottom prendem ao hero, nao ao box do
   .container; (c) conteudo acima do fundo. */
.banner__background--malha{
  -webkit-mask-image:none !important;
  mask-image:none !important;
  top:0;left:0;right:0;bottom:0;width:100%}
.banner--malha>.container{position:relative;z-index:5}"""


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    mudou = escrever_bloco_css(pub, "hero-malha-cheia", CSS, onda="onda14")
    print("bloco onda14:hero-malha-cheia %s" % ("gravado" if mudou else "ja estava igual"))
    alterados = []
    for rel in HOMES:
        p = os.path.join(pub, rel.replace("/", os.sep))
        h = ler(p)
        novo = h
        m = REX_DIV.search(novo)
        if m:
            bloco = m.group(0).strip()
            bloco = bloco.replace('<div class="banner__background">',
                                  '<div class="banner__background banner__background--malha">')
            sem = novo[:m.start()] + "\n" + novo[m.end():]
            i = sem.find('<section class="banner')
            fim = sem.find('</section>', i)
            novo = sem[:fim] + "    " + bloco + "\n" + sem[fim:]
        novo = novo.replace('<section class="banner">',
                            '<section class="banner banner--malha">', 1)
        if novo != h:
            gravar(p, novo)
            alterados.append(rel)
    print("paginas alteradas: %s" % (", ".join(alterados) or "nenhuma (ja estava igual)"))


if __name__ == "__main__":
    main()
