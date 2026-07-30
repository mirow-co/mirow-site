# -*- coding: utf-8 -*-
"""
12_bio_joao_daniel.py — da ao Joao Daniel Ramos card com contatos + modal de bio completo.

Uso:  python tools_onda6/12_bio_joao_daniel.py <raiz-da-arvore>

- Vale para as 4 paginas de lideres (PT sem prefixo, /pt/, /en/, /de/). Na home o
  quadro tem so 4 lideres (decisao do Mario), por isso o card com bio dele mora nas
  paginas de lideres.
- Card: mesmo markup do tema (page-leaders__list-item), com foto, nome, cargo, os
  icones de LinkedIn e e-mail e os 3 bullets de abertura; abre o modal.
- Modal: mesmo markup dos modais do Andreas/Felipe (modal-leaders), com Projetos
  Recentes (7), Outras Experiencias, Educacao e Curiosidades.
- FONTE UNICA do conteudo: 05_NovoMarketing/08_Site/2026-07-29_plano-perfil-joao-
  daniel-ramos.md, secao 2 (transcricao literal dos slides 42-44). Nada inventado.
  A versao EN corrige o erro de origem do slide 44 (os bullets do Kumon e das
  atuacoes previas estavam emendados). DE e traducao fiel do EN.
- Os SVGs dos icones sao COLHIDOS da propria pagina — nenhuma arte nova.
- Idempotente: se o card/modal dele ja existe no formato novo, reescreve igual.
"""
import io
import os
import re
import sys

FOTO = "wp-content/uploads/2026/07/joao-daniel-ramos.png"
NOME = u"João Daniel Ramos"
SLUG = "joao-daniel-ramos"
EMAIL = "joao.ramos@mirow.com.br"
LINKEDIN = "https://www.linkedin.com/in/joao-daniel-palma-ramos/"

CONTEUDO = {
    "pt": {
        "cargo": u"Gerente de projetos",
        "mais": u"Saiba mais",
        "abertura": [
            u"João Daniel Ramos é consultor da Mirow &amp; Co. no escritório de São Paulo",
            u"Serve clientes em setores como automotivo, papel &amp; celulose, educação e energia",
            u"Atua em ampla variedade de temas, sobretudo estratégia, logística, marketing e "
            u"eficiência operacional",
        ],
        "grupos": [
            (u"Projetos Recentes", [
                u"Apoiou uma grande empresa do setor de papel &amp; celulose na definição da "
                u"melhor localização para uma nova unidade industrial",
                u"Conduziu a transformação da operação de peças de reposição de uma grande "
                u"empresa do setor automotivo, envolvendo mudança de local e terceirização "
                u"de pessoal",
                u"Avaliou os mercados dos Estados Unidos e Europa para entrada de empresa do "
                u"setor de papel &amp; celulose com um novo produto",
                u"Avaliou estratégias para entrada em gás natural para uma grande empresa do "
                u"setor de energia",
                u"Conduziu a otimização de estoque de peças produtivas em grande empresa do "
                u"setor automotivo",
                u"Mapeou oportunidades de aumento da geração de valor em multinacional do "
                u"setor de energia elétrica, por meio da otimização da receita regulatória",
                u"Avaliou oportunidade de otimização de estoque de peças de reposição em "
                u"grande empresa do setor automotivo",
            ]),
            (u"Outras Experiências", [
                u"Kumon Institute of Education — Head de Marketing e Operações",
                u"Atuações prévias na Petrobras, HSBC e Dexco",
            ]),
            (u"Educação", [
                u"Mestrado em administração pela FECAP (São Paulo)",
                u"Graduação em matemática aplicada pela Universidade Federal do Paraná",
            ]),
            (u"Curiosidades", [
                u"Tênis, futebol e viagens, especialmente para conhecer o “lado B” das "
                u"localidades",
            ]),
        ],
    },
    "en": {
        "cargo": u"Engagement manager",
        "mais": u"Learn more",
        "abertura": [
            u"João Daniel Ramos is a consultant at Mirow &amp; Co. in the São Paulo office",
            u"Serves clients in sectors such as automotive, pulp &amp; paper, education, "
            u"and energy",
            u"Works on a wide range of topics, primarily in strategy, logistics, marketing, "
            u"and operational efficiency",
        ],
        "grupos": [
            (u"Recent studies", [
                u"Supported a major company in the pulp &amp; paper sector in determining the "
                u"best location for a new industrial facility",
                u"Led the transformation of the spare parts operation for a large company in "
                u"the automotive sector, which involved relocation and outsourcing of personnel",
                u"Assessed the United States and European markets for the entry of a pulp "
                u"&amp; paper company with a new product",
                u"Evaluated strategies for entering the natural gas market for a major company "
                u"in the energy sector",
                u"Conducted inventory optimization for production parts in a large automotive "
                u"company",
                u"Mapped opportunities to increase value generation for a multinational in the "
                u"electric energy sector by optimizing regulatory revenue",
                u"Assessed the opportunity to optimize spare parts inventory for a large "
                u"company in the automotive sector",
            ]),
            (u"Professional background", [
                u"Kumon Institute of Education — Head of Marketing and Operations",
                u"Previous roles at Petrobras, HSBC and Dexco",
            ]),
            (u"Educational background", [
                u"Master&#8217;s degree in administration from FECAP (São Paulo)",
                u"Degree in applied mathematics from the Federal University of Paraná",
            ]),
            (u"Other", [
                u"Tennis, football (soccer), and traveling, especially to explore the "
                u"“off-the-beaten-path” side of destinations",
            ]),
        ],
    },
    "de": {
        "cargo": u"Engagement Manager",
        "mais": u"Erfahren Sie mehr",
        "abertura": [
            u"João Daniel Ramos ist Berater bei Mirow &amp; Co. im Büro São Paulo",
            u"Betreut Kunden in Branchen wie Automotive, Papier &amp; Zellstoff, Bildung "
            u"und Energie",
            u"Arbeitet an einem breiten Themenspektrum, vor allem Strategie, Logistik, "
            u"Marketing und operative Effizienz",
        ],
        "grupos": [
            (u"Kürzlich durchgeführte Projekte", [
                u"Unterstützte ein großes Unternehmen der Papier- und Zellstoffbranche bei "
                u"der Bestimmung des besten Standorts für ein neues Industriewerk",
                u"Leitete die Transformation des Ersatzteilgeschäfts eines großen "
                u"Automotive-Unternehmens, einschließlich Standortwechsel und Outsourcing "
                u"von Personal",
                u"Bewertete die Märkte in den USA und Europa für den Markteintritt eines "
                u"Papier- und Zellstoffunternehmens mit einem neuen Produkt",
                u"Bewertete Strategien für den Einstieg in den Erdgasmarkt für ein großes "
                u"Energieunternehmen",
                u"Führte die Bestandsoptimierung von Produktionsteilen in einem großen "
                u"Automotive-Unternehmen durch",
                u"Identifizierte Möglichkeiten zur Steigerung der Wertschöpfung bei einem "
                u"multinationalen Stromversorger durch Optimierung der regulatorischen Erlöse",
                u"Bewertete die Möglichkeit zur Optimierung des Ersatzteilbestands bei einem "
                u"großen Automotive-Unternehmen",
            ]),
            (u"Weitere Erfahrungen", [
                u"Kumon Institute of Education — Leiter Marketing und Operations",
                u"Frühere Positionen bei Petrobras, HSBC und Dexco",
            ]),
            (u"Bildung", [
                u"Master in Betriebswirtschaft an der FECAP (São Paulo)",
                u"Studium der Angewandten Mathematik an der Bundesuniversität Paraná",
            ]),
            (u"Kuriositäten", [
                u"Tennis, Fußball und Reisen, besonders um die weniger bekannte Seite von "
                u"Orten zu entdecken",
            ]),
        ],
    },
}

