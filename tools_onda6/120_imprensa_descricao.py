# -*- coding: utf-8 -*-
"""Onda 61: as paginas de imprensa EN e DE anunciavam a POLITICA DE PRIVACIDADE.

ACHADO (18/08, ao procurar o endereco da sede): o `og:description` de
`en/press/` e `de/presse/` traz o texto da politica de privacidade, com CNPJ e
endereco — "Privacy Policy Mirow & Co. do Brasil Consultoria Ltda., registered
under CNPJ n° 15.353.236/0001-89, and located at Rua Lauro Muller...". Quem
compartilha a pagina de imprensa no LinkedIn ve ISSO na previa.

CAUSA: as duas paginas nasceram na onda 29 (S-106) de um molde da politica de
privacidade, e o bloco de meta veio junto — a MESMA origem do bug de `hreflang`
que a onda 33b consertou. O `pt/imprensa/` nao tem o problema: a descricao dele
esta correta ("Mirow na imprensa. Veja nossas ultimas contribuicoes...").

O QUE ESTE SCRIPT FAZ:
  - reescreve `og:description` e `twitter:description` das 3 paginas de imprensa
  - adiciona `meta name="description"` (nenhuma das 3 tinha), no padrao da onda 59

Idempotente: 2o run reporta 0 mudancas.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public

TEXTOS = {
    "pt/imprensa/index.html": (
        u"Mirow & Co. na imprensa: nossas contribuições e análises nos principais "
        u"veículos de negócios do Brasil e do mundo, sobre estratégia, energia, "
        u"pricing e compras."),
    "en/press/index.html": (
        u"Mirow & Co. in the press: our contributions and analyses in leading business "
        u"media in Brazil and abroad, on strategy, energy, pricing and procurement."),
    "de/presse/index.html": (
        u"Mirow & Co. in der Presse: unsere Beiträge und Analysen in führenden "
        u"Wirtschaftsmedien in Brasilien und weltweit — Strategie, Energie, Pricing "
        u"und Einkauf."),
}

RE_OG = re.compile(r'(<meta property="og:description" content=")([^"]*)(")')
RE_TW = re.compile(r'(<meta name="twitter:description" content=")([^"]*)(")')
RE_META = re.compile(r'<meta name="description" content="[^"]*" data-onda="onda61-imprensa">\n?')


def main(raiz):
    pub = resolve_public(raiz)
    tocados = 0
    for rel, texto in TEXTOS.items():
        p = os.path.join(pub, rel.replace("/", os.sep))
        with io.open(p, encoding="utf-8") as f:
            h = f.read()
        o = h
        esc = texto.replace("&", "&amp;")
        h = RE_OG.sub(lambda m: m.group(1) + esc + m.group(3), h, count=1)
        h = RE_TW.sub(lambda m: m.group(1) + esc + m.group(3), h, count=1)
        # meta description propria (nenhuma das 3 tinha)
        if not re.search(r'<meta name="description"(?![^>]*onda61-imprensa)', h):
            tag = ('<meta name="description" content="%s" data-onda="onda61-imprensa">\n'
                   % esc)
            if RE_META.search(h):
                h = RE_META.sub(lambda _m: tag, h, count=1)
            else:
                h = h.replace("</head>", tag + "</head>", 1)
        if h != o:
            with io.open(p, "w", encoding="utf-8", newline="") as f:
                f.write(h)
            tocados += 1
            print("imprensa: %s" % rel)
    print("arquivos alterados: %d" % tocados)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
