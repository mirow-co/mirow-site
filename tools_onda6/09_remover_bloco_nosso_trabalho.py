# -*- coding: utf-8 -*-
"""
09_remover_bloco_nosso_trabalho.py — tira o bloco "CONHECA MAIS SOBRE O NOSSO TRABALHO".

Uso:  python tools_onda6/09_remover_bloco_nosso_trabalho.py <raiz-da-arvore>

- Remove a <section class="our-jobs"> das 4 homes (o botao/faixa que ficava logo
  depois da barra de logos de clientes). Pedido do Mario na revisao da onda 6.
- A pagina /sobre-nos/nosso-trabalho/ continua existindo e linkada pelo menu.
- Nao ha <section> aninhada dentro dela.
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

PADRAO = re.compile(r'[ \t]*<section class="our-jobs">.*?</section>\n?', re.S)


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
            print("sem bloco our-jobs (ja removido): %s" % rel)
            continue
        if any("<section" in a[len('<section class="our-jobs">'):] for a in achados):
            print("AVISO: secao aninhada inesperada em %s — nada feito" % rel)
            continue
        html = PADRAO.sub("", html)
        with io.open(path, "w", encoding="utf-8", newline="") as f:
            f.write(html)
        alterados += 1
        print("bloco 'nosso trabalho' removido: %s" % rel)
    print("\nresumo: %d arquivo(s) alterado(s)" % alterados)


if __name__ == "__main__":
    main()
