# -*- coding: utf-8 -*-
"""84 — onda 29, S-106 (#164): Imprensa passa a existir em EN e DE.

Uso:
    python tools_onda6/84_imprensa_en_de.py <raiz-que-contem-public>

Achado da onda 27: o menu PT tem 6 itens e o EN/DE tem 5 — faltava
Imprensa/Press/Presse, porque a pagina so existia em portugues. Era a unica
diferenca de barra entre URLs que CSS nao resolvia. Decisao do Mario (04/08):
criar as paginas traduzidas.

O que faz:
  1. Gera `public/en/press/` e `public/de/presse/` a partir de um DOADOR do mesmo
     idioma (a pagina de politica de privacidade, que usa o mesmo template
     `page-default`): assim header, rodape, menu e metadados ja nascem no idioma
     certo. So o <main> e substituido pelo conteudo de imprensa.
  2. A LISTA de artigos e copiada verbatim da pagina PT — o titulo de cada
     materia fica no idioma em que foi publicada, que e o correto. So o titulo da
     pagina e a linha de apoio sao traduzidos.
  3. Liga as tres paginas: canonical/og:url proprios e o seletor de idiomas das
     tres apontando uma para a outra (hoje o da PT jogava EN e DE na home).
  4. Poe o item no menu de EN e DE, depois de Insights e antes de Carreiras — a
     ordem que o Mario definiu na S-104 — no header E no clone do rodape (a
     assercao S36 exige que as duas barras sejam identicas byte a byte).

Idempotente: as paginas so sao escritas se o conteudo mudar; o item de menu so
entra se ainda nao existir.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, ler, resolve_public  # noqa: E402

PT = "pt/imprensa/index.html"

# (idioma, pasta nova, doador do mesmo idioma, titulo, linha de apoio, <title>, rotulo no menu)
ALVOS = [
    ("en", "en/press",
     "en/privacy-policy/index.html",
     u"Mirow in the press",
     u"Our latest contributions to leading media in Brazil and around the world",
     u"Press - Mirow",
     u"Press"),
    ("de", "de/presse",
     "de/datenschutzrichtlinie/index.html",
     u"Mirow in der Presse",
     u"Unsere neuesten Beiträge in führenden Medien in Brasilien und weltweit",
     u"Presse - Mirow",
     u"Presse"),
]

URLS = {
    "pt": "/mirow-site/pt/imprensa/",
    "en": "/mirow-site/en/press/",
    "de": "/mirow-site/de/presse/",
}
BASE = "https://mirow-co.github.io"

MARK = "<!-- onda29:imprensa-%s -->"


def lista_de_artigos(pub):
    """O <ul class="onda18-imprensa"> da pagina PT, com os marcadores da onda 18."""
    h = ler(os.path.join(pub, PT.replace("/", os.sep)))
    m = re.search(r'<!-- onda18:imprensa-lista -->.*?<!-- /onda18:imprensa-lista -->',
                  h, re.S)
    if not m:
        raise SystemExit("nao achei a lista de imprensa em %s" % PT)
    return m.group(0)


def corpo(lang, titulo, apoio, lista):
    return (
        u'%s<div class="container page-default"><div class="row"><div class="col">'
        u'<!-- wp:heading {"level":1} -->\n'
        u'<h1 class="wp-block-heading">%s</h1>\n'
        u'<!-- /wp:heading -->\n\n'
        u'<!-- wp:heading {"level":5} -->\n'
        u'<h5 class="wp-block-heading">%s</h5>\n'
        u'<!-- /wp:heading -->\n\n'
        u'<!-- wp:spacer -->\n'
        u'<div style="height:100px" aria-hidden="true" class="wp-block-spacer"></div>\n'
        u'<!-- /wp:spacer -->\n\n'
        u'%s</div></div></div>' % (MARK % lang, titulo, apoio, lista))


def trocar_main(html, novo_corpo):
    m = re.search(r'(<main class="[^"]*">)(.*?)(</main>)', html, re.S)
    if not m:
        raise SystemExit("doador sem <main>")
    return html[:m.start(2)] + novo_corpo + html[m.end(2):]


def trocar_switcher(html):
    """Aponta o seletor de idiomas para as tres paginas de imprensa."""
    m = re.search(r'(<ul class="menu__languages-list">)(.*?)(</ul>)', html, re.S)
    if not m:
        return html
    bloco = m.group(2)

    def sub(mm):
        # a ordem das <li> e sempre pt, en, de (Polylang)
        sub.i += 1
        lang = ("pt", "en", "de")[min(sub.i - 1, 2)]
        return '<a href="%s"' % URLS[lang]
    sub.i = 0
    novo = re.sub(r'<a href="[^"]+"', sub, bloco)
    # o rodape tem uma segunda lista (clone) — a funcao e chamada por ocorrencia
    return html[:m.start(2)] + novo + html[m.end(2):]


def switcher_em_tudo(html):
    """Reescreve TODAS as listas de idiomas da pagina (header e clone do rodape)."""
    partes = html.split('<ul class="menu__languages-list">')
    if len(partes) == 1:
        return html
    out = [partes[0]]
    for p in partes[1:]:
        fim = p.find("</ul>")
        bloco, resto = p[:fim], p[fim:]
        i = [0]

        def sub(mm):
            lang = ("pt", "en", "de")[min(i[0], 2)]
            i[0] += 1
            return '<a href="%s"' % URLS[lang]
        bloco = re.sub(r'<a href="[^"]+"', sub, bloco)
        out.append(bloco + resto)
    return '<ul class="menu__languages-list">'.join(out)


def metadados(html, lang, titulo_head):
    url = URLS[lang]
    html = re.sub(r'<title>[^<]*</title>', '<title>%s</title>' % titulo_head, html)
    html = re.sub(r'(rel="canonical" href=")[^"]*(")', r'\g<1>%s\g<2>' % url, html)
    html = re.sub(r'(property="og:url" content=")[^"]*(")',
                  r'\g<1>%s%s\g<2>' % (BASE, url), html)
    html = re.sub(r'(property="og:title" content=")[^"]*(")',
                  r'\g<1>%s\g<2>' % titulo_head, html)
    return html


def item_de_menu(html, rotulo, url):
    """Poe o item de imprensa depois de Insights, no header e no clone do rodape."""
    # a checagem tem de ser pelo ITEM DE MENU, nao pela URL solta: na propria
    # pagina de imprensa a URL aparece no canonical e no og:url, e um `in html`
    # simples fazia o script achar que o item ja existia
    if 'class="menu__nav-link " href="%s"' % url in html:
        return html, False
    item = ('<div class="menu__nav-item"><a class="menu__nav-link " href="%s" '
            'target="_self">%s</a></div>' % (url, rotulo))
    padrao = re.compile(r'(<div class="menu__nav-item"><a class="menu__nav-link[^"]*" '
                        r'href="[^"]*/insights/"[^>]*>[^<]*</a></div>)')
    novo, n = padrao.subn(lambda m: m.group(1) + item, html)
    return novo, n > 0


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    lista = lista_de_artigos(pub)

    # 1) as duas paginas novas
    for lang, pasta, doador, titulo, apoio, titulo_head, rotulo in ALVOS:
        d = ler(os.path.join(pub, doador.replace("/", os.sep)))
        pagina = trocar_main(d, corpo(lang, titulo, apoio, lista))
        pagina = metadados(pagina, lang, titulo_head)
        pagina = switcher_em_tudo(pagina)
        # o item de menu entra JA aqui: senao a pagina sai do doador sem ele no
        # primeiro run e com ele no segundo (o doador tambem ganha o item no
        # passo 3), e o script deixaria de ser idempotente
        pagina, _ = item_de_menu(pagina, rotulo, URLS[lang])
        destino = os.path.join(pub, pasta.replace("/", os.sep))
        os.makedirs(destino, exist_ok=True)
        p = os.path.join(destino, "index.html")
        antes = ler(p) if os.path.exists(p) else None
        if antes == pagina:
            print("  %s/ ja estava igual" % pasta)
        else:
            gravar(p, pagina)
            print("  %s/ %s" % (pasta, "atualizada" if antes else "criada"))

    # 2) o seletor de idiomas das paginas PT de imprensa aponta para as novas
    for rel in ("pt/imprensa/index.html", "imprensa/index.html"):
        p = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(p):
            continue
        h = ler(p)
        novo = switcher_em_tudo(h)
        if novo != h:
            gravar(p, novo)
            print("  seletor de idiomas ligado em %s" % rel)

    # 3) o item no menu de EN e DE (todas as paginas daquele idioma)
    from _onda7_css import idioma_da_pagina
    rotulos = {lang: (rot, URLS[lang]) for lang, _p, _d, _t, _a, _th, rot in ALVOS}
    n = 0
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if nome != "index.html":
                continue
            p = os.path.join(dirpath, nome)
            h = ler(p)
            if "menu__nav-item" not in h:
                continue
            lang = idioma_da_pagina(h)
            if lang not in rotulos:
                continue
            rotulo, url = rotulos[lang]
            novo, mudou = item_de_menu(h, rotulo, url)
            if mudou:
                gravar(p, novo)
                n += 1
    print("S-106 paginas com o item novo no menu: %d" % n)


if __name__ == "__main__":
    main()
