# -*- coding: utf-8 -*-
"""
25_hero_pills_v2.py — onda 8.1: pills de contato do hero maiores e legiveis.

Uso:  python tools_onda6/25_hero_pills_v2.py <raiz-que-contem-public>

Contexto: o Mario viu os contatos QUEBRADOS no ar (texto azul empilhado, icones
minusculos, clique sem efeito). A causa raiz nao foi o CSS — foi cache: o <link>
do onda6.css nao tinha query de versao e o navegador dele serviu a versao velha
do arquivo, sem o bloco onda8. Sem CSS, os <li> viram lista vertical, o <a> pega
o azul padrao do navegador e o `.banner__background` (absolute, z-index 1) fica
POR CIMA dos links, engolindo o clique. Isso se resolve no 27 (cache-busting).

Aqui vai o pedido explicito do Mario para quando o CSS chegar: pills maiores.

  - icone 24px (era 17)
  - texto 17px, branco travado com !important (o tema pinta <a> com --linkColor)
  - contorno mais visivel (branco 78% e 1.5px) e fundo navy mais opaco
  - z-index/position reforcados no proprio <a>, para o video do hero nunca mais
    ficar por cima da area clicavel

Este script controla o bloco onda8:hero-contatos-v2, que vem DEPOIS do bloco do
script 22 no onda6.css e por isso vence nas regras repetidas. O 22 continua dono
do HTML e do estilo base; este aqui e so o ajuste de tamanho/contraste.

Idempotente.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, resolve_public  # noqa: E402

CSS = u"""/* onda8.1 — pills do hero maiores, texto branco travado e clique garantido */
.hero-contatos{gap:12px;margin-top:26px;position:relative;z-index:6}
.hero-contatos__link{
  padding:11px 20px;
  font-size:17px;
  gap:10px;
  color:#fff !important;
  text-decoration:none !important;
  border:1.5px solid rgba(255,255,255,.78);
  background:rgba(2,14,102,.45);
  position:relative;
  z-index:6;
}
.hero-contatos__link svg{width:24px;height:24px}
.hero-contatos__link svg path{fill:currentColor !important;stroke:none}
.hero-contatos__link:hover,.hero-contatos__link:focus-visible{
  color:#020e66 !important;background:#00adec;border-color:#00adec}
.hero-contatos__link--wa:hover,.hero-contatos__link--wa:focus-visible{
  color:#fff !important;background:#25d366;border-color:#25d366}
@media only screen and (max-width: 767px){
  .hero-contatos{gap:9px;margin-top:20px}
  .hero-contatos__link{padding:9px 15px;font-size:15px}
  .hero-contatos__link svg{width:20px;height:20px}
}
"""


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    if escrever_bloco_css(pub, "hero-contatos-v2", CSS, onda="onda8"):
        print("css onda8:hero-contatos-v2 gravado")
    else:
        print("css onda8:hero-contatos-v2 ja atualizado")


if __name__ == "__main__":
    main()
