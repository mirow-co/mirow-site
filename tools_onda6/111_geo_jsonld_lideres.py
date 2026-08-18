# -*- coding: utf-8 -*-
"""Onda 59 (GEO, mirow-marketing#230): bloco JSON-LD com Organization +
6 Persons nas 3 listagens de lideres (pt/en/de).

- Segue o handoff do Felipe (11/08/2026). foundingDate REMOVIDO (nao publicado;
  campo inventado e pior que campo ausente). Elmar Gans e Joao Daniel Ramos
  FICAM FORA por decisao do Felipe.
- Person: jobTitle, description e sameAs vem dos cards da PROPRIA listagem do
  idioma (fonte unica, P3); url/@id apontam para a pagina individual (slug novo
  do Michael, mirow-marketing#231). knowsAbout/alumniOf: constantes do handoff.
- O bloco convive com o JSON-LD do Yoast; e uma segunda tag <script>, com
  id="onda59-geo" para idempotencia (reescrito por igual a cada run).
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
mod = __import__("110_geo_bios_lideres")

LISTAGENS = mod.LISTAGENS
PAGINAS = mod.PAGINAS

ORG_DESC = {
    "pt": (u"Consultoria estratégica brasileira, com sede no Rio de Janeiro, "
           u"especializada em estratégia, inovação, go-to-market e pricing, e "
           u"sourcing e compras. Atende clientes em português, inglês e alemão."),
    "en": (u"Brazilian strategy consulting firm headquartered in Rio de Janeiro, "
           u"specialized in strategy, innovation, go-to-market and pricing, and "
           u"sourcing and procurement. Serves clients in Portuguese, English and German."),
    "de": (u"Brasilianische Strategieberatung mit Sitz in Rio de Janeiro, "
           u"spezialisiert auf Strategie, Innovation, Go-to-Market und Pricing sowie "
           u"Sourcing und Einkauf. Betreut Kunden auf Portugiesisch, Englisch und Deutsch."),
}

HOME = {"pt": "https://mirow.com.br/pt/", "en": "https://mirow.com.br/en/", "de": "https://mirow.com.br/de/"}

# constantes do handoff do Felipe (por pessoa, idioma-invariantes exceto traducao)
KNOWS = {
    u"Andreas Mirow": {
        "pt": [u"Estratégia corporativa", u"Pricing", u"Marketing e vendas"],
        "en": [u"Corporate strategy", u"Pricing", u"Marketing and sales"],
        "de": [u"Unternehmensstrategie", u"Pricing", u"Marketing und Vertrieb"],
    },
    u"Felipe Diniz": {
        "pt": [u"Estratégia", u"Energia", u"Inovação", u"Governança corporativa"],
        "en": [u"Strategy", u"Energy", u"Innovation", u"Corporate governance"],
        "de": [u"Strategie", u"Energie", u"Innovation", u"Corporate Governance"],
    },
    u"Prof. Dr Stephan Friedrich": {
        "pt": [u"Gestão da inovação", u"Estratégia corporativa", u"Modelos de negócio"],
        "en": [u"Innovation management", u"Corporate strategy", u"Business models"],
        "de": [u"Innovationsmanagement", u"Unternehmensstrategie", u"Geschäftsmodelle"],
    },
    u"Renato Alvarenga": {
        "pt": [u"Energia", u"Novos negócios", u"Estratégia"],
        "en": [u"Energy", u"New businesses", u"Strategy"],
        "de": [u"Energie", u"Neue Geschäftsfelder", u"Strategie"],
    },
    u"Michael Munch": {
        "pt": [u"Pricing", u"Advanced analytics", u"Finanças corporativas", u"Digitalização"],
        "en": [u"Pricing", u"Advanced analytics", u"Corporate finance", u"Digitalization"],
        "de": [u"Pricing", u"Advanced Analytics", u"Unternehmensfinanzen", u"Digitalisierung"],
    },
    u"Raoni Morais": {
        "pt": [u"Energia", u"Energias renováveis", u"Planejamento energético", u"Infraestrutura"],
        "en": [u"Energy", u"Renewable energy", u"Energy planning", u"Infrastructure"],
        "de": [u"Energie", u"Erneuerbare Energien", u"Energieplanung", u"Infrastruktur"],
    },
}

ALUMNI = {
    u"Andreas Mirow": [u"Universidade Técnica de Berlim"],
    u"Raoni Morais": [u"Instituto Militar de Engenharia (IME)", u"Universitat de Barcelona",
                      u"Universidade Federal do Rio de Janeiro (UFRJ)"],
}

INI_RE = re.compile(r'<script type="application/ld\+json" id="onda59-geo">.*?</script>\n?', re.S)


def montar(lang, cards):
    org_id = "https://mirow.com.br/#organization"
    grafo = [{
        "@type": ["Organization", "ProfessionalService"],
        "@id": org_id,
        "name": "Mirow & Co.",
        "url": HOME[lang],
        "description": ORG_DESC[lang],
        "address": {
            "@type": "PostalAddress",
            "streetAddress": u"Rua Lauro Müller, 116 — sala 1504",
            "addressLocality": "Rio de Janeiro",
            "addressRegion": "RJ",
            "postalCode": "22290-160",
            "addressCountry": "BR",
        },
        "areaServed": {"@type": "Country", "name": "Brasil"},
        "knowsLanguage": ["pt-BR", "en", "de"],
        "sameAs": [
            "https://www.linkedin.com/company/mirow-co-/",
            "https://www.instagram.com/mirowandco",
        ],
        "founder": {"@id": "https://mirow.com.br/pt/lider/andreas-mirow/#person"},
        "foundingLocation": {"@type": "Place", "name": "Rio de Janeiro, Brasil"},
    }]
    for nome, paginas in PAGINAS.items():
        d = cards[nome]
        url = "https://mirow.com.br/%s/" % paginas[lang]
        pid = "https://mirow.com.br/%s/#person" % paginas["pt"]
        pessoa = {
            "@type": "Person",
            "@id": pid,
            "name": nome.replace(u"Prof. Dr Stephan Friedrich", u"Prof. Dr. Stephan Friedrich"),
            "jobTitle": d["cargo"],
            "worksFor": {"@id": org_id},
            "url": url,
            "description": ". ".join(d["bio"]) + ".",
            "knowsAbout": KNOWS[nome][lang],
        }
        if nome in ALUMNI:
            pessoa["alumniOf"] = [{"@type": "CollegeOrUniversity", "name": n} for n in ALUMNI[nome]]
        if d["linkedin"]:
            pessoa["sameAs"] = [d["linkedin"]]
        grafo.append(pessoa)
    return {"@context": "https://schema.org", "@graph": grafo}


def main(raiz):
    pub = os.path.join(os.path.abspath(raiz), "public")
    mudancas = 0
    for lang, rel in LISTAGENS.items():
        p = os.path.join(pub, rel.replace("/", os.sep))
        h = mod.ler(p)
        cards = mod.extrai_cards(h)
        for nome in PAGINAS:
            if nome not in cards or not cards[nome]["bio"] or not cards[nome]["linkedin"]:
                raise SystemExit(u"dados incompletos para %s em %s" % (nome, lang))
        bloco = json.dumps(montar(lang, cards), ensure_ascii=False, indent=1)
        tag = '<script type="application/ld+json" id="onda59-geo">%s</script>\n' % bloco
        novo = INI_RE.sub("", h)
        novo = novo.replace("</head>", tag + "</head>", 1)
        if novo != h:
            mod.gravar(p, novo)
            mudancas += 1
            print("json-ld: %s" % rel)
    print("total de mudancas: %d" % mudancas)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
