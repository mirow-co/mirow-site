# -*- coding: utf-8 -*-
"""
19_historia_ate_2026.py — item 5 da lista do Mario (onda 7).

Uso:  python tools_onda6/19_historia_ate_2026.py <raiz-que-contem-public>

A timeline de "Nossa historia" terminava em 2022 — "parece que a empresa fechou".
Este script acrescenta 3 marcos institucionais (2024, 2025 e 2026) nas 3 linguas,
com o MESMO markup dos itens ja existentes (.timeline__list-item sem imagem, como
os de 2015 e 2020).

Regra R1 (rastreabilidade): nenhum marco e inventado e nenhum cliente e nomeado.
A fonte de cada afirmacao esta documentada em tools_onda6/historia-fontes.md,
minerada no acervo Mirow (MCP mirow-rag). Os textos ficam deliberadamente
institucionais/genericos — descrevem a evolucao da firma, nao os projetos.

Idempotente: bloco marcado <!-- onda7:historia --> ... <!-- /onda7:historia -->
inserido logo antes do fechamento do .timeline__list.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import (gravar, idioma_da_pagina, ler, paginas,  # noqa: E402
                        resolve_public)

MARK_INI = "<!-- onda7:historia -->"
MARK_FIM = "<!-- /onda7:historia -->"

MARCOS = {
    "pt": [
        ("2024", u"<b>A pr&aacute;tica de Energia se consolida como uma das frentes "
                 u"centrais da firma</b>, com projetos consecutivos em 2023 e 2024 para "
                 u"grandes grupos do setor el&eacute;trico brasileiro, cobrindo gera&ccedil;&atilde;o "
                 u"distribu&iacute;da, comercializa&ccedil;&atilde;o no mercado livre e planejamento "
                 u"estrat&eacute;gico."),
        ("2025", u"<b>A Mirow &amp; Co. passa a atuar fora da Am&eacute;rica Latina</b>, "
                 u"assessorando investidores em projetos de infraestrutura de energia na "
                 u"&Aacute;frica Austral — do plano de neg&oacute;cios &agrave; avalia&ccedil;&atilde;o de "
                 u"viabilidade econ&ocirc;mica de linhas de transmiss&atilde;o e gera&ccedil;&atilde;o."),
        ("2026", u"<b>A firma estrutura seu programa de intelig&ecirc;ncia artificial "
                 u"aplicada &agrave; consultoria</b> e revisa sua proposta de valor: a IA acelera "
                 u"a an&aacute;lise, e o diferencial se desloca para o julgamento estrat&eacute;gico e "
                 u"a execu&ccedil;&atilde;o lado a lado com o cliente. A atua&ccedil;&atilde;o internacional "
                 u"se amplia para novos mercados na &Aacute;frica."),
    ],
    "en": [
        ("2024", u"<b>The Energy practice consolidates as one of the firm's core "
                 u"fronts</b>, with consecutive projects in 2023 and 2024 for major players "
                 u"in the Brazilian power sector, covering distributed generation, retail "
                 u"energy sales and strategic planning."),
        ("2025", u"<b>Mirow &amp; Co. begins working beyond Latin America</b>, advising "
                 u"investors on energy infrastructure projects in Southern Africa — from "
                 u"business plans to the economic feasibility assessment of transmission "
                 u"and generation assets."),
        ("2026", u"<b>The firm structures its programme on artificial intelligence "
                 u"applied to consulting</b> and revisits its value proposition: AI speeds "
                 u"up analysis, while the differentiator shifts to strategic judgement and "
                 u"execution side by side with the client. International work expands into "
                 u"new African markets."),
    ],
    "de": [
        ("2024", u"<b>Die Energie-Praxis etabliert sich als einer der Schwerpunkte der "
                 u"Firma</b> — mit aufeinanderfolgenden Projekten in den Jahren 2023 und 2024 "
                 u"f&uuml;r gro&szlig;e Unternehmen des brasilianischen Stromsektors, von der "
                 u"dezentralen Erzeugung &uuml;ber die Vermarktung im freien Markt bis zur "
                 u"strategischen Planung."),
        ("2025", u"<b>Mirow &amp; Co. ist erstmals au&szlig;erhalb Lateinamerikas t&auml;tig</b> "
                 u"und ber&auml;t Investoren bei Energieinfrastrukturprojekten im s&uuml;dlichen "
                 u"Afrika — vom Businessplan bis zur Wirtschaftlichkeitsbewertung von "
                 u"&Uuml;bertragungs- und Erzeugungsanlagen."),
        ("2026", u"<b>Die Firma baut ihr Programm zur Anwendung k&uuml;nstlicher Intelligenz "
                 u"in der Beratung auf</b> und &uuml;berarbeitet ihr Wertversprechen: KI "
                 u"beschleunigt die Analyse, w&auml;hrend sich der Unterschied auf strategisches "
                 u"Urteilsverm&ouml;gen und die Umsetzung an der Seite des Kunden verlagert. Die "
                 u"internationale T&auml;tigkeit weitet sich auf neue M&auml;rkte in Afrika aus."),
    ],
}


def fim_do_bloco(html, ini):
    """Indice logo depois do </div> que fecha a div aberta em `ini`."""
    i = ini
    nivel = 0
    while i < len(html):
        a = html.find("<div", i)
        f = html.find("</div>", i)
        if f < 0:
            raise ValueError("</div> nao encontrado")
        if 0 <= a < f:
            nivel += 1
            i = a + 4
        else:
            nivel -= 1
            i = f + 6
            if nivel == 0:
                return f
    raise ValueError("bloco nao fecha")


def item(ano, texto):
    return ('<div class="timeline__list-item" data-aos="fade-up"><h3>%s</h3>'
            '<div class="timeline__list-content"><h4></h4>'
            '<div class="timeline__list-text"><p>%s</p>\n</div></div></div>'
            % (ano, texto))


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    alvos = paginas(pub, 'class="timeline__list"')
    print("paginas de historia: %d" % len(alvos))

    alterados = 0
    for path, rel in alvos:
        html = ler(path)
        orig = html
        idioma = idioma_da_pagina(html)
        bloco = MARK_INI + "".join(item(a, t) for a, t in MARCOS[idioma]) + MARK_FIM

        if MARK_INI in html:
            i = html.find(MARK_INI)
            j = html.find(MARK_FIM) + len(MARK_FIM)
            html = html[:i] + bloco + html[j:]
        else:
            ini = html.find('<div class="timeline__list">')
            if ini < 0:
                print("AVISO: timeline nao encontrada em %s" % rel)
                continue
            fecha = fim_do_bloco(html, ini)
            html = html[:fecha] + bloco + html[fecha:]

        if html != orig:
            gravar(path, html)
            alterados += 1
            print("marcos 2024-2026 aplicados: %s (%s)" % (rel, idioma))
        else:
            print("sem mudanca: %s" % rel)

    print("\nresumo: %d arquivo(s) alterado(s)" % alterados)


if __name__ == "__main__":
    main()
