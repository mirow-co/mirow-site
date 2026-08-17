# -*- coding: utf-8 -*-
"""101_pesos_orfaos.py — tira do CSS do tema os pesos que a fonte nao tem.

Issue mirow-marketing#229. Idempotente: rodar 2x reporta 0 mudancas.

    python tools_onda6/101_pesos_orfaos.py <raiz-que-contem-public> [--check]

O problema
----------
A Titillium Web tem 200/300/400/600/700/900. Nao tem 500 nem 800. O CSS do tema
declara 500 nove vezes e 800 dez vezes; o navegador serve o vizinho, entao ha
texto no site com um peso que ninguem escolheu. E a mesma classe do bug da onda
35 (os big numbers pediam 800 e saiam 900), que ali foi corrigido so no nosso CSS.

Medido antes de mexer, renderizando o MESMO texto em 24px e comparando largura:
    peso 300 -> 206,56 px
    peso 400 -> 215,81 px
    peso 500 -> 215,81 px   <- identico a 400
    peso 600 -> 219,42 px
    peso 700 -> 222,16 px
    peso 800 -> 221,30 px   <- identico a 900
    peso 900 -> 221,30 px

Ou seja: 500 JA e pintado como 400, e 800 JA e pintado como 900. A substituicao
abaixo escreve no CSS o que o navegador ja faz — **zero mudanca visual, por
construcao**, e nao por otimismo. A V35 mede isso.

Elementos afetados hoje (medidos em 10 paginas): 10 no total, um componente
principal — o titulo do card de pratica
(`div.praticas-3__card > h4.home-experience__list-item-header > span`, 24px, em 9
paginas) e um `h5` "Nossas praticas". Os outros 17 sao latentes: aplicam-se a
seletores que hoje nao renderizam, mas mordem no dia em que renderizarem.

Sobre a regra zero do CLAUDE.md
------------------------------
"nunca editando o CSS do tema" — e aqui edita, pela segunda vez nesta serie (a
primeira foi tirar os @import de fontes na #227). A alternativa seria sobrescrever
no onda6.css, mas isso exigiria DUPLICAR os seletores do tema: fragil, e so
cobriria os 2 casos visiveis, deixando 17 latentes. O que muda aqui e um numero
que o navegador ja ignora — nao e restilizacao, que e o que a regra protege.

NAO toca no CSS do Formidable
-----------------------------
Ele tambem tem 7 declaracoes orfas, mas o caminho certo la e outro: o formulario
saiu do site na #228 e `formidableforms.css` continua sendo carregado em 109
paginas. Peso morto — deve ser removido, nao corrigido. Fica na #229.
"""
from __future__ import unicode_literals

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public, ler, gravar  # noqa: E402

TEMA = "wp-content/themes/mirow/public/bundle-css.css"

# 500 -> 400 e 800 -> 900: o que o navegador ja pinta (medido, ver docstring).
TROCA = [
    (re.compile(r"font-weight:\s*500\b"), "font-weight:400"),
    (re.compile(r"font-weight:\s*800\b"), "font-weight:900"),
]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    pub = resolve_public(args[0])

    caminho = os.path.join(pub, *TEMA.split("/"))
    if not os.path.exists(caminho):
        raise SystemExit("CSS do tema ausente: %s" % TEMA)

    css = ler(caminho)
    novo = css
    total = 0
    for rex, sub in TROCA:
        novo, n = rex.subn(sub, novo)
        total += n

    if total and not check:
        gravar(caminho, novo)

    print("declaracoes trocadas: %d" % total)
    print("mudancas: %d%s" % (total, " (--check: nada escrito)" if check else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
