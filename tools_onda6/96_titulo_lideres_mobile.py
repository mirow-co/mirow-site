# -*- coding: utf-8 -*-
"""Onda 41 / S-134 (issue mirow-marketing#189): o título "Nossos Líderes"
volta a aparecer no mobile.

Observação aberta desde a onda 26: no mobile o tema aplica display:none ao
h2 .home-leaders__subtitle (que é o título real da seção — o
.home-leaders__title é um h2 VAZIO do tema) e a seção abre sem título.

O override devolve o display no breakpoint mobile. A tipografia já vem da
.onda30-titulo-secao, que o título carrega desde a onda 30.

Uso: python tools_onda6/96_titulo_lideres_mobile.py <raiz>
"""
import sys

from _onda7_css import resolve_public, escrever_bloco_css

CSS = """
/* S-134: o tema esconde o titulo da secao de lideres abaixo de 992px
   (display:none em .home-leaders__subtitle — MEDIDO: some de 320 a 991px,
   volta em 992) e a secao abre sem titulo. Devolve o display na faixa toda;
   tamanho/cor vem da .onda30-titulo-secao. */
@media only screen and (max-width: 991px){
  .home-leaders .home-leaders__subtitle{display:block !important}
}
"""


def main(root):
    pub = resolve_public(root)
    mudou = escrever_bloco_css(pub, "titulo-lideres-mobile", CSS, onda="onda41")
    print("onda6.css %s" % ("atualizado" if mudou else "ja estava assim"))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
