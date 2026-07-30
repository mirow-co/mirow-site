# -*- coding: utf-8 -*-
"""
02_remover_posts_home.py — tira os posts/insights da pagina inicial.

Uso:  python tools_onda6/02_remover_posts_home.py <raiz-da-arvore>

- Remove o bloco <div class="banner__insights">...</div> do hero (o carrossel de
  cards de post: "A Inteligencia Artificial vai dominar o mundo?", "Green
  hydrogen...", etc.).
- As paginas de insights continuam existindo; elas so saem da home.
- Idempotente: rodar de novo nao acha mais nada.
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

# o bloco tem exatamente 2 niveis de div (wrap + itens <a>), sem div aninhada extra
PADRAO = re.compile(r'<div class="banner__insights">.*?</div></div>', re.S)


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
        n = len(PADRAO.findall(html))
        if n == 0:
            print("sem posts no hero (ja removido): %s" % rel)
            continue
        html = PADRAO.sub("", html)
        with io.open(path, "w", encoding="utf-8", newline="") as f:
            f.write(html)
        alterados += 1
        print("posts do hero removidos: %s (%d bloco[s])" % (rel, n))
    print("\nresumo: %d arquivo(s) alterado(s)" % alterados)


if __name__ == "__main__":
    main()
