# -*- coding: utf-8 -*-
u"""135 — issues #212/#213/#214: "Como usamos IA" nas 3 práticas core.

Uso: python tools_onda6/135_ia_nas_praticas.py <raiz-que-contem-public>

PEDIDO (conversa Andreas/Mario/Luciana, 12/08, verbatim)
--------------------------------------------------------
> Na pagina de estrategia precisamos falar como usamos IA nesses tipos de projetos
> Na pagina de compras a mesma coisa
> Na outra pagina a mesma coisa

São 9 páginas: as 3 práticas core × pt/en/de.

**ESTE CONTEÚDO VAI PARA STAGING, NÃO PARA PRODUÇÃO.** O critério de aceite das
três issues diz, com essas palavras: *"Gate: staging → OK Andreas → produção"*.
É texto de posicionamento, e a decisão sobre o que a firma afirma publicamente
sobre o próprio método não é minha nem do script.

DE ONDE VEM O CONTEÚDO, E O QUE ELE DELIBERADAMENTE NÃO FAZ
-----------------------------------------------------------
O critério das issues pede *"exemplos concretos (não genéricos)"* e tom
*"fato/capital intelectual, não autopromoção"*. Então cada item abaixo descreve
**uma etapa de trabalho que existe**, no vocabulário do que ela faz — não
adjetivo, não promessa, não nome de produto.

O que ficou FORA de propósito:

* **Nome de cliente.** Nenhum. Onde um caso ajudaria, o setor entra e o nome não.
* **Número de resultado atribuído à IA.** Não temos medição isolada do efeito da
  IA sobre o resultado dos projetos; afirmar "reduz X%" seria inventar. Os
  números que já estão nas páginas são dos casos, e continuam sendo dos casos.
* **Política de dados.** A frase natural aqui seria "os dados do cliente não
  alimentam modelo de terceiro" — e eu **não sei** se isso é verdade em todos os
  casos. É exatamente o tipo de afirmação que precisa vir do Andreas, não de mim.
* **As outras 5 práticas.** A conversa citou as 3 core (nota de escopo da #214).

Idempotente: rodar 2x reporta 0 mudanças.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, gravar, ler, resolve_public  # noqa: E402

# ----------------------------------------------------------------- os rotulos
ROTULO = {
    "pt": (u"Como usamos IA", u"O que a inteligência artificial muda no método"),
    "en": (u"How we use AI", u"What artificial intelligence changes in the method"),
    "de": (u"Wie wir KI einsetzen", u"Was künstliche Intelligenz an der Methode ändert"),
}

FECHO = {
    "pt": (u"Em todos os casos a IA encurta o levantamento e amplia a base de "
           u"evidência. O julgamento — o que a evidência significa para aquela "
           u"empresa e o que decidir a partir dela — continua sendo trabalho de "
           u"consultor, feito com a equipe do cliente."),
    "en": (u"In every case AI shortens the fact-finding and widens the evidence "
           u"base. The judgement — what the evidence means for that company and "
           u"what to decide from it — remains consulting work, done together with "
           u"the client's team."),
    "de": (u"In allen Fällen verkürzt KI die Erhebung und verbreitert die "
           u"Evidenzbasis. Die Beurteilung — was die Evidenz für dieses "
           u"Unternehmen bedeutet und was daraus zu entscheiden ist — bleibt "
           u"Beratungsarbeit, gemeinsam mit dem Team des Kunden."),
}

# --------------------------------------------------- conteudo por pratica/idioma
# (issue, {lang: [(pt-titulo, pt-texto), ...]})
CONTEUDO = {
    "estrategia": (u"#212", {
        "pt": [
            (u"Radar de tendências",
             u"Varredura contínua de fontes públicas — regulação, publicações "
             u"setoriais, movimentos de concorrentes e de investimento — com "
             u"triagem e classificação assistidas por IA. O efeito prático é que "
             u"a primeira discussão de estratégia começa com o material já "
             u"organizado, em vez de consumir as semanas iniciais do projeto em "
             u"levantamento."),
            (u"Leitura do acervo do cliente",
             u"Estudos, atas, modelos e apresentações antigas são lidos e "
             u"estruturados preservando a origem de cada dado — documento, página "
             u"e trecho. Isso permite responder “de onde veio esse número?” em "
             u"qualquer ponto do projeto, inclusive meses depois."),
            (u"Verificação antes da entrega",
             u"Cada afirmação quantitativa do material é conferida contra a fonte "
             u"declarada, e o que não fecha volta para revisão em vez de seguir "
             u"para o cliente."),
        ],
        "en": [
            (u"Trend radar",
             u"Continuous sweep of public sources — regulation, sector "
             u"publications, competitor and investment moves — with AI-assisted "
             u"triage and classification. In practice, the first strategy "
             u"discussion starts with the material already organised, instead of "
             u"spending the project's opening weeks on fact-finding."),
            (u"Reading the client's own archive",
             u"Studies, minutes, models and older presentations are read and "
             u"structured while preserving the origin of every figure — document, "
             u"page and excerpt. That makes “where did this number come from?” "
             u"answerable at any point in the project, months later included."),
            (u"Verification before delivery",
             u"Every quantitative claim in the material is checked against the "
             u"source it cites, and whatever does not reconcile goes back for "
             u"review instead of going to the client."),
        ],
        "de": [
            (u"Trendradar",
             u"Laufende Auswertung öffentlicher Quellen — Regulierung, "
             u"Branchenpublikationen, Wettbewerbs- und Investitionsbewegungen — "
             u"mit KI-gestützter Vorauswahl und Klassifizierung. Praktisch heißt "
             u"das: die erste Strategiediskussion beginnt mit bereits geordnetem "
             u"Material, statt die ersten Projektwochen mit Erhebung zu "
             u"verbrauchen."),
            (u"Auswertung des Kundenarchivs",
             u"Studien, Protokolle, Modelle und ältere Präsentationen werden "
             u"gelesen und strukturiert, wobei die Herkunft jeder Zahl erhalten "
             u"bleibt — Dokument, Seite und Textstelle. Damit bleibt „woher kommt "
             u"diese Zahl?“ jederzeit beantwortbar, auch Monate später."),
            (u"Prüfung vor der Auslieferung",
             u"Jede quantitative Aussage im Material wird gegen die angegebene "
             u"Quelle geprüft; was nicht aufgeht, geht zurück in die Revision "
             u"statt zum Kunden."),
        ],
    }),
    "operacoes": (u"#213", {
        "pt": [
            (u"Categorização da base de compras",
             u"Bases de spend com dezenas de milhares de linhas são classificadas "
             u"integralmente em taxonomia de categorias, em vez de por amostragem. "
             u"Muda o que se pode afirmar: a conversa passa a ser sobre o gasto "
             u"inteiro, não sobre a parte que deu tempo de olhar."),
            (u"Leitura da carteira de contratos",
             u"Extração de prazos, índices de reajuste, condições de renovação e "
             u"cláusulas de risco de contratos em volume, com comparação de termos "
             u"entre fornecedores da mesma categoria."),
            (u"Benchmark e cenários de captura",
             u"Comparação de preço contra referência por item e faixas de captura "
             u"— conservadora, base e otimista — para que a meta de economia leve "
             u"à mesa de negociação um número defensável, com a premissa à vista."),
        ],
        "en": [
            (u"Categorising the spend base",
             u"Spend files with tens of thousands of lines are classified in full "
             u"against a category taxonomy, rather than by sampling. That changes "
             u"what can be claimed: the discussion becomes about the whole spend, "
             u"not about the share there was time to look at."),
            (u"Reading the contract portfolio",
             u"Extraction of terms, indexation clauses, renewal conditions and "
             u"risk clauses across contracts at volume, comparing terms between "
             u"suppliers in the same category."),
            (u"Benchmark and capture scenarios",
             u"Price comparison against reference per item and capture ranges — "
             u"conservative, base and optimistic — so the savings target arrives "
             u"at the negotiation table as a defensible number, with the "
             u"assumption in plain sight."),
        ],
        "de": [
            (u"Kategorisierung der Einkaufsbasis",
             u"Spend-Daten mit Zehntausenden Zeilen werden vollständig in eine "
             u"Kategorientaxonomie eingeordnet, nicht per Stichprobe. Das ändert, "
             u"was behauptbar ist: das Gespräch dreht sich um die gesamten "
             u"Ausgaben, nicht um den Teil, für den Zeit war."),
            (u"Auswertung des Vertragsbestands",
             u"Extraktion von Fristen, Indexierungsklauseln, "
             u"Verlängerungsbedingungen und Risikoklauseln über Verträge in "
             u"großer Zahl, mit Vergleich der Konditionen zwischen Lieferanten "
             u"derselben Kategorie."),
            (u"Benchmark und Realisierungsszenarien",
             u"Preisvergleich gegen Referenzwerte je Position und "
             u"Realisierungsbänder — konservativ, Basis, optimistisch — damit das "
             u"Einsparziel als belegbare Zahl an den Verhandlungstisch kommt, mit "
             u"offen ausgewiesener Annahme."),
        ],
    }),
    "marketing-vendas-e-pricing": (u"#214", {
        "pt": [
            (u"Cobertura comercial e carteira",
             u"Modelagem da carteira de clientes e do território de vendas sobre a "
             u"base transacional inteira, para localizar onde a cobertura está "
             u"desalinhada do potencial — e não onde a percepção do time diz que "
             u"está."),
            (u"Faixas de preço por segmento",
             u"Análise do histórico de transações para estimar sensibilidade a "
             u"preço por segmento, canal e produto, com as faixas de desconto "
             u"praticadas expostas lado a lado com as autorizadas."),
            (u"Diagnóstico de maturidade",
             u"Avaliação estruturada da prática de pricing e do processo comercial "
             u"contra um referencial, para que o plano comece pelo que está "
             u"faltando e não pelo que é mais fácil de mudar."),
        ],
        "en": [
            (u"Commercial coverage and portfolio",
             u"Modelling of the client portfolio and sales territory over the "
             u"whole transactional base, to locate where coverage is misaligned "
             u"with potential — rather than where the team's perception says it is."),
            (u"Price bands by segment",
             u"Analysis of transaction history to estimate price sensitivity by "
             u"segment, channel and product, with the discount bands actually "
             u"practised shown alongside the authorised ones."),
            (u"Maturity assessment",
             u"Structured assessment of the pricing practice and the commercial "
             u"process against a reference, so the plan starts from what is "
             u"missing rather than from what is easiest to change."),
        ],
        "de": [
            (u"Vertriebsabdeckung und Kundenportfolio",
             u"Modellierung des Kundenportfolios und des Vertriebsgebiets über die "
             u"gesamte Transaktionsbasis, um zu finden, wo die Abdeckung nicht zum "
             u"Potenzial passt — und nicht, wo das Team sie vermutet."),
            (u"Preisbänder je Segment",
             u"Auswertung der Transaktionshistorie zur Schätzung der "
             u"Preissensitivität je Segment, Kanal und Produkt, wobei die "
             u"tatsächlich gewährten Rabattbänder neben den genehmigten stehen."),
            (u"Reifegradanalyse",
             u"Strukturierte Bewertung der Pricing-Praxis und des Vertriebs"
             u"prozesses gegen eine Referenz, damit der Plan beim Fehlenden "
             u"beginnt und nicht beim leicht Änderbaren."),
        ],
    }),
}

# pratica -> {lang: caminho}
PAGINAS = {
    "estrategia": {"pt": "pt/pratica/estrategia/index.html",
                   "en": "en/practice/strategy/index.html",
                   "de": "de/branchen/strategie/index.html"},
    "operacoes": {"pt": "pt/pratica/operacoes/index.html",
                  "en": "en/practice/operations/index.html",
                  "de": "de/branchen/betrieb/index.html"},
    "marketing-vendas-e-pricing": {
        "pt": "pt/pratica/marketing-vendas-e-pricing/index.html",
        "en": "en/practice/marketing-sales-and-pricing/index.html",
        "de": "de/branchen/marketing-vertrieb-und-preisgestaltung/index.html"},
}

CSS = """
/* ---- onda68 (#212/#213/#214): "Como usamos IA" na pagina de pratica ---------
   Reusa a gramatica do bloco de Cases (h4 titulo + h5 subtitulo + lista), para
   nao inventar componente. O acento ciano na lateral e o unico sinal proprio:
   marca que a secao fala de IA, no mesmo vocabulario do selo do hero. */
