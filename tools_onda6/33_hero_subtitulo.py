# -*- coding: utf-8 -*-
"""33 — S-24 (issue #74): subtitulo novo do hero das 4 homes.

Uso:
    python tools_onda6/33_hero_subtitulo.py <raiz-que-contem-public> [--variante=V1|V2|V3]

PEDIDO (verbatim — Andreas via Mario, 2026-07-31)
------------------------------------------------
    Subtitulo: algum texto com:
    Focamos em estrategia, compras, e go-to market/pricing
    E entregamos resultados garantidos

TRES VARIANTES (as 3 estao na issue #74; o Mario escolhe)
--------------------------------------------------------
V1 — fiel ao verbatim, com a palavra "garantidos".
V2 — RECOMENDADA (implementada): mesma promessa de entrega, sem "garantidos".
     "Garantidos" e uma promessa que a firma nao consegue sustentar por escrito
     numa home publica; o ETHOS de honestidade vence a forca da frase (e, em
     conflito entre meta e ethos, o ethos vence).
V3 — compromisso explicito e mensuravel, alternativa se o Mario quiser manter a
     forca do V1 sem a palavra absoluta.

Trocar a escolha = rodar com --variante=V1 (ou V3). Idempotente em qualquer
variante: o script reconhece qualquer uma das 9 frases e substitui.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _onda7_css import gravar, idioma_da_pagina, ler, resolve_public  # noqa: E402

HOMES = ["pt/index.html", "en/index.html", "de/index.html", "en/homepage/index.html"]

VARIANTE_PADRAO = "V2"

TEXTOS = {
    # V1 incrementada a pedido do Mario (31/07, issue #74): mantém o
    # "garantidos" do verbatim do Andreas e ganha o "lado a lado" da V2.
    # Decisão explícita do Mario sobre a recomendação V2 — registrada na #74.
    "V1": {
        "pt": u"Focamos em estratégia, compras e go-to-market/pricing "
              u"— e entregamos resultados garantidos, lado a lado com a sua equipe",
        "en": u"We focus on strategy, procurement and go-to-market/pricing "
              u"— and we deliver guaranteed results, side by side with your team",
        "de": u"Wir fokussieren uns auf Strategie, Einkauf und Go-to-Market/Pricing "
              u"— und liefern garantierte Ergebnisse, Seite an Seite mit Ihrem Team",
    },
    "V2": {
        "pt": u"Focamos em estratégia, compras e go-to-market/pricing "
              u"— e entregamos resultados lado a lado com a sua equipe",
        "en": u"We focus on strategy, procurement and go-to-market/pricing "
              u"— and we deliver results side by side with your team",
        "de": u"Wir fokussieren uns auf Strategie, Einkauf und Go-to-Market/Pricing "
              u"— und liefern Ergebnisse Seite an Seite mit Ihrem Team",
    },
    "V3": {
        "pt": u"Focamos em estratégia, compras e go-to-market/pricing "
              u"— com compromisso de resultado, medido e acordado com você",
        "en": u"We focus on strategy, procurement and go-to-market/pricing "
              u"— with a results commitment we measure and agree with you",
        "de": u"Wir fokussieren uns auf Strategie, Einkauf und Go-to-Market/Pricing "
              u"— mit einem Ergebnisversprechen, das wir mit Ihnen messen und vereinbaren",
    },
}

# o <p> imediatamente depois do <h2> do slogan e o subtitulo do hero
REX = re.compile(r'(<h2 data-aos="fade-right">.*?</h2>\s*)(<p>)(.*?)(</p>)', re.S)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    variante = VARIANTE_PADRAO
    for a in sys.argv[2:]:
        if a.startswith("--variante="):
            variante = a[len("--variante="):].upper()
    if variante not in TEXTOS:
        raise SystemExit(u"variante desconhecida: %s (use V1, V2 ou V3)" % variante)

    alteradas = []
    for rel in HOMES:
        p = os.path.join(pub, rel.replace("/", os.sep))
        h = ler(p)
        m = REX.search(h)
        if not m:
            raise SystemExit(u"nao achei o <p> de subtitulo do hero em %s" % rel)
        novo = TEXTOS[variante][idioma_da_pagina(h)]
        if m.group(3) == novo:
            continue
        gravar(p, h[:m.start(3)] + novo + h[m.end(3):])
        alteradas.append(rel)
    print(u"variante aplicada: %s" % variante)
    print(u"paginas alteradas: %s" % (u", ".join(alteradas) if alteradas else u"nenhuma (ja estava igual)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
