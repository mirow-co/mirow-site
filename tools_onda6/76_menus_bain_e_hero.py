# -*- coding: utf-8 -*-
"""76 — onda 21, S-78/S-79/S-80/S-81/S-83 (issues #136 #137 #138 #139 #141).

Uso:
    python tools_onda6/76_menus_bain_e_hero.py <raiz-que-contem-public>

S-83 + S-80 — "o azul que aparece ao passar o mouse sobre praticas precisa ...
  contrastar com o fundo e ser mais visivel" + "as praticas podem ser melhor
  distribuidas dentro da caixa azul, de forma a ocupar mais do seu width".
  Referencia dada pelo Mario: a barra da https://www.bain.com/ . O que ela faz e
  o que passa a valer aqui:
    - o painel e BRANCO (nao azul): contrasta com qualquer fundo, e ainda combina
      com a barra do topo, que ja fica branca no hover
    - o titulo da secao aparece grande, em cima
    - os itens vao numa GRADE de colunas que ocupa a largura util
    - um filete colorido fecha o painel embaixo (no Bain e vermelho; aqui, ciano)
  Praticas: 3 colunas iguais, palavra grande, separadas por linha vertical cinza
  (o "|" pedido na S-65 vira o divisor da coluna — assim ocupa o width inteiro).
  Sobre nos: 3 colunas, texto maior.

S-81 — "sobre nos altere a ordem para Nossos Valores, Nossos Lideres, Nossa
  Historia, Reconhecimentos, Nossa Rede". Reordena os <li> DENTRO do marcador
  onda7:menu-sobre, casando por URL (nao por texto) — funciona nos 3 idiomas.

S-79 — "nao faz sentido a barra de cima esticar o branco ate os cantos e a barra
  debaixo nao". A barra do rodape e um clone dentro do .container, entao o
  background branco do :hover parava na borda do container. Agora ela sangra
  100vw, como a de cima.

S-78 — "em 90% dos nossos clientes nos contratam novamente, deixe 'nos contratam
  novamente' em uma nova linha."

Idempotente: CSS em bloco marcado; a reordenacao e o <br> so entram se faltarem.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import (escrever_bloco_css, gravar, idioma_da_pagina, ler,  # noqa: E402
                        resolve_public)

REX_SOBRE = re.compile(
    r'(<!-- onda7:menu-sobre -->.*?<ul class="menu__nav-sublinks[^"]*">)(.*?)(</ul>)', re.S)
REX_LI = re.compile(r'<li class="menu__nav-sublinkitem[^"]*">.*?</li>', re.S)

# S-81 — ordem pedida, casada pelo SLUG da URL (vale para pt/en/de)
ORDEM = [
    ("nossos-valores", "our-values", "unsere-werte"),
    ("lideres", "leaders", "fuehrungskraefte"),
    ("nossa-historia", "our-history", "unsere-geschichte"),
    ("reconhecimentos", "recognitions", "anerkennungen"),
    ("nossa-rede", "our-network", "unser-netzwerk"),
]

# S-81 — rotulos como o Mario escreveu ("Nossos Valores, Nossos Lideres, Nossa
# Historia, Reconhecimentos, Nossa Rede"): "Lideres" -> "Nossos Lideres" e
# "Nossa historia" -> "Nossa Historia". Casado pelo href, para nao pegar outro link.
ROTULOS = [
    ("/sobre-nos/lideres/", u"Nossos Líderes"),
    ("/about-us/leaders/", u"Our Leaders"),
    ("/ueber-uns/fuehrungskraefte/", u"Unsere Führungskräfte"),
    ("/sobre-nos/nossa-historia/", u"Nossa História"),
]

# S-78 — onde quebrar a linha do big number de 90%, por idioma
QUEBRA = {
    "pt": (u"dos nossos clientes nos contratam novamente",
           u"dos nossos clientes<br>nos contratam novamente"),
    "en": (u"of our clients hire us again",
           u"of our clients<br>hire us again"),
    "de": (u"unserer Kunden beauftragen uns erneut",
           u"unserer Kunden<br>beauftragen uns erneut"),
}

CSS = """/* ---- S-83 + S-80: o painel do menu no modelo da barra da Bain -----------
   Painel BRANCO (contrasta com qualquer fundo e combina com a barra do topo, que
   ja fica branca no hover), titulo grande em cima, itens em GRADE ocupando a
   largura util, e um filete ciano fechando embaixo. */
