# -*- coding: utf-8 -*-
"""32 — S-01 (issue #51): slogan do hero em escadinha (indentacao progressiva).

Uso:
    python tools_onda6/32_hero_slogan_escadinha.py <raiz-que-contem-public>

O PEDIDO
--------
    Estrategia
        Confianca
            Resultado

As 3 linhas ja existem desde a onda 8.2 (altura e espacamento acertados). O que
faltava era o RECUO CRESCENTE. As palavras NAO mudam — a tripla esta em decisao
na issue #79; aqui so muda a apresentacao.

COMO
----
Cada palavra vira um <span class="onda10-degrau onda10-degrau--N">. Os <br>
continuam sendo exatamente 2 (a assercao H01 conta eles) e as palavras seguem
dentro do <h2 data-aos="fade-right">.

Os spans ficam **inline** (nao inline-block) de proposito: elemento inline aceita
margin horizontal e nao cria caixa de linha propria, entao a altura do <h2> — e
com ela a primeira dobra exata (V01–V05) — nao muda um pixel.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _onda7_css import escrever_bloco_css, gravar, ler, resolve_public  # noqa: E402

CHAVE = "hero-escadinha"
ONDA = "onda10"

HOMES = ["pt/index.html", "en/index.html", "de/index.html", "en/homepage/index.html"]

REX_H2 = re.compile(r'(<h2 data-aos="fade-right">)(.*?)(</h2>)', re.S)

CSS = u"""
/* onda10 (S-01 / #51) — slogan do hero em escadinha */
.homepage .banner h2 .onda10-degrau{display:inline}
.homepage .banner h2 .onda10-degrau--2{margin-left:.55em}
.homepage .banner h2 .onda10-degrau--3{margin-left:1.1em}
@media only screen and (min-width: 992px){
  .homepage .banner h2 .onda10-degrau--2{margin-left:.9em}
  .homepage .banner h2 .onda10-degrau--3{margin-left:1.8em}
}
"""


def transformar(bloco):
    """<h2>A<br>B<br>C</h2> -> spans com degrau. Idempotente."""
    if "onda10-degrau" in bloco:
        return bloco
    partes = bloco.split("<br>")
    if len(partes) != 3:
        raise SystemExit(u"esperava 3 linhas no slogan, achei %d: %r" % (len(partes), bloco))
    novas = []
    for i, p in enumerate(partes, 1):
        novas.append(u'<span class="onda10-degrau onda10-degrau--%d">%s</span>' % (i, p.strip()))
    return u"<br>".join(novas)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    mudou_css = escrever_bloco_css(pub, CHAVE, CSS, onda=ONDA)
    alteradas = []
    for rel in HOMES:
        p = os.path.join(pub, rel.replace("/", os.sep))
        h = ler(p)
        m = REX_H2.search(h)
        if not m:
            raise SystemExit(u"nao achei o <h2> do slogan em %s" % rel)
        novo_bloco = transformar(m.group(2))
        if novo_bloco == m.group(2):
            continue
        gravar(p, h[:m.start(2)] + novo_bloco + h[m.end(2):])
        alteradas.append(rel)
    print(u"bloco %s:%s %s" % (ONDA, CHAVE, u"gravado" if mudou_css else u"ja estava igual"))
    print(u"paginas alteradas: %s" % (u", ".join(alteradas) if alteradas else u"nenhuma (ja estava igual)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
