# -*- coding: utf-8 -*-
"""95_barra_critica.py — CSS critico inline para a barra nao piscar branca.

Issue mirow-marketing#223. Idempotente: rodar 2x reporta 0 mudancas.

    python tools_onda6/95_barra_critica.py <raiz-que-contem-public> [--check]

O bug (relatado pelo Mario em 14/08, no celular dele)
-----------------------------------------------------
"no celular a barra superior fica branca e nao mostra o mirow, so o &".

Reproduzido bloqueando o CSS no navegador: sem o onda6.css, `.menu` fica
`rgba(0,0,0,0)` sobre fundo branco. O logo (marca-mirow-co.svg) tem 8 paths
`fill="white"` — as letras M-I-R-O-W-C-O — e 1 path `fill="#00ABFF"`, que e o "&".
Branco sobre branco desaparece; sobra o "&" ciano. Exatamente o sintoma.

Nao e regressao da onda 27: aquela pintou a barra de navy no onda6.css, e a
assercao V14 continua verde. O que ninguem tinha medido e o intervalo ANTES de o
CSS externo chegar. No desktop dura milissegundos; num celular em rede movel,
dura o bastante para ser visto — e por isso so o Mario, no celular, notou.

Por que inline, contra a regra zero do CLAUDE.md
------------------------------------------------
A regra manda todo CSS novo viver em bloco marcado dentro do onda6.css. Aqui isso
seria autoderrotado: o bug E a ausencia do onda6.css. A correcao precisa estar no
proprio HTML, antes de qualquer <link>. Sao DUAS declaracoes, o minimo para o
logo ser legivel; todo o resto do estilo da barra continua no onda6.css.

Cuidado de valor gemeo (P2.1): o #020E66 aqui e o mesmo da barra no onda6.css. Se
a cor da barra mudar la, muda aqui. A assercao V32 mede as duas situacoes — com e
sem o CSS externo — entao uma divergencia aparece como falha, nao em silencio.
"""
from __future__ import unicode_literals

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public, ler, gravar  # noqa: E402

MARCA = "onda55:barra-critica"

BLOCO = (
    '  <style id="%s">/* barra navy e logo no tamanho certo ANTES do CSS externo '
    'chegar: sem isto o logo branco fica invisivel no flash (mirow-marketing#223) */\n'
    '  .menu{background:#020E66}.menu__logo img{max-width:160px;height:auto}</style>'
) % MARCA

# Stub de redirect nao tem barra; mesmo criterio de Suite.eh_stub.
META_REFRESH = re.compile(r'<meta\s+http-equiv=["\']refresh["\']', re.I)


def eh_stub(rel, html):
    if rel == "index.html":
        return True
    return META_REFRESH.search(html) is not None and '<footer class="footer">' not in html


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    pub = resolve_public(args[0])

    injetados = ja_ok = stubs = 0
    problemas = []

    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if not nome.endswith(".html"):
                continue
            caminho = os.path.join(dirpath, nome)
            rel = os.path.relpath(caminho, pub).replace("\\", "/")
            html = ler(caminho)

            if MARCA in html:
                ja_ok += 1
                continue
            if rel == "404.html" or eh_stub(rel, html):
                stubs += 1
                continue

            # Depois do <meta charset>, como os outros injetores — e antes de
            # qualquer <link>, que e o que importa aqui.
            anc = (re.search(r"<meta[^>]+charset[^>]*>", html, re.I)
                   or re.search(r"<head[^>]*>", html, re.I))
            if not anc:
                problemas.append(rel)
                continue

            novo = html[:anc.end()] + "\n" + BLOCO + html[anc.end():]
            if not check:
                gravar(caminho, novo)
            injetados += 1

    print("injetado:          %d" % injetados)
    print("ja tinham o bloco: %d" % ja_ok)
    print("stub/404 (fora):   %d" % stubs)
    if problemas:
        print("sem <head> nem charset: %d -> %s" % (len(problemas), ", ".join(problemas[:5])))
    print("mudancas: %d%s" % (injetados, " (--check: nada escrito)" if check else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
