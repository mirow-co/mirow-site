# -*- coding: utf-8 -*-
"""
104_texto_expertise_18px.py -- S-134 (#198): o texto dos 3 cards de "Nossas
areas de expertise" no tamanho do subtitulo do hero (18px). O 14px vem do CSS
do tema (intocavel, regra n. zero), entao a mudanca e um bloco marcado no
onda6.css. O lado dos setores ("Setores em que atuamos") foi editado NO LUGAR,
no bloco onda18:planeta-setores do 71_home_planeta_setores.py -- sem override,
pela regra dos valores gemeos.

Uso:  python tools_onda6/104_texto_expertise_18px.py <raiz-que-contem-public>

Idempotente: escrever_bloco_css reescreve o mesmo bloco marcado.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, resolve_public  # noqa: E402

CSS = u"""
/* S-134 (#198, 10/08): texto dos cards de expertise = subtitulo do hero (18px).
   O tema dava 14px a ambos (paragrafo e "Conheca a pratica"). */
.praticas-3__card .home-experience__list-item-content p,
.praticas-3__card .home-experience__list-item-more{font-size:18px}
"""


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    mudou = escrever_bloco_css(pub, "texto-expertise", CSS, onda="onda43")
    print("bloco onda43:texto-expertise %s" % ("atualizado" if mudou else "ja em dia"))


if __name__ == "__main__":
    main()
