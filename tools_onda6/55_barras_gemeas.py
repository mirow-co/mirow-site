# -*- coding: utf-8 -*-
"""55 — S-36: barras superior e inferior gemeas (fonte, itens, canais, tamanho).

Uso:
    python tools_onda6/55_barras_gemeas.py <raiz-que-contem-public>

Pedido do Mario (31/07): "barra inferior precisa ser a mesma que aquela barra
superior. acho inclusive que a barra superior (sobre nos, praticas, etc.)
precisa ser refeita com a mesma fonte que aquela usada para a barra inferior.
mas a barra inferior faltam os links para os canais de comunicacao (que em
ambas as barras precisam ter tamanhos maiores. vamos mante-las (essas 2
barras) sempre paralelas uma a outra"

O QUE FAZ
---------
1. HTML: em toda pagina com a nav do rodape (onda14:rodape-menu), acrescenta
   os 4 canais de comunicacao — o bloco onda8:menu-contatos do header da
   PROPRIA pagina e clonado para dentro da nav do rodape (mesmos links,
   mesmos icones, fonte unica). Marcadores onda15:rodape-contatos.
2. CSS (bloco onda15:barras-gemeas):
   - barra superior refeita com a fonte da inferior: peso 400, 15px
     (o tema usava 26px/bold reduzido por transform — tipografia unificada);
   - rodape-menu tambem a 15px;
   - icones dos canais MAIORES nas duas barras (17px -> 22px).

A paridade "sempre paralelas" e protegida por assercao (S36 na suite):
os itens da nav do rodape tem que ser os mesmos do header, pagina a pagina.

Idempotente: o bloco do rodape e regravado entre marcadores.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, gravar, ler, resolve_public  # noqa: E402

MARK_INI = "<!-- onda15:rodape-contatos -->"
MARK_FIM = "<!-- /onda15:rodape-contatos -->"

REX_CONTATOS = re.compile(
    r'<!-- onda8:menu-contatos -->(.*?)<!-- /onda8:menu-contatos -->', re.S)
FIM_NAV = '</ul></div></div><!-- /onda14:rodape-menu -->'

CSS = """/* S-36: as duas barras gemeas. A superior adota a fonte da inferior
   (peso 400, 15px); os canais de comunicacao ganham tamanho nas duas. */
.menu__nav-link{font-weight:400 !important;font-size:15px !important}
.rodape-menu a{font-size:15px}
.menu__contatos svg{width:22px !important;height:22px !important}
.rodape-contatos{display:flex;justify-content:center;gap:22px;
  margin:14px 0 0;padding:0;list-style:none}
/* o tema esconde .menu__contatos no mobile e empurra para a direita no
   desktop (margin-left:auto) — no rodape ele fica visivel e centrado */
.rodape-contatos .menu__contatos{display:flex;gap:26px;align-items:center;
  margin-left:0 !important;padding-right:0 !important}
.rodape-contatos .menu__contatos-link{color:#fff;opacity:.9}
.rodape-contatos .menu__contatos-link:hover{color:#00ADEC;opacity:1}
.rodape-contatos .menu__contatos-link svg{width:22px !important;
  height:22px !important}"""


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    mudou_css = escrever_bloco_css(pub, "barras-gemeas", CSS, onda="onda15")
    print("bloco onda15:barras-gemeas %s" % ("gravado" if mudou_css else "ja estava igual"))

    alterados = 0
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if not n.endswith(".html"):
                continue
            p = os.path.join(dp, n)
            h = ler(p)
            if "onda14:rodape-menu" not in h:
                continue
            m = REX_CONTATOS.search(h)
            if not m:
                continue
            bloco = ('%s<div class="rodape-contatos">%s</div>%s'
                     % (MARK_INI, m.group(1).strip(), MARK_FIM))
            if MARK_INI in h:
                velho = h[h.index(MARK_INI):h.index(MARK_FIM) + len(MARK_FIM)]
                novo = h.replace(velho, bloco, 1)
            elif FIM_NAV in h:
                # entra logo depois do </ul> da nav, dentro do col-12
                novo = h.replace(
                    FIM_NAV,
                    '</ul>' + bloco + '</div></div><!-- /onda14:rodape-menu -->', 1)
            else:
                continue
            if novo != h:
                gravar(p, novo)
                alterados += 1
    print("resumo: %d pagina(s) com canais no rodape" % alterados)


if __name__ == "__main__":
    main()
