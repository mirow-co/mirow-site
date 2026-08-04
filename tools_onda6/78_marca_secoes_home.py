# -*- coding: utf-8 -*-
"""78 — onda 23, S-85: a marca de secao como framework da home, e titulos parelhos.

Uso:
    python tools_onda6/78_marca_secoes_home.py <raiz-que-contem-public>

Pedido do Mario: "gostei do icone do lado de PRATICAS, coloque algo assim do lado de
Setores em que atuamos e Nossos Lideres. retirar o super titulo Lideres. faca com que
esse icone e suas variacoes sejam como um framework/mapa da pagina inicial. delete a
palavra praticas, coloque o icone do lado de Nossas areas de expertise. padronize os
tamanhos de titulo nesses blocos que agora identificamos. precisa ser tudo 'paralelo'
em termos de tamanho de fonte, estilo, caps ou nao, etc."

DE ONDE VEM O ICONE
-------------------
Nao e asset novo: e o glifo que o tema ja desenhava em
`.home-experience__title::after` (quadrado 34x34) + `::before` (quadradinho 10x10),
que so existia ao lado da palavra "PRATICAS". Aqui ele e extraido para um componente
proprio e ganha VARIACOES.

O FRAMEWORK (a parte "mapa da pagina")
--------------------------------------
A variacao e a POSICAO da secao na home. Percorrendo a home de cima para baixo, a
marca aponta 1, 2, 3, 4 — o leitor tem um indice visual de onde esta. O DESENHO da
variacao mudou na v2 (ver "V2 DO MARCADOR" abaixo): era quadrado grande + N
quadradinhos, hoje e a grade 2x2 com o quadrante da secao maior.

  1 · Nossas areas de expertise   (era o bloco "PRATICAS")
  2 · Setores em que atuamos
  3 · Nossos Lideres
  4 · Reconhecimentos

TITULOS PARELHOS
----------------
Os 4 titulos passam a ter EXATAMENTE a mesma tipografia: 48px, peso 700, sentence
case (nenhum em caps), alinhados a esquerda, mesma margem. Antes eram: 20px em caps
com letter-spacing 0.64em ("PRATICAS"), 80px ("Nossos Lideres"), 64px ("Setores em
que atuamos") e 20px ("Reconhecimentos").
O que NAO fica igual e a COR — e nao pode: o gradiente da home vai de claro a escuro,
entao navy nos blocos claros e #e9f0ff nos escuros (regra de legibilidade da onda 20).

TEXTOS QUE SAEM
---------------
- a palavra "Praticas" (era um rotulo acima do titulo de verdade)
- o super titulo "Lideres" (a marca d'agua gigante de 335px atras do bloco)
Os dois elementos ficam vazios no HTML e escondidos no CSS.

V2 DO MARCADOR (S-86)
---------------------
Pedido do Mario: "esse marcador pode ser em azul escuro sempre, e ter como 4 blocos
em que um esta um pouco maior que os outros (o atual), e os outros pequenos em cada
quadrante, sempre do lado esquerdo dos titulos, menor e mais discreto."

Mudou de "quadrado grande + N quadradinhos empilhados" para uma GRADE 2x2 de quatro
blocos: o bloco do QUADRANTE da secao fica um pouco maior e opaco, os outros tres
ficam pequenos e esmaecidos. O mapa continua legivel — a posicao do bloco grande diz
onde voce esta:

    [1] [2]      1 Nossas areas de expertise    2 Setores em que atuamos
    [3] [4]      3 Nossos Lideres               4 Reconhecimentos

Tres consequencias do pedido:
  - COR FIXA navy #020E66 (saiu o currentColor da v1). Nos dois blocos de fundo
    escuro o marcador fica de proposito discreto — foi o que ele pediu ("mais
    discreto"); nao e falta de contraste por descuido.
  - VAI A ESQUERDA do titulo, nao acima: `float:left` resolve sem tocar no markup
    do tema (o titulo e bloco e flui ao lado do float).
  - MENOR: 26px no total, contra 34px + quadradinhos da v1.

Idempotente: a marca so entra se ainda nao existe; CSS em bloco marcado.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, gravar, ler, resolve_public  # noqa: E402

# (classe do titulo, numero da secao no mapa)
SECOES = [
    ("home-experience__subtitle", 1),
    ("home-leaders__subtitle", 3),
    ("certificates__title", 4),
]
# a secao 2 (Setores em que atuamos) e gerada pelo 71_home_planeta_setores.py,
# que emite a propria marca com a mesma classe onda22-marca--2

# elementos cujo TEXTO sai
VAZIOS = ["home-experience__title", "home-leaders__title"]

CSS = """/* ---- S-85 + S-86: a marca de secao como framework da home ---------------
   Nasceu do glifo que o tema desenhava ao lado de "PRATICAS"
   (.home-experience__title::after + ::before). Na v2 (S-86) e uma GRADE 2x2 de
   quatro blocos: o bloco do quadrante da secao fica maior e opaco, os outros
   tres pequenos e esmaecidos — "voce esta aqui" no mapa da home.
       [1] [2]     1 expertise   2 setores
       [3] [4]     3 lideres     4 reconhecimentos
   Navy fixo (#020E66) e float:left, a pedido: nos blocos de fundo escuro o
   marcador fica discreto de proposito. */
.onda22-marca{float:left;display:grid;
  grid-template-columns:repeat(2,1fr);grid-template-rows:repeat(2,1fr);
  gap:4px;width:26px;height:26px;margin:12px 14px 0 0}
