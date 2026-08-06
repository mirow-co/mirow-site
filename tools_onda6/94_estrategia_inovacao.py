# -*- coding: utf-8 -*-
"""Onda 41 / S-132 (issue mirow-marketing#187): a caixinha de expertise
"Estratégia" da home vira "Estratégia e Inovação".

Pedido dos sócios (FD+AM, 05/08, MMK-CONV009-C06). Muda SÓ o título do card
`praticas-3__card#estrategia` nas 4 homes — o hero ("Estratégia / Confiança /
Resultados"), o menu Práticas e a página /pratica/estrategia/ ficam como estão.

A âncora é o ícone do card (icon-strategy.svg) seguido do <span>, o que impede
de tocar as outras ocorrências da palavra na página.

Uso: python tools_onda6/94_estrategia_inovacao.py <raiz>
"""
import sys

from _onda7_css import resolve_public, ler, gravar, idioma_da_pagina

# en/homepage/ era a 4a home quando este script rodou pela 1a vez; na mesma
# onda ela virou stub (97_home_en_canonica). O loop pula stubs.
HOMES = ["pt/index.html", "en/index.html", "de/index.html",
         "en/homepage/index.html"]

ANCORA = 'icon-strategy.svg"><span>'
NOVO = {
    "pt": "Estratégia e Inovação",
    "en": "Strategy &amp; Innovation",
    "de": "Strategie &amp; Innovation",
}
ANTIGO = {
    "pt": "Estratégia",
    "en": "Strategy",
    "de": "Strategie",
}


def main(root):
    pub = resolve_public(root)
    mudadas = 0
    for rel in HOMES:
        path = "%s/%s" % (pub, rel)
        html = ler(path)
        if "menu__nav-item" not in html:      # stub de redirect (onda 41)
            print("pulado (stub): %s" % rel)
            continue
        idi = idioma_da_pagina(html)
        alvo_novo = ANCORA + NOVO[idi] + "</span>"
        if alvo_novo in html:
            print("ok (ja feito): %s" % rel)
            continue
        alvo_antigo = ANCORA + ANTIGO[idi] + "</span>"
        if alvo_antigo not in html:
            raise SystemExit("nao achei o card de estrategia em %s" % rel)
        gravar(path, html.replace(alvo_antigo, alvo_novo, 1))
        mudadas += 1
        print("renomeado: %s (%s -> %s)" % (rel, ANTIGO[idi], NOVO[idi]))
    print("%d pagina(s) mudada(s)" % mudadas)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
