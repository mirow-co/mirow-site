# -*- coding: utf-8 -*-
"""
10_reconhecimentos_depois_lideres.py — desce os reconhecimentos para depois dos lideres.

Uso:  python tools_onda6/10_reconhecimentos_depois_lideres.py <raiz-da-arvore>

- Ordem final da home pedida pelo Mario na revisao da onda 6:
  numeros (our-numbers) -> lideres (home-leaders) -> reconhecimentos (certificates).
- O bloco <section class="certificates"> e recortado inteiro e reinserido logo antes
  de <section class="links"> (que e o ultimo bloco da home, "Como podemos ajudar?").
  Fica depois da secao de lideres e depois dos modais de bio, que moram entre as duas.
- Move o markup como esta, sem editar uma linha do conteudo nem do tema.
- Idempotente: se certificates ja vem depois de home-leaders, nao faz nada.
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

RE_CERT = re.compile(r'[ \t]*<section class="certificates">.*?</section>\n?', re.S)
ANCORA = '<section class="links">'


def resolve_public(root):
    root = os.path.abspath(root)
    if os.path.basename(root) == "public":
        return root
    cand = os.path.join(root, "public")
    if os.path.isdir(cand):
        return cand
    raise SystemExit("nao achei public/ em %s" % root)


def ordem(html):
    return re.findall(r'<section class="([a-z0-9\-]+)"', html)


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
        secoes = ordem(html)
        if "certificates" not in secoes or "home-leaders" not in secoes:
            print("AVISO: secoes esperadas nao encontradas em %s" % rel)
            continue
        if secoes.index("certificates") > secoes.index("home-leaders"):
            print("ja esta na ordem certa: %s" % rel)
            continue
        m = RE_CERT.search(html)
        if not m:
            print("AVISO: nao consegui recortar certificates em %s" % rel)
            continue
        bloco = m.group(0)
        html_sem = html[:m.start()] + html[m.end():]
        pos = html_sem.find(ANCORA)
        if pos < 0:
            print("AVISO: ancora <section class=\"links\"> nao encontrada em %s" % rel)
            continue
        novo = html_sem[:pos] + bloco.strip("\n") + "\n\n" + html_sem[pos:]
        with io.open(path, "w", encoding="utf-8", newline="") as f:
            f.write(novo)
        alterados += 1
        print("reconhecimentos movidos: %s (%s)" % (rel, " > ".join(ordem(novo))))
    print("\nresumo: %d arquivo(s) alterado(s)" % alterados)


if __name__ == "__main__":
    main()
