# -*- coding: utf-8 -*-
"""Onda 72 (mirow-marketing#250): bio nova do Felipe Diniz, em todas as superficies.

Pedido do Felipe (e-mail de 24/08/2026 + anexo geo-mirow-consertos-para-mario-2026-08-23.md):
- a bio atual o descreve so como consultor de energia e diz "15 anos" (sao 18);
- os 3 bullets viram a descricao curta nova (18 anos, 5 frentes, PhD Chicago);
- os 9 exemplos de projeto (todos de energia) viram os 8 rebalanceados do anexo.

As superficies sao TODAS as replicas do card/modal: homes, listagens de lider,
paginas de pratica — por isso a varredura e em todo public/**/*.html, trocando as
strings exatas por idioma. O JSON-LD e a pagina individual NAO sao tocados aqui:
sao regenerados pelo 110 e pelo 111 (rodar os dois depois deste).

Traducoes en/de: minhas, a partir do verbatim pt do Felipe. Pontos finais dos
itens do anexo removidos — bullet do site nao leva ponto (convencao ja no ar).
"""
import io
import os
import re
import sys

BULLETS = {
    "pt": [
        (u"Extensa experiência em estratégia, inovação, análise de mercado, reestruturação organizacional e governança",
         u"Sócio da Mirow & Co., com 18 anos de consultoria estratégica em setores intensivos em capital"),
        (u"15 anos de experiência em setores intensivos em capital, especialmente em energia",
         u"Atua em planejamento estratégico, inovação, redução de custos, finanças corporativas e organização, com concentração em energia, óleo e gás"),
        (u"Previamente atuou na Monitor Deloitte, Schlumberger Business Consulting e McKinsey & Company",
         u"PhD em Economia pela University of Chicago. Previamente na Monitor Deloitte, Schlumberger Business Consulting e McKinsey & Company"),
    ],
    "en": [
        (u"Extensive experience in strategy, innovation, market analysis, organizational restructuring and governance",
         u"Partner at Mirow & Co., with 18 years of strategy consulting in capital-intensive sectors"),
        (u"15 years of experience in capital-intensive sectors, especially in energy",
         u"Works in strategic planning, innovation, cost reduction, corporate finance and organization, with a focus on energy and oil & gas"),
        (u"Previously worked at Monitor Deloitte, Schlumberger Business Consulting and McKinsey & Company. Has a PhD in Economics (University of Chicago) and master's in economics (FGV-RJ)",
         u"PhD in Economics from the University of Chicago. Previously at Monitor Deloitte, Schlumberger Business Consulting and McKinsey & Company"),
    ],
    "de": [
        (u"Langjährige Erfahrung in Strategie, Innovation, Marktanalyse, organisatorischer Restrukturierung und Governance",
         u"Partner bei Mirow & Co., mit 18 Jahren Strategieberatung in kapitalintensiven Branchen"),
        (u"15 Jahre Erfahrung in kapitalintensiven Branchen, insbesondere im Energiesektor",
         u"Tätig in strategischer Planung, Innovation, Kostensenkung, Corporate Finance und Organisation, mit Schwerpunkt auf Energie sowie Öl und Gas"),
        (u"Zuvor tätig bei Monitor Deloitte, Schlumberger Business Consulting und McKinsey & Company",
         u"PhD in Wirtschaftswissenschaften an der University of Chicago. Zuvor bei Monitor Deloitte, Schlumberger Business Consulting und McKinsey & Company"),
    ],
}

PROJETOS_VELHOS = {
    "pt": [
        u"Construção de cenários para o mercado de veículos elétricos no Brasil e desenvolvimento de solução de recarga",
        u"Apoio ao planejamento estratégico de empresa de transmissão de energia elétrica",
        u"Apoio ao planejamento estratégico de empresa operadora de gasodutos",
        u"Apoio ao desenho de nova jornada de clientes para empresa de distribuição de GLP",
        u"Apoio ao planejamento estratégico e definição de estratégia de inovação para empresa de tecnologia",
        u"Desenvolvimento de modelo de man power planing para empresa de geração de energia",
        u"Avaliação de projeto de capital para empresa de geração de energia",
        u"Desenvolvimento de modelo de negócio inovador para grande seguradora brasileira",
        u"Apoio ao planejamento estratégico de empresa de distribuição de gás natural",
    ],
    "en": [
        u"Building scenarios for the electric vehicle market in Brazil and developing a charging solution",
        u"Strategic planning support for an electricity transmission company",
        u"Strategic planning support for a gas pipeline operating company",
        u"Support for the design of a new customer journey for an LPG distribution company",
        u"Support for strategic planning and definition of innovation strategy for technology company",
        u"Development of a manpower planning model for a power generation company",
        u"Capital project assessment for a power generation company",
        u"Development of an innovative business model for a major Brazilian insurance company",
        u"Strategic planning support for a natural gas distribution company",
    ],
    "de": [
        u"Entwicklung von Szenarien für den Markt für Elektrofahrzeuge in Brasilien und Entwicklung einer Ladelösung",
        u"Unterstützung bei der strategischen Planung eines Unternehmens für die Übertragung von elektrischer Energie",
        u"Unterstützung bei der strategischen Planung eines Unternehmens, das Gasleitungen betreibt",
        u"Unterstützung bei der Gestaltung einer neuen Kundenreise für ein Unternehmen für die Verteilung von Flüssiggas (GLP)",
        u"Unterstützung bei der strategischen Planung und Definition der Innovationsstrategie für ein Technologieunternehmen",
        u"Entwicklung eines Modells für das Personalmanagement für ein Energieerzeugungsunternehmen",
        u"Bewertung von Investitionsprojekten für ein Energieerzeugungsunternehmen",
        u"Entwicklung eines innovativen Geschäftsmodells für eine große brasilianische Versicherungsgesellschaft",
        u"Unterstützung bei der strategischen Planung eines Unternehmens für die Verteilung von Erdgas",
    ],
}

