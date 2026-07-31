# -*- coding: utf-8 -*-
"""
39_menus_praticas.py -- nomes completos das 3 praticas nos MENUS (275 paginas)
e nos 3 cards de pratica da HOME (issue S-26 / #76).

*** ESTE SCRIPT NAO FOI EXECUTADO NESTA SESSAO. ***
Fica pronto para o orquestrador rodar na integracao, para evitar conflito com
outro agente mexendo nas mesmas 275 paginas (menu) / nas 4 homes ao mesmo
tempo. Ver relato da sessao.

Uso:  python tools_onda6/39_menus_praticas.py <raiz-da-arvore>

Duas frentes, cada uma dentro de um marcador ja existente (idempotente por
construcao -- so mexe dentro do marcador, nunca fora):

1) Menu "Praticas" (submenu do header, identico nas 275 paginas), dentro de
   <!-- onda7:menu-praticas --> ... <!-- /onda7:menu-praticas -->:
     PT: "Pricing" -> "Go-to-market e Pricing" · "Sourcing" -> "Sourcing, Compras e Estoques"
     EN: "Pricing" -> "Go-to-market &amp; Pricing" · "Sourcing" -> "Sourcing, Procurement &amp; Inventory"
     DE: "Pricing" -> "Go-to-Market &amp; Pricing" · "Sourcing" -> "Sourcing, Einkauf &amp; Bestände"
   ("Estrategia"/"Strategy"/"Strategie" ja e o nome completo -- sem mudanca.)

2) Cards de pratica da home (rotulo do <h4>, NAO o texto do card -- isso e a
   S-05/#54, que depende de aprovacao do Mario), dentro de
   <!-- onda6:praticas --> ... <!-- /onda6:praticas -->, nos 4 arquivos de
   home (pt/index.html, en/index.html, en/homepage/index.html, de/index.html):
     <span>Pricing</span> -> <span>NOVO NOME</span>
     <span>Sourcing</span> -> <span>NOVO NOME</span>

Por que um script a parte (e nao no 36_renomear_praticas_paginas.py): o menu
aparece IDENTICO nas 275 paginas do espelho (nao so nas paginas de pratica) e
os cards da home ficam na propria home -- fora do escopo desta sessao, que foi
restrita as paginas de pratica/expertise. Rodar isso ao mesmo tempo que outro
agente mexe em qualquer uma das 275 paginas arrisca conflito; por isso o
orquestrador roda este script sozinho, na integracao.

Idempotente: se o novo nome ja estiver no menu/card, os replaces (escopados ao
marcador) nao acham o padrao antigo e nao fazem nada (0 mudancas no 2o run).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, ler, resolve_public  # noqa: E402

MENU_INI = "<!-- onda7:menu-praticas -->"
MENU_FIM = "<!-- /onda7:menu-praticas -->"
HOME_INI = "<!-- onda6:praticas -->"
HOME_FIM = "<!-- /onda6:praticas -->"

# idioma -> {rotulo antigo: rotulo novo}
NOMES_MENU = {
    "pt": {"Pricing": "Go-to-market e Pricing",
           "Sourcing": "Sourcing, Compras e Estoques"},
    "en": {"Pricing": "Go-to-market &amp; Pricing",
           "Sourcing": "Sourcing, Procurement &amp; Inventory"},
    "de": {"Pricing": "Go-to-Market &amp; Pricing",
           "Sourcing": u"Sourcing, Einkauf &amp; Bestände"},
}

HOMES = [
    ("pt/index.html", "pt"),
    ("en/index.html", "en"),
    ("en/homepage/index.html", "en"),
    ("de/index.html", "de"),
]


def idioma_da_pagina(html):
    m = re.search(r'pll_language=([a-z]{2})', html)
    return m.group(1) if m and m.group(1) in ("pt", "en", "de") else "pt"


def trocar_dentro(html, ini_marcador, fim_marcador, substituicoes):
    """Aplica {old: new} SO no trecho entre ini_marcador e fim_marcador."""
    ini = html.find(ini_marcador)
    if ini < 0:
        return html, 0
    fim = html.find(fim_marcador, ini)
    if fim < 0:
        return html, 0
    fim += len(fim_marcador)
    trecho = html[ini:fim]
    novo_trecho = trecho
    n = 0
    for old, new in substituicoes.items():
        c = novo_trecho.count(old)
        if c:
            novo_trecho = novo_trecho.replace(old, new)
            n += c
    if novo_trecho == trecho:
        return html, 0
    return html[:ini] + novo_trecho + html[fim:], n


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    # 1) menu, nas 275 paginas
    alterados_menu = 0
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if nome != "index.html":
                continue
            path = os.path.join(dirpath, nome)
            html = ler(path)
            if MENU_INI not in html:
                continue
            idioma = idioma_da_pagina(html)
            subs = {(">%s</a>" % k): (">%s</a>" % v)
                    for k, v in NOMES_MENU[idioma].items()}
            novo_html, n = trocar_dentro(html, MENU_INI, MENU_FIM, subs)
            if n:
                gravar(path, novo_html)
                alterados_menu += 1
                rel = os.path.relpath(path, pub).replace(os.sep, "/")
                print("menu atualizado (%d, %s): %s" % (n, idioma, rel))

    # 2) cards da home
    alterados_home = 0
    for rel, idioma in HOMES:
        path = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(path):
            print("AVISO: nao existe %s" % rel)
            continue
        html = ler(path)
        subs = {("<span>%s</span>" % k): ("<span>%s</span>" % v)
                for k, v in NOMES_MENU[idioma].items()}
        novo_html, n = trocar_dentro(html, HOME_INI, HOME_FIM, subs)
        if n:
            gravar(path, novo_html)
            alterados_home += 1
            print("card da home atualizado (%d, %s): %s" % (n, idioma, rel))

    print("\nresumo: %d pagina(s) de menu alterada(s), %d home(s) alterada(s)"
          % (alterados_menu, alterados_home))


if __name__ == "__main__":
    main()
