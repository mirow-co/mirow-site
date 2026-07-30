# -*- coding: utf-8 -*-
"""
08_remover_modais_orfaos.py — remove os modais (bios) de quem saiu do quadro de lideres.

Uso:  python tools_onda6/08_remover_modais_orfaos.py <raiz-da-arvore>

- Depois do 06, os cards de Giulia Turcato, Lucas Duarte, Mariana Nakagawa e
  Matheus Strapasson sairam das paginas — mas os <div class="modal fade"
  id="modal_<slug>"> com a bio deles continuavam no HTML (invisiveis e ainda
  rastreaveis). Este script remove esses modais orfaos.
- Casamento de </div> feito por contagem, para nao cortar no lugar errado.
- Nao apaga nenhuma imagem do espelho (fotos ficam como arquivos orfaos, de proposito).
- Idempotente.
"""
import io
import os
import re
import sys

SLUGS_FORA = ["giulia-turcato", "lucas-duarte", "mariana-nakagawa", "matheus-strapasson"]

RE_DIV = re.compile(r'<div\b|</div>')


def resolve_public(root):
    root = os.path.abspath(root)
    if os.path.basename(root) == "public":
        return root
    cand = os.path.join(root, "public")
    if os.path.isdir(cand):
        return cand
    raise SystemExit("nao achei public/ em %s" % root)


def recorta_modal(html, slug):
    """Devolve (html_sem_modal, achou)."""
    marca = 'id="modal_%s"' % slug
    pos = html.find(marca)
    if pos < 0:
        return html, False
    ini = html.rfind("<div", 0, pos)
    if ini < 0:
        return html, False
    nivel = 0
    for m in RE_DIV.finditer(html, ini):
        nivel += 1 if m.group(0) == "<div" else -1
        if nivel == 0:
            return html[:ini] + html[m.end():], True
    return html, False


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    alterados = 0
    for root, _dirs, files in os.walk(pub):
        for f in files:
            if f != "index.html":
                continue
            path = os.path.join(root, f)
            with io.open(path, encoding="utf-8") as fh:
                html = fh.read()
            if not any('id="modal_%s"' % s in html for s in SLUGS_FORA):
                continue
            rel = os.path.relpath(path, pub).replace(os.sep, "/")
            tirados = []
            for slug in SLUGS_FORA:
                while True:
                    html, achou = recorta_modal(html, slug)
                    if not achou:
                        break
                    tirados.append(slug)
            with io.open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(html)
            alterados += 1
            print("modais orfaos removidos: %s (%s)" % (rel, ", ".join(tirados)))
    print("\nresumo: %d arquivo(s) alterado(s)" % alterados)


if __name__ == "__main__":
    main()
