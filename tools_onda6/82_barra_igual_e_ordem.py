# -*- coding: utf-8 -*-
"""82 — onda 27, S-104 e S-105.

Uso:
    python tools_onda6/82_barra_igual_e_ordem.py <raiz-que-contem-public>

S-104 (#162) — "quero que a ordem seja sobre nos -> praticas -> insights ->
  imprensa -> carreiras -> contato."
  Hoje Carreiras vem antes de Imprensa. O script troca os dois blocos de item
  do menu — e faz isso no HTML INTEIRO, o que cobre de uma vez a barra do header
  e o clone dela no rodape (a assercao S36 exige que as duas sejam identicas byte
  a byte; mexer numa e esquecer a outra derrubaria a suite).
  EN e DE nao tem item de Imprensa (a pagina so existe em portugues — issue
  #164/S-106), entao nessas linguas nao ha nada a reordenar.

S-105 (#163) — "eu tenho a impressao que a barra superior e diferente dependendo
  de cada pagina que eu estiver ... garanta que a barra e a mesma para todas as
  paginas."
  CAUSA RAIZ (medida, nao suposta): o HTML da barra e IDENTICO nas 275 paginas —
  mesmos itens, mesmos 4 canais, mesmo seletor de idiomas, 98px de altura em toda
  pagina. O que muda e o FUNDO: o tema deixa a barra transparente
  (`.menu{background:rgba(0,0,0,0)}`), entao ela mostra o que a pagina puser
  atras — o hero navy na home, uma FOTO nas paginas internas, o gradiente claro
  nas 26 paginas sem banner. Somando `.menu:hover{background:#fff}` (que a deixa
  branca com texto navy), dava a impressao de tres barras diferentes.
  Correcao: **fundo navy solido em repouso, em toda pagina**. A aparencia deixa de
  depender do que ha atras. O branco no hover fica — e o que casa com o painel
  branco do menu (S-83) — mas agora e o mesmo comportamento em todas as paginas.
  Nao muda altura nem layout (a barra ja ocupava 98px estaticos), entao a dobra
  exata da home segue valendo.

Idempotente: a troca de ordem so ocorre se a ordem antiga estiver presente; CSS em
bloco marcado.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, gravar, ler, resolve_public  # noqa: E402

# Carreiras vem embrulhada nos marcadores da onda 7; Imprensa e um item simples.
RE_CARREIRAS = (r'(?:<!-- onda7:menu-carreiras -->)?'
                r'<div class="menu__nav-item"><a class="menu__nav-link[^"]*" '
                r'href="[^"]*/carreiras/"[^>]*>[^<]*</a></div>'
                r'(?:<!-- /onda7:menu-carreiras -->)?')
RE_IMPRENSA = (r'<div class="menu__nav-item"><a class="menu__nav-link[^"]*" '
               r'href="[^"]*/imprensa/"[^>]*>[^<]*</a></div>')
RE_PAR = re.compile(r'(?P<carreiras>%s)(?P<imprensa>%s)' % (RE_CARREIRAS, RE_IMPRENSA))

CSS = u"""/* ---- S-105: a MESMA barra em toda pagina --------------------------------
   O HTML da barra sempre foi identico nas 275 paginas (mesmos itens, 4 canais,
   seletor de idiomas, 98px). O que mudava era o FUNDO: o tema a deixa
   transparente (`.menu{background:rgba(0,0,0,0)}`), entao ela exibia o que
   estivesse atras — hero navy na home, FOTO nas internas, gradiente claro nas 26
   paginas sem banner. Agora o repouso e navy solido em todas.
   O hover branco (que casa com o painel branco do menu, S-83) continua: precisa
   de seletor mais especifico para vencer a regra de repouso. */
.header .menu{background:#020E66 !important;
  transition:background 300ms ease-in-out}
.header .menu:hover,
.header .menu.menu--mobile-opened{background:#fff !important}
/* o clone do rodape mora sobre o navy do footer: mesma cor, sem costura */
.rodape-barra .menu{background:#020E66 !important}
.rodape-barra .menu:hover{background:#fff !important}"""


def reordenar(html):
    """S-104: Imprensa passa a vir antes de Carreiras (header e clone do rodape)."""
    def sub(m):
        return m.group("imprensa") + m.group("carreiras")
    return RE_PAR.sub(sub, html)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    mudou = escrever_bloco_css(pub, "barra-igual", CSS, onda="onda27")
    print("bloco onda27:barra-igual %s" % ("gravado" if mudou else "ja estava igual"))

    n = 0
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if nome != "index.html":
                continue
            p = os.path.join(dirpath, nome)
            h = ler(p)
            if "/imprensa/" not in h:
                continue
            novo = reordenar(h)
            if novo != h:
                gravar(p, novo)
                n += 1
    print("S-104 paginas reordenadas: %d" % n)


if __name__ == "__main__":
    main()