.onda22-marca i{align-self:center;justify-self:center;
  width:7px;height:7px;background:#020E66;opacity:.42}
/* o quadrante da secao: um pouco maior e opaco — e o "voce esta aqui" */
.onda22-marca--1 i:nth-child(1),
.onda22-marca--2 i:nth-child(2),
.onda22-marca--3 i:nth-child(3),
.onda22-marca--4 i:nth-child(4){width:12px;height:12px;opacity:1}

/* ---- titulos parelhos: mesma fonte, peso, caixa, alinhamento e margem ----- */
.home-experience__subtitle,
.onda18-orbe__titulo,
.home-leaders__subtitle,
.certificates__title,
.certificates h2{
  font-size:48px !important;font-weight:700 !important;line-height:1.1 !important;
  letter-spacing:normal !important;text-transform:none !important;
  text-align:left !important;margin:0 0 28px !important;
  font-family:var(--fontFamily),Arial,sans-serif}
/* S-91: os 4 titulos em NAVY, e o "darken" ao rolar sai de cena.
   Como o tema fazia: `.home-experience::after` e um VEU CLARO (#A2BAE4) por cima
   da secao, e `.home-experience--dark-mode::after{opacity:0}` tirava o veu ao
   rolar — dai o fundo escurecer e o titulo navy sumir (era a S-87). Mantendo o
   veu sempre opaco, o fundo fica claro e navy funciona nos quatro blocos.
   As secoes de Setores e Lideres seguem o mesmo veu porque ficam dentro da mesma
   faixa clara do gradiente. */
.home-experience--dark-mode::after{opacity:1 !important}
.home-experience__subtitle,
.onda18-orbe__titulo,
.home-experience--dark-mode .home-experience__subtitle,
.home-leaders__subtitle,
.certificates__title,.certificates h2{color:#020E66 !important}
/* o titulo de Reconhecimentos tinha uma linha decorativa que estica ao lado */
.certificates h2::after{display:none !important}
/* o link do titulo dos lideres (onda 7) herda a cor e o tamanho novos */
.home-leaders__subtitle .onda7-titulo-link{color:inherit;font-size:inherit}

/* ---- textos que saem: "Praticas" e o super titulo "Lideres" -------------- */
.home-experience__title,.home-leaders__title{display:none !important}
/* sem a marca d'agua de 335px, a grade dos lideres sobe */
.home-leaders .container .row__titles{padding-top:0}

@media only screen and (max-width: 991px){
  .home-experience__subtitle,.onda18-orbe__titulo,.home-leaders__subtitle,
  .certificates__title,.certificates h2{font-size:34px !important;
    margin-bottom:22px !important}
  .onda22-marca{width:22px;height:22px;gap:3px;margin:8px 12px 0 0}
  .onda22-marca i{width:6px;height:6px}
  .onda22-marca--1 i:nth-child(1),.onda22-marca--2 i:nth-child(2),
  .onda22-marca--3 i:nth-child(3),.onda22-marca--4 i:nth-child(4){
    width:10px;height:10px}
}
@media only screen and (max-width: 767px){
  .home-experience__subtitle,.onda18-orbe__titulo,.home-leaders__subtitle,
  .certificates__title,.certificates h2{font-size:28px !important}
}"""


def marca(n):
    """Grade 2x2: um <i> por quadrante; o do quadrante n fica maior (CSS)."""
    return ('<span class="onda22-marca onda22-marca--%d" aria-hidden="true">'
            '<i></i><i></i><i></i><i></i></span>' % n)


def aplicar(html):
    """Insere a marca antes de cada titulo e esvazia os textos que saem."""
    mudou = False

    # upgrade da v1 (span vazio) para a v2 (grade 2x2 com 4 filhos)
    for n in range(1, 5):
        velho = ('<span class="onda22-marca onda22-marca--%d" aria-hidden="true">'
                 '</span>' % n)
        if velho in html:
            html = html.replace(velho, marca(n))
            mudou = True

    for classe, n in SECOES:
        # a marca entra imediatamente ANTES da tag do titulo
        rex = re.compile(r'(<h[1-6][^>]*class="%s"[^>]*>)' % re.escape(classe))
        m = rex.search(html)
        if not m:
            continue
        antes = html[max(0, m.start() - 220):m.start()]
        if "onda22-marca--%d" % n in antes:
            continue     # ja aplicada
        html = html[:m.start()] + marca(n) + html[m.start():]
        mudou = True

    for classe in VAZIOS:
        rex = re.compile(r'(<h[1-6][^>]*class="%s"[^>]*>)(.*?)(</h[1-6]>)'
                         % re.escape(classe), re.S)

        def limpa(mm):
            if not mm.group(2).strip():
                return mm.group(0)
            return mm.group(1) + mm.group(3)
        novo = rex.sub(limpa, html)
        if novo != html:
            html = novo
            mudou = True

    return html, mudou


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    gravou = escrever_bloco_css(pub, "marca-secoes", CSS, onda="onda22")
    print("bloco onda22:marca-secoes %s" % ("gravado" if gravou else "ja estava igual"))

    alterados = 0
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if not n.endswith(".html"):
                continue
            p = os.path.join(dp, n)
            h = ler(p)
            if 'class="home-experience"' not in h:
                continue
            novo, mudou = aplicar(h)
            if mudou and novo != h:
                gravar(p, novo)
                alterados += 1
                print("  %s" % os.path.relpath(p, pub).replace(os.sep, "/"))
    print("resumo: %d home(s) com a marca de secao" % alterados)


if __name__ == "__main__":
    main()
