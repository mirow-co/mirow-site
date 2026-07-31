# -*- coding: utf-8 -*-
"""
44_atualizar-cargo-elmar-insights.py — Insights: Elmar Gans de socio para Senior Expert.

Issue: mirow-co/mirow-marketing#59 (S-10)

Uso:  python tools_onda6/44_atualizar-cargo-elmar-insights.py <raiz-da-arvore>

Contexto
--------
O Elmar Gans aparece como "socio" em bylines/bio do artigo "Preco que vale ouro"
(unico Insight com um trecho de bio/cargo dele em texto corrido). Hoje ele e
Senior Expert (ja corrigido na pagina de lideres pela issue #2). Este script
alinha as MENCOES DE CARGO desse artigo, sem tocar no conteudo analitico do
texto nem na autoria (o post continua atribuido ao autor original).

O QUE MUDA (3 trechos, nos 2 arquivos-espelho do mesmo Insight):
1. meta og:description — "Carta do socio, por Elmar Gans" -> "Carta do Senior
   Expert, por Elmar Gans"
2. kicker visivel no topo do artigo — mesma troca
3. paragrafo de bio no rodape do artigo — "e socio-diretor e lider da pratica
   de Marketing, Sales & Pricing da Mirow & Co." -> "e Senior Expert da Mirow
   & Co. e liderou a pratica de Marketing, Sales & Pricing da firma." (passado,
   para nao afirmar uma lideranca atual que nao foi confirmada — R1 honestidade)

NAO mexe em:
- Giulia Turcato como autora (meta/schema) de "10 anos de Mirow" — ela saiu da
  firma, mas a decisao de bylines de quem saiu e da issue #66, nao desta.
- A mencao "Os nossos socios Andreas Mirow, Elmar Gans e Felipe Diniz" em
  "10 anos de Mirow" — e uma descricao historica do video (verdadeira na data
  de publicacao), nao uma bio/byline; mudar seria alterar o conteudo do artigo.
- Fernando Fabbris ("socio-associado") no artigo de transicao climatica — nao
  esta na lista de quem saiu (#66); fora do escopo desta issue.

Idempotente: na 2a execucao os textos novos ja nao contem "socio", 0 mudanca.
"""
import io
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from _onda7_css import resolve_public, ler, gravar  # noqa: E402

ALVOS = ["preco-que-vale-ouro/index.html", "pt/preco-que-vale-ouro/index.html"]

TROCAS = [
    (
        u"Carta do sócio, por Elmar Gans",
        u"Carta do Senior Expert, por Elmar Gans",
    ),
    (
        u'<a href="https://www.linkedin.com/in/elmar-gans-2329a422/">Elmar Gans</a> '
        u'é sócio-diretor e líder da prática de Marketing, Sales &amp; Pricing da Mirow &amp; Co.',
        u'<a href="https://www.linkedin.com/in/elmar-gans-2329a422/">Elmar Gans</a> '
        u'é Senior Expert da Mirow &amp; Co. e liderou a prática de Marketing, Sales &amp; Pricing da firma.',
    ),
]

MARCADOR_INI = u"<!-- onda12:elmar-cargo-insights -->"
MARCADOR_FIM = u"<!-- /onda12:elmar-cargo-insights -->"


def aplicar(html):
    feitos = []
    for velho, novo in TROCAS:
        n = html.count(velho)
        if n:
            html = html.replace(velho, novo)
            feitos.append(u"%dx: %.40s..." % (n, novo))
    # marca a bio atualizada (parágrafo final do artigo) para rastreio em
    # tools/verificacoes.py, sem duplicar em reexecuções
    bio_nova = TROCAS[1][1]
    if bio_nova in html and MARCADOR_INI not in html:
        alvo = u"<p style=\"font-size:18px\"><strong>%s</strong></p>" % bio_nova
        if alvo in html:
            html = html.replace(
                alvo,
                MARCADOR_INI + alvo + MARCADOR_FIM,
                1,
            )
            feitos.append(u"marcador onda12:elmar-cargo-insights")
    return html, feitos


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    alterados = 0
    vistos = 0
    for rel in ALVOS:
        path = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(path):
            print(u"AUSENTE (esperado): %s" % rel)
            continue
        vistos += 1
        html = ler(path)
        novo, feitos = aplicar(html)
        if novo != html:
            gravar(path, novo)
            alterados += 1
            print(u"%s: %s" % (rel, "; ".join(feitos)))
        else:
            print(u"%s: sem mudança (já aplicado)" % rel)
    print(u"\nresumo: %d de %d página(s)-alvo alterada(s)" % (alterados, vistos))

    # ------------------------------------------------------------- achados
    # Bylines de quem saiu da firma, encontrados durante a varredura dos
    # Insights — reportados aqui (stdout) para a issue #66 decidir, sem
    # alterar nada.
    achados = []
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if nome != "index.html":
                continue
            p = os.path.join(dirpath, nome)
            h = ler(p)
            if "single-post" not in h:
                continue
            rel = os.path.relpath(p, pub).replace(os.sep, "/")
            for pessoa in (u"Giulia Turcato", u"Giulia", u"Lucas", u"Mariana", u"Matheus"):
                if pessoa in h:
                    achados.append((rel, pessoa))
    if achados:
        print(u"\nACHADOS (não alterados — decisão na issue #66):")
        for rel, pessoa in sorted(set(achados)):
            print(u"  %s -> menciona '%s'" % (rel, pessoa))


if __name__ == "__main__":
    main()
