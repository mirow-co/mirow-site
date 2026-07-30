# -*- coding: utf-8 -*-
"""
04_praticas_tres_cards.py — troca a roda (mandala) de 8 praticas por 3 cards estaticos.

Uso:  python tools_onda6/04_praticas_tres_cards.py <raiz-da-arvore>

- Na secao <section class="home-experience"> das homes, substitui todo o
  <div class="row row__content"> (mandala de 8 pontos + lista que abria ao clicar)
  por 3 cards estaticos, com o texto sempre visivel: Estrategia, Pricing, Sourcing.
- Os cards reusam as classes do tema (.home-experience__list-item, __list-item-header,
  __list-item-content, __list-item-more) — mesma familia visual, mesmas cores/fontes.
- Os textos vem do proprio site (cards da roda + paginas de pratica: Estrategia,
  Marketing/Vendas/Pricing e o bloco Procurement de Operacoes), encurtados.
- CSS novo (so a distribuicao em 3 colunas e o texto visivel no mobile) em
  wp-content/uploads/2026/07/onda6/onda6.css, com <link> no <head>.
- Idempotente: reconhece os marcadores <!-- onda6:praticas --> e reescreve o bloco.
"""
import io
import os
import re
import sys

MARK_INI = "<!-- onda6:praticas -->"
MARK_FIM = "<!-- /onda6:praticas -->"
CSS_REL = "wp-content/uploads/2026/07/onda6/onda6.css"
CSS_LINK_ID = "onda6-css"

SETA = (
    '<svg width="17" height="12" viewBox="0 0 17 12" fill="none" '
    'xmlns="http://www.w3.org/2000/svg"><path d="M9.79289 0.292893C10.1834 -0.0976309 '
    '10.8166 -0.0976312 11.2071 0.292893L16.2071 5.29289C16.3946 5.48043 16.5 5.73478 '
    '16.5 6C16.5 6.26521 16.3946 6.51957 16.2071 6.70711L11.2071 11.7071C10.8166 '
    '12.0976 10.1834 12.0976 9.7929 11.7071C9.40237 11.3166 9.40237 10.6834 9.7929 '
    '10.2929L13.0858 7L1.5 7C0.947715 7 0.5 6.55228 0.5 6C0.5 5.44771 0.947715 5 1.5 '
    '5L13.0858 5L9.79289 1.70711C9.40237 1.31658 9.40237 0.683418 9.79289 '
    '0.292893Z" fill="#0E41A7" /></svg>'
)

ICONES = {
    "estrategia": "wp-content/uploads/2023/02/icon-strategy.svg",
    "pricing": "wp-content/uploads/2023/02/icon-mkt.svg",
    "sourcing": "wp-content/uploads/2023/02/icon-operations.svg",
}

# idioma -> (rotulo do link, [(slug, titulo, href relativo, texto)])
CARDS = {
    "pt": (u"Conheça a prática", [
        ("estrategia", u"Estratégia", "pt/pratica/estrategia/",
         u"Auxiliamos empresas de diversas indústrias a enfrentar seus desafios "
         u"estratégicos mais complexos, com metodologias inovadoras e uma abordagem "
         u"“aberta”. Apoiamos nossos clientes em cada etapa do processo estratégico, "
         u"da análise dos mercados e da formulação da estratégia até a implementação "
         u"de iniciativas que geram valor."),
        ("pricing", u"Pricing", "pt/pratica/marketing-vendas-e-pricing/",
         u"Atuamos em toda a cadeia de <em>marketing</em>, vendas e <em>pricing</em>, "
         u"ajudando organizações a construir modelos de precificação mais inteligentes. "
         u"Nossa solução Mirow Pricing Optimizer aborda cinco elementos: estratégia, "
         u"construção, execução, controle e cultura de <em>pricing</em>."),
        ("sourcing", u"Sourcing", "pt/pratica/operacoes/",
         u"A excelência na aquisição de matérias-primas, bens ou serviços não significa "
         u"apenas cortar custos: é também assegurar o nível de serviço esperado e elevar "
         u"a colaboração entre fornecedores e funções internas. Conduzimos projetos de "
         u"<em>sourcing</em> estratégico apoiados na avaliação de <em>spend</em> e na "
         u"identificação de oportunidades de eficiência."),
    ]),
    "en": (u"Learn more", [
        ("estrategia", u"Strategy", "en/practice/strategy/",
         u"We assist companies across various industries in tackling their most complex "
         u"strategic challenges, employing innovative methodologies and an “open” "
         u"approach. We support our clients at every stage of the strategic process, "
         u"from market analysis and strategy formulation to the implementation of "
         u"value-generating initiatives."),
        ("pricing", u"Pricing", "en/practice/marketing-sales-and-pricing/",
         u"We engage across the entire marketing, sales and pricing spectrum, helping "
         u"organizations craft smarter pricing models. Our Mirow Pricing Optimizer "
         u"solution addresses five key elements: pricing strategy, construction, "
         u"execution, control, and pricing infrastructure and culture."),
        ("sourcing", u"Sourcing", "en/practice/operations/",
         u"Procurement excellence involves more than just cost-cutting; it is about "
         u"ensuring the expected level of service and enhancing collaboration between "
         u"suppliers and internal functions. We conduct strategic sourcing projects to "
         u"evaluate spending and identify opportunities for efficiency gains."),
    ]),
    "de": (u"Branche entdecken", [
        ("estrategia", u"Strategie", "de/branchen/strategie/",
         u"Wir helfen Unternehmen aus den verschiedensten Branchen bei der Bewältigung "
         u"ihrer komplexesten strategischen Herausforderungen, indem wir innovative "
         u"Methoden und einen „offenen“ Ansatz anwenden. Wir unterstützen unsere Kunden "
         u"in jeder Phase des strategischen Prozesses — von der Marktanalyse bis zur "
         u"Umsetzung wertschaffender Initiativen."),
        ("pricing", u"Pricing", "de/branchen/marketing-vertrieb-und-preisgestaltung/",
         u"Wir arbeiten an Projekten, die den gesamten Marketing-, Vertriebs- und "
         u"Pricingsprozess umfassen, und entwickeln intelligente Pricingsmodelle. "
         u"Unsere Lösung Mirow Pricing Optimizer umfasst Preisstrategie, "
         u"Preisgestaltung, Preisumsetzung, Preisüberwachung sowie Preisinfrastruktur "
         u"und -kultur."),
        ("sourcing", u"Sourcing", "de/branchen/betrieb/",
         u"Exzellenz in der Beschaffung bedeutet nicht nur Kostenreduzierung, sondern "
         u"auch die Sicherstellung des erwarteten Serviceniveaus und die Förderung der "
         u"Zusammenarbeit zwischen Lieferanten und internen Funktionen. Wir führen "
         u"Projekte zum strategischen Sourcing durch, die auf einer gründlichen "
         u"Spend-Analyse aufbauen."),
    ]),
}

