# -*- coding: utf-8 -*-
"""35 — S-27 (issue #77): big numbers empilhados no lado direito da capa (hero).

Uso:
    python tools_onda6/35_hero_big_numbers.py <raiz-que-contem-public>

PEDIDO (verbatim — Andreas via Mario, 2026-07-31)
------------------------------------------------
    Parte dos numeros tem que ficar bem mais em cima
    -> Colocar na capa, do lado direito os big numbers um em cima do outro em
       sequencia

DE ONDE VEM O CONTEUDO
----------------------
Dos MESMOS numeros da secao "nossos numeros" da propria pagina (nada e inventado
nem redigitado): o script le os pares <strong>/<span> de `our-numbers__list` e
monta a pilha. O ponto final e removido aqui tambem, para o script nao depender
da ordem de execucao com o 34 (S-06).

PRIMEIRA DOBRA
--------------
A pilha e `position:absolute` dentro do `.container` do hero: nao entra no fluxo,
entao a altura do hero — e a dobra exata medida pelas assercoes V01–V05 — nao
muda. Abaixo de 1200px a pilha some (os numeros seguem na secao propria, logo
abaixo); nessa largura nao ha coluna livre a direita sem espremer o slogan.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _onda7_css import escrever_bloco_css, gravar, ler, resolve_public  # noqa: E402

CHAVE = "hero-numeros"
ONDA = "onda10"

HOMES = ["pt/index.html", "en/index.html", "de/index.html", "en/homepage/index.html"]

ANCORA = "<!-- /onda8:hero-contatos -->"

REX_BLOCO = re.compile(r'\s*<!-- onda10:hero-numeros -->.*?<!-- /onda10:hero-numeros -->', re.S)
REX_LISTA = re.compile(r'<div class="row our-numbers__list">(.*?)</div>\s*</div>\s*</section>', re.S)
REX_PAR = re.compile(r'<strong>(.*?)</strong>\s*<span>(.*?)</span>', re.S)

ROTULO = {"pt": u"Nossos números", "en": u"Our figures", "de": u"Unsere Zahlen"}

CSS = u"""
/* onda10 (S-27 / #77) — big numbers empilhados a direita da capa */
.hero-numeros{display:none}
@media only screen and (min-width: 1200px){
  .homepage .banner .container{position:relative}
  /* o texto do hero para antes da pilha, para nao passar por baixo dela */
  .homepage .banner .row>[class^=col]>h2,
  .homepage .banner .row>[class^=col]>p,
  .homepage .banner .row>[class^=col]>.hero-contatos{max-width:62%}
  .hero-numeros{
    display:flex;flex-direction:column;justify-content:center;gap:20px;
    list-style:none;margin:0;padding:0;
    position:absolute;right:calc(var(--bs-gutter-x, 1.5rem) * .5);top:50%;
    transform:translateY(-50%);
    width:300px;text-align:right;z-index:4}
  .hero-numeros__item{display:block;border-right:2px solid rgba(0,173,236,.85);
    padding-right:14px}
  .hero-numeros__valor{display:block;
    font-family:var(--fontFamily);font-weight:800;
    font-size:40px;line-height:1;color:#00adec}
  .hero-numeros__texto{display:block;margin-top:5px;
    font-family:var(--secondaryFontFamily);font-weight:400;
    font-size:14px;line-height:1.3;color:rgba(255,255,255,.92)}
}
@media only screen and (min-width: 1200px) and (max-height: 820px){
  .hero-numeros{gap:13px;width:270px}
  .hero-numeros__valor{font-size:33px}
  .hero-numeros__texto{font-size:13px}
}
"""


def numeros_da_pagina(h, rel):
    m = REX_LISTA.search(h)
    if not m:
        raise SystemExit(u"nao achei a secao our-numbers em %s" % rel)
    pares = REX_PAR.findall(m.group(1))
    if len(pares) < 3:
        raise SystemExit(u"esperava >= 3 numeros em %s, achei %d" % (rel, len(pares)))
    return [(v.strip(), t.strip().rstrip(u".")) for v, t in pares]


def montar(pares, rotulo):
    itens = u"".join(
        u'<li class="hero-numeros__item">'
        u'<strong class="hero-numeros__valor">%s</strong>'
        u'<span class="hero-numeros__texto">%s</span></li>' % (v, t)
        for v, t in pares)
    return (u'\n                <!-- onda10:hero-numeros -->'
            u'\n                <ul class="hero-numeros" aria-label="%s">%s</ul>'
            u'\n                <!-- /onda10:hero-numeros -->' % (rotulo, itens))


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    mudou_css = escrever_bloco_css(pub, CHAVE, CSS, onda=ONDA)
    alteradas = []
    for rel in HOMES:
        p = os.path.join(pub, rel.replace("/", os.sep))
        h = ler(p)
        from _onda7_css import idioma_da_pagina
        bloco = montar(numeros_da_pagina(h, rel), ROTULO[idioma_da_pagina(h)])
        limpo = REX_BLOCO.sub(u"", h)
        i = limpo.find(ANCORA)
        if i < 0:
            raise SystemExit(u"nao achei a ancora %s em %s" % (ANCORA, rel))
        i += len(ANCORA)
        novo = limpo[:i] + bloco + limpo[i:]
        if novo == h:
            continue
        gravar(p, novo)
        alteradas.append(rel)
    print(u"bloco %s:%s %s" % (ONDA, CHAVE, u"gravado" if mudou_css else u"ja estava igual"))
    print(u"paginas alteradas: %s" % (u", ".join(alteradas) if alteradas else u"nenhuma (ja estava igual)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
