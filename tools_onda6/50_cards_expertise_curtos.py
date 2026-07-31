# -*- coding: utf-8 -*-
"""50 — S-05 (issue #54): textos dos 3 cards de expertise curtos e executivos.

Uso:
    python tools_onda6/50_cards_expertise_curtos.py <raiz-que-contem-public>

Pedido do Mario (31/07): "vamos tambem resumir o texto dos blocos da 'nossa
area de expertise'". Os paragrafos atuais tem 45-60 palavras; viram 1 frase
executiva (~15-20 palavras) por card, nas 3 linguas. O titulo, o icone e o
CTA "conheca a pratica" nao mudam.

Mecanica: substitui o CONTEUDO do <p> dentro de
<div class="home-experience__list-item-content"> de cada card (por id:
estrategia / pricing / sourcing), nas 4 homes. Idempotente: quando o texto
ja e o novo, nada muda.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, idioma_da_pagina, ler, resolve_public  # noqa: E402

HOMES = ["pt/index.html", "en/index.html", "de/index.html", "en/homepage/index.html"]

TEXTOS = {
    "pt": {
        "estrategia": u"Da análise de mercado à execução: formulamos e implementamos "
                      u"estratégias que geram valor mensurável.",
        "pricing": u"Modelos de pricing mais inteligentes em toda a cadeia de marketing "
                   u"e vendas, com o Mirow Pricing Optimizer.",
        "sourcing": u"Sourcing estratégico que reduz custo sem sacrificar nível de "
                    u"serviço — da avaliação de spend à captura.",
    },
    "en": {
        "estrategia": u"From market analysis to execution: we formulate and implement "
                      u"strategies that deliver measurable value.",
        "pricing": u"Smarter pricing models across marketing and sales, powered by "
                   u"the Mirow Pricing Optimizer.",
        "sourcing": u"Strategic sourcing that cuts cost without sacrificing service "
                    u"levels — from spend assessment to capture.",
    },
    "de": {
        "estrategia": u"Von der Marktanalyse bis zur Umsetzung: Wir entwickeln und "
                      u"implementieren Strategien mit messbarem Wert.",
        "pricing": u"Intelligentere Pricing-Modelle entlang von Marketing und Vertrieb "
                   u"— mit dem Mirow Pricing Optimizer.",
        "sourcing": u"Strategischer Einkauf, der Kosten senkt, ohne das Serviceniveau "
                    u"zu opfern — vom Spend-Assessment bis zur Umsetzung.",
    },
}


def trocar(html, card_id, novo):
    rex = re.compile(
        r'(id="%s".*?home-experience__list-item-content"><p>)(.*?)(</p>)' % card_id, re.S)
    m = rex.search(html)
    if not m or m.group(2).strip() == novo:
        return html, False
    return html[:m.start(2)] + novo + html[m.end(2):], True


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    alterados = []
    for rel in HOMES:
        p = os.path.join(pub, rel.replace("/", os.sep))
        h = ler(p)
        idioma = idioma_da_pagina(h)
        mudou = False
        for card_id, novo in TEXTOS[idioma].items():
            h, m = trocar(h, card_id, novo)
            mudou = mudou or m
        if mudou:
            gravar(p, h)
            alterados.append(rel)
    print("paginas alteradas: %s" % (", ".join(alterados) or "nenhuma (ja estava igual)"))


if __name__ == "__main__":
    main()
