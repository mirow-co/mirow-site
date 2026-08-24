# -*- coding: utf-8 -*-
"""Onda 59 (GEO, mirow-marketing#230): bloco JSON-LD com Organization +
5 Persons nas 3 listagens de lideres E nas 3 homes (pt/en/de).

- Eram 6 Persons ate 20/08/2026, quando o Michael Munch saiu da firma e o Mario
  pediu para tira-lo "de tudo" -- ele sai por  no 110.

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

# Onda 68: o bloco passa a ser escrito TAMBEM nas 3 homes. Ele so vivia nas 3
# listagens de lider, e a home e a pagina que o Google e os assistentes de IA leem
# primeiro -- era o no rico do site inteiro escondido a dois cliques da entrada.
HOMES = {"pt": "pt/index.html", "en": "en/index.html", "de": "de/index.html"}

# O raster quadrado do "m" gerado pelo 142. Mesma marca do favicon e do manifest.
ICONE_LOGO = ("https://mirow.com.br/wp-content/uploads/2026/08/onda68/"
              "icone-mirow-512.png")

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

ESCRITORIO_NOME = {"pt": u"Escritório São Paulo",
                   "en": u"São Paulo office",
                   "de": u"Büro São Paulo"}

HOME = {"pt": "https://mirow.com.br/pt/", "en": "https://mirow.com.br/en/", "de": "https://mirow.com.br/de/"}

# constantes do handoff do Felipe (por pessoa, idioma-invariantes exceto traducao)
KNOWS = {
    u"Andreas Mirow": {
        "pt": [u"Estratégia corporativa", u"Pricing", u"Marketing e vendas"],
        "en": [u"Corporate strategy", u"Pricing", u"Marketing and sales"],
        "de": [u"Unternehmensstrategie", u"Pricing", u"Marketing und Vertrieb"],
    },
    # Onda 72 (#250, e-mail do Felipe de 24/08/2026): de 4 para os 10 termos que
    # ele mandou no anexo. Traducoes en/de minhas, a partir do verbatim pt.
    u"Felipe Diniz": {
        "pt": [u"Planejamento estratégico", u"Inovação e novos modelos de negócio",
               u"Finanças corporativas", u"Avaliação de projetos de capital e business cases",
               u"Redução de custos e eficiência operacional", u"Estratégia comercial e pricing",
               u"Gás natural", u"Energia elétrica e óleo e gás",
               u"Organização e governança corporativa", u"Economia aplicada e modelagem econométrica"],
        "en": [u"Strategic planning", u"Innovation and new business models",
               u"Corporate finance", u"Capital project evaluation and business cases",
               u"Cost reduction and operational efficiency", u"Commercial strategy and pricing",
               u"Natural gas", u"Electricity and oil & gas",
               u"Organization and corporate governance", u"Applied economics and econometric modeling"],
        "de": [u"Strategische Planung", u"Innovation und neue Geschäftsmodelle",
               u"Corporate Finance", u"Bewertung von Investitionsprojekten und Business Cases",
               u"Kostensenkung und operative Effizienz", u"Vertriebsstrategie und Pricing",
               u"Erdgas", u"Elektrizität sowie Öl und Gas",
               u"Organisation und Corporate Governance", u"Angewandte Ökonomie und ökonometrische Modellierung"],
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
    u"Raoni Morais": {
        "pt": [u"Energia", u"Energias renováveis", u"Planejamento energético", u"Infraestrutura"],
        "en": [u"Energy", u"Renewable energy", u"Energy planning", u"Infrastructure"],
        "de": [u"Energie", u"Erneuerbare Energien", u"Energieplanung", u"Infrastruktur"],
    },
}

ALUMNI = {
    u"Andreas Mirow": [u"Universidade Técnica de Berlim"],
    # Onda 72 (#249, e-mail do Felipe de 24/08/2026): so o diploma alemao chegava a
    # maquina — pista que fazia os assistentes deduzirem "consultoria alema". O PhD
    # de Chicago ja estava no modal, mas so em texto para humano. Stephan e Renato
    # entram quando autorizarem (o Mario confirma com eles).
    u"Felipe Diniz": [u"University of Chicago", u"Fundação Getulio Vargas — EPGE"],
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
        # Onda 60b — os tres fatos que o Mario deu em 18/08:
        #  - a SEDE (assento juridico, CNPJ 15.353.236/0001-89 ativo) segue no RIO, e e
        #    ela que fica no `address` e no que a descricao afirma;
        #  - o ESCRITORIO onde o time trabalha e em SAO PAULO, e entra como `location`
        #    (Place), que e como o schema.org diz "onde a organizacao esta" sem
        #    sobrescrever o assento juridico;
        #  - fundacao em 12/04/2012. `foundingLocation` fica no Rio porque a firma
        #    nasceu la como Portas Consulting Brasil, o que a Nossa Historia do site diz.
        "location": {
            "@type": "Place",
            "name": ESCRITORIO_NOME[lang],
            "address": {
                "@type": "PostalAddress",
                "streetAddress": u"Av. Ibirapuera, 2033 — conjunto 133",
                "addressLocality": u"São Paulo",
                "addressRegion": "SP",
                "postalCode": "04029-100",
                "addressCountry": "BR",
            },
        },
        "foundingDate": "2012-04-12",
        "foundingLocation": {"@type": "Place", "name": "Rio de Janeiro, Brasil"},
        # Onda 68 (#247) -- `logo` e `image`, que faltavam. O levantamento de icones
        # achou o site com QUATRO Organization no grafo: as tres do Yoast, com @id
        # RELATIVO por idioma (`/pt/#organization`, `/en/...`, `/de/...`), que tinham
        # logo e nenhum endereco; e esta, com @id absoluto, que tinha endereco,
        # descricao, fundacao e socios -- e nenhum logo. Nenhuma das quatro dizia ao
        # mesmo tempo quem somos E qual e a nossa marca. O 143 aponta os @id do Yoast
        # para este, e este passa a declarar a marca.
        #
        # O logo NAO e o `logo_mirow_azul_e_branco1svg.svg` que o Yoast usava: aquele
        # SVG tem `viewBox="0 0 210 297"` e `width="210mm" height="297mm"` -- e uma
        # prancha A4, nao um logo, e era por isso que a dimensao declarada parecia
        # torta. Aqui entra o raster quadrado do "m", o mesmo glifo que a onda 68 pos
        # no favicon e no manifest: uma marca, coerente em todas as superficies.
        "logo": {
            "@type": "ImageObject",
            "@id": "https://mirow.com.br/#logo",
            "url": ICONE_LOGO,
            "contentUrl": ICONE_LOGO,
            "width": 512,
            "height": 512,
            "caption": "Mirow & Co.",
        },
        "image": {"@id": "https://mirow.com.br/#logo"},
    }]
    for nome, paginas in PAGINAS.items():
        d = cards[nome]
        url = "https://mirow.com.br/%s/" % paginas[lang]
        pid = "https://mirow.com.br/%s/#person" % paginas["pt"]
        # Onda 72 (#250): o Felipe pediu jobTitle de ficha mais especifico que o
        # "Partner" visivel do card ("Sócio — Prática de Energia e Inovação, Mirow
        # & Co."). O ", Mirow & Co." fica de fora porque worksFor ja o declara.
        cargo_ficha = {
            u"Felipe Diniz": {"pt": u"Sócio — Prática de Energia e Inovação",
                              "en": u"Partner — Energy and Innovation Practice",
                              "de": u"Partner — Practice Energie und Innovation"},
        }.get(nome, {}).get(lang, d["cargo"])
        pessoa = {
            "@type": "Person",
            "@id": pid,
            "name": nome.replace(u"Prof. Dr Stephan Friedrich", u"Prof. Dr. Stephan Friedrich"),
            "jobTitle": cargo_ficha,
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
        # Substituir NO LUGAR quando a tag ja existe. Remover-e-anexar nao serve: o
        # 112 tambem insere antes de </head>, e os dois passavam a brigar pela ultima
        # posicao — cada run empurrava o outro e nenhum era idempotente.
        #
        # Onda 68: o MESMO bloco vai para a listagem E para a home daquele idioma. O
        # @id e o mesmo nas duas, e no schema.org isso e uma entidade so -- as
        # propriedades se somam em vez de competir. A home entrou porque e a pagina
        # que o Google e os assistentes de IA leem primeiro, e o no rico do site
        # estava a dois cliques da entrada.
        for destino in (rel, HOMES[lang]):
            pd = os.path.join(pub, destino.replace("/", os.sep))
            hd = mod.ler(pd)
            if INI_RE.search(hd):
                novo = INI_RE.sub(lambda _m: tag, hd, count=1)
            else:
                novo = hd.replace("</head>", tag + "</head>", 1)
            if novo != hd:
                mod.gravar(pd, novo)
                mudancas += 1
                print("json-ld: %s" % destino)
    print("total de mudancas: %d" % mudancas)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