HOMES = [
    ("pt/index.html", "pt"),
    ("en/index.html", "en"),
    ("en/homepage/index.html", "en"),
    ("de/index.html", "de"),
]

CSS = """/* onda6 — 3 cards estaticos de praticas na home. CSS proprio, nao toca no tema. */
.praticas-3{display:flex;flex-wrap:wrap;gap:20px;margin:0;padding:0;list-style:none}
.praticas-3__card{flex:1 1 300px;display:flex;flex-direction:column;margin-bottom:0}
.praticas-3__card .home-experience__list-item-content{display:block;flex:1 0 auto;
  margin-bottom:20px}
.praticas-3__card .home-experience__list-item-more{display:inline-block;margin-top:auto}
@media only screen and (max-width: 991px){
  .praticas-3{gap:10px}
  .praticas-3__card{flex:1 1 100%}
}
"""


def resolve_public(root):
    root = os.path.abspath(root)
    if os.path.basename(root) == "public":
        return root
    cand = os.path.join(root, "public")
    if os.path.isdir(cand):
        return cand
    raise SystemExit("nao achei public/ em %s" % root)


def base_prefix(html):
    m = re.search(r'(?:src|href)="(/[^"]*?/)wp-content/', html)
    return m.group(1) if m else "/"


def bloco(idioma, prefix):
    rotulo, cards = CARDS[idioma]
    partes = []
    for slug, titulo, href, texto in cards:
        partes.append(
            '        <div class="home-experience__list-item praticas-3__card" id="%s">\n'
            '          <h4 class="home-experience__list-item-header">'
            '<img class="home-experience__list-item-header-icon" src="%s%s">'
            '<span>%s</span></h4>\n'
            '          <div class="home-experience__list-item-content"><p>%s</p></div>\n'
            '          <a class="home-experience__list-item-more" href="%s%s" '
            'target=" _self ">%s %s</a>\n'
            '        </div>'
            % (slug, prefix, ICONES[slug], titulo, texto, prefix, href, rotulo, SETA)
        )
    return (
        '%s\n'
        '                <div class="row row__content">\n'
        '                    <div class="col-12">\n'
        '                      <div class="praticas-3">\n'
        '%s\n'
        '                      </div>\n'
        '                    </div>\n'
        '                </div>\n'
        '                %s\n' % (MARK_INI, "\n".join(partes), MARK_FIM)
    )


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    css_path = os.path.join(pub, CSS_REL.replace("/", os.sep))
    os.makedirs(os.path.dirname(css_path), exist_ok=True)
    antigo = ""
    if os.path.exists(css_path):
        with io.open(css_path, encoding="utf-8") as f:
            antigo = f.read()
    if antigo != CSS:
        with io.open(css_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(CSS)
        print("css escrito: %s" % CSS_REL)
    else:
        print("css ja atualizado: %s" % CSS_REL)

    alterados = 0
    for rel, idioma in HOMES:
        path = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(path):
            print("AVISO: nao existe %s" % rel)
            continue
        with io.open(path, encoding="utf-8") as f:
            html = f.read()
        orig = html
        prefix = base_prefix(html)

        if CSS_LINK_ID not in html:
            link = '<link rel="stylesheet" id="%s" href="%s%s" media="all" />\n' % (
                CSS_LINK_ID, prefix, CSS_REL)
            html = html.replace("</head>", link + "</head>", 1)

        novo = bloco(idioma, prefix)
        if MARK_INI in html:
            html = re.sub(re.escape(MARK_INI) + r".*?" + re.escape(MARK_FIM) + r"\n?",
                          novo, html, flags=re.S)
        else:
            sec = html.find('<section class="home-experience"')
            if sec < 0:
                print("AVISO: secao home-experience nao encontrada em %s" % rel)
                continue
            ini = html.find('<div class="row row__content">', sec)
            fim = html.find("</section>", sec)
            if ini < 0 or fim < 0:
                print("AVISO: ancoras da secao nao encontradas em %s" % rel)
                continue
            # recorta do row__content ate o fim da secao e refaz o fechamento
            html = (html[:ini] + novo
                    + "            </div>\n        " + html[fim:])

        if html != orig:
            with io.open(path, "w", encoding="utf-8", newline="") as f:
                f.write(html)
            alterados += 1
            print("3 cards de praticas aplicados: %s (%s)" % (rel, idioma))
        else:
            print("sem mudanca: %s" % rel)
    print("\nresumo: %d arquivo(s) alterado(s)" % alterados)


if __name__ == "__main__":
    main()