RE_CARD_BUTTON = re.compile(r'<button class="page-leaders__list-item".*?</button>', re.S)
RE_CARD_DIV = re.compile(r'<div class="page-leaders__list-item".*?</span></span></div>', re.S)
RE_DIV = re.compile(r'<div\b|</div>')


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


def idioma_do_caminho(rel):
    if rel.startswith("de/"):
        return "de"
    if rel.startswith("en/"):
        return "en"
    return "pt"


def colhe_svgs(html):
    """Pega o SVG do LinkedIn e do envelope que a propria pagina ja usa nos contatos."""
    li = re.search(r'<a target="_blank" href="https://www\.linkedin\.com/[^"]+">\s*(<svg.*?</svg>)',
                   html, re.S)
    mail = re.search(r'<a href="mailto:[^"]+">\s*(<svg.*?</svg>)', html, re.S)
    return (li.group(1) if li else None), (mail.group(1) if mail else None)


def fim_balanceado(html, ini):
    nivel = 0
    for m in RE_DIV.finditer(html, ini):
        nivel += 1 if m.group(0) == "<div" else -1
        if nivel == 0:
            return m.end()
    return -1


def bloco_card(c, prefix, svg_li, svg_mail):
    contatos = []
    if svg_li:
        contatos.append('<li><a target="_blank" href="%s">%s</a></li>' % (LINKEDIN, svg_li))
    if svg_mail:
        contatos.append('<li><a href="mailto:%s">%s</a></li>' % (EMAIL, svg_mail))
    bullets = "".join("<li>%s</li>" % b for b in c["abertura"])
    return (
        '<button class="page-leaders__list-item" data-bs-toggle="modal"  '
        'data-bs-target="#modal_%s">'
        '<span class="page-leaders__list-wrap-image">'
        '<span class="page-leaders__list-image" style="background-image: url(%s%s)">'
        '</span></span>'
        '<span class="page-leaders__list-wrap-content">'
        '<span class="page-leaders__list-wrap-content-header">'
        '<h3 class="page-leaders__list-title">%s'
        '<small class="page-leaders__list-role">%s</small></h3>'
        '<ul class="page-leaders__list-contacts">%s</ul></span>'
        '<ul class="page-leaders__list-wrap-content-summary">%s</ul></span>'
        '<span class="page-leaders__list-item-more">%s</span></button>'
        % (SLUG, prefix, FOTO, NOME, c["cargo"], "".join(contatos), bullets, c["mais"])
    )


