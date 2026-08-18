# -*- coding: utf-8 -*-
"""Onda 60 (PageSpeed 18/08): atributos de acessibilidade e o alt da marca.

Todos os consertos aqui sao ATRIBUTOS que nao afetam layout — nenhum pixel muda.
Origem: relatorio PageSpeed mobile+desktop de 18/08/2026.

1. alt da logo: "Stratigital" (nome do tema anterior) -> "Mirow & Co."
   Achado nosso, nao do relatorio: o <h1> das 109 paginas anunciava a marca errada.
2. aria-label no botao hambúrguer e no seletor de idiomas (falha "Buttons do not
   have an accessible name" no mobile e no desktop; e a UNICA falha da categoria
   Agentic Browsing, que mede se um agente de IA entende a pagina).
3. alt nas 4 fotos de lider do card da home (falha em acessibilidade E em SEO).
   A causa-raiz esta no gerador 06_quadro_lideres.py — corrigida la tambem.
4. aria-label nos 3 links "Conheca a pratica" (falha "Identical links have the
   same purpose": mesmo texto, tres destinos).
5. aria-level nos dois <h4> que quebram a ordem hierarquica. NAO trocamos a tag
   por <h3> porque o CSS do tema estiliza h4 por TAG (`h4{...}`) — trocar mudaria
   o visual. aria-level corrige a semantica com zero risco.
6. target=" _self " -> target="_self" (o valor com espacos nao e reconhecido).

Idempotente: 2o run reporta 0 mudancas.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public

ALT_ERRADO = 'alt="Stratigital"'
ALT_CERTO = 'alt="Mirow &amp; Co."'

ROTULO_MENU = {
    "pt": u"Abrir o menu",
    "en": u"Open the menu",
    "de": u"Menü öffnen",
}
ROTULO_IDIOMA = {
    "pt": u"Escolher idioma",
    "en": u"Choose language",
    "de": u"Sprache wählen",
}

# O slug da pratica muda em cada idioma (pt/pratica/, en/practice/, de/branchen/),
# entao o casamento e pelo ULTIMO segmento do href -> nome da pratica no idioma.
SLUG_PRATICA = {
    # pt
    "estrategia": u"Estratégia e Inovação",
    "marketing-vendas-e-pricing": u"Go-to-market e Pricing",
    "operacoes": u"Sourcing, Compras e Estoques",
    # en
    "strategy": u"Strategy and Innovation",
    "marketing-sales-and-pricing": u"Go-to-market and Pricing",
    "operations": u"Sourcing, Procurement and Inventory",
    # de
    "strategie": u"Strategie und Innovation",
    "marketing-vertrieb-und-preisgestaltung": u"Go-to-market und Pricing",
    "betrieb": u"Sourcing, Einkauf und Bestände",
}
RE_LINK_PRATICA = re.compile(
    r'<a class="home-experience__list-item-more" href="([^"]+)"([^>]*)>')
CONHECA = {"pt": u"Conheça a prática", "en": u"Learn about the practice",
           "de": u"Mehr über den Bereich"}

# O alt da foto de lider e LIDO DO PROPRIO CARD (o <h4> ao lado traz o nome), nao de
# uma tabela de nome de arquivo. A home alema usa variantes `-232x239-1.png` das
# mesmas fotos, e qualquer tabela de arquivos perderia essas tres. Ler do markup
# tambem sobrevive a troca de foto de qualquer lider.
RE_CARD_LIDER = re.compile(
    r'(<(?:button|div) class="home-leaders__card"[^>]*>\s*<img\b)([^>]*)(>\s*<span>\s*'
    r'<h4[^>]*>)(.*?)(</h4>)', re.S)

RE_H4_EXPERTISE = re.compile(r'<h4 class="home-experience__list-item-header">')
# o card do lider e <button|div class="home-leaders__card" ...><img ...><span><h4>Nome</h4>
RE_H4_LIDER = re.compile(
    r'(<(?:button|div) class="home-leaders__card"[^>]*>\s*<img[^>]*>\s*<span>)<h4>')


def ler(p):
    with io.open(p, encoding="utf-8") as f:
        return f.read()


def gravar(p, s):
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)


def idioma(rel):
    if rel.startswith("de/") or rel.startswith("de\\"):
        return "de"
    if rel.startswith("en/") or rel.startswith("en\\"):
        return "en"
    return "pt"


def main(raiz):
    pub = resolve_public(raiz)
    tocados = 0
    for dp, _d, fs in os.walk(pub):
        if os.sep + ".git" in dp:
            continue
        for nome in fs:
            if not nome.endswith(".html"):
                continue
            fp = os.path.join(dp, nome)
            rel = os.path.relpath(fp, pub).replace(os.sep, "/")
            lang = idioma(rel)
            h = ler(fp)
            orig = h

            # 1. alt da marca
            h = h.replace(ALT_ERRADO, ALT_CERTO)

            # 2. nome acessivel nos dois botoes
            h = h.replace(
                '<button class="menu__hamburguer">',
                '<button class="menu__hamburguer" aria-label="%s">' % ROTULO_MENU[lang])
            h = h.replace(
                '<button class="menu__languages-button">',
                '<button class="menu__languages-button" aria-label="%s">'
                % ROTULO_IDIOMA[lang])

            # 3. alt nas fotos de lider, com o nome tirado do <h4> do proprio card
            def alt_do_card(m):
                abre_img, attrs, meio, nome_h4, fecha = m.groups()
                if "alt=" in attrs:
                    return m.group(0)
                pessoa = re.sub(r"<[^>]+>", "", nome_h4).replace("Private:", "").strip()
                if not pessoa:
                    return m.group(0)
                return "%s%s alt=\"%s\"%s%s%s" % (
                    abre_img, attrs.rstrip(), pessoa, meio, nome_h4, fecha)
            h = RE_CARD_LIDER.sub(alt_do_card, h)

            # 4. aria-label distinto nos 3 links de pratica
            def rotula(m):
                href, resto = m.group(1), m.group(2)
                if "aria-label" in resto:
                    return m.group(0)
                slug = href.rstrip("/").rsplit("/", 1)[-1]
                nome = SLUG_PRATICA.get(slug)
                if not nome:
                    return m.group(0)
                return ('<a class="home-experience__list-item-more" href="%s"%s'
                        ' aria-label="%s: %s">' % (href, resto, CONHECA[lang], nome))
            h = RE_LINK_PRATICA.sub(rotula, h)

            # 5. aria-level nos h4 que quebram a ordem (h2 -> h4)
            h = RE_H4_EXPERTISE.sub(
                '<h4 class="home-experience__list-item-header" aria-level="3">', h)
            h = RE_H4_LIDER.sub(r'\1<h4 aria-level="3">', h)

            # 6. target com espacos
            h = h.replace('target=" _self "', 'target="_self"')

            if h != orig:
                gravar(fp, h)
                tocados += 1
    print("arquivos alterados: %d" % tocados)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
