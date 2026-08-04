# -*- coding: utf-8 -*-
"""67 — onda 18, S-56 (issue #114): insights ja comecam coloridos.

Uso:
    python tools_onda6/67_insights_colorido.py <raiz-que-contem-public>

Pedido do Mario: "os insights nao precisam comecar como preto e branco para
quando passar o mouse ficarem coloridos - podem comecar coloridos".

O tema tem, no bundle:
  .page-insights__list-image        -> filter: grayscale(100%) brightness(0.3)
  .page-insights__list-item:hover … -> filter: grayscale(0%)  brightness(0.3) + scale(1.2)

Ou seja: o grayscale e o unico estado que muda; o brightness(0.3) esta nos dois e
existe para o titulo branco ter contraste sobre a foto. Aqui so o grayscale cai —
o escurecimento fica (sem ele o titulo some, que seria trocar um bug por outro).
O zoom no hover continua, para o card nao perder a resposta ao mouse.

Sem mudanca de HTML: e um bloco CSS por cima do tema (regra nº zero).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, resolve_public  # noqa: E402

CSS = """/* S-56: card de insight nasce colorido (o grayscale inicial sai).
   O brightness fica: e o que garante contraste do titulo branco sobre a foto. */
.page-insights__list-image{filter:grayscale(0%) brightness(0.38) !important}
.page-insights__list-item:hover .page-insights__list-image{
  filter:grayscale(0%) brightness(0.3) !important}"""


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    mudou = escrever_bloco_css(pub, "insights-colorido", CSS, onda="onda18")
    print("bloco onda18:insights-colorido %s" % ("gravado" if mudou else "ja estava igual"))


if __name__ == "__main__":
    main()