def bloco_modal(c, prefix, svg_li, svg_mail):
    contatos = []
    if svg_li:
        contatos.append('<li><a target="_blank" href="%s">%s</a></li>' % (LINKEDIN, svg_li))
    if svg_mail:
        contatos.append('<li><a href="mailto:%s">%s</a></li>' % (EMAIL, svg_mail))
    grupos = []
    for titulo, itens in c["grupos"]:
        grupos.append('<div class="modal-leaders__curriculum-group"><h6>%s</h6>'
                      '<ul class="modal-leaders__curriculum-list">%s</ul></div>'
                      % (titulo, "".join("<li>%s</li>" % i for i in itens)))
    bullets = "".join("<li>%s</li>" % b for b in c["abertura"])
    return (
        '<div class="modal fade" id="modal_%s" tabindex="-1" '
        'aria-labelledby="exampleModalLabel" aria-hidden="true">'
        '<div class="modal-dialog modal-xl"><div class="modal-content">'
        '<div class="modal-body modal-leaders">'
        '<button type="button" class="btn-close" data-bs-dismiss="modal" '
        'aria-label="Close"></button>'
        '<div class="modal-leaders__intro">'
        '<span class="modal-leaders__image-wrap">'
        '<span class="modal-leaders__image" style="background-image: url(%s%s)">'
        '</span></span>'
        '<h4 class="modal-leaders__title">%s</h4>'
        '<h5 class="modal-leaders__role">%s</h5>'
        '<ul class="modal-leaders__summary">%s</ul>'
        '<ul class="modal-leaders__contacts">%s</ul></div>'
        '<div class="modal-leaders__curriculum">%s</div>'
        '</div></div></div></div>'
        % (SLUG, prefix, FOTO, NOME, c["cargo"], bullets, "".join(contatos), "".join(grupos))
    )


def processa(path, pub):
    rel = os.path.relpath(path, pub).replace(os.sep, "/")
    with io.open(path, encoding="utf-8") as f:
        html = f.read()
    if "page-leaders__list-item" not in html or NOME not in html:
        return None
    orig = html
    prefix = base_prefix(html)
    c = CONTEUDO[idioma_do_caminho(rel)]
    svg_li, svg_mail = colhe_svgs(html)
    if not svg_li or not svg_mail:
        print("AVISO: nao achei os SVGs de contato em %s — nada feito" % rel)
        return False

    # 1) card dele (button novo ou div antigo) -> card novo com contatos e bullets
    alvo = None
    for rex in (RE_CARD_BUTTON, RE_CARD_DIV):
        for m in rex.finditer(html):
            if NOME in m.group(0):
                alvo = m
                break
        if alvo:
            break
    if not alvo:
        print("AVISO: card do Joao nao encontrado em %s" % rel)
        return False
    html = html[:alvo.start()] + bloco_card(c, prefix, svg_li, svg_mail) + html[alvo.end():]

    # 2) modal dele: substitui se ja existe, senao insere depois do ultimo modal
    novo_modal = bloco_modal(c, prefix, svg_li, svg_mail)
    marca = 'id="modal_%s"' % SLUG
    pos = html.find(marca)
    if pos >= 0:
        ini = html.rfind("<div", 0, pos)
        fim = fim_balanceado(html, ini)
        html = html[:ini] + novo_modal + html[fim:]
    else:
        ult = html.rfind('class="modal fade"')
        if ult < 0:
            print("AVISO: nenhum modal existente em %s — nada feito" % rel)
            return False
        ini = html.rfind("<div", 0, ult)
        fim = fim_balanceado(html, ini)
        html = html[:fim] + novo_modal + html[fim:]

    if html == orig:
        print("sem mudanca: %s" % rel)
        return False
    with io.open(path, "w", encoding="utf-8", newline="") as f:
        f.write(html)
    print("card + modal do Joao aplicados: %s (%s)" % (rel, idioma_do_caminho(rel)))
    return True


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    alterados = 0
    for root, _dirs, files in os.walk(pub):
        for f in files:
            if f != "index.html":
                continue
            if processa(os.path.join(root, f), pub):
                alterados += 1
    print("\nresumo: %d arquivo(s) alterado(s)" % alterados)


if __name__ == "__main__":
    main()
