# -*- coding: utf-8 -*-
"""
40_hero_contatos_contato.py — onda 11, issue S-08.

Uso:  python tools_onda6/40_hero_contatos_contato.py <raiz-que-contem-public>

Pedido (issue mirow-co/mirow-marketing#57): o hero da pagina de CONTATO hoje so
mostra o LinkedIn ("Confira nosso Linkedin"). As homes ja tem os 4 canais
(WhatsApp, e-mail, LinkedIn, Instagram) desde a onda 8 (22_hero_contatos.py) —
aqui replicamos o MESMO padrao (mesmas classes CSS `.hero-contatos` /
`.hero-contatos__link`, ja escritas em onda6.css pela onda 8) na secao
`internal-banner__links` das paginas de contato.

Zero CSS novo: as classes reaproveitadas ja existem em
public/wp-content/uploads/2026/07/onda6/onda6.css (blocos onda8:hero-contatos e
onda8:hero-contatos-v2). Este script so mexe em HTML.

Paginas atingidas (todas as variantes de contato do espelho, mesma lista do
29_contato_enxuto.py):
    contato/  ·  pt/contato/  ·  en/contact-us/  ·  de/kontakt/  ·  novo/contato/

Idempotente: se o marcador onda11:s08-hero-contatos ja esta presente, o script
tira a versao antiga antes de gravar a nova (mesma logica do 22).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import (base_prefix, garantir_link_css, gravar,  # noqa: E402
                        idioma_da_pagina, ler, resolve_public)
from _onda8_contatos import (ARIA, EMAIL, INSTAGRAM, LINKEDIN, ROTULOS,  # noqa: E402
                             SVG_IG, SVG_LI, SVG_MAIL, SVG_WA, url_whatsapp)

PAGINAS = [
    "contato/index.html",
    "pt/contato/index.html",
    "en/contact-us/index.html",
    "de/kontakt/index.html",
    "novo/contato/index.html",
]

INI = u"<!-- onda11:s08-hero-contatos -->"
FIM = u"<!-- /onda11:s08-hero-contatos -->"

ANTIGO = re.compile(
    r'<ul class="internal-banner__links"[^>]*>.*?<ul>',
    re.S,
)


def bloco(idioma):
    lab_wa, lab_mail, lab_li, lab_ig = ROTULOS[idioma]
    wa = url_whatsapp(idioma)
    itens = [
        (u"hero-contatos__link hero-contatos__link--wa", wa, SVG_WA, lab_wa, True),
        (u"hero-contatos__link", u"mailto:%s" % EMAIL, SVG_MAIL, lab_mail, False),
        (u"hero-contatos__link", LINKEDIN, SVG_LI, lab_li, True),
        (u"hero-contatos__link", INSTAGRAM, SVG_IG, lab_ig, True),
    ]
    lis = []
    for cls, href, svg, rotulo, externo in itens:
        extra = u' target="_blank" rel="noopener noreferrer"' if externo else u""
        lis.append(u'<li><a class="%s" href="%s"%s>%s<span>%s</span></a></li>'
                   % (cls, href, extra, svg, rotulo))
    return (u'%s<ul class="hero-contatos" aria-label="%s" data-aos="fade-right">%s</ul>%s'
            % (INI, ARIA[idioma], u"".join(lis), FIM))


def aplicar(html, idioma):
    # idempotencia: tira marcador antigo (se ja rodou antes) e o <ul> original
    # do tema (se ainda for a primeira vez).
    if INI in html:
        html = re.sub(re.escape(INI) + r".*?" + re.escape(FIM), "__PLACEHOLDER__",
                      html, count=1, flags=re.S)
        html = html.replace("__PLACEHOLDER__", bloco(idioma), 1)
        return html, True
    if not ANTIGO.search(html):
        return html, False
    novo = ANTIGO.sub(lambda m: bloco(idioma), html, count=1)
    return novo, True


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    alterados = 0
    for rel in PAGINAS:
        path = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(path):
            print("AVISO: nao existe %s" % rel)
            continue
        html = ler(path)
        idioma = idioma_da_pagina(html)
        novo, ok = aplicar(html, idioma)
        if not ok:
            print("AVISO: bloco internal-banner__links nao encontrado em %s" % rel)
            continue
        novo = garantir_link_css(novo, base_prefix(novo))
        if novo != html:
            gravar(path, novo)
            alterados += 1
            print("hero com 4 contatos (%s): %s" % (idioma, rel))
        else:
            print("sem mudanca: %s" % rel)

    print("\nresumo: %d arquivo(s) HTML alterado(s)" % alterados)


if __name__ == "__main__":
    main()
