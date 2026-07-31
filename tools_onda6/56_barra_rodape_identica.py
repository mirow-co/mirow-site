# -*- coding: utf-8 -*-
"""56 — S-36 v2 (issue #91): a barra do rodape e um CLONE da barra superior.

Uso:
    python tools_onda6/56_barra_rodape_identica.py <raiz-que-contem-public>

Pedido do Mario (31/07, segunda rodada): "voce nao viu que a barra inferior
esta diferente da superior? quero que sejam IDENTICAS IDENTICAS IDENTICAS".

A v1 (scripts 51+55) RECRIAVA a barra no rodape com markup proprio — fonte e
espacamento nunca seriam identicos. A v2 CLONA o <nav class="menu"> inteiro
do header da propria pagina para dentro do rodape: mesmo HTML, mesmas classes,
mesmo CSS do tema => identica por construcao. A paridade vira assercao (S36):
o clone tem que ser igual ao header byte a byte (modulo os ajustes abaixo).

Ajustes no clone (unicos):
  - id="check" -> id="check-rodape" (e for=/href= correspondentes): id
    duplicado quebraria o seletor de idioma do header;
  - data-scroll-header removido (o JS do tema so deve controlar a de cima).

O bloco antigo (onda14:rodape-menu, com onda15:rodape-contatos dentro) e
REMOVIDO — substituido pelo onda15:rodape-barra.

CSS (bloco onda15:rodape-barra): o clone e estatico (a barra do tema e fixa
no topo), os submenus abrem PARA CIMA, e um respiro separa da linha legal.

Idempotente: o bloco do clone e regravado entre marcadores.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, gravar, ler, resolve_public  # noqa: E402

MARK_INI = "<!-- onda15:rodape-barra -->"
MARK_FIM = "<!-- /onda15:rodape-barra -->"

REX_VELHO = re.compile(
    r'\s*<!-- onda14:rodape-menu -->.*?<!-- /onda14:rodape-menu -->', re.S)
REX_FOOTER = re.compile(r'(<footer class="footer">\s*<div class="container">)')

CSS = """/* S-36 v2: a barra do rodape e um CLONE literal da superior (mesmo HTML e
   CSS do tema). Aqui so o que muda de contexto: estatica (a original e fixa
   no topo), submenus abrindo para cima, respiro antes da linha legal. */
.rodape-barra{position:relative;margin:0 0 24px;padding:6px 0 10px;
  border-bottom:1px solid rgba(170,213,232,.25)}
.rodape-barra .menu{position:static !important;transform:none !important}
.rodape-barra .menu__nav-submenu{top:auto !important;bottom:100%}
"""


def clonar(nav):
    nav = nav.replace('id="check"', 'id="check-rodape"')
    nav = nav.replace('for="check"', 'for="check-rodape"')
    nav = nav.replace('href="#check"', 'href="#check-rodape"')
    nav = nav.replace(' data-scroll-header=""', '').replace(' data-scroll-header', '')
    return nav


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    mudou_css = escrever_bloco_css(pub, "rodape-barra", CSS, onda="onda15")
    print("bloco onda15:rodape-barra %s" % ("gravado" if mudou_css else "ja estava igual"))

    alterados = 0
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if not n.endswith(".html"):
                continue
            p = os.path.join(dp, n)
            h = ler(p)
            if '<footer class="footer">' not in h:
                continue
            i = h.find('<nav class="menu"')
            if i < 0:
                continue
            fim_nav = h.find('</nav>', i)
            if fim_nav < 0:
                continue
            clone = ('%s<div class="rodape-barra">%s</div>%s'
                     % (MARK_INI, clonar(h[i:fim_nav + 6]), MARK_FIM))
            novo = REX_VELHO.sub('', h)
            if MARK_INI in novo:
                velho = novo[novo.index(MARK_INI):novo.index(MARK_FIM) + len(MARK_FIM)]
                novo = novo.replace(velho, clone, 1)
            else:
                novo = REX_FOOTER.sub(lambda m: m.group(1) + "\n            " + clone,
                                      novo, count=1)
            if novo != h:
                gravar(p, novo)
                alterados += 1
    print("resumo: %d pagina(s) com a barra clonada no rodape" % alterados)


if __name__ == "__main__":
    main()
