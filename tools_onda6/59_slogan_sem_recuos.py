# -*- coding: utf-8 -*-
"""59 — S-39: slogan sem os recuos de escadinha (alinhado a esquerda).

Uso:
    python tools_onda6/59_slogan_sem_recuos.py <raiz-que-contem-public>

Pedido do Mario (31/07, fim do dia): "vamos remover o espaco 'escadinha'
entre estratégia confiança e resultados" — a indentação progressiva da S-01
(#51) sai; as 3 palavras ficam alinhadas à esquerda, uma por linha.

Mecanica: regrava o bloco onda10:hero-escadinha do onda6.css com margem zero
nos degraus (os <span class="onda10-degrau"> ficam no HTML — a estrutura em
3 linhas e a assercao S01 continuam valendo; muda so a apresentacao).

Idempotente (escrever_bloco_css regrava igual = 0 mudancas).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, resolve_public  # noqa: E402

CSS = """/* onda10 (S-01/#51) virou S-39 (31/07): os recuos de escadinha SAIRAM por
   decisao do Mario — as 3 palavras alinhadas a esquerda. Os spans .onda10-degrau
   ficam (estrutura de 3 linhas protegida pela S01). */
.homepage .banner h2 .onda10-degrau{display:inline;margin-left:0 !important}"""


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    mudou = escrever_bloco_css(pub, "hero-escadinha", CSS, onda="onda10")
    print("bloco onda10:hero-escadinha %s" % ("regravado sem recuos" if mudou else "ja estava igual"))


if __name__ == "__main__":
    main()
