# -*- coding: utf-8 -*-
"""34 — S-06 (issue #55): secao "nossos numeros" da home.

Uso:
    python tools_onda6/34_numeros_home.py <raiz-que-contem-public>

PEDIDO
------
(a) tirar o ponto final dos 4 textos ("clientes atendidos." -> "clientes atendidos");
(b) setinhas / escada de progressao entre os numeros;
(c) numero um pouco menor e texto um pouco maior.

COMO
----
(a) e HTML: so o ponto FINAL de cada <span> do bloco `our-numbers__list` cai —
    abreviacoes internas (o alemao tem "Mrd.") ficam intactas.
(b) e (c) sao CSS, no bloco marcado onda10:numeros do onda6.css:
    - o tema ja escalonava as 4 colunas de forma aleatoria (110/20/60/0px).
      Aqui vira escada de verdade: 120/80/40/0 — cada numero um degrau acima do
      anterior — com uma seta ↗ ciana entre colunas vizinhas (pseudo-elemento,
      sem tocar no HTML).
    - numero 90px -> 72px; texto 22px -> 26px.

A secao fica abaixo da primeira dobra, entao V01–V05 nao sao afetadas.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _onda7_css import escrever_bloco_css, gravar, ler, resolve_public  # noqa: E402

CHAVE = "numeros"
ONDA = "onda10"

HOMES = ["pt/index.html", "en/index.html", "de/index.html", "en/homepage/index.html"]

REX_LISTA = re.compile(r'(<div class="row our-numbers__list">)(.*?)(</div>\s*</div>\s*</section>)',
                       re.S)
REX_SPAN = re.compile(r'(<span>)([^<]*?)\.(</span>)')

CSS = u"""
/* onda10 (S-06 / #55) — numeros da home: escada de progressao, numero menor,
   texto maior. O ponto final saiu do HTML (nao da para tirar por CSS). */
.our-numbers__list>[class^=col]{position:relative}
@media only screen and (min-width: 992px){
  /* escada: cada numero um degrau acima do anterior (o tema escalonava sem ordem) */
  .our-numbers__list>[class^=col]:nth-child(1){margin-top:120px}
  .our-numbers__list>[class^=col]:nth-child(2){margin-top:80px}
  .our-numbers__list>[class^=col]:nth-child(3){margin-top:40px}
  .our-numbers__list>[class^=col]:nth-child(4){margin-top:0}
  /* seta de progressao entre colunas vizinhas */
  .our-numbers__list>[class^=col]+[class^=col]::before{
    content:"↗";
    position:absolute;left:-16px;top:-44px;
    color:#00adec;font-size:34px;line-height:1;font-weight:700;
    pointer-events:none}
  .our-numbers__list strong{font-size:72px;font-size:4.5rem;padding-bottom:12px}
  .our-numbers__list span{font-size:26px;font-size:1.625rem}
}
@media only screen and (max-width: 991px){
  .our-numbers__list strong{font-size:52px;font-size:3.25rem}
  .our-numbers__list span{font-size:19px;font-size:1.1875rem}
}
"""


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    mudou_css = escrever_bloco_css(pub, CHAVE, CSS, onda=ONDA)
    alteradas = []
    for rel in HOMES:
        p = os.path.join(pub, rel.replace("/", os.sep))
        h = ler(p)
        m = REX_LISTA.search(h)
        if not m:
            raise SystemExit(u"nao achei o bloco our-numbers__list em %s" % rel)
        novo = REX_SPAN.sub(r"\1\2\3", m.group(2))
        if novo == m.group(2):
            continue
        gravar(p, h[:m.start(2)] + novo + h[m.end(2):])
        alteradas.append(rel)
    print(u"bloco %s:%s %s" % (ONDA, CHAVE, u"gravado" if mudou_css else u"ja estava igual"))
    print(u"paginas alteradas: %s" % (u", ".join(alteradas) if alteradas else u"nenhuma (ja estava igual)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
