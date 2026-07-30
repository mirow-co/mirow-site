# -*- coding: utf-8 -*-
"""
14_logos_clientes_sem_inline_svg.py — protege a barra de logos do plugin SVG Support.

Uso:  python tools_onda6/14_logos_clientes_sem_inline_svg.py <raiz-da-arvore>

O problema (achado no QA da revisao da onda 6, depois de repor o jQuery):
- O site usa o plugin "SVG Support" com ForceInlineSVGActive="true". Com jQuery
  funcionando, ele troca TODO <img src="....svg"> por um <svg> inline.
- Os 13 logos vetoriais de clientes da barra da onda 5 vinham de fontes diferentes e
  usam ids/classes internas genericas (`a`, `st0`, `clip0`...). Inline no mesmo
  documento, essas definicoes colidem entre si (e ainda passam pelo DOMPurify) e os
  logos saem picados/deformados. Na onda 5 isso passou batido porque o jQuery estava
  404 no espelho e o plugin nunca rodava.

A protecao:
- Acrescentar `?ver=1` ao src dos logos. O plugin so inlina quando o src termina em
  "svg" (`h.endsWith("svg")` no svgs-inline-min.js), entao com a query ele ignora
  esses <img> e o navegador renderiza o SVG como imagem — exatamente o resultado que
  o Mario aprovou na onda 5.
- Nada de tema alterado, nada de arquivo de logo alterado, nenhum outro <img> tocado
  (os icones das praticas continuam inline, como no site de producao).
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

# so os logos da barra de clientes
RE_LOGO = re.compile(r'(<img src="[^"]*?/uploads/2026/07/clientes/[^"]+\.svg)(")')
VER = '?ver=1'


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
        n = len(RE_LOGO.findall(html))
        if n == 0:
            print("logos ja protegidos: %s" % rel)
            continue
        html = RE_LOGO.sub(lambda m: m.group(1) + VER + m.group(2), html)
        with io.open(path, "w", encoding="utf-8", newline="") as f:
            f.write(html)
        alterados += 1
        print("logos protegidos do inline: %s (%d logo[s] svg)" % (rel, n))
    print("\nresumo: %d arquivo(s) alterado(s)" % alterados)


if __name__ == "__main__":
    main()
