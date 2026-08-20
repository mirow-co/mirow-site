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
    # As 3 listagens NAO entram neste dicionario: a frase delas cita a lista de
    # lideres, e lista de lider e dado que mora no `PAGINAS` do 110 (a mesma fonte do
    # JSON-LD e dos cartoes de preview). Hardcodear aqui foi valor gemeo, e ele
    # divergiu na primeira oportunidade: quando o Michael Munch saiu em 20/08/2026, o
    # card saiu do HTML e o `Person` saiu do JSON-LD, mas estas 3 frases seguiram
    # anunciando o nome dele. Agora sao MONTADAS em `desc_listagem()`.
}

# `mod` e o 110: mesma fonte de verdade do JSON-LD e dos cartoes de lider.
mod = __import__("110_geo_bios_lideres")

LISTAGEM_REL = {
    "pt": "pt/sobre-nos/lideres/index.html",
    "en": "en/about-us/leaders/index.html",
    "de": "de/ueber-uns/fuehrungskraefte/index.html",
}

# `Prof. Dr Stephan Friedrich` aparece na frase como "Stephan Friedrich": a meta
# description e prosa corrida, nao registro. O mapa cobre so quem precisa encurtar.
CURTO = {u"Prof. Dr Stephan Friedrich": u"Stephan Friedrich"}

MOLDE = {
    "pt": (u"Os líderes da Mirow & Co.: %s — trajetórias em McKinsey, "
           u"Monitor Deloitte e grandes indústrias."),
    "en": (u"The leaders of Mirow & Co.: %s — backgrounds at McKinsey, "
           u"Monitor Deloitte and major industries."),
    "de": (u"Die Führungskräfte von Mirow & Co.: %s — Stationen bei "
           u"McKinsey, Monitor Deloitte und in der Industrie."),
}

E = {"pt": u" e ", "en": u" and ", "de": u" und "}


def desc_listagem(lang):
    """A frase da listagem, montada da MESMA lista que o resto da onda 59 usa."""
    nomes = [CURTO.get(n, n) for n in mod.PAGINAS]
    if len(nomes) > 1:
        lista = u", ".join(nomes[:-1]) + E[lang] + nomes[-1]
    else:
        lista = nomes[0] if nomes else u""
    return MOLDE[lang] % lista


for _lang, _rel in LISTAGEM_REL.items():
    TEXTOS[_rel] = desc_listagem(_lang)


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
