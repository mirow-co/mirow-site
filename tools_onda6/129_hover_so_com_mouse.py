# -*- coding: utf-8 -*-
r"""129_hover_so_com_mouse.py — a barra branca no :hover so onde existe ponteiro.

    python tools_onda6/129_hover_so_com_mouse.py <raiz-que-contem-public> [--check]

Idempotente: rodar 2x reporta 0 mudancas.

PEDIDO (Mario, 19/08/2026): "no mobile, quando eu clico nas 3 linhas para
selecionar a barra superior, depois fecho, a barra volta a ser branca e o mirow
fica ilegivel."

A CAUSA, REPRODUZIDA NO NAVEGADOR (nao suposta)
-----------------------------------------------
A primeira hipotese -- a classe `menu--mobile-opened` nao sair ao fechar -- foi
MEDIDA E DESCARTADA:

    passo                      classe                       fundo
    inicial                    menu                         navy
    menu aberto                menu menu--mobile-opened     navy
    menu fechado               menu                         navy   <- classe sai certo
    ponteiro parado na barra   menu                         BRANCO <- e aqui

O culpado e `.header .menu:hover{background:#fff !important}` (onda 27, S-105).
No desktop isso e proposital: o painel do submenu e branco, entao a barra
acompanha. Em tela de toque **nao existe sair do hover** -- depois do tap no
hamburguer o navegador mantem o estado `:hover` naquele elemento ate o proximo
toque em outro lugar. Resultado: barra branca com o logo branco por cima.

O CONSERTO
----------
`@media (hover:hover) and (pointer:fine)` -- a regra passa a existir so onde ha
ponteiro que consegue de fato entrar e sair de um elemento. Nao e numero magico
nem media query de largura: e a consulta que descreve exatamente a condicao que
a regra pressupoe. Tablet grande com dedo tambem fica protegido, e um laptop com
tela de toque continua com o hover funcionando pelo mouse.

Editado NO LUGAR, dentro do bloco onda27 (regra dos valores gemeos): o
`background:#fff` do hover continua existindo uma vez so.

O `.menu--mobile-opened` continua branco em qualquer aparelho -- ali o branco e
correto, porque o painel do menu aberto e branco.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public

CSS = "wp-content/uploads/2026/07/onda6/onda6.css"

ANTIGO = """.header .menu:hover,
.header .menu.menu--mobile-opened{background:#fff !important}"""

NOVO = """/* onda64 (19/08): o hover branco so onde existe ponteiro de verdade. Em tela
   de toque o :hover GRUDA depois do tap -- o Mario abriu o menu pelo hamburguer,
   fechou, e a barra ficou branca com o logo branco por cima. Reproduzido no
   navegador: a classe menu--mobile-opened sai certo ao fechar; quem pintava era
   o :hover. `(hover:hover) and (pointer:fine)` e a condicao que a regra sempre
   pressupos, agora escrita. O menu ABERTO segue branco em qualquer aparelho,
   porque ali o painel e branco mesmo. */
.header .menu.menu--mobile-opened{background:#fff !important}
@media (hover:hover) and (pointer:fine){
  .header .menu:hover{background:#fff !important}
}"""

ANTIGO_RODAPE = ".rodape-barra .menu:hover{background:#fff !important}"
NOVO_RODAPE = """@media (hover:hover) and (pointer:fine){
  .rodape-barra .menu:hover{background:#fff !important}
}"""


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    check = "--check" in sys.argv
    pub = resolve_public(sys.argv[1])
    fp = os.path.join(pub, CSS.replace("/", os.sep))

    with io.open(fp, encoding="utf-8") as f:
        css = f.read()

    if "onda64 (19/08)" in css:
        print("0 mudanca(s) -- ja aplicado")
        return

    faltando = [t for t in (ANTIGO, ANTIGO_RODAPE) if t not in css]
    if faltando:
        raise SystemExit("nao achei no CSS: %s" % [t[:40] for t in faltando])

    novo = css.replace(ANTIGO, NOVO).replace(ANTIGO_RODAPE, NOVO_RODAPE)

    if check:
        print("[--check] envolveria as 2 regras de hover em (hover:hover) and (pointer:fine)")
        return

    with io.open(fp, "w", encoding="utf-8", newline="") as f:
        f.write(novo)
    print("1 mudanca -- hover branco restrito a ponteiro fino (header e clone do rodape)")


if __name__ == "__main__":
    main()