/* ATENCAO: o branco vai no >div INTERNO. O tema pinta
   `.menu__nav-submenu>div{background:url(texture-7.png),#020e66}` — pintar so o
   pai deixava esse div navy por cima do branco, e o texto navy sumia. */
.menu__nav-submenu{background:transparent !important}
.menu__nav-submenu>div{background:#fff !important;padding:26px 0 30px !important;
  box-shadow:0 20px 44px rgba(2,14,102,.20);border-bottom:3px solid #00ADEC}
.menu__nav-submenu h5{color:#020E66 !important;font-size:21px;font-weight:700;
  margin:0 0 18px}
.menu__nav-sublink{color:#020E66 !important;font-weight:400}
.menu__nav-sublink:hover,.menu__nav-sublink:focus-visible{color:#00ADEC !important}

/* Largura do painel — duas camadas, as duas necessarias (medido via CDP):
   dentro do submenu, o .container do tema e flex, entao o .row e um FLEX ITEM e
   encolhia no conteudo; e o .col, dentro do .row, tambem. Sem os dois, a grade
   ficava agrupada a esquerda em vez de ocupar a largura util. */
.menu__nav-submenu .container>.row{flex:1 1 100%;width:100%}
.menu__nav-submenu .row>.col{flex:0 0 100%;width:100%;max-width:100%}
/* Sobre nos: os 5 itens espalhados no width, como o painel da Bain */
.menu__nav-sublinks:not(.onda18-praticas){display:grid;
  grid-template-columns:repeat(5,max-content);justify-content:space-between;
  gap:2px 24px}
.menu__nav-sublinks:not(.onda18-praticas) .menu__nav-sublink{font-size:19px !important}

/* Praticas: 3 colunas iguais ocupando o width, divididas por linha cinza
   (o "|" da S-65 vira o divisor da coluna — e o que faz ocupar a caixa toda) */
/* S-88: colunas do tamanho do conteudo e espalhadas — com 3 colunas iguais,
   "Sourcing, Compras e Estoques" nao cabia e quebrava em 2 linhas. */
.menu__nav-sublinks.onda18-praticas{display:grid !important;
  grid-template-columns:repeat(3,max-content);justify-content:space-between;
  gap:0;align-items:center}
.menu__nav-sublinks.onda18-praticas .menu__nav-sublink{white-space:nowrap}
.menu__nav-sublinks.onda18-praticas .menu__nav-sublinkitem{margin:0;padding:0 24px}
.menu__nav-sublinks.onda18-praticas .menu__nav-sublinkitem+.menu__nav-sublinkitem{
  border-left:1px solid rgba(127,127,127,.55)}
.menu__nav-sublinks.onda18-praticas .menu__nav-sublinkitem:first-child{padding-left:0}
.menu__nav-sublinks.onda18-praticas .menu__nav-sublinkitem+.menu__nav-sublinkitem::before{
  content:none}
.menu__nav-sublinks.onda18-praticas .menu__nav-sublink{font-size:26px !important;
  font-weight:700;line-height:1.2;display:block}
@media only screen and (max-width: 1440px){
  .menu__nav-sublinks.onda18-praticas .menu__nav-sublink{font-size:22px !important}
}
@media only screen and (max-width: 1200px){
  .menu__nav-sublinks.onda18-praticas .menu__nav-sublink{font-size:19px !important}
}

/* ---- S-90: o balao de idiomas no navy Mirow, nao mais preto -------------- */
.menu__languages-list{background:#020E66 !important;
  box-shadow:0 14px 30px rgba(2,14,102,.32)}
/* a setinha do balao acompanha (no header aponta para cima; no rodape, S-52,
   ela e invertida e vira border-top) */
.menu__languages-list::after{border-bottom-color:#020E66 !important}
.rodape-barra .menu__languages-list::after{border-top-color:#020E66 !important}
.menu__languages-list li a{color:#fff !important}
.menu__languages-list li:not(.menu__languages-list-current) a:hover{
  color:#00ADEC !important}
.menu__languages-list li.menu__languages-list-current a{color:#00ADEC !important}

/* ---- S-79: a barra do rodape sangra 100vw, como a de cima ---------------- */
.rodape-barra{width:100vw;margin-left:calc(50% - 50vw) !important;
  margin-right:calc(50% - 50vw) !important;padding-left:0;padding-right:0}
.rodape-barra .menu{padding-left:0;padding-right:0}

/* no mobile o menu do tema e lista empilhada — a grade volta a coluna */
@media only screen and (max-width: 991px){
  .menu__nav-sublinks:not(.onda18-praticas),
  .menu__nav-sublinks.onda18-praticas{display:block !important}
  .menu__nav-sublinks.onda18-praticas .menu__nav-sublinkitem{padding:0}
  .menu__nav-sublinks.onda18-praticas .menu__nav-sublinkitem+.menu__nav-sublinkitem{
    border-left:0}
  .menu__nav-sublinks.onda18-praticas .menu__nav-sublink{font-size:19px !important;
    white-space:normal}
}"""


def reordenar_sobre(html):
    """S-81 — ordena os itens do submenu Sobre nos pela ordem pedida."""
    def sub(m):
        itens = REX_LI.findall(m.group(2))
        if not itens:
            return m.group(0)

        def rank(li):
            for i, slugs in enumerate(ORDEM):
                if any(("/%s/" % s) in li for s in slugs):
                    return i
            return len(ORDEM)     # desconhecido vai para o fim, na ordem original
        novos = sorted(itens, key=rank)
        return m.group(1) + "".join(novos) + m.group(3)
    return REX_SOBRE.sub(sub, html)


def rotulos_sobre(html):
    """S-81 — acerta o texto de 2 itens do submenu, casando pelo href."""
    for href, novo in ROTULOS:
        html = re.sub(
            r'(<a class="menu__nav-sublink" href="[^"]*' + re.escape(href) + r'">)[^<]*(</a>)',
            lambda m: m.group(1) + novo + m.group(2), html)
    return html


def quebrar_90(html, lang):
    de, para = QUEBRA.get(lang, QUEBRA["pt"])
    if para in html:
        return html
    return html.replace(de, para)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    mudou = escrever_bloco_css(pub, "menus-bain", CSS, onda="onda21")
    print("bloco onda21:menus-bain %s" % ("gravado" if mudou else "ja estava igual"))

    tot = {"ordem": 0, "quebra": 0}
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if not n.endswith(".html"):
                continue
            p = os.path.join(dp, n)
            h = ler(p)
            if "<!-- onda7:menu-sobre -->" not in h:
                continue
            lang = idioma_da_pagina(h)
            orig = h

            antes = h
            h = reordenar_sobre(h)
            if h != antes:
                tot["ordem"] += 1
            antes = h
            h = rotulos_sobre(h)
            if h != antes:
                tot["rotulos"] = tot.get("rotulos", 0) + 1
            antes = h
            h = quebrar_90(h, lang)
            if h != antes:
                tot["quebra"] += 1

            if h != orig:
                gravar(p, h)
    print("resumo: ordem em %d pagina(s), rotulos em %d, quebra do 90%% em %d"
          % (tot["ordem"], tot.get("rotulos", 0), tot["quebra"]))


if __name__ == "__main__":
    main()
