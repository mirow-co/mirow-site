# -*- coding: utf-8 -*-
"""80 — onda 26, os quatro pedidos que sao so CSS (S-97 a S-100).

Uso:
    python tools_onda6/80_fonte_unica_e_barra.py <raiz-que-contem-public>

S-97 (#155) — "Ver todos os lideres em azul."
  O link nasceu branco na onda 7, quando a secao dos lideres tinha fundo escuro.
  Depois da S-91 (veu claro sempre opaco, 4 titulos em navy) ele ficou branco
  sobre claro. Passa a navy #020E66, hover ciano — igual ao titulo ao lado.

S-98 (#156) — "garantir que a pagina inicial tem apenas uma fonte throughout ...
  apenas uma fonte em todas as paginas do site."
  CAUSA RAIZ (medida, nao suposta): o tema declara tres familias em variaveis
  (`--fontFamily` Archivo, `--secondaryFontFamily` Libre Franklin,
  `--tertiaryFontFamily` Roboto Serif) e NENHUMA delas e carregada — o unico
  webfont no <head> das 275 paginas e o Titillium Web, aplicado a `body,html`.
  Ou seja: onde o tema forcava Archivo/Libre Franklin o navegador caia no
  sans-serif do sistema (Arial); onde nao forcava, ficava Titillium. Era esse o
  contraste entre "Nossas areas de expertise" (cards do tema, Arial) e "Setores
  em que atuamos" (cards da onda 18, sem font-family, logo Titillium).
  Correcao: as tres variaveis — e as do Bootstrap — passam a apontar para a
  unica fonte de fato carregada. Nao se carrega webfont novo (custo zero de
  rede, e o tema segue intocado: e sobrescrita de variavel).

S-99 (#157) — "dentro de praticas na barra superior, o tamanho da fonte tem que
  ser o mesmo throughout na barra (mesmo tamanho de fonte que sobre nos)."
  Praticas ia a 26px (22px/19px nos breakpoints menores) e Sobre nos a 19px.
  Agora os dois em 19px em toda largura. Substitui a decisao da S-94, que tinha
  mantido o tamanho diferente de proposito — o Mario reafirmou incluindo o
  tamanho. O divisor "|" cinza entre as tres praticas continua.

S-100 (#158) — "nao precisa separar a politica de privacidade da barra inferior
  por uma linha/barra de separacao."
  Sai o `border-bottom` da `.rodape-barra` (vinha da S-36 v2).

Idempotente: so escreve blocos marcados no onda6.css.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, resolve_public  # noqa: E402

FONTE = u'"Titillium Web",sans-serif'

CSS_FONTE = u"""/* ---- S-98: UMA fonte em todo o site ------------------------------------
   O tema pedia Archivo/Libre Franklin/Roboto Serif por variavel, mas nenhuma
   das tres e carregada em nenhuma das 275 paginas — so o Titillium Web esta no
   <head>. As variaveis passam a apontar para ela; assim as ~130 regras do tema
   que usam var(--fontFamily)/var(--secondaryFontFamily) continuam valendo e
   convergem para a mesma familia. */
:root{
  --fontFamily:%(f)s;
  --secondaryFontFamily:%(f)s;
  --secondaryfontFamily:%(f)s; /* typo que existe no CSS do tema */
  --tertiaryFontFamily:%(f)s;
  --bs-font-sans-serif:%(f)s;
  --bs-body-font-family:%(f)s;
}
body,html,button,input,optgroup,select,textarea{font-family:%(f)s}
/* o widget "chosen" e o unico lugar do tema que nomeia sans-serif na mao */
.chosen-container-single .chosen-search input[type=text],
.chosen-container-multi .chosen-choices li.search-field input[type=text]{
  font-family:%(f)s}""" % {"f": FONTE}

CSS_AJUSTES = u"""/* ---- S-97: "Ver todos os lideres" em azul ------------------------------
   Era branco (onda 7, quando a secao era escura). Depois da S-91 o fundo ficou
   claro — navy e o que le. */
.onda7-vertodos{color:#020E66 !important}
.onda7-vertodos:hover,.onda7-vertodos:focus-visible{color:#00ADEC !important}

/* ---- S-99: Praticas no mesmo tamanho de Sobre nos (19px) ---------------
   Revoga o tamanho maior da S-65/S-88 (26px no desktop). Vale em toda a
   largura, no header e no rodape. */
.menu__nav-sublinks.onda18-praticas .menu__nav-sublink,
.menu__nav-sublinks:not(.onda18-praticas) .menu__nav-sublink{
  font-size:19px !important}
@media only screen and (max-width: 1440px){
  .menu__nav-sublinks.onda18-praticas .menu__nav-sublink{font-size:19px !important}
}
@media only screen and (max-width: 1200px){
  .menu__nav-sublinks.onda18-praticas .menu__nav-sublink{font-size:19px !important}
}
/* o "|" que separa as praticas acompanha o texto menor */
.menu__nav-sublinks.onda18-praticas .menu__nav-sublinkitem+.menu__nav-sublinkitem::before{
  font-size:19px}

/* ---- S-100: nada separando a politica de privacidade da barra ---------- */
.rodape-barra{border-bottom:0 !important}"""


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    for chave, css in (("fonte-unica", CSS_FONTE), ("ajustes-s97-s100", CSS_AJUSTES)):
        mudou = escrever_bloco_css(pub, chave, css, onda="onda26")
        print("bloco onda26:%s %s" % (chave, "gravado" if mudou else "ja estava igual"))


if __name__ == "__main__":
    main()
