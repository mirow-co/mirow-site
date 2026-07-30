# -*- coding: utf-8 -*-
"""
03_matar_slogan.py — troca o slogan "Embrace to Enhance" (e suas versoes PT/DE)
por "Consultoria de estrategia" / "Strategy consulting" / "Strategieberatung".

Uso:  python tools_onda5/03_matar_slogan.py <raiz-da-arvore>

- Varre TODAS as paginas .html do espelho (pega tambem caminhos-alias).
- Troca apenas TEXTO (hero <h2>, <title>, meta). Nao mexe em classe, tag, estilo.
- Idempotente: rodar de novo nao acha mais nada.
"""
import io
import os
import sys

# (antigo, novo)
TROCAS = [
    ("Envolver para desenvolver", u"Consultoria de estratégia"),
    ("Embrace to Enhance", "Strategy consulting"),
    ("Embrace to enhance", "Strategy consulting"),
    ("Einbinden, um zu entwickeln", "Strategieberatung"),
    ("Einbeziehen um zu entwickeln", "Strategieberatung"),
]


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
    total = 0
    for root, _dirs, files in os.walk(pub):
        for f in files:
            if not f.endswith(".html"):
                continue
            path = os.path.join(root, f)
            with io.open(path, encoding="utf-8") as fh:
                html = fh.read()
            novo = html
            achados = []
            for antigo, sub in TROCAS:
                if antigo in novo:
                    achados.append("%s x%d" % (antigo, novo.count(antigo)))
                    novo = novo.replace(antigo, sub)
            if novo != html:
                with io.open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(novo)
                alterados += 1
                print("slogan trocado em %s (%s)"
                      % (os.path.relpath(path, pub).replace(os.sep, "/"), "; ".join(achados)))
            total += 1
    print("\nresumo: %d de %d arquivo(s) alterado(s)" % (alterados, total))


if __name__ == "__main__":
    main()
