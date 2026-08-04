# -*- coding: utf-8 -*-
"""64 — onda 18, S-52/S-53/S-54/S-65/S-66 (issues #110 #111 #112 #123 #124):
as duas barras (header e rodape).

Uso:
    python tools_onda6/64_barras_onda18.py <raiz-que-contem-public>

  S-52  no rodape, o seletor de idiomas abre para CIMA (hoje abre para baixo e a
        bandeira da Alemanha, ultima da lista, cai fora da tela)
  S-53  menos espaco entre a linha divisoria e "Politica de privacidade"
  S-54  texto maior nas duas barras e icones de contato maiores
  S-65  hover em "Praticas" abre lista HORIZONTAL, palavras grandes, separadas
        por "|" cinza. Precisa de um gancho de classe: o script injeta
        class="onda18-praticas" no <ul> DENTRO do marcador onda7:menu-praticas
        (as 3 praticas do menu ja sao exatamente as 3 principais da firma)
  S-66  "Sobre nos" segue VERTICAL, com texto maior

Idempotente: CSS em bloco marcado; a classe do <ul> so entra se ainda nao existe.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, gravar, ler, resolve_public  # noqa: E402

REX_PRAT = re.compile(
    r'(<!-- onda7:menu-praticas -->\s*<ul class="menu__nav-sublinks)([^"]*)(")')

CSS = """/* ---- S-54: texto e icones maiores nas duas barras ---------------------- */
.menu__nav-link{font-size:17px !important}
.rodape-menu a{font-size:17px}
.menu__contatos svg{width:26px !important;height:26px !important}
.rodape-contatos .menu__contatos-link svg{width:26px !important;height:26px !important}
.menu__languages-button svg{width:27px;height:27px}
.menu__languages-list li a{font-size:16px}
.rodape-legal .footer__contacts-link{font-size:14px}
@media only screen and (min-width: 992px){
  /* com fonte e icones maiores a barra fica mais apertada — o gap cede antes
     de a barra quebrar em 992px */
  .menu__contatos{gap:14px}
}

/* ---- S-52: no rodape o seletor de idiomas abre para CIMA ---------------- */
.rodape-barra .menu__languages-list{top:auto !important;bottom:calc(100% - 2px)}
/* a setinha do balao vira para baixo (no header ela aponta para cima) */
.rodape-barra .menu__languages-list::after{top:auto;bottom:-5px;
  border-bottom:0;border-top:5px solid #000}

/* ---- S-53: menos espaco entre a linha e a politica de privacidade ------- */
.rodape-barra{margin-bottom:8px !important;padding-bottom:6px !important}
.rodape-legal{padding-top:0 !important}
.rodape-menu{margin-bottom:16px;padding-bottom:12px}

/* ---- S-66: "Sobre nos" segue vertical, com texto maior ----------------- */
.menu__nav-sublink{font-size:19px !important}
.menu__nav-submenu h5{font-size:15px}

/* ---- S-65: "Praticas" abre em linha, palavras grandes, "|" cinza -------- */
.menu__nav-sublinks.onda18-praticas{display:flex;flex-wrap:wrap;align-items:center;
  gap:0 18px;margin:6px 0 0}
.menu__nav-sublinks.onda18-praticas .menu__nav-sublinkitem{margin:0;display:flex;
  align-items:center}
.menu__nav-sublinks.onda18-praticas .menu__nav-sublinkitem+.menu__nav-sublinkitem::before{
  content:"|";color:#7F7F7F;font-size:30px;font-weight:300;line-height:1;
  margin-right:18px}
.menu__nav-sublinks.onda18-praticas .menu__nav-sublink{font-size:30px !important;
  font-weight:600;line-height:1.15;padding:2px 0 !important}
@media only screen and (max-width: 1366px){
  .menu__nav-sublinks.onda18-praticas .menu__nav-sublink{font-size:24px !important}
  .menu__nav-sublinks.onda18-praticas .menu__nav-sublinkitem+.menu__nav-sublinkitem::before{
    font-size:24px}
}
/* no mobile o menu do tema e uma lista empilhada — volta a coluna */
@media only screen and (max-width: 991px){
  .menu__nav-sublinks.onda18-praticas{display:block}
  .menu__nav-sublinks.onda18-praticas .menu__nav-sublinkitem+.menu__nav-sublinkitem::before{
    content:none}
  .menu__nav-sublinks.onda18-praticas .menu__nav-sublink{font-size:19px !important}
}"""


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    mudou = escrever_bloco_css(pub, "barras", CSS, onda="onda18")
    print("bloco onda18:barras %s" % ("gravado" if mudou else "ja estava igual"))

    alterados = 0
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if not n.endswith(".html"):
                continue
            p = os.path.join(dp, n)
            h = ler(p)
            if "<!-- onda7:menu-praticas -->" not in h:
                continue

            def add_classe(m):
                classes = m.group(2)
                if "onda18-praticas" in classes:
                    return m.group(0)
                return m.group(1) + classes + " onda18-praticas" + m.group(3)

            novo = REX_PRAT.sub(add_classe, h)
            if novo != h:
                gravar(p, novo)
                alterados += 1
    print("resumo: %d pagina(s) com class onda18-praticas no <ul> das praticas" % alterados)


if __name__ == "__main__":
    main()
