# -*- coding: utf-8 -*-
"""Onda 42 / S-137 (issue mirow-marketing#191): a barra superior fica fixa no
topo durante o scroll.

Pedido do Mario (06/08): "fazer com que a barra superior esteja sempre lá em
cima da página mesmo scrolling down".

`position:sticky` (não fixed) de propósito: o sticky mantém a barra NO FLUXO —
a primeira dobra exata (V01–V05, medida em runtime pelo onda8-dobra.js) não
muda, nenhum conteúdo pula para debaixo da barra, e âncoras seguem funcionando.
O contêiner é o `.header` (filho direto do body em toda página de conteúdo).

z-index 90: acima do conteúdo (o "m" do hero usa 10, o botão de voltar ao topo
usa menos) e abaixo de nada que importe — os submenus moram DENTRO da barra e
herdam o contexto.

Uso: python tools_onda6/99_header_fixo.py <raiz>
"""
import sys

from _onda7_css import resolve_public, escrever_bloco_css

CSS = """
/* S-137 (#191): barra superior sempre visivel no scroll.
   FIXED, nao sticky: o tema ja desenha o header FORA do fluxo
   (.header{position:absolute;top:0} — ele sobrepoe o hero). Sticky o poria
   NO fluxo e empurraria a primeira dobra em 98px (foi o que a V01 pegou).
   Fixed mantem exatamente a geometria de carga e so muda o comportamento
   no scroll. O tema tambem esconde o header rolado (opacity:0 via JS de
   scroll) — os overrides abaixo mantem a barra visivel e clicavel. */
.header{position:fixed !important;top:0;left:0;right:0;z-index:90;
  opacity:1 !important;pointer-events:auto !important;
  transform:none !important;visibility:visible !important}
"""


def main(root):
    pub = resolve_public(root)
    mudou = escrever_bloco_css(pub, "header-fixo", CSS, onda="onda42")
    print("onda6.css %s" % ("atualizado" if mudou else "ja estava assim"))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
