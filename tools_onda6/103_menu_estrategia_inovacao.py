# -*- coding: utf-8 -*-
"""
103_menu_estrategia_inovacao.py -- S-135 (#199): o submenu Praticas do header
passa a dizer "Estrategia e Inovacao", como o card da home ja diz desde a #187.
EN/DE acompanham os rotulos dos cards das homes.

Uso:  python tools_onda6/103_menu_estrategia_inovacao.py <raiz-que-contem-public>

Escopo: SO o trecho entre <!-- onda7:menu-praticas --> e o marcador de fim, nas
275 paginas. Idempotente: com o rotulo novo no lugar, o padrao antigo nao casa
e o 2o run reporta 0 mudancas.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, idioma_da_pagina, ler, resolve_public  # noqa: E402

MENU_INI = "<!-- onda7:menu-praticas -->"
MENU_FIM = "<!-- /onda7:menu-praticas -->"

# idioma -> (rotulo antigo, rotulo novo) — espelha os cards das homes
NOMES = {
    "pt": (u">Estratégia</a>", u">Estratégia e Inovação</a>"),
    "en": (u">Strategy</a>", u">Strategy &amp; Innovation</a>"),
    "de": (u">Strategie</a>", u">Strategie &amp; Innovation</a>"),
}


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    alterados = 0
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if nome != "index.html":
                continue
            path = os.path.join(dirpath, nome)
            html = ler(path)
            ini = html.find(MENU_INI)
            if ini < 0:
                continue
            fim = html.find(MENU_FIM, ini)
            if fim < 0:
                continue
            fim += len(MENU_FIM)
            velho, novo = NOMES[idioma_da_pagina(html)]
            trecho = html[ini:fim]
            if velho not in trecho:
                continue
            gravar(path, html[:ini] + trecho.replace(velho, novo) + html[fim:])
            alterados += 1
    print("menu Praticas atualizado em %d pagina(s)" % alterados)


if __name__ == "__main__":
    main()
