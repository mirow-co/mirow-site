# -*- coding: utf-8 -*-
"""52 — S-33 (issue #85): fundo da home conforme o conteudo (sem sobra clara).

Uso:
    python tools_onda6/52_fundo_sem_sobras.py <raiz-que-contem-public>

O PROBLEMA
----------
Na home, o wrapper div.wrap-gradient-2 (so existe nas homes) tem
padding:0 0 100px e um gradiente proprio que termina em azul-claro #A2BAE4
na base. Esses 100px viram uma faixa clara ORFA entre o CTA ("Como podemos
ajudar?" / "Transforme sua carreira") e o footer navy — a "sobra" que o Mario
apontou (31/07).

O QUE FAZ
---------
CSS-only, bloco marcado onda14:fundo-sem-sobras: zera o padding-bottom do
wrapper nas homes (body.home). O CTA passa a encostar no footer, navy com
navy. Nenhum HTML muda.

Idempotente (escrever_bloco_css regrava igual = 0 mudancas).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, resolve_public  # noqa: E402

CSS = """/* S-33 (#85): o padding-bottom de 100px do wrap-gradient-2 expunha o fim
   azul-claro do gradiente entre o CTA e o footer — a "sobra" da home. */
.home .wrap-gradient-2{padding-bottom:0}"""


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    mudou = escrever_bloco_css(pub, "fundo-sem-sobras", CSS, onda="onda14")
    print("bloco onda14:fundo-sem-sobras %s" % ("gravado" if mudou else "ja estava igual"))


if __name__ == "__main__":
    main()
