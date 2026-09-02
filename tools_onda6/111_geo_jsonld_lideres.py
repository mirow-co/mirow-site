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
    },    # Onda 80b. Os temas dos dois saem do CARD deles na propria listagem de
    # lideres -- o texto que a firma ja publica sobre cada um --, nao de leitura
    # minha do LinkedIn. Assim o que a maquina le e o que o humano le.
    u"Elmar Gans": {
        "pt": [u"Estratégia corporativa", u"Desempenho comercial", u"S&OP"],
        "en": [u"Corporate strategy", u"Commercial performance", u"S&OP"],
        "de": [u"Unternehmensstrategie", u"Vertriebsleistung", u"S&OP"],
    },
    u"João Daniel Ramos": {
        "pt": [u"Estratégia", u"Logística", u"Marketing", u"Eficiência operacional"],
        "en": [u"Strategy", u"Logistics", u"Marketing", u"Operational efficiency"],
        "de": [u"Strategie", u"Logistik", u"Marketing", u"Operative Effizienz"],
    },

}

ALUMNI = {
    # Onda 73 (25/08/2026): o Stevens Institute of Technology entra. O site dizia
    # "2o mestrado, Gestao de Tecnologia, EUA, Fulbright" SEM instituicao, e por
    # isso o campo ficava fora do alumniOf -- a lacuna que o handoff registrava
    # como "perguntar a ele". Lido do LinkedIn dele em 25/08 ("Scholarship and
    # Master of Technology Management of the Stevens Institute of Technology") e
    # autorizado pelo Mario. Fonte autodeclarada, mesmo critério da 72b.
    u"Andreas Mirow": [u"Universidade Técnica de Berlim",
                       u"Stevens Institute of Technology"],
    # Onda 72 (#249, e-mail do Felipe de 24/08/2026): so o diploma alemao chegava a
    # maquina — pista que fazia os assistentes deduzirem "consultoria alema". O PhD
    # de Chicago ja estava no modal, mas so em texto para humano. Stephan e Renato
    # entram quando autorizarem (o Mario confirma com eles).
    # Onda 73: a PUC-Rio (graduacao em Economia, 1994-1998) entra -- estava no
    # LinkedIn dele e nunca no site.
    u"Felipe Diniz": [u"University of Chicago", u"Fundação Getulio Vargas — EPGE",
                      u"Pontifícia Universidade Católica do Rio de Janeiro (PUC-Rio)"],
    u"Raoni Morais": [u"Instituto Militar de Engenharia (IME)", u"Universitat de Barcelona",
                      u"Universidade Federal do Rio de Janeiro (UFRJ)"],
    # Onda 80b (01/09/2026): o Elmar e o Joao Daniel entram no cadastro. Pedido do
    # Mario, verbatim: "o elmar deve estar dentro do schema. o joao daniel deve ter
    # pagina propria" -- e as duas coisas sao o MESMO trabalho, porque o no Person
    # so existe no grafo se tiver uma URL propria como @id.
    #
    # SO ENTRA O QUE EU MEDI. Li os dois perfis no Chrome em 01/09 e o cartao de
    # topo de cada um declara UMA instituicao: WHU para o Elmar, FECAP para o Joao
    # Daniel. A pagina /details/education/ dos dois volta VAZIA -- nenhum dos dois
    # publica a secao de formacao completa.
    #
    # A tabela de logos do 153 tem tambem LMU Munchen, UMass Amherst e UFPR,
    # baixados numa sessao anterior para estes dois. NAO entram: eu nao encontrei
    # fonte para eles em nada que eu tenha medido, e chip de faculdade errada num
    # card de lider e pior que chip faltando. Se o Mario confirmar, e uma linha.
    # Onda 84 (02/09/2026). O Mario autorizou incluir as faculdades que estavam na
    # tabela de logos sem fonte ("sim pode incluir"), e ao voltar na fonte eu
    # descobri que meu "os dois nao publicam formacao" de 01/09 estava ERRADO: a
    # pagina /details/education/ do Elmar tinha ficado presa no spinner e eu li a
    # tela em branco como ausencia de dado. Carregada, ela lista QUATRO, e traz
    # uma que nem estava na tabela de logos -- a PUC-Rio, cujo brasao ja temos por
    # causa do Felipe. Lido no Chrome em 02/09:
    #   WHU (PhD, Business Administration, 2007-2009)
    #   University of Massachusetts Amherst (Master Thesis, Corporate Finance, 2004-2005)
    #   Ludwig-Maximilians-Universitat Munchen (MBA/MSc, 2000-2005)
    #   PUC-Rio (2002)
    # Isto e o erro 2 do R13 na pratica: tela vazia nao e "nao ha dado" -- pode ser
    # "ainda nao carregou". Distinguir custou 4 segundos de espera.
    u"Elmar Gans": [u"WHU – Otto Beisheim School of Management",
                    u"University of Massachusetts Amherst",
                    u"Ludwig-Maximilians-Universität München",
                    u"Pontifícia Universidade Católica do Rio de Janeiro (PUC-Rio)"],
    # A UFPR estava na tabela de logos como sendo de um dos dois, e NAO entra: nao
    # aparece em lugar nenhum do perfil do Joao Daniel (procurada no proprio
    # LinkedIn em 02/09, zero ocorrencia) nem no do Elmar, cujas quatro estao
    # acima. Autorizacao do Mario para incluir nao supre a falta de fonte sobre
    # DE QUEM ela e -- faculdade na pessoa errada e um erro factual publicado.
    u"João Daniel Ramos": [u"Fundação Escola de Comércio Álvares Penteado (FECAP)"],
    # Onda 72b (#249): Mario confirmou Stephan e Renato em 24/08. Fonte: o proprio
    # modal de lideres do site (Educacao). O vinculo do Stephan com Bremen e
    # DOCENCIA, nao formacao — nao entra no alumniOf.
    u"Prof. Dr Stephan Friedrich": [u"Universität Karlsruhe", u"Universität Mannheim"],
    u"Renato Alvarenga": [u"Carnegie Mellon University — Tepper School of Business",
                          u"Universidade de Brasília (UnB)"],
}

