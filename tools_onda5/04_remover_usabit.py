# -*- coding: utf-8 -*-
"""
04_remover_usabit.py — remove a barra/credito do fornecedor "Usabit" de todas as paginas.

Uso:  python tools_onda5/04_remover_usabit.py <raiz-da-arvore>

Remove:
  1) o bloco <div class="footer__signature"> ... </div> (logo + link usabit.com.br)
     imediatamente antes de </footer>;
  2) o valor "developer":"Usabit - contato@usabit.com.br" no objeto siteData
     (fica string vazia — a chave e mantida para nao quebrar o JS do tema).

Nao toca em mais nada do footer. Idempotente.
"""
import io
import os
import re
import sys

SIG_RE = re.compile(r'[ \t]*<div class="footer__signature">.*?</div>\s*(?=</footer>)', re.S)
DEV_ANTIGO = '"developer":"Usabit - contato@usabit.com.br"'
DEV_NOVO = '"developer":""'


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
    sobrou = []
    for root, _dirs, files in os.walk(pub):
        for f in files:
            if not f.endswith(".html"):
                continue
            path = os.path.join(root, f)
            with io.open(path, encoding="utf-8") as fh:
                html = fh.read()
            novo = SIG_RE.sub("\n    ", html)
            novo = novo.replace(DEV_ANTIGO, DEV_NOVO)
            if novo != html:
                with io.open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(novo)
                alterados += 1
            if re.search("usabit", novo, re.I):
                sobrou.append(os.path.relpath(path, pub).replace(os.sep, "/"))
    print("usabit removido: %d arquivo(s) alterado(s)" % alterados)
    if sobrou:
        print("ATENCAO: ainda ha mencao a usabit em %d arquivo(s):" % len(sobrou))
        for p in sobrou[:20]:
            print("  -", p)
    else:
        print("nenhuma mencao a usabit restante no espelho")


if __name__ == "__main__":
    main()
