# -*- coding: utf-8 -*-
"""51 — S-32 (issue #84): dropdown do menu ajustado ao conteudo + nav no rodape.

Uso:
    python tools_onda6/51_menu_executivo_e_rodape.py <raiz-que-contem-public>

DUAS ENTREGAS
-------------
(a) CSS (bloco onda14:menu-executivo): o tema abre o painel do menu com
    min-height:calc(100vh - 68px) + gradiente PRETO de tela inteira — e o
    "fundo preto" que o Mario reclamou. O painel passa a ter a altura do
    proprio conteudo, com tipografia/padding comprimidos (executivo).
    Vale para Praticas e Sobre nos (que "ocupava MUITO espaco").

(b) Rodape espelha a barra superior: em toda pagina com <footer class="footer">,
    entra uma linha de navegacao compacta (marcador onda14:rodape-menu) com os
    itens da barra do proprio idioma — Sobre nos, as 3 praticas (no lugar do
    guarda-chuva "Praticas", que nao tem pagina propria), Insights, Carreiras,
    Imprensa e Contato. Os links sao EXTRAIDOS do header da propria pagina
    (fonte unica: o menu ja existente), nunca hardcoded por idioma.

Idempotente: o bloco do rodape e regravado entre marcadores (igual = 0 mudancas).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, gravar, ler, resolve_public  # noqa: E402

MARK_INI = "<!-- onda14:rodape-menu -->"
MARK_FIM = "<!-- /onda14:rodape-menu -->"

REX_TOP = re.compile(
    r'<(a|button)[^>]*class="[^"]*menu__nav-link[^"]*"[^>]*>(.*?)</\1>', re.S)
REX_HREF = re.compile(r'href="([^"]*)"')
REX_PRAT = re.compile(
    r'<!-- onda7:menu-praticas -->(.*?)<!-- /onda7:menu-praticas -->', re.S)
REX_SUB = re.compile(r'<a class="menu__nav-sublink" href="([^"]*)">([^<]*)</a>')
REX_FOOTER = re.compile(r'(<footer class="footer">\s*<div class="container">)')

CSS = """/* (a) dropdown com a altura do conteudo — sai o painel preto de tela inteira
   (o tema usa min-height:calc(100vh - 68px) + gradiente preto). */
.menu__nav-submenu{min-height:0 !important;background:none !important;
  padding-top:0 !important}
.menu__nav-submenu>div{padding:22px 0 26px}
.menu__nav-sublink{font-size:17px !important;padding:6px 0 !important;
  font-weight:300}
.menu__nav-submenu h5{margin:12px 0}
/* (b) navegacao do rodape — espelho compacto da barra superior */
.rodape-menu{display:flex;flex-wrap:wrap;justify-content:center;gap:8px 26px;
  margin:0 0 26px;padding:0 0 20px;list-style:none;
  border-bottom:1px solid rgba(170,213,232,.25)}
.rodape-menu li{margin:0}
.rodape-menu a{color:#fff;font-size:14px;text-decoration:none;
  transition:color 200ms ease}
.rodape-menu a:hover{color:#00ADEC}"""


def links_da_pagina(html):
    """Extrai (label, href) do header da propria pagina, praticas expandidas."""
    itens = []
    praticas = []
    m = REX_PRAT.search(html)
    if m:
        praticas = REX_SUB.findall(m.group(1))
    for m in REX_TOP.finditer(html):
        tag = m.group(0)
        href = REX_HREF.search(tag)
        label = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if not label:
            continue
        if not href or href.group(1) in ("#", ""):
            # o guarda-chuva "Praticas" nao tem pagina — entram as 3 praticas
            itens.extend((lab, u) for u, lab in praticas)
        else:
            itens.append((label, href.group(1)))
        if len(itens) > 12:
            break
    # dedup preservando ordem
    vistos, unicos = set(), []
    for lab, u in itens:
        if u in vistos:
            continue
        vistos.add(u)
        unicos.append((lab, u))
    return unicos


def bloco_nav(itens):
    lis = "".join('<li><a href="%s">%s</a></li>' % (u, lab) for lab, u in itens)
    return ('%s<div class="row"><div class="col-12">'
            '<ul class="rodape-menu">%s</ul>'
            '</div></div>%s' % (MARK_INI, lis, MARK_FIM))


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    mudou_css = escrever_bloco_css(pub, "menu-executivo", CSS, onda="onda14")
    print("bloco onda14:menu-executivo %s" % ("gravado" if mudou_css else "ja estava igual"))

    alterados = 0
    sem_menu = 0
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if not n.endswith(".html"):
                continue
            p = os.path.join(dp, n)
            h = ler(p)
            if '<footer class="footer">' not in h:
                continue
            itens = links_da_pagina(h)
            if not itens:
                sem_menu += 1
                continue
            novo_bloco = bloco_nav(itens)
            if MARK_INI in h:
                velho = h[h.index(MARK_INI):h.index(MARK_FIM) + len(MARK_FIM)]
                novo = h.replace(velho, novo_bloco, 1)
            else:
                novo = REX_FOOTER.sub(lambda m: m.group(1) + "\n            " + novo_bloco,
                                      h, count=1)
            if novo != h:
                gravar(p, novo)
                alterados += 1
    print("resumo: %d pagina(s) com nav no rodape alterada(s), %d sem menu no header"
          % (alterados, sem_menu))


if __name__ == "__main__":
    main()
