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
   S-133 (onda 41, 2026-08-06): o brightness(0.38) que garantia o titulo
   branco APAGAVA a foto (feedback FD+AM 05/08). A foto sobe para 0.9/0.78 e
   a legibilidade passa a vir do scrim ::after abaixo. */
.page-insights__list-image{filter:grayscale(0%) brightness(0.9) !important}
.page-insights__list-item:hover .page-insights__list-image{
  filter:grayscale(0%) brightness(0.78) !important}
/* scrim: denso embaixo (onde mora o titulo), quase nada em cima */
.page-insights__list-image{position:relative}
.page-insights__list-image::after{content:"";position:absolute;inset:0;
  background:linear-gradient(180deg,rgba(4,21,69,.10) 0%,rgba(4,21,69,.28) 55%,
  rgba(4,21,69,.82) 100%)}
/* o conteudo (titulo) fica acima do scrim */
.page-insights__list-wrap-content{position:relative;z-index:2}
"""


def main(root):
    pub = resolve_public(root)
    mudou = escrever_bloco_css(pub, "insights-colorido", CSS, onda="onda18")
    print("onda6.css %s" % ("atualizado" if mudou else "ja estava assim"))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