.onda68-ia{margin:0 0 46px}
.onda68-ia__titulo{color:#020E66;font-weight:700;
  font-size:clamp(20px,16.6px + 0.53vw,24px);margin:0 0 4px}
.onda68-ia__subtitulo{color:#7F7F7F;font-weight:400;
  font-size:clamp(15px,13.6px + 0.19vw,17px);margin:0 0 20px}
.onda68-ia__lista{list-style:none;margin:0 0 18px;padding:0;display:grid;gap:16px}
.onda68-ia__item{border-left:3px solid #00ADEC;padding:2px 0 2px 16px}
.onda68-ia__item-titulo{display:block;color:#020E66;font-weight:700;
  font-size:clamp(16px,14.6px + 0.19vw,18px);line-height:1.3;margin:0 0 4px}
.onda68-ia__item-texto{display:block;color:#071C25;
  font-size:clamp(15px,13.9px + 0.15vw,17px);line-height:1.55}
.onda68-ia__fecho{color:#071C25;font-size:clamp(15px,13.9px + 0.15vw,17px);
  line-height:1.55;margin:0;padding:16px 18px;background:#F2F2F2}
@media only screen and (max-width: 991px){
  .onda68-ia__item{padding-left:13px}
}
"""

REX_CASES = re.compile(r'<div class="experience-single__cases">')


def bloco(lang, itens):
    titulo, subtitulo = ROTULO[lang]
    lis = u"".join(
        u'<li class="onda68-ia__item">'
        u'<span class="onda68-ia__item-titulo">%s</span>'
        u'<span class="onda68-ia__item-texto">%s</span></li>' % (t, x)
        for t, x in itens)
    return (u'<div class="onda68-ia">'
            u'<h4 class="onda68-ia__titulo">%s</h4>'
            u'<h5 class="onda68-ia__subtitulo">%s</h5>'
            u'<ul class="onda68-ia__lista">%s</ul>'
            u'<p class="onda68-ia__fecho">%s</p>'
            u'</div>' % (titulo, subtitulo, lis, FECHO[lang]))


def main(argv):
    pub = resolve_public(argv[1] if len(argv) > 1 else ".")
    mudou, jatinha = [], []

    for pratica, (issue, por_lang) in sorted(CONTEUDO.items()):
        for lang, itens in sorted(por_lang.items()):
            rel = PAGINAS[pratica][lang]
            p = os.path.join(pub, rel.replace("/", os.sep))
            if not os.path.exists(p):
                raise SystemExit(u"falta a pagina %s" % rel)
            html = ler(p)
            if 'class="onda68-ia"' in html:
                jatinha.append(rel)
                continue
            m = REX_CASES.search(html)
            if not m:
                raise SystemExit(u"%s: nao achei o bloco de Cases, que e a ancora "
                                 u"de insercao" % rel)
            html = html[:m.start()] + bloco(lang, itens) + html[m.start():]
            gravar(p, html)
            mudou.append(u"%s (%s)" % (rel, issue))
            print(u"  + %s  %s" % (issue, rel))

    for rel in jatinha:
        print(u"  = %s (ja tem)" % rel)

    mudou_css = escrever_bloco_css(pub, "ia-praticas", CSS, onda="onda68")

    # rele e confere o EFEITO
    problemas = []
    for pratica, (_i, por_lang) in CONTEUDO.items():
        for lang in por_lang:
            rel = PAGINAS[pratica][lang]
            h = ler(os.path.join(pub, rel.replace("/", os.sep)))
            if 'class="onda68-ia"' not in h:
                problemas.append(u"%s sem o bloco" % rel)
                continue
            if ROTULO[lang][0] not in h:
                problemas.append(u"%s: titulo fora do idioma" % rel)
            n = h.count('class="onda68-ia__item"')
            if n != 3:
                problemas.append(u"%s: %d item(ns), esperado 3" % (rel, n))
            if h.count('class="onda68-ia"') != 1:
                problemas.append(u"%s: bloco duplicado" % rel)
    if problemas:
        for pr in problemas:
            print(u"  ERRO: %s" % pr)
        raise SystemExit(1)

    print(u"\n%d pagina(s) alterada(s), %d ja tinham; bloco onda68:ia-praticas %s"
          % (len(mudou), len(jatinha), u"gravado" if mudou_css else u"ja estava igual"))
    print(u"\nATENCAO: este conteudo e de POSICIONAMENTO e o critério das issues "
          u"#212/#213/#214 exige\ngate STAGING -> OK do Andreas -> producao. "
          u"Nao publicar direto.")


if __name__ == "__main__":
    main(sys.argv)