# Onda 73 (25/08/2026): a experiencia ANTERIOR passa a existir para a maquina.
# Ate aqui o grafo dizia apenas "worksFor: Mirow & Co." -- para um assistente de
# IA, cinco pessoas sem passado. Lido do LinkedIn de cada um em 25/08 (arquivos em
# docs/wikidata/2026-08-25_cv-*.md) e autorizado pelo Mario.
#
# Regra de curadoria, para nao precisar decidir caso a caso depois:
#  - vinculo com ORGANIZACAO NOMEADA e duracao >= 12 meses;
#  - a Mirow & Co. fica fora daqui (ja e o worksFor corrente);
#  - autonomo/"Independent Consultant" e ano sabatico ficam fora (nao ha org);
#  - varios cargos na MESMA organizacao viram um vinculo, com o cargo mais senior
#    e o intervalo somado (ex.: as duas diretorias do Renato na Cam).
# O que a regra deixou de fora, de proposito: IBP e o segundo periodo do Raoni na
# Catavento (4 meses cada), a docencia de 4 meses do Felipe no college de Chicago
# e a Cerj do Renato (11 meses).
#
# roleName vai VERBATIM do LinkedIn, sem traduzir por idioma: cargo de terceiro
# traduzido e cargo inventado, e o mesmo bloco e servido nas 3 linguas.
# Formato: (roleName, organizacao, inicio, fim ou None quando corrente).
EXPERIENCIA = {
    u"Andreas Mirow": [
        (u"Principal", u"McKinsey & Company", "2001-09", "2012-06"),
        (u"Manager of Sales and Marketing and Corporate Planning",
         u"Aracruz Celulose S.A.", "1996-08", "2001-08"),
        (u"Senior Associate", u"Booz Allen Hamilton", "1990", "1995"),
    ],
    u"Felipe Diniz": [
        (u"Director of Strategy", u"Monitor Deloitte", "2015-03", "2018-02"),
        (u"Senior Engagement Manager", u"McKinsey & Company", "2008-04", "2013-03"),
        (u"Academic Adviser at the Executive MBA",
         u"University of Chicago Booth School of Business", "2007-04", "2008-03"),
    ],
    u"Prof. Dr Stephan Friedrich": [
        (u"Managing Partner", u"Innovative Management Partner (IMP)", "2010", None),
        (u"Honorarprofessur für Betriebswirtschaftslehre", u"Universität Bremen", "2014", None),
        (u"Partner und Mitglied der Geschäftsleitung", u"Malik Management", "2006", "2009"),
        (u"Partner und Leiter Geschäftsbereich Strategy & Organisation",
         u"Arthur D. Little", "2003", "2006"),
    ],
    u"Renato Alvarenga": [
        (u"CFO", u"RC Alvarenga Engenharia e Construções", "2014-08", None),
        (u"Director of Sales and Logistics", u"Cam", "2007-12", "2010-08"),
        (u"Innovation Manager", u"Ampla", "2005-09", "2007-12"),
        (u"Project Manager", u"Chilectra (Enel Distribución Chile)", "2004-05", "2005-09"),
        (u"Engagement Manager", u"McKinsey & Company", "1999-09", "2003-04"),
        (u"Partner and Chief Engineer", u"Arcoplan Construtora", "1995-07", "1997-07"),
    ],
    u"Raoni Morais": [
        (u"Partner and Consultant", u"Catavento Consultoria", "2015-06", "2016-08"),
        (u"Project Manager", u"Consórcio Integrador Rio de Janeiro (CIRJ)", "2012-08", "2015-05"),
        (u"Business Analyst", u"Schlumberger", "2011-04", "2012-06"),
    ],
    # Onda 80b. Lido do LinkedIn dos dois em 01/09/2026, com a mesma regra de
    # curadoria das outras cinco: organizacao nomeada, 12 meses ou mais, sem a
    # Mirow e sem autonomo. Por isso ficam de fora, no Elmar, o estagio de 3 meses
    # no Rothschild (2003) e os cargos de conselho/associado que sao part-time e
    # correntes; e, nos dois, o vinculo com a propria Mirow.
    #
    # RESTRICAO DO MARIO, e ela vale para o site inteiro: nao se menciona, em
    # lugar nenhum, o vinculo atual do Elmar com a startup dele. O perfil abre com
    # esse cargo; ele nao entra aqui, nem na bio, nem no schema.
    u"Elmar Gans": [
        (u"Engagement Manager", u"McKinsey & Company", "2005-04", "2012-01"),
        (u"Sports editor", u"Mediengruppe Münchner Merkur tz", "2000-01", "2004-10"),
    ],
    # Kumon: 12 anos, quatro cargos. Fica o mais SENIOR com as datas DELE, nunca o
    # cargo mais alto esticado sobre o periodo inteiro da empresa -- isso seria
    # inventar data. O chip do card mostra "Kumon" uma vez de qualquer jeito,
    # porque a lista e deduplicada por organizacao.
    u"João Daniel Ramos": [
        (u"Gerente Sr de Operações e Expansão", u"Kumon Brasil", "2020-01", "2022-05"),
        (u"Gerente Sr de Marketing e Planejamento", u"Kumon Brasil", "2015-10", "2019-12"),
        (u"Analista de remuneração", u"Dexco", "2009-02", "2010-06"),
    ],
}

