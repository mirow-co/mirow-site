# -*- coding: utf-8 -*-
r"""127_medicao_defer.py — o script de medicao para de bloquear o desenho.

    python tools_onda6/127_medicao_defer.py <raiz-que-contem-public> [--check]

Idempotente: rodar 2x reporta 0 mudancas.

O PROBLEMA, nomeado pelo PageSpeed de 18/08 (mobile)
----------------------------------------------------
`onda31-medicao.js` aparece na lista de "Render-blocking requests" custando **236 ms**.
Ele entra como `<script src=...>` sem `defer` nem `async`, entao o navegador PARA de
montar a pagina para buscar e executar 5,7 KB de GA4 antes de desenhar qualquer coisa.

Por que isso importa aqui e nao e cosmetico: o elemento de LCP da home e **texto** --
o relatorio nomeia `div.hero-texto > p` ("Oferecemos consultoria estrategica...").
Nao ha imagem no caminho critico para otimizar; o que atrasa aquele paragrafo e
exatamente o que bloqueia o render antes dele.

POR QUE `defer` E SEGURO AQUI
-----------------------------
O arquivo e uma IIFE que so instala `window.dataLayer`/`window.gtag` e liga listeners.
Nao usa `document.write` (o unico caso em que `defer` quebra de verdade) e nada no
HTML depende de ele ter rodado antes do parse terminar. Com `defer` o script baixa em
paralelo e executa antes do DOMContentLoaded, na ordem — que e tudo que ele precisa.

NAO mexe no tema (REGRA Nº ZERO): o arquivo e nosso, criado na onda 31.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public, ler, gravar

ALVO = "onda31-medicao.js"
# <script src="...onda31-medicao.js?v=NN"> sem defer/async
RE_TAG = re.compile(r'<script(?![^>]*\bdefer\b)(?![^>]*\basync\b)([^>]*\bsrc="[^"]*'
                    + re.escape(ALVO) + r'[^"]*")([^>]*)>')


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    check = "--check" in sys.argv
    pub = resolve_public(sys.argv[1])

    tocadas = ja = 0
    for dp, _d, fs in os.walk(pub):
        if os.sep + ".git" in dp:
            continue
        for nome in fs:
            if not nome.endswith(".html"):
                continue
            fp = os.path.join(dp, nome)
            h = ler(fp)
            if ALVO not in h:
                continue
            novo = RE_TAG.sub(lambda m: "<script defer%s%s>" % (m.group(1), m.group(2)), h)
            if novo != h:
                if not check:
                    gravar(fp, novo)
                tocadas += 1
            else:
                ja += 1

    print("%s%d pagina(s) com defer aplicado, %d ja tinham"
          % ("[--check] " if check else "", tocadas, ja))


if __name__ == "__main__":
    main()
