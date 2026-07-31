# -*- coding: utf-8 -*-
"""58 — S-38: linha legal do rodape enxuta — so o link da politica.

Uso:
    python tools_onda6/58_rodape_legal_enxuto.py <raiz-que-contem-public>

Pedido do Mario (31/07): "tambem nao precisa de tudo isso aqui mais. basta um
link pequeno para a politica de privacidade" — com a barra clonada (S-36 v2)
no rodape, a linha legal antiga (politica | LOGO GRANDE | linkedin) ficou
redundante: o logo e o LinkedIn ja estao na propria barra.

O QUE FAZ
---------
Em toda pagina com <footer class="footer">, substitui a row legal (a que
contem .footer__brand) por uma linha unica com SO o link da politica de
privacidade — o proprio <a class="footer__contacts-link"> da pagina (mesmo
href/rotulo por idioma; fonte unica). CSS (bloco onda15:rodape-legal) deixa
o link pequeno e discreto, centrado.

Idempotente: o bloco novo e regravado entre marcadores.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, gravar, ler, resolve_public  # noqa: E402

MARK_INI = "<!-- onda15:rodape-legal -->"
MARK_FIM = "<!-- /onda15:rodape-legal -->"

REX_LINK = re.compile(r'<a class="footer__contacts-link"[^>]*>[^<]*</a>')

CSS = """/* S-38: linha legal enxuta — o logo e o LinkedIn ja moram na barra clonada
   (S-36 v2); sobra so o link pequeno da politica, discreto e centrado. */
.rodape-legal{text-align:center;padding:2px 0 0}
.rodape-legal .footer__contacts-link{font-size:12px;opacity:.65}
.rodape-legal .footer__contacts-link:hover{opacity:1}"""


def achar_row_legal(h):
    """(ini, fim) da <div class="row"> que contem .footer__brand."""
    marca = h.find("footer__brand")
    if marca < 0:
        return None
    ini = h.rfind('<div class="row">', 0, marca)
    if ini < 0:
        return None
    # anda pelos <div até fechar a row
    pos = ini + 1
    nivel = 1
    rex = re.compile(r'<div\b|</div>')
    while nivel:
        m = rex.search(h, pos)
        if not m:
            return None
        nivel += 1 if m.group(0) == '<div' else -1
        pos = m.end()
    return ini, pos


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    mudou_css = escrever_bloco_css(pub, "rodape-legal", CSS, onda="onda15")
    print("bloco onda15:rodape-legal %s" % ("gravado" if mudou_css else "ja estava igual"))

    alterados = 0
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if not n.endswith(".html"):
                continue
            p = os.path.join(dp, n)
            h = ler(p)
            if '<footer class="footer">' not in h:
                continue
            mlink = REX_LINK.search(h)
            if not mlink:
                continue
            bloco = ('%s<div class="row"><div class="col-12 rodape-legal">%s'
                     '</div></div>%s' % (MARK_INI, mlink.group(0), MARK_FIM))
            if MARK_INI in h:
                velho = h[h.index(MARK_INI):h.index(MARK_FIM) + len(MARK_FIM)]
                novo = h.replace(velho, bloco, 1)
            else:
                par = achar_row_legal(h)
                if not par:
                    continue
                ini, fim = par
                novo = h[:ini] + bloco + h[fim:]
            if novo != h:
                gravar(p, novo)
                alterados += 1
    print("resumo: %d pagina(s) com a linha legal enxuta" % alterados)


if __name__ == "__main__":
    main()
