# -*- coding: utf-8 -*-
"""
17_barra_superior.py — item 4 (a, b, c) da lista do Mario (onda 7).

Uso:  python tools_onda6/17_barra_superior.py <raiz-que-contem-public>

Aplica em TODAS as ~272 paginas do espelho (3 idiomas), porque a barra superior e
repetida no HTML de cada pagina:

 (a) Praticas — o dropdown listava 8 praticas; passa a listar so as 3 que a firma
     comunica hoje (Estrategia, Pricing, Sourcing), apontando para as MESMAS
     paginas que os 3 cards de praticas da home linkam.
 (b) Carreiras — tinha setinha e um submenu com um unico item ("Trabalhe conosco");
     vira link direto para a pagina de carreiras. (No DE ja era link direto.)
 (c) Sobre nos — o dropdown era dividido em duas abas ("Sobre nos" / "Nossa rede").
     A separacao sai: vira uma lista unica, e "Nossa rede" passa a ser um item
     comum, apontando para a pagina de rede do idioma (criada pelo script 21).

Sem CSS novo: a lista unica reusa exatamente o mesmo markup do submenu de Praticas
(<h5> + ul.menu__nav-sublinks--col1), que o tema ja estiliza. O JS do tema so
filtra itens quando existe .menu__nav-subitem — sem as abas, todos aparecem.

Idempotente: cada bloco tem marcadores <!-- onda7:menu-* --> e e reescrito.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import (base_prefix, gravar, idioma_da_pagina, ler,  # noqa: E402
                        paginas, resolve_public)

# idioma -> (titulo do menu, [(rotulo, href relativo)])
SOBRE = {
    "pt": (u"Sobre nós", [
        (u"Nossa história", "pt/sobre-nos/nossa-historia/"),
        (u"Líderes", "pt/sobre-nos/lideres/"),
        (u"Reconhecimentos", "pt/sobre-nos/reconhecimentos/"),
        (u"Nosso Trabalho", "pt/sobre-nos/nosso-trabalho/"),
        (u"Nossa Rede", "pt/sobre-nos/nossa-rede/"),
    ]),
    "en": (u"About us", [
        (u"Our History", "en/about-us/our-history/"),
        (u"Leaders", "en/about-us/leaders/"),
        (u"Recognitions", "en/about-us/recognitions/"),
        (u"Our work", "en/about-us/our-work/"),
        (u"Our network", "en/about-us/our-network/"),
    ]),
    "de": (u"Über uns", [
        (u"Unsere Geschichte", "de/ueber-uns/unsere-geschichte/"),
        (u"Führungkräfte", "de/ueber-uns/fuehrungskraefte/"),
        (u"Anerkennungen", "de/ueber-uns/anerkennungen/"),
        (u"Unsere Arbeit", "de/ueber-uns/unsere-arbeit/"),
        (u"Unser Netzwerk", "de/ueber-uns/unser-netzwerk/"),
    ]),
}

# as 3 praticas: os mesmos destinos dos 3 cards da home (script 04 da onda 6)
PRATICAS = {
    "pt": (u"Práticas", [
        (u"Estratégia", "pt/pratica/estrategia/"),
        (u"Pricing", "pt/pratica/marketing-vendas-e-pricing/"),
        (u"Sourcing", "pt/pratica/operacoes/"),
    ]),
    "en": (u"Practices", [
        (u"Strategy", "en/practice/strategy/"),
        (u"Pricing", "en/practice/marketing-sales-and-pricing/"),
        (u"Sourcing", "en/practice/operations/"),
    ]),
    "de": (u"Branchen", [
        (u"Strategie", "de/branchen/strategie/"),
        (u"Pricing", "de/branchen/marketing-vertrieb-und-preisgestaltung/"),
        (u"Sourcing", "de/branchen/betrieb/"),
    ]),
}

M_SOBRE = ("<!-- onda7:menu-sobre -->", "<!-- /onda7:menu-sobre -->")
M_PRAT = ("<!-- onda7:menu-praticas -->", "<!-- /onda7:menu-praticas -->")
M_CARR = ("<!-- onda7:menu-carreiras -->", "<!-- /onda7:menu-carreiras -->")

RE_SUBTABS = re.compile(
    r'<ul class="menu__nav-subtabs">.*?</ul>'
    r'<ul class="menu__nav-sublinks menu__nav-sublinks--col1">.*?</ul>', re.S)
RE_PRAT = re.compile(
    r'<ul class="menu__nav-sublinks menu__nav-sublinks--col2">.*?</ul>', re.S)
RE_CARR = re.compile(
    r'<div class="menu__nav-item">'
    r'<a class="menu__nav-link menu__nav-link--has-submenu" '
    r'href="([^"]*(?:carreiras|careers|karrieren)/)" target="_self">([^<]+)'
    r'<svg.*?</svg></a>'
    r'<div class="menu__nav-submenu">.*?</ul>'
    r'</div></div></div></div></div></div>', re.S)


def lista(titulo, itens, prefix):
    lis = "".join(
        '<li class="menu__nav-sublinkitem tab_">'
        '<a class="menu__nav-sublink" href="%s%s">%s</a></li>' % (prefix, href, rot)
        for rot, href in itens)
    return ('<h5>%s</h5><ul class="menu__nav-sublinks menu__nav-sublinks--col1">%s</ul>'
            % (titulo, lis))


def troca(html, marcas, regex, novo):
    """Reescreve o bloco marcado; na 1a vez, casa o markup original."""
    ini, fim = marcas
    alvo = ini + novo + fim
    if ini in html:
        return re.sub(re.escape(ini) + r".*?" + re.escape(fim),
                      lambda _m: alvo, html, flags=re.S), True
    m = regex.search(html)
    if not m:
        return html, False
    return html[:m.start()] + alvo + html[m.end():], True


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    alvos = paginas(pub, 'class="menu__nav"')
    print("paginas com a barra superior: %d" % len(alvos))

    alterados = 0
    faltas = {"sobre": [], "praticas": [], "carreiras": []}
    por_idioma = {"pt": 0, "en": 0, "de": 0}
    for path, rel in alvos:
        html = ler(path)
        orig = html
        prefix = base_prefix(html)
        idioma = idioma_da_pagina(html)
        por_idioma[idioma] = por_idioma.get(idioma, 0) + 1

        html, ok = troca(html, M_SOBRE, RE_SUBTABS,
                         lista(SOBRE[idioma][0], SOBRE[idioma][1], prefix))
        if not ok:
            faltas["sobre"].append(rel)

        html, ok = troca(html, M_PRAT, RE_PRAT,
                         '<ul class="menu__nav-sublinks menu__nav-sublinks--col1">%s</ul>'
                         % "".join(
                             '<li class="menu__nav-sublinkitem tab_">'
                             '<a class="menu__nav-sublink" href="%s%s">%s</a></li>'
                             % (prefix, href, rot)
                             for rot, href in PRATICAS[idioma][1]))
        if not ok:
            faltas["praticas"].append(rel)

        m = RE_CARR.search(html) if M_CARR[0] not in html else None
        if m:
            novo = ('%s<div class="menu__nav-item">'
                    '<a class="menu__nav-link " href="%s" target="_self">%s</a></div>%s'
                    % (M_CARR[0], m.group(1), m.group(2), M_CARR[1]))
            html = html[:m.start()] + novo + html[m.end():]
        elif M_CARR[0] not in html and idioma != "de":
            faltas["carreiras"].append(rel)

        if html != orig:
            gravar(path, html)
            alterados += 1

    print("idiomas detectados: %s" % por_idioma)
    for chave, lst in faltas.items():
        if lst:
            print("AVISO: bloco '%s' nao encontrado em %d pagina(s), ex.: %s"
                  % (chave, len(lst), lst[:3]))
    print("\nresumo: %d arquivo(s) alterado(s)" % alterados)


if __name__ == "__main__":
    main()