# Onda 74 (31/08/2026, #252): o `sameAs` do Wikidata fecha o circuito do handoff
# GEO do Felipe. Ate aqui o site dizia quem somos e o Wikidata dizia quem somos,
# sem nada ligando os dois -- e e o link explicito que faz o assistente tratar as
# duas afirmacoes como UMA entidade, em vez de duas parecidas.
#
# MESTRE dos QIDs (P3). Criados em 31/08/2026: a empresa a mao pela interface, as
# 5 pessoas por lote no QuickStatements, tudo com referencia. O outro lado da
# ligacao ja existe la: cada pessoa tem P108 -> a empresa, e a empresa tem P112 ->
# Andreas.
WIKIDATA_URL = "https://www.wikidata.org/wiki/%s"
WIKIDATA = {
    u"Mirow & Co.": "Q141241992",
    u"Andreas Mirow": "Q141242514",
    u"Felipe Diniz": "Q141242515",
    u"Prof. Dr Stephan Friedrich": "Q141242518",
    u"Raoni Morais": "Q141242520",
    u"Renato Alvarenga": "Q141242521",
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
            WIKIDATA_URL % WIKIDATA["Mirow & Co."],
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
            # Onda 73: worksFor deixa de ser um valor e passa a ser lista -- a
            # Mirow corrente mais o historico, no padrao Role do schema.org
            # (propriedade -> Role -> a MESMA propriedade -> valor), que e a
            # unica forma de pendurar data num vinculo de emprego.
            "worksFor": [{"@id": org_id}] + [
                dict([("@type", "OrganizationRole"), ("roleName", cargo),
                      ("startDate", ini)]
                     + ([("endDate", fim)] if fim else [])
                     + [("worksFor", {"@type": "Organization", "name": org})])
                for cargo, org, ini, fim in EXPERIENCIA.get(nome, [])],
            "url": url,
            "description": ". ".join(d["bio"]) + ".",
            "knowsAbout": KNOWS[nome][lang],
        }
        if nome in ALUMNI:
            pessoa["alumniOf"] = [{"@type": "CollegeOrUniversity", "name": n} for n in ALUMNI[nome]]
        if d["linkedin"]:
            pessoa["sameAs"] = [d["linkedin"]]
        if nome in WIKIDATA:
            pessoa.setdefault("sameAs", []).append(WIKIDATA_URL % WIKIDATA[nome])
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
