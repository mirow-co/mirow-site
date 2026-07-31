# -*- coding: utf-8 -*-
"""54 — S-35: slogan pt "Resultado" -> "Resultados".

Uso:
    python tools_onda6/54_slogan_resultados.py <raiz-que-contem-public>

Pedido do Mario (31/07): "mudar Estrategia Confianca Resultado -> Estrategia
Confianca Resultados". So o pt muda — en ("Results") e de ("Ergebnisse") ja
sao plurais.

Troca literal no degrau 3 da escadinha, nas homes pt (pt/index.html; as
en/de nao contem o texto pt). Idempotente.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, ler, resolve_public  # noqa: E402

HOMES = ["pt/index.html", "en/index.html", "de/index.html", "en/homepage/index.html"]

VELHO = u'<span class="onda10-degrau onda10-degrau--3">Resultado</span>'
NOVO = u'<span class="onda10-degrau onda10-degrau--3">Resultados</span>'


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    alterados = []
    for rel in HOMES:
        p = os.path.join(pub, rel.replace("/", os.sep))
        h = ler(p)
        novo = h.replace(VELHO, NOVO)
        if novo != h:
            gravar(p, novo)
            alterados.append(rel)
    print("paginas alteradas: %s" % (", ".join(alterados) or "nenhuma (ja estava igual)"))


if __name__ == "__main__":
    main()
