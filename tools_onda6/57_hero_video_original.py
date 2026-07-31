# -*- coding: utf-8 -*-
"""57 — S-37: hero volta ao VIDEO original da lampada (como no mirow.com.br).

Uso:
    python tools_onda6/57_hero_video_original.py <raiz-que-contem-public>

Pedido do Mario (31/07, terceira rodada): "nao gostei da animacao da lampada
atual, tem que ficar como era no site https://mirow.com.br/pt/".

A "animacao atual" era a foto estatica (frame do video) + canvas plexus por
cima (S-34). Volta o <video> original do tema (video-bg-home-1.mp4, autoplay
muted loop, opacity .5 via CSS do tema) — MAS mantendo o que o Mario aprovou:

  - full-bleed (S-30): o div continua filho direto da section.banner, sem a
    mascara vertical do tema — o video estica pelo hero inteiro;
  - paineis de vidro (S-34) e o resto do hero ficam como estao.

Custo consciente: as homes voltam a baixar o MP4 de 22,8 MB — decisao
explicita do dono (registrada na issue #92); o ganho de peso do #73 e
revertido. A camada canvas (onda13-hero-plexus.js) sai das paginas.

Idempotente.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import base_prefix, gravar, ler, resolve_public  # noqa: E402

HOMES = ["pt/index.html", "en/index.html", "de/index.html", "en/homepage/index.html"]

REX_MALHA = re.compile(
    r'<!-- onda13:hero-malha -->.*?<!-- /onda13:hero-malha -->', re.S)

VIDEO = (u'<!-- onda13:hero-malha -->\n'
         u'                <video autoplay="true" muted="true" loop="true">\n'
         u'                    <source src="{pfx}wp-content/uploads/2024/04/'
         u'video-bg-home-1.mp4" type="video/mp4">\n'
         u'                    Your browser does not support the video tag.\n'
         u'                </video>\n'
         u'                <!-- /onda13:hero-malha -->')


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    alterados = []
    for rel in HOMES:
        p = os.path.join(pub, rel.replace("/", os.sep))
        h = ler(p)
        pfx = base_prefix(h)
        novo = REX_MALHA.sub(VIDEO.format(pfx=pfx), h, count=1)
        if novo != h:
            gravar(p, novo)
            alterados.append(rel)
    print("paginas alteradas: %s" % (", ".join(alterados) or "nenhuma (ja estava igual)"))


if __name__ == "__main__":
    main()
