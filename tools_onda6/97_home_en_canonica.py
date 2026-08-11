# -*- coding: utf-8 -*-
"""Onda 41 / S-135 (issue mirow-marketing#65): /en/ é a home EN canônica;
/en/homepage/ vira stub de redirect.

Decisão (06/08): /en/ — simétrica a /pt/ e /de/, e é para ela que o menu, o
seletor de idiomas e a raiz do Pages já apontam. Nenhuma página de conteúdo
linka /en/homepage/ (medido: só ela mesma se citava). Fecha também a pendência
da onda 33b: a en/homepage era a única página de conteúdo sem hreflang possível
porque a decisão estava aberta.

O script:
1. substitui public/en/homepage/index.html pelo stub padrão da onda 29 (com o
   snippet de medição, como os demais stubs pós-S123);
2. REMOVE o bloco de hreflang que a 1ª versão deste script somou às homes —
   medido depois: as homes JÁ tinham o trio completo do tema (pt/en/de +
   x-default), e o bloco extra criava declarações duplicadas (pt × pt-BR).
   O registro da 33b ("sem hreflang") valia só para a en/homepage.

O sitemap é regenerado à parte (90_sitemap_e_raiz.py) — o stub é noindex e sai
sozinho.

Uso: python tools_onda6/97_home_en_canonica.py <raiz>
"""
import io
import os
import sys

from _onda7_css import resolve_public, ler, gravar

MARK = "onda41:home-en-canonica"
DESTINO = "/mirow-site/en/"

STUB = (u'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">\n'
        u'  <!-- Medicao Mirow (GA4) - issue mirow-marketing#3. Config e eventos em wp-content/uploads/2026/07/onda6/onda31-medicao.js -->\n'
        u'  <script src="/mirow-site/wp-content/uploads/2026/07/onda6/onda31-medicao.js?v=33"></script>\n'
        u'  <script async src="https://www.googletagmanager.com/gtag/js?id=G-5VTS0MZK79"></script>\n'
        u'<!-- %s: uma URL por pagina — esta era duplicata da canonica (#65) -->\n'
        u'<meta http-equiv="refresh" content="0;url=%s">\n'
        u'<link rel="canonical" href="%s">\n'
        u'<meta name="robots" content="noindex,follow">\n'
        u'<title>Mirow &amp; Co.</title></head>\n'
        u'<body><p>This page has moved. <a href="%s">Go to the page</a>.</p></body></html>\n'
        % (MARK, DESTINO, DESTINO, DESTINO))

HREFLANG_MARK = "onda41:hreflang-homes"
HOMES_HREFLANG = {
    "pt/index.html": None, "en/index.html": None, "de/index.html": None,
}
BLOCO_HREFLANG = (u'<!-- %s: as 3 homes se apontam (fecha a pendencia da S124/33b) -->'
                  u'<link rel="alternate" href="/mirow-site/pt/" hreflang="pt-BR" />'
                  u'<link rel="alternate" href="/mirow-site/en/" hreflang="en-US" />'
                  u'<link rel="alternate" href="/mirow-site/de/" hreflang="de-DE" />'
                  u'<link rel="alternate" href="/mirow-site/pt/" hreflang="x-default" />'
                  % HREFLANG_MARK)


def main(root):
    pub = resolve_public(root)

    alvo = os.path.join(pub, "en", "homepage", "index.html")
    atual = ler(alvo)
    if MARK in atual:
        print("ok (ja e stub): en/homepage/index.html")
    else:
        gravar(alvo, STUB)
        print("en/homepage/index.html virou stub -> %s" % DESTINO)

    for rel in HOMES_HREFLANG:
        p = os.path.join(pub, rel.replace("/", os.sep))
        h = ler(p)
        if BLOCO_HREFLANG in h:
            gravar(p, h.replace(BLOCO_HREFLANG, "", 1))
            print("bloco duplicado de hreflang removido: %s" % rel)
        else:
            print("ok (sem bloco duplicado): %s" % rel)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
