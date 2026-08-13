# -*- coding: utf-8 -*-
"""
106_ia_praticas.py -- S141 (#212/#213/#214): secao "Como usamos IA" nas 3
praticas core (Estrategia, Sourcing/Operacoes, GTM/Pricing), nos 3 idiomas.

Pedido verbatim (Andreas, 12/08): "Na pagina de estrategia precisamos falar
como usamos IA nesses tipos de projetos" (+ compras e GTM/pricing). Tom:
fato/capital intelectual, nao autopromocao. Provas reais anonimizadas
(radar de tendencias AI-powered; pipeline de 8 agentes para contratos;
pricing dinamico com ML) -- fontes internas no doc de solucao da onda,
repo privado mirow-marketing.

A secao entra no FIM do corpo (experience-single__content), antes do bloco
de Cases, usando markup do proprio tema (wp-block-heading + <p>) -- zero
CSS novo, zero JS, nada de AOS (blindado contra o modo de falha da #208).

Uso:  python tools_onda6/106_ia_praticas.py <raiz-que-contem-public>

Idempotente: remove o bloco marcado existente e reinsere.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public  # noqa: E402

INI = "<!-- onda48:ia-pratica:ini -->"
FIM = "<!-- onda48:ia-pratica:fim -->"

SPACER = u'<div style="height:30px" aria-hidden="true" class="wp-block-spacer"></div>'


def bloco(titulo, paragrafos):
    partes = [INI, SPACER,
              u'<h3 class="wp-block-heading" id="como-usamos-ia">%s</h3>' % titulo]
    partes += [u"<p>%s</p>" % p for p in paragrafos]
    partes.append(FIM)
    return u"\n".join(partes)


CONTEUDO = {
    # ---------------- Estrategia e Inovacao (#212) ----------------
    "pt/pratica/estrategia/index.html": bloco(
        u"Como usamos IA em projetos de estratégia", [
            u"Três usos já rodam em projetos reais:",
            u"<strong>Radar de tendências com IA.</strong> Agentes de pesquisa "
            u"varrem e cruzam centenas de fontes de mercado, tecnologia, regulação "
            u"e cadeia, e ranqueiam as tendências por impacto, urgência e grau de "
            u"preparo da empresa. O resultado é um mapa por horizonte que vira tese "
            u"estratégica.",
            u"<strong>Pesquisa e síntese aceleradas.</strong> Times de agentes fazem "
            u"em dias o levantamento setorial que levava semanas: dados públicos "
            u"estruturados, benchmarks e evidência rastreável fonte a fonte.",
            u"<strong>Cenários com dados vivos.</strong> Barômetros setoriais "
            u"montados a partir de dados públicos atualizáveis, para que o cenário "
            u"do projeto continue válido depois da entrega.",
            u"O método continua o da casa: hipótese, evidência e recomendação com "
            u"fonte. A IA aumenta a profundidade e a velocidade das análises.",
        ]),
    "en/practice/strategy/index.html": bloco(
        u"How we use AI in strategy projects", [
            u"Three uses already run in real projects:",
            u"<strong>AI-powered trend radar.</strong> Research agents scan and "
            u"cross-reference hundreds of sources on markets, technology, regulation "
            u"and supply chains, and rank trends by impact, urgency and the "
            u"company's readiness. The result is a map by horizon that turns into "
            u"strategic theses.",
            u"<strong>Faster research and synthesis.</strong> Agent teams complete "
            u"in days the sector research that used to take weeks: structured "
            u"public data, benchmarks and evidence traceable source by source.",
            u"<strong>Scenarios built on live data.</strong> Sector barometers "
            u"built from continuously updated public data, so the project's "
            u"scenario stays valid after delivery.",
            u"The method stays the same: hypothesis, evidence and recommendations "
            u"with sources. AI raises the depth and speed of the analysis.",
        ]),
    "de/branchen/strategie/index.html": bloco(
        u"Wie wir KI in Strategieprojekten einsetzen", [
            u"Drei Anwendungen laufen bereits in realen Projekten:",
            u"<strong>KI-gestützter Trendradar.</strong> Research-Agenten "
            u"durchsuchen und verknüpfen Hunderte von Quellen zu Markt, Technologie, "
            u"Regulierung und Lieferketten und priorisieren Trends nach Wirkung, "
            u"Dringlichkeit und Reifegrad des Unternehmens. Das Ergebnis ist eine "
            u"Landkarte nach Zeithorizont, aus der strategische Thesen entstehen.",
            u"<strong>Schnellere Recherche und Synthese.</strong> Agenten-Teams "
            u"erledigen in Tagen die Branchenanalyse, die früher Wochen dauerte: "
            u"strukturierte öffentliche Daten, Benchmarks und Quelle für Quelle "
            u"nachvollziehbare Evidenz.",
            u"<strong>Szenarien mit lebenden Daten.</strong> Branchenbarometer auf "
            u"Basis laufend aktualisierter öffentlicher Daten, damit das Szenario "
            u"des Projekts auch nach der Übergabe gültig bleibt.",
            u"Die Methode bleibt dieselbe: Hypothese, Evidenz und Empfehlungen mit "
            u"Quellenangabe. KI erhöht Tiefe und Geschwindigkeit der Analysen.",
        ]),
    # ---------------- Sourcing, Compras e Estoques (#213) ----------------
    "pt/pratica/operacoes/index.html": bloco(
        u"Como usamos IA em projetos de sourcing e compras", [
            u"<strong>Inteligência contratual.</strong> Um pipeline de oito agentes "
            u"de IA processa contratos de fornecedores de ponta a ponta: extrai os "
            u"dados, mapeia riscos de cláusula, faz due diligence do fornecedor em "
            u"bases públicas, compara preços com benchmarks e licitações públicas, "
            u"analisa termos financeiros e sugere alavancas de negociação. Tudo em "
            u"minutos, e cada conclusão sai com a fonte que a sustenta.",
            u"<strong>Spend analysis avançada.</strong> Classificação automática do "
            u"gasto, curvas ABC, matriz de Kraljic e potencial de savings por "
            u"categoria: a base analítica de uma frente de sourcing pronta em "
            u"fração do tempo tradicional.",
            u"<strong>Radar de riscos de suprimentos.</strong> Monitoramento "
            u"contínuo de sinais regulatórios, geopolíticos e de mercado, com "
            u"alerta sobre o que ameaça ou favorece cada categoria.",
            u"Aplicado em projetos reais de suprimentos em setores como papel e "
            u"celulose, serviços financeiros e indústria pesada.",
        ]),
    "en/practice/operations/index.html": bloco(
        u"How we use AI in sourcing and procurement projects", [
            u"<strong>Contract intelligence.</strong> A pipeline of eight AI agents "
            u"processes supplier contracts end to end: it extracts the data, maps "
            u"clause risks, runs supplier due diligence on public databases, "
            u"compares prices against benchmarks and public tenders, analyses "
            u"financial terms and suggests negotiation levers. All in minutes, and "
            u"every conclusion comes with the source behind it.",
            u"<strong>Advanced spend analysis.</strong> Automatic spend "
            u"classification, ABC curves, Kraljic matrix and savings potential by "
            u"category: the analytical base of a sourcing effort ready in a "
            u"fraction of the traditional time.",
            u"<strong>Supply risk radar.</strong> Continuous monitoring of "
            u"regulatory, geopolitical and market signals, with alerts on what "
            u"threatens or favours each category.",
            u"Applied in real procurement projects in sectors such as pulp and "
            u"paper, financial services and heavy industry.",
        ]),
    "de/branchen/betrieb/index.html": bloco(
        u"Wie wir KI in Sourcing- und Einkaufsprojekten einsetzen", [
            u"<strong>Vertragsintelligenz.</strong> Eine Pipeline aus acht "
            u"KI-Agenten verarbeitet Lieferantenverträge von Anfang bis Ende: Sie "
            u"extrahiert die Daten, kartiert Klauselrisiken, prüft Lieferanten über "
            u"öffentliche Datenbanken, vergleicht Preise mit Benchmarks und "
            u"öffentlichen Ausschreibungen, analysiert Finanzkonditionen und "
            u"schlägt Verhandlungshebel vor. Alles in Minuten, und jede "
            u"Schlussfolgerung kommt mit ihrer Quelle.",
            u"<strong>Fortgeschrittene Spend-Analyse.</strong> Automatische "
            u"Klassifizierung der Ausgaben, ABC-Kurven, Kraljic-Matrix und "
            u"Einsparpotenzial je Kategorie: die analytische Basis eines "
            u"Sourcing-Projekts in einem Bruchteil der üblichen Zeit.",
            u"<strong>Risikoradar für Lieferketten.</strong> Kontinuierliches "
            u"Monitoring regulatorischer, geopolitischer und Marktsignale, mit "
            u"Hinweisen darauf, was jede Kategorie bedroht oder begünstigt.",
            u"Eingesetzt in realen Einkaufsprojekten in Sektoren wie Zellstoff und "
            u"Papier, Finanzdienstleistungen und Schwerindustrie.",
        ]),
    # ---------------- Go-to-market e Pricing (#214) ----------------
    "pt/pratica/marketing-vendas-e-pricing/index.html": bloco(
        u"Como usamos IA em projetos de go-to-market e pricing", [
            u"<strong>Pricing dinâmico com machine learning.</strong> Modelos de "
            u"predição de demanda e elasticidade-preço por produto e ponto de "
            u"venda, integrados ao ERP do cliente. O preço responde à oferta e à "
            u"demanda em vez de esperar a próxima revisão manual.",
            u"<strong>Pricing guidance para o time comercial.</strong> Sugestão de "
            u"preço e margem ótimos por transação, com o contexto que o vendedor "
            u"precisa para negociar melhor.",
            u"<strong>Inteligência de mercado para go-to-market.</strong> Análise "
            u"de grandes volumes de dados de consumo e concorrência para orientar "
            u"segmentação, campanhas e lançamentos.",
            u"Também produzimos pesquisa aberta sobre o tema: o estudo "
            u"“Uso de IA no setor automotivo brasileiro” (2025), em "
            u"parceria com a Automotive Business.",
        ]),
    "en/practice/marketing-sales-and-pricing/index.html": bloco(
        u"How we use AI in go-to-market and pricing projects", [
            u"<strong>Dynamic pricing with machine learning.</strong> Demand "
            u"prediction and price-elasticity models by product and point of sale, "
            u"integrated with the client's ERP. Prices respond to supply and demand "
            u"instead of waiting for the next manual review.",
            u"<strong>Pricing guidance for the sales team.</strong> Optimal price "
            u"and margin suggestions per transaction, with the context salespeople "
            u"need to negotiate better.",
            u"<strong>Market intelligence for go-to-market.</strong> Analysis of "
            u"large volumes of consumer and competitor data to guide segmentation, "
            u"campaigns and launches.",
            u"We also publish open research on the subject: the 2025 study "
            u"“AI adoption in the Brazilian automotive sector”, in "
            u"partnership with Automotive Business.",
        ]),
    "de/branchen/marketing-vertrieb-und-preisgestaltung/index.html": bloco(
        u"Wie wir KI in Go-to-market- und Pricing-Projekten einsetzen", [
            u"<strong>Dynamisches Pricing mit Machine Learning.</strong> Modelle "
            u"für Nachfrageprognose und Preiselastizität je Produkt und "
            u"Verkaufsstelle, integriert in das ERP des Kunden. Der Preis reagiert "
            u"auf Angebot und Nachfrage, statt auf die nächste manuelle Überprüfung "
            u"zu warten.",
            u"<strong>Pricing-Guidance für den Vertrieb.</strong> Vorschläge für "
            u"optimalen Preis und optimale Marge je Transaktion, mit dem Kontext, "
            u"den das Vertriebsteam für bessere Verhandlungen braucht.",
            u"<strong>Marktintelligenz für Go-to-market.</strong> Analyse großer "
            u"Mengen von Konsum- und Wettbewerbsdaten zur Steuerung von "
            u"Segmentierung, Kampagnen und Launches.",
            u"Zum Thema veröffentlichen wir auch offene Forschung: die Studie "
            u"“KI im brasilianischen Automobilsektor” (2025), in "
            u"Partnerschaft mit Automotive Business.",
        ]),
}

RE_BLOCO = re.compile(
    r"[ \t]*" + re.escape(INI) + r".*?" + re.escape(FIM) + r"\n[ \t]*", re.S)


def inserir(html, secao):
    html = RE_BLOCO.sub("", html)
    i = html.find('experience-single__cases"')
    if i < 0:
        return None
    j = html.rfind("</div>", 0, i)
    if j < 0:
        return None
    return html[:j] + secao + u"\n                " + html[j:]


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    for rel, secao in sorted(CONTEUDO.items()):
        p = os.path.join(pub, rel.replace("/", os.sep))
        with io.open(p, encoding="utf-8") as f:
            html = f.read()
        novo = inserir(html, secao)
        if novo is None:
            raise SystemExit("ancora experience-single__cases nao achada em %s" % rel)
        if novo != html:
            with io.open(p, "w", encoding="utf-8", newline="") as f:
                f.write(novo)
            print("%s atualizado" % rel)
        else:
            print("%s ja em dia" % rel)


if __name__ == "__main__":
    main()
