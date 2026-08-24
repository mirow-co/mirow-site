# -*- coding: utf-8 -*-
"""Onda 72 (mirow-marketing#251): <meta name="description"> nas paginas individuais
de lider — nenhuma das 5 tinha (conferido pelo Felipe em 23/08 e remedido aqui).

Padrao do anexo do Felipe: "[Nome], [cargo] da Mirow & Co., consultoria estrategica
brasileira com sede no Rio de Janeiro. [Uma frase de especialidade]."
A frase de especialidade vem da bio de cada um. Traducoes en/de minhas.

Idempotente: a tag leva id="onda72-desc" e e reescrita por igual a cada run,
inserida logo apos <meta charset...> (antes de qualquer og:).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public  # noqa: E402
mod = __import__("110_geo_bios_lideres")
ler, gravar = mod.ler, mod.gravar
PAGINAS = mod.PAGINAS

FIRMA = {
    "pt": u"da Mirow & Co., consultoria estratégica brasileira com sede no Rio de Janeiro",
    "en": u"at Mirow & Co., a Brazilian strategy consulting firm headquartered in Rio de Janeiro",
    "de": u"bei Mirow & Co., einer brasilianischen Strategieberatung mit Sitz in Rio de Janeiro",
}

CARGO = {
    u"Andreas Mirow": {"pt": u"Managing Partner", "en": u"Managing Partner", "de": u"Managing Partner"},
    u"Felipe Diniz": {"pt": u"sócio", "en": u"partner", "de": u"Partner"},
    u"Prof. Dr Stephan Friedrich": {"pt": u"sócio", "en": u"partner", "de": u"Partner"},
    u"Renato Alvarenga": {"pt": u"senior advisor", "en": u"senior advisor", "de": u"Senior Advisor"},
    u"Raoni Morais": {"pt": u"senior expert", "en": u"senior expert", "de": u"Senior Expert"},
}

ESPECIALIDADE = {
    u"Andreas Mirow": {
        "pt": u"Fundador da firma, atua em estratégia corporativa, pricing, marketing e vendas.",
        "en": u"Founder of the firm, working on corporate strategy, pricing, marketing and sales.",
        "de": u"Gründer der Firma, tätig in Unternehmensstrategie, Pricing, Marketing und Vertrieb.",
    },
    u"Felipe Diniz": {
        "pt": u"Lidera a prática de Energia e Inovação; 18 anos de consultoria estratégica e PhD em Economia pela University of Chicago.",
        "en": u"Leads the Energy and Innovation practice; 18 years of strategy consulting and a PhD in Economics from the University of Chicago.",
        "de": u"Leitet die Practice Energie und Innovation; 18 Jahre Strategieberatung und PhD in Wirtschaftswissenschaften der University of Chicago.",
    },
    u"Prof. Dr Stephan Friedrich": {
        "pt": u"Atua em gestão da inovação, estratégia corporativa e modelos de negócio.",
        "en": u"Works on innovation management, corporate strategy and business models.",
        "de": u"Tätig in Innovationsmanagement, Unternehmensstrategie und Geschäftsmodellen.",
    },
    u"Renato Alvarenga": {
        "pt": u"Atua em energia, novos negócios e estratégia.",
        "en": u"Works on energy, new businesses and strategy.",
        "de": u"Tätig in Energie, neuen Geschäftsfeldern und Strategie.",
    },
    u"Raoni Morais": {
        "pt": u"Atua em energia, energias renováveis, planejamento energético e infraestrutura.",
        "en": u"Works on energy, renewable energy, energy planning and infrastructure.",
        "de": u"Tätig in Energie, erneuerbaren Energien, Energieplanung und Infrastruktur.",
    },
}

NOME_EXIBIDO = {u"Prof. Dr Stephan Friedrich": u"Prof. Dr. Stephan Friedrich"}

RE_TAG = re.compile(r'<meta name="description" id="onda72-desc" content="[^"]*"\s*/?>\n?')
RE_CHARSET = re.compile(r'(<meta charset[^>]*>)', re.I)


def frase(nome, lang):
    n = NOME_EXIBIDO.get(nome, nome)
    return u"%s, %s %s. %s" % (n, CARGO[nome][lang], FIRMA[lang], ESPECIALIDADE[nome][lang])


def main(raiz):
    pub = resolve_public(raiz)
    mudancas = 0
    for nome, paginas in PAGINAS.items():
        for lang, rel in paginas.items():
            p = os.path.join(pub, rel.replace("/", os.sep), "index.html")
            h = ler(p)
            tag = u'<meta name="description" id="onda72-desc" content="%s">\n' % frase(nome, lang).replace('"', "&quot;")
            if RE_TAG.search(h):
                novo = RE_TAG.sub(lambda _m: tag, h, count=1)
            else:
                m = RE_CHARSET.search(h)
                if not m:
                    raise SystemExit("meta charset ausente em %s" % rel)
                novo = h.replace(m.group(1), m.group(1) + "\n" + tag, 1)
            if novo != h:
                gravar(p, novo)
                mudancas += 1
                print("meta-desc: %s" % rel)
    print("total de mudancas: %d" % mudancas)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
