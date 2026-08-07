# -*- coding: utf-8 -*-
"""Onda 41 / S-133 (issue mirow-marketing#187): fotos dos Insights sem o
apagado — brightness sobe e o contraste do título vem de um scrim.

Pedido dos sócios (FD+AM, 05/08, MMK-CONV009-C07): "melhorar contraste das
fotos, melhorar cor — aparece 'apagado'".

O apagado era a S-56 (onda 18): a foto inteira ficava a brightness(0.38) para
o título branco ler por cima. A correção separa os dois papéis:
- a FOTO volta a quase-plena (0.9 em repouso, 0.78 no hover — o hover segue
  mais escuro que o repouso, como era);
- a LEGIBILIDADE do título vem de um scrim ::after em gradiente navy, mais
  denso embaixo, onde o título fica.

Editado NO LUGAR (mesmo bloco onda18:insights-colorido, regra dos valores
gêmeos) em vez de um bloco de override — dois lugares declarando o mesmo
filter é a classe de bug da onda 31.

Uso: python tools_onda6/95_insights_contraste.py <raiz>
"""
import sys

from _onda7_css import resolve_public, escrever_bloco_css

CSS = """
/* S-56 (onda 18): card nasce colorido, sem grayscale.
   S-133 (onda 41): brightness 0.38 -> 0.9 + scrim.
   S-139 (onda 42, 2026-08-06, #193): segunda rodada do "apagado" — a foto vai
   a COR PLENA (1.0), o scrim fica so na base (atras do titulo), e o card
   ganha acento cyan no hover. */
.page-insights__list-image{filter:grayscale(0%) brightness(1) !important}
.page-insights__list-item:hover .page-insights__list-image{
  filter:grayscale(0%) brightness(0.88) !important}
/* scrim: denso em CIMA — e no topo do card que o tema poe o titulo
   (medido: .page-insights__list-title rende dentro do terco superior) */
.page-insights__list-image{position:relative}
.page-insights__list-image::after{content:"";position:absolute;inset:0;
  background:linear-gradient(180deg,rgba(4,21,69,.78) 0%,rgba(4,21,69,.30) 45%,
  rgba(4,21,69,0) 75%)}
/* o conteudo (titulo) fica acima do scrim */
.page-insights__list-wrap-content{position:relative;z-index:2}
/* acento de cor no vocabulario do tema: filete cyan que acende no hover */
.page-insights__list-item{position:relative}
.page-insights__list-item::before{content:"";position:absolute;left:0;right:0;
  bottom:0;height:4px;background:#00ADEC;transform:scaleX(0);
  transform-origin:left;transition:transform 260ms ease;z-index:3}
.page-insights__list-item:hover::before{transform:scaleX(1)}
.page-insights__list-item:hover .page-insights__list-title{color:#7FDBFF}
"""


def main(root):
    pub = resolve_public(root)
    mudou = escrever_bloco_css(pub, "insights-colorido", CSS, onda="onda18")
    print("onda6.css %s" % ("atualizado" if mudou else "ja estava assim"))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
