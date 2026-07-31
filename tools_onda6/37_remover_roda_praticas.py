# -*- coding: utf-8 -*-
"""
37_remover_roda_praticas.py -- remove a roda (mandala) de 8 praticas das
paginas de pratica/expertise e poe no lugar uma navegacao simples entre as
3 praticas atuais (issue S-09 / #58; resolve tambem S-20 / #69 -- ver nota
no fim deste docstring).

Uso:  python tools_onda6/37_remover_roda_praticas.py <raiz-da-arvore>

O bloco alvo e a secao "Conheca nossas outras praticas" dentro de
<section class="experience-single__others">: um <h5> + uma <ul class="mandala">
com 8 <li> (um por pratica antiga, incluindo icones .svg que nao existem mais
no espelho -- e exatamente a causa da S-20/#69). A firma hoje tem 3 praticas
("Estrategia", "Go-to-market e Pricing"/"& Pricing", "Sourcing, Compras e
Estoques"/"Sourcing, Procurement & Inventory"), entao a roda de 8 (com auto-
referencia a pratica atual, incluindo as 5 descontinuadas: Inovacao, Digital,
Pessoas e Organizacao, Adaptacao Climatica e Sustentabilidade, Transformacao
Turnaround e M&A) deixou de fazer sentido.

Substitui a <div class="row experience-single__others-experiences ...">
inteira (o h5 + a coluna com o mandala-wrap) por um h5 + uma lista simples de
3 links (sem SVG, sem imagem, sem wheel) apontando para as 3 paginas canonicas
de pratica no idioma da propria pagina -- roda em TODAS as paginas de
pratica/expertise, inclusive as 5 antigas (que ficam so com links para as 3
atuais, sem se autolistarem, ja que nao sao mais praticas ativas).

Marcado com <!-- onda12:praticas-nav --> / <!-- /onda12:praticas-nav --> para
idempotencia (2o run: 0 mudancas).

CSS: nao mexe em wp-content/uploads/2026/07/onda6/onda6.css (fora do escopo
desta sessao). Os 3 links usam a classe nova "praticas-nav" sem regra propria
-- herdam a tipografia/cor de link do tema, o que ja funciona como navegacao
simples. Um bloco de CSS PROPOSTO (para deixar a lista com espacamento e
layout em linha) fica em tools_onda6/_css_pending_praticas.css, para o
orquestrador avaliar e fundir em onda6.css na integracao (nao escrito por
este script automaticamente em onda6.css, por instrucao explicita da sessao).

Nota S-20/#69: as 6 imagens quebradas da issue sao icones .svg da mandala de
8 (praticas descontinuadas) que nao existem no espelho. Como este script
remove a mandala inteira, as 6 <img> quebradas somem junto -- ver o texto
sugerido para comentar/fechar a #69 no retorno desta sessao.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import base_prefix, gravar, ler, resolve_public  # noqa: E402

MARK_INI = "<!-- onda12:praticas-nav -->"
MARK_FIM = "<!-- /onda12:praticas-nav -->"

INICIO_ANTIGO = '<div class="row experience-single__others-experiences align-items-center">'
FIM_ANTIGO_MARCADOR = (
    '<span class="mandala-wrap__hover-section"></span>\n'
    '                </div>\n'
    '            </div>'
)

# idioma -> (titulo da secao, [(nome, href-canonico-relativo)])
NAV = {
    "pt": (u"Nossas práticas", [
        (u"Estratégia", "pt/pratica/estrategia/"),
        (u"Go-to-market e Pricing", "pt/pratica/marketing-vendas-e-pricing/"),
        (u"Sourcing, Compras e Estoques", "pt/pratica/operacoes/"),
    ]),
    "en": (u"Our practices", [
        (u"Strategy", "en/practice/strategy/"),
        (u"Go-to-market &amp; Pricing", "en/practice/marketing-sales-and-pricing/"),
        (u"Sourcing, Procurement &amp; Inventory", "en/practice/operations/"),
    ]),
    "de": (u"Unsere Praktiken", [
        (u"Strategie", "de/branchen/strategie/"),
        (u"Go-to-Market &amp; Pricing", "de/branchen/marketing-vertrieb-und-preisgestaltung/"),
        (u"Sourcing, Einkauf &amp; Bestände", "de/branchen/betrieb/"),
    ]),
}


def idioma_da_pagina(html):
    m = re.search(r'pll_language=([a-z]{2})', html)
    return m.group(1) if m and m.group(1) in ("pt", "en", "de") else "pt"


def bloco(idioma, prefix):
    titulo, links = NAV[idioma]
    itens = "\n".join(
        '                        <li class="praticas-nav__item">'
        '<a class="praticas-nav__link" href="%s%s">%s</a></li>'
        % (prefix, href, nome)
        for nome, href in links
    )
    return (
        '%s\n'
        '                <div class="col-12">\n'
        '                    <h5>%s</h5>\n'
        '                    <ul class="praticas-nav">\n'
        '%s\n'
        '                    </ul>\n'
        '                </div>\n'
        '                %s' % (MARK_INI, titulo, itens, MARK_FIM)
    )


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    alterados = 0
    ja_ok = 0
    sem_bloco = 0
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if nome != "index.html":
                continue
            path = os.path.join(dirpath, nome)
            html = ler(path)
            rel = os.path.relpath(path, pub).replace(os.sep, "/")

            if MARK_INI in html:
                ja_ok += 1
                continue

            ini = html.find(INICIO_ANTIGO)
            if ini < 0:
                # pagina sem a secao "outras praticas" (nao e pagina de pratica)
                sem_bloco += 1
                continue

            fim_marcador_idx = html.find(FIM_ANTIGO_MARCADOR, ini)
            if fim_marcador_idx < 0:
                print("AVISO: achei o inicio da roda mas nao o fim esperado em %s" % rel)
                continue
            fim = fim_marcador_idx + len(FIM_ANTIGO_MARCADOR)

            idioma = idioma_da_pagina(html)
            prefix = base_prefix(html)
            novo_bloco = bloco(idioma, prefix)

            html = html[:ini] + novo_bloco + html[fim:]
            gravar(path, html)
            alterados += 1
            print("roda removida -> nav simples (%s): %s" % (idioma, rel))

    print(
        "\nresumo: %d arquivo(s) alterado(s), %d ja estavam ok, "
        "%d sem o bloco (pagina nao-pratica)" % (alterados, ja_ok, sem_bloco)
    )


if __name__ == "__main__":
    main()
