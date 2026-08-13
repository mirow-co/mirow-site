# -*- coding: utf-8 -*-
u"""106 — issue #220: inclui na lista de imprensa a coluna Vaivem (Folha, 10/02/2026)
em que Andreas Mirow alerta para o desequilibrio estrutural da celulose.

Uso:
    python tools_onda6/106_imprensa_folha_vaivem_2026.py <raiz-que-contem-public>

Pedido do Mario (13/08): "me ajude a adicionar o link para esse artigo no
mirow-imprensa" + URL da Folha.

Dados conferidos NA FONTE (JSON-LD da propria pagina da Folha, baixada em 13/08):
  headline      Exportacao de celulose cresce, mas setor pode ter desequilibrio
  datePublished 2026-02-10T20:00:00Z
  subtitle      "Especialista Andreas Mirow alerta sobre uma diferenca entre
                 oferta e demanda"
  coluna        Vaivem das Commodities

O item entra como o MAIS RECENTE (10/02/2026 > 30/04/2025, topo atual) nas tres
paginas — pt/imprensa, en/press, de/presse — que listam os mesmos 28 itens.

O logo da Folha ja existe no repo (imprensa-logos/folha.svg), usado pelo item de
02/03/2024; nao ha download nem chamada externa.

Idempotente: se a URL ja estiver na lista, nao faz nada (0 mudancas no 2o run).
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, ler, resolve_public  # noqa: E402

PAGINAS = [
    os.path.join("pt", "imprensa", "index.html"),
    os.path.join("en", "press", "index.html"),
    os.path.join("de", "presse", "index.html"),
]

URL = ("https://www1.folha.uol.com.br/colunas/vaivem/2026/02/"
       "exportacao-de-celulose-cresce-mas-setor-pode-ter-desequilibrio.shtml")
VEICULO = u"Folha de S.Paulo"
LOGO = "/wp-content/uploads/2026/08/imprensa-logos/folha.svg?ver=1"
DATA_ISO = "2026-02-10"
DATA_BR = "10/02/2026"
TITULO = u"Exportação de celulose cresce, mas setor pode ter desequilíbrio"

ITEM = (
    u'<li class="onda18-imprensa__item">'
    u'<a class="onda26-imprensa__link" href="%s" target="_blank" rel="noopener noreferrer">'
    u'<img class="onda41-imprensa__logo" src="%s" alt="%s">'
    u'<span class="onda18-imprensa__veiculo">%s</span>'
    u'<time class="onda18-imprensa__data" datetime="%s">%s</time>'
    u'<span class="onda18-imprensa__titulo">%s</span>'
    u'</a></li>'
) % (URL, LOGO, VEICULO, VEICULO, DATA_ISO, DATA_BR, TITULO)

REX_PRIMEIRO = re.compile(r'<li class="onda18-imprensa__item">', re.S)


def aplicar(pub):
    mudou = 0
    for rel in PAGINAS:
        p = os.path.join(pub, rel)
        if not os.path.exists(p):
            print(u"  ! ausente: %s" % rel)
            continue
        h = ler(p)
        if URL in h:
            print(u"  = %s (ja tem)" % rel)
            continue
        m = REX_PRIMEIRO.search(h)
        if not m:
            print(u"  ! %s: lista nao encontrada" % rel)
            continue
        h = h[:m.start()] + ITEM + h[m.start():]
        gravar(p, h)
        mudou += 1
        print(u"  + %s" % rel)
    return mudou


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    pub = resolve_public(sys.argv[1])
    print(u"106 — Folha/Vaivem 10/02/2026 na lista de imprensa")
    n = aplicar(pub)
    print(u"%d pagina(s) alterada(s)" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
