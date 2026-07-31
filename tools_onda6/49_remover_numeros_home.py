# -*- coding: utf-8 -*-
"""49 — S-31 (issue #83): remover a secao "Nossos numeros" da home.

Uso:
    python tools_onda6/49_remover_numeros_home.py <raiz-que-contem-public>

Pedido do Mario (31/07): "nao precisa mais da secao 'nossos numeros' na pagina
inicial, ja que eles estao na capa agora" — os 4 numeros vivem no hero desde a
S-27 (onda 10, lidos DESTA secao na epoca; o markup do hero e independente e
permanece).

Remove <section class="our-numbers ..."> ... </section> das 4 homes, por corte
de texto com contagem de <section> aninhadas (nunca regex guloso).

Idempotente: segunda execucao nao acha a secao e nao grava nada.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, ler, resolve_public  # noqa: E402

HOMES = ["pt/index.html", "en/index.html", "de/index.html", "en/homepage/index.html"]

REX_INI = re.compile(r'<section class="our-numbers[^"]*"[^>]*>')


def cortar_secao(html):
    m = REX_INI.search(html)
    if not m:
        return None
    i = m.start()
    pos = m.end()
    nivel = 1
    rex_tag = re.compile(r'</?section\b')
    while nivel:
        t = rex_tag.search(html, pos)
        if not t:
            return None
        nivel += 1 if html[t.start() + 1] != '/' else -1
        pos = t.end()
    fim = html.find('>', pos) + 1
    return html[:i] + html[fim:]


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    alterados = []
    for rel in HOMES:
        p = os.path.join(pub, rel.replace("/", os.sep))
        h = ler(p)
        novo = cortar_secao(h)
        if novo:
            gravar(p, novo)
            alterados.append(rel)
    print("paginas alteradas: %s" % (", ".join(alterados) or "nenhuma (ja estava igual)"))


if __name__ == "__main__":
    main()
