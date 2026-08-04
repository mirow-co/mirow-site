# -*- coding: utf-8 -*-
"""83 — onda 28, S-109 (#167).

Uso:
    python tools_onda6/83_painel_submenu_mesma_altura.py <raiz-que-contem-public>

S-109 — "percebi que a barra tem tamanhos diferentes a depender de qual item do
  menu esta selecionado."
  CAUSA RAIZ (medida no navegador, 1400x900): o painel de "Sobre nos" tinha 159px
  e o de "Praticas" 129px, porque os dois valores nasceram em ondas diferentes e
  ninguem os igualou:

      | ..................... | Sobre nos      | Praticas        |
      | altura do painel      | 159px          | 129px           |
      | margin-top da lista   | 40px (do tema) | 6px (S-65)      |
      | padding do link       | 6px 0          | 2px 0           |
      | altura da linha       | 35px           | 27px            |

  Correcao: os dois passam a usar os MESMOS numeros (18px de margem na lista,
  4px de padding no link) — media entre o aberto do tema e o apertado da S-65.
  Como os dois paineis tem a mesma cabeca (h5 de 21px) e uma linha de itens, isso
  basta para a altura ficar igual.

  Nao se mexe no tamanho da fonte (19px nos dois, S-99) nem no divisor cinza das
  praticas (S-65) — so no espacamento vertical.

Idempotente: CSS em bloco marcado.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, resolve_public  # noqa: E402

CSS = u"""/* ---- S-109: os dois paineis de submenu com a MESMA altura ---------------
   "Sobre nos" media 159px e "Praticas" 129px: a lista do primeiro herdava
   margin-top:40px do tema e a do segundo levava 6px da S-65, e o padding do link
   era 6px x 2px. Aqui os dois lados usam os mesmos numeros — o resto (fonte de
   19px da S-99, divisor cinza da S-65) fica como esta. */
.menu__nav-submenu .menu__nav-sublinks,
.menu__nav-submenu .menu__nav-sublinks.onda18-praticas,
.menu__nav-submenu .menu__nav-sublinks:not(.onda18-praticas){
  margin:18px 0 0 !important}
.menu__nav-submenu .menu__nav-sublink,
.menu__nav-submenu .menu__nav-sublinks.onda18-praticas .menu__nav-sublink{
  padding:4px 0 !important;line-height:1.2 !important}
/* no mobile o menu do tema e lista empilhada: cada item respira igual */
@media only screen and (max-width: 991px){
  .menu__nav-submenu .menu__nav-sublinks,
  .menu__nav-submenu .menu__nav-sublinks.onda18-praticas{margin:10px 0 0 !important}
}"""


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    mudou = escrever_bloco_css(pub, "painel-mesma-altura", CSS, onda="onda28")
    print("bloco onda28:painel-mesma-altura %s"
          % ("gravado" if mudou else "ja estava igual"))


if __name__ == "__main__":
    main()