PROJETOS_NOVOS = {
    "pt": [
        u"Índice de competitividade do gás natural por segmento e faixa de consumo em quatro distribuidoras estaduais do Nordeste, frente a GLP, diesel, óleo combustível, etanol e gasolina",
        u"Modelo de cost to serve com 13 alavancas de valor na formação de preço, para revisão de pricing e portfólio de distribuidora nacional de GLP",
        u"Identificação de oportunidades de eficiência e redução de custos em empresa de óleo e gás",
        u"Business case para a construção de estaleiro de reparação naval no Brasil",
        u"Modelo de negócio inovador para grande seguradora brasileira",
        u"Estrutura organizacional e governança corporativa de empresa líder do setor de metalurgia no Brasil",
        u"Estratégias de competitividade econômica estadual, ambiente de negócios e clusters no Estado do Rio de Janeiro",
        u"Novo modelo de negócios e ecossistema de inovação para instituição de ensino superior",
    ],
    "en": [
        u"Natural gas competitiveness index by segment and consumption bracket at four state distribution companies in Brazil's Northeast, against LPG, diesel, fuel oil, ethanol and gasoline",
        u"Cost-to-serve model with 13 value levers in price formation, for the pricing and portfolio review of a national LPG distribution company",
        u"Identification of efficiency and cost reduction opportunities at an oil and gas company",
        u"Business case for the construction of a ship repair yard in Brazil",
        u"Innovative business model for a major Brazilian insurance company",
        u"Organizational structure and corporate governance for a leading metallurgy company in Brazil",
        u"State economic competitiveness, business environment and cluster strategies for the State of Rio de Janeiro",
        u"New business model and innovation ecosystem for a higher education institution",
    ],
    "de": [
        u"Wettbewerbsfähigkeitsindex für Erdgas nach Segment und Verbrauchsklasse bei vier staatlichen Verteilungsunternehmen im Nordosten Brasiliens, im Vergleich zu Flüssiggas, Diesel, Heizöl, Ethanol und Benzin",
        u"Cost-to-serve-Modell mit 13 Werthebeln in der Preisbildung, für die Überprüfung von Pricing und Portfolio eines nationalen Flüssiggas-Verteilungsunternehmens",
        u"Identifizierung von Effizienz- und Kostensenkungspotenzialen in einem Öl- und Gasunternehmen",
        u"Business Case für den Bau einer Schiffsreparaturwerft in Brasilien",
        u"Innovatives Geschäftsmodell für eine große brasilianische Versicherungsgesellschaft",
        u"Organisationsstruktur und Corporate Governance für ein führendes Metallurgieunternehmen in Brasilien",
        u"Strategien für wirtschaftliche Wettbewerbsfähigkeit, Geschäftsumfeld und Cluster im Bundesstaat Rio de Janeiro",
        u"Neues Geschäftsmodell und Innovationsökosystem für eine Hochschule",
    ],
}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public  # noqa: E402
mod = __import__("110_geo_bios_lideres")
ler, gravar = mod.ler, mod.gravar


RE_QUALQUER_LI = re.compile(u"<li>(.*?)</li>", re.S)


def normaliza(texto):
    # As replicas do modal divergem em detalhe (espaco nas bordas, ponto final
    # nas paginas de/branchen). Compara-se o texto normalizado, nao o byte.
    t = re.sub(r"\s+", " ", texto).strip()
    return t[:-1].strip() if t.endswith(".") else t


def trocar(html, lang):
    mapa = {}
    for velho, novo in BULLETS[lang]:
        mapa[normaliza(velho)] = novo
    velhos, novos = PROJETOS_VELHOS[lang], PROJETOS_NOVOS[lang]
    for i, velho in enumerate(velhos):
        mapa[normaliza(velho)] = novos[i] if i < len(novos) else None  # None = apagar (9 viram 8)
    contagem = [0]

    def sub(m):
        chave = normaliza(m.group(1))
        if chave not in mapa:
            return m.group(0)
        contagem[0] += 1
        novo = mapa[chave]
        return u"" if novo is None else u"<li>%s</li>" % novo

    return RE_QUALQUER_LI.sub(sub, html), contagem[0]


def idioma_do_caminho(rel):
    topo = rel.replace("\\", "/").split("/")[0]
    return topo if topo in ("pt", "en", "de") else None


def main(raiz):
    pub = resolve_public(raiz)
    arquivos = 0
    trocas = 0
    for base, _dirs, files in os.walk(pub):
        for f in files:
            if not f.endswith(".html"):
                continue
            p = os.path.join(base, f)
            lang = idioma_do_caminho(os.path.relpath(p, pub))
            if not lang:
                continue
            h = ler(p)
            novo, n = trocar(h, lang)
            if n:
                gravar(p, novo)
                arquivos += 1
                trocas += n
                print("felipe-bio: %s (%d trocas)" % (os.path.relpath(p, pub), n))
    print("total: %d arquivos, %d trocas" % (arquivos, trocas))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
