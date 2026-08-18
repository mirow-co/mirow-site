# -*- coding: utf-8 -*-
"""Onda 59 (GEO, mirow-marketing#232): meta description nas homes (pt/en/de)
e nas 3 listagens de lideres. Texto da home pt: sugestao do Felipe, verbatim.

Idempotente: a tag leva o marcador onda59-meta e e reescrita por igual.
"""
import io
import os
import re
import sys

TEXTOS = {
    "pt/index.html": (u"Mirow & Co. — consultoria estratégica brasileira, sede no Rio de "
                      u"Janeiro. Estratégia, inovação, pricing e compras para empresas de "
                      u"grande porte. Atendimento em português, inglês e alemão."),
    "en/index.html": (u"Mirow & Co. — Brazilian strategy consulting firm headquartered in "
                      u"Rio de Janeiro. Strategy, innovation, pricing and procurement for "
                      u"large companies. Service in Portuguese, English and German."),
    "de/index.html": (u"Mirow & Co. — brasilianische Strategieberatung mit Sitz in Rio de "
                      u"Janeiro. Strategie, Innovation, Pricing und Einkauf für "
                      u"Großunternehmen. Betreuung auf Portugiesisch, Englisch und Deutsch."),
    "pt/sobre-nos/lideres/index.html": (
        u"Os líderes da Mirow & Co.: Andreas Mirow, Felipe Diniz, Stephan Friedrich, "
        u"Renato Alvarenga, Michael Munch e Raoni Morais — trajetórias em McKinsey, "
        u"Monitor Deloitte e grandes indústrias."),
    "en/about-us/leaders/index.html": (
        u"The leaders of Mirow & Co.: Andreas Mirow, Felipe Diniz, Stephan Friedrich, "
        u"Renato Alvarenga, Michael Munch and Raoni Morais — backgrounds at McKinsey, "
        u"Monitor Deloitte and major industries."),
    "de/ueber-uns/fuehrungskraefte/index.html": (
        u"Die Führungskräfte von Mirow & Co.: Andreas Mirow, Felipe Diniz, Stephan "
        u"Friedrich, Renato Alvarenga, Michael Munch und Raoni Morais — Stationen bei "
        u"McKinsey, Monitor Deloitte und in der Industrie."),
}

RE_TAG = re.compile(r'<meta name="description" content="[^"]*" data-onda="onda59-meta">\n?')


def main(raiz):
    pub = os.path.join(os.path.abspath(raiz), "public")
    mudancas = 0
    for rel, texto in TEXTOS.items():
        p = os.path.join(pub, rel.replace("/", os.sep))
        with io.open(p, encoding="utf-8") as f:
            h = f.read()
        if re.search(r'<meta name="description"(?![^>]*onda59-meta)', h):
            raise SystemExit("ja existe meta description alheia em %s — nao duplicar" % rel)
        tag = '<meta name="description" content="%s" data-onda="onda59-meta">\n' % texto
        # Mesmo cuidado do 111: substituir no lugar, senao os dois disputam a posicao
        # imediatamente anterior a </head> e nenhum fica idempotente.
        if RE_TAG.search(h):
            novo = RE_TAG.sub(lambda _m: tag, h, count=1)
        else:
            novo = h.replace("</head>", tag + "</head>", 1)
        if novo != h:
            with io.open(p, "w", encoding="utf-8", newline="") as f:
                f.write(novo)
            mudancas += 1
            print("meta description: %s" % rel)
    print("total de mudancas: %d" % mudancas)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
