# -*- coding: utf-8 -*-
"""
20_nosso_trabalho_ordem.py — item 6 da lista do Mario (onda 7).

Uso:  python tools_onda6/20_nosso_trabalho_ordem.py <raiz-que-contem-public>

A pagina "Nosso trabalho" (3 linguas) vinha na ordem
    1. Por que a Mirow?   (<section class="reasons">)
    2. Nossa Cultura      (<section class="culture">)
    3. Industrias         (<section class="segments">)
e passa a
    1. Nossa Cultura
    2. Por que a Mirow?
    3. Industrias
ou seja: as secoes "culture" e "reasons" trocam de lugar. O markup de cada secao
nao e tocado — os blocos sao movidos inteiros.

Idempotente: se "culture" ja vier antes de "reasons", nao faz nada.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, ler, paginas, resolve_public  # noqa: E402

RE_REASONS = re.compile(r'<section class="reasons">.*?</section>', re.S)
RE_CULTURE = re.compile(r'<section class="culture">.*?</section>', re.S)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    alvos = paginas(pub, '<section class="culture">')
    print("paginas 'nosso trabalho': %d" % len(alvos))

    alterados = 0
    for path, rel in alvos:
        html = ler(path)
        mr = RE_REASONS.search(html)
        mc = RE_CULTURE.search(html)
        if not mr or not mc:
            print("AVISO: secoes nao encontradas em %s" % rel)
            continue
        if mc.start() < mr.start():
            print("ja na ordem certa: %s" % rel)
            continue
        # reasons vem primeiro: troca os dois blocos preservando o miolo entre eles
        meio = html[mr.end():mc.start()]
        html = (html[:mr.start()] + mc.group(0) + meio + mr.group(0)
                + html[mc.end():])
        gravar(path, html)
        alterados += 1
        print("cultura movida para antes de 'por que a Mirow': %s" % rel)

    print("\nresumo: %d arquivo(s) alterado(s)" % alterados)


if __name__ == "__main__":
    main()
