# -*- coding: utf-8 -*-
"""
03_remover_depoimentos.py — remove os cards de depoimento da home (todas as linguas).

Uso:  python tools_onda6/03_remover_depoimentos.py <raiz-da-arvore>

- Remove a <section class="testimonial"> inteira das homes (PT/EN/DE), com os
  depoimentos tipo "PROJETO DE OPERACOES, INDUSTRIA AUTOMOTIVA - a Mirow se
  diferencia pela empatia...".
- Nao ha <section> aninhada dentro dela; o recorte vai do inicio da secao ate o
  primeiro </section>.
- Idempotente.
"""
import io
import os
import re
import sys

HOMES = [
    "pt/index.html",
    "en/index.html",
    "en/homepage/index.html",
    "de/index.html",
]

PADRAO = re.compile(r'[ \t]*<section class="testimonial">.*?</section>\n?', re.S)


def resolve_public(root):
    root = os.path.abspath(root)
    if os.path.basename(root) == "public":
        return root
    cand = os.path.join(root, "public")
    if os.path.isdir(cand):
        return cand
    raise SystemExit("nao achei public/ em %s" % root)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    alterados = 0
    for rel in HOMES:
        path = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(path):
            print("AVISO: nao existe %s" % rel)
            continue
        with io.open(path, encoding="utf-8") as f:
            html = f.read()
        achados = PADRAO.findall(html)
        if not achados:
            print("sem depoimentos (ja removido): %s" % rel)
            continue
        if any("<section" in a[len('<section class="testimonial">'):] for a in achados):
            print("AVISO: secao aninhada inesperada em %s — nada feito" % rel)
            continue
        html = PADRAO.sub("", html)
        with io.open(path, "w", encoding="utf-8", newline="") as f:
            f.write(html)
        alterados += 1
        print("depoimentos removidos: %s (%d secao[oes])" % (rel, len(achados)))
    print("\nresumo: %d arquivo(s) alterado(s)" % alterados)


if __name__ == "__main__":
    main()
