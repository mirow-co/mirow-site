# -*- coding: utf-8 -*-
"""
15_home_hero_e_espacos.py — itens 1 e 2 da lista do Mario (onda 7).

Uso:  python tools_onda6/15_home_hero_e_espacos.py <raiz-que-contem-public>

Item 1 — hero mais compacto nas 4 homes:
  - o tema usa .banner{height:100vh} a partir de 992px, com align-items:center;
    o slogan comecava muito abaixo e a faixa de logos ficava fora da primeira dobra;
  - aqui o hero passa a ter altura pelo conteudo (padding controlado), o bloco sobe
    e o espacamento entre as 3 linhas do slogan aumenta (line-height 100% -> 116%).

Item 2 — menos vazio antes de "Nossas areas de expertise":
  - .wrap-gradient-1 na home e um bloco VAZIO com 98px de padding em cima e embaixo;
  - .home-experience tem padding-top de 200px.
  Juntos davam ~400px de gradiente sem conteudo. Aqui viram 0 + 90px.

Tudo escopado em .homepage (classe do <main> das homes), para nao tocar nas
paginas internas que reusam .wrap-gradient-1. Nenhum arquivo do tema e alterado:
o CSS vai para um bloco marcado em wp-content/uploads/2026/07/onda6/onda6.css.

Idempotente: reescreve o bloco /* onda7:home-hero:ini */ e garante o <link>.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import (base_prefix, escrever_bloco_css, garantir_link_css,  # noqa: E402
                        gravar, ler, resolve_public)

HOMES = ["pt/index.html", "en/index.html", "en/homepage/index.html", "de/index.html"]

CSS = u"""/* onda7 — home: hero compacto + menos vazio antes das praticas */
.homepage .banner{min-height:0;padding:150px 0 60px}
.homepage .banner h2{line-height:116%}
@media only screen and (min-width: 992px){
  .homepage .banner{height:auto;min-height:0;padding:170px 0 80px;align-items:flex-start}
  .homepage .banner h2{line-height:116%;margin-bottom:26px}
}
.homepage .wrap-gradient-1{padding:0}
.homepage .home-experience{padding-top:90px}
@media only screen and (max-width: 991px){
  .homepage .home-experience{padding-top:70px}
}
"""


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    if escrever_bloco_css(pub, "home-hero", CSS):
        print("css onda7:home-hero gravado")
    else:
        print("css onda7:home-hero ja atualizado")

    alterados = 0
    for rel in HOMES:
        path = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(path):
            print("AVISO: nao existe %s" % rel)
            continue
        html = ler(path)
        novo = garantir_link_css(html, base_prefix(html))
        if novo != html:
            gravar(path, novo)
            alterados += 1
            print("link do css garantido: %s" % rel)
        else:
            print("sem mudanca: %s" % rel)

    print("\nresumo: %d arquivo(s) HTML alterado(s)" % alterados)


if __name__ == "__main__":
    main()
