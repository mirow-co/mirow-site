# -*- coding: utf-8 -*-
"""
36_renomear_praticas_paginas.py -- nomes completos das 3 praticas (issue S-26 / #76).

Uso:  python tools_onda6/36_renomear_praticas_paginas.py <raiz-da-arvore>

Escopo DESTE script: SOMENTE as paginas de pratica em public/**/index.html
(qualquer alias de path -- pratica/practice/branchen, com ou sem prefixo de
idioma). NAO toca em menus (aparecem nas 275 paginas, ver 39_menus_praticas.py,
que fica pronto mas nao roda) nem nos cards de pratica da home (mesmo motivo).

Pedido do Mario/Andreas (verbatim, issue #76):
  Estrategia -> mantem "Estrategia" / "Strategy" / "Strategie" (ja e o nome
  completo -- nada a fazer nessa pratica).
  "Marketing, Vendas e Pricing" -> "Go-to-market e Pricing" (PT)
  "Marketing, Sales and Pricing" -> "Go-to-market & Pricing" (EN)
  "Marketing, Vertrieb und Preisgestaltung" -> "Go-to-Market & Pricing" (DE, proposta)
  "Operacoes" -> "Sourcing, Compras e Estoques" (PT)
  "Operations" -> "Sourcing, Procurement & Inventory" (EN)
  "Betrieb" -> "Sourcing, Einkauf & Bestaende" (DE, proposta)

Metodo: substituicoes ANCORADAS (nao substring global) -- <title>, og:title,
JSON-LD (name da WebPage + name do ultimo item do breadcrumb) e o <h1> do
banner. Isso evita corromper palavras compostas em alemao (ex.: "Betrieb"
aparece dentro de "Betriebsleitern", "Betriebspraxis", "Betriebswirtschaftslehre"
em textos sem relacao com o nome da pratica) e evita mexer em texto corrido
generico (ex.: "nossa pratica de marketing, vendas & pricing otimiza..." em
minusculo, que e descritivo e nao o rotulo da pratica).

O bloco "Conheca nossas outras praticas" (roda de 8) tambem contem o nome
antigo (auto-referencia da pratica atual dentro da mandala) -- esse bloco e
removido inteiro pela 37_remover_roda_praticas.py (issue S-09/#58), entao este
script nao precisa tratar a mandala.

Idempotente: se o novo nome ja estiver la, os replaces nao acham o padrao
antigo e nao fazem nada (0 mudancas no 2o run).
"""
import io
import os
import sys

# (nome antigo, nome novo) por idioma. So as 2 praticas que mudam de nome.
RENOMEIOS = [
    ("Marketing, Vendas e Pricing", "Go-to-market e Pricing"),
    (u"Operações", "Sourcing, Compras e Estoques"),
    ("Marketing, Sales and Pricing", "Go-to-market & Pricing"),
    ("Operations", "Sourcing, Procurement & Inventory"),
    (u"Marketing, Vertrieb und Preisgestaltung", u"Go-to-Market & Pricing"),
    ("Betrieb", u"Sourcing, Einkauf & Bestände"),
]


def resolve_public(root):
    root = os.path.abspath(root)
    if os.path.basename(root) == "public":
        return root
    cand = os.path.join(root, "public")
    if os.path.isdir(cand):
        return cand
    raise SystemExit("nao achei public/ em %s" % root)


def aplicar(html, old, new):
    """Substituicoes ancoradas -- title, og:title, JSON-LD, h1. Devolve (html, n).

    O "&" do novo nome (Pricing/Inventory/Bestaende) e HTML-escapado para
    "&amp;" nos contextos de HTML (title/og/h1), como o restante do site ja
    faz (ver og:description com "&amp;"). Dentro do JSON-LD (texto puro de um
    <script>, nao passa por parser de entidade HTML) o "&" fica cru.
    """
    new_html = new.replace("&", "&amp;")
    padroes = [
        ("<title>%s - Mirow</title>" % old, "<title>%s - Mirow</title>" % new_html),
        ('content="%s - Mirow" />' % old, 'content="%s - Mirow" />' % new_html),
        ('"name":"%s - Mirow"' % old, '"name":"%s - Mirow"' % new),
        ('"name":"%s"}' % old, '"name":"%s"}' % new),
        ('data-aos="fade-right">%s</h1>' % old,
         'data-aos="fade-right">%s</h1>' % new_html),
    ]
    n = 0
    for antigo, novo in padroes:
        c = html.count(antigo)
        if c:
            html = html.replace(antigo, novo)
            n += c
    return html, n


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    arquivos_alterados = 0
    substituicoes = 0
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if nome != "index.html":
                continue
            path = os.path.join(dirpath, nome)
            with io.open(path, encoding="utf-8") as f:
                html = f.read()
            orig = html
            total = 0
            for old, new in RENOMEIOS:
                html, n = aplicar(html, old, new)
                total += n
            if html != orig:
                with io.open(path, "w", encoding="utf-8", newline="") as f:
                    f.write(html)
                rel = os.path.relpath(path, pub).replace(os.sep, "/")
                print("renomeado (%d ocorrencias): %s" % (total, rel))
                arquivos_alterados += 1
                substituicoes += total

    print("\nresumo: %d arquivo(s) alterado(s), %d substituicao(oes)"
          % (arquivos_alterados, substituicoes))


if __name__ == "__main__":
    main()
