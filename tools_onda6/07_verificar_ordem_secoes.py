# -*- coding: utf-8 -*-
"""
07_verificar_ordem_secoes.py — confere (e reordena, se preciso) a ordem das secoes da home.

Uso:  python tools_onda6/07_verificar_ordem_secoes.py <raiz-da-arvore>

Ordem esperada apos a onda 6 (lista do Mario, itens 3 a 7):

  banner (titulo + subtitulo) -> clientes-logos -> our-jobs -> home-experience
  -> our-numbers (numeros) -> certificates (reconhecimentos) -> home-leaders -> links

- Nao ha mais testimonial nem posts no hero.
- Script de leitura: reporta a ordem encontrada e falha (exit 1) se divergir, para
  a divergencia aparecer no QA em vez de passar batido. Nao edita nada.
"""
import io
import os
import re
import sys

ESPERADA = ["banner", "clientes-logos", "our-jobs", "home-experience",
            "our-numbers", "certificates", "home-leaders", "links"]

PROIBIDAS = ["testimonial"]

HOMES = ["pt/index.html", "en/index.html", "en/homepage/index.html", "de/index.html"]


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
    problemas = 0
    for rel in HOMES:
        path = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(path):
            print("AVISO: nao existe %s" % rel)
            continue
        with io.open(path, encoding="utf-8") as f:
            html = f.read()
        achadas = re.findall(r'<section class="([a-z0-9\-]+)"', html)
        ok = achadas == ESPERADA
        proibida = [p for p in PROIBIDAS if p in achadas]
        posts = "banner__insights" in html
        print("%s %s: %s%s%s" % ("OK  " if (ok and not proibida and not posts) else "ERRO",
                                 rel, " > ".join(achadas),
                                 "  [secao proibida: %s]" % ", ".join(proibida) if proibida else "",
                                 "  [ainda ha posts no hero]" if posts else ""))
        if not ok or proibida or posts:
            problemas += 1
    print("\nresumo: %d home(s) fora do esperado" % problemas)
    sys.exit(1 if problemas else 0)


if __name__ == "__main__":
    main()
