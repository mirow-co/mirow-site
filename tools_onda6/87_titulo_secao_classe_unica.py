# -*- coding: utf-8 -*-
"""87 — onda 30, S-110 (#168): os 4 titulos da home numa classe so.

Uso:
    python tools_onda6/87_titulo_secao_classe_unica.py <raiz-que-contem-public>

Pedido do Mario: "o titulo setores em que atuamos nao compartilha da mesma animacao
que nossas areas de expertise, nossos lideres e reconhecimentos. ele deveria, por
ser um titulo do mesmo tipo. nao da para voce manter todos em uma mesma classe que
compartilha tamanho, cor, estilo, animacao, etc.?"

CAUSA (medida): os quatro nunca foram a mesma coisa no HTML —

    | titulo                    | tag | data-aos |
    | Nossas areas de expertise | h3  | fade-up  |
    | Setores em que atuamos    | h2  | NENHUM   |  <- nasceu na onda 18, fora do tema
    | Nossos Lideres            | h2  | fade-up  |
    | Reconhecimentos           | h2  | fade-up  |

E a tipografia deles so era igual porque a S-85 escreveu uma regra CSS com os
QUATRO seletores lado a lado: quatro fontes de verdade que podem divergir de novo —
foi exatamente o que aconteceu com a fonte do site (S-98) e com a altura do painel
do submenu (S-109).

O que este script faz:
  1. Poe a classe compartilhada `onda30-titulo-secao` nos quatro titulos das 4 homes
     e garante `data-aos="fade-up"` nos quatro (o de setores nao tinha).
  2. Promove o titulo de expertise de `h3` para `h2` — sao titulos do mesmo nivel
     (nenhuma regra do tema depende da tag; foi conferido).
  3. Reescreve o bloco da onda 22 para NAO repetir tipografia/cor por seletor: a
     regra passa a ser uma so, da classe nova. O que era especifico de cada um
     (marca 2x2, veu da secao, linha do Reconhecimentos, titulos que saem) fica.

Idempotente: classe e atributo so entram se faltarem; CSS em bloco marcado.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, gravar, ler, resolve_public  # noqa: E402

CLASSE = "onda30-titulo-secao"

# classe historica de cada titulo (a do tema ou a da onda 18) -> nada mais muda
TITULOS = ["home-experience__subtitle", "onda18-orbe__titulo",
           "home-leaders__subtitle", "certificates__title"]

CSS_ONDA30 = u"""/* ---- S-110: UMA classe para os 4 titulos de secao da home ---------------
   Antes, tamanho/peso/cor viviam numa regra com os quatro seletores lado a lado
   (S-85) e a animacao dependia de cada HTML — o titulo de Setores, que nasceu na
   onda 18 fora do tema, ficou sem `data-aos` e nao animava. Agora ha UMA fonte de
   verdade: esta classe. Quem tem estilo proprio de secao (a marca 2x2, o veu, a
   linha do Reconhecimentos) segue no bloco da onda 22 — o que NAO se repete mais
   aqui e tipografia. */
.onda30-titulo-secao{
  font-family:var(--fontFamily),Arial,sans-serif !important;
  font-size:48px !important;font-weight:700 !important;line-height:1.1 !important;
  letter-spacing:normal !important;text-transform:none !important;
  text-align:left !important;margin:0 0 28px !important;
  color:#020E66 !important}
/* o link do titulo dos lideres (onda 7) herda tudo da classe */
.onda30-titulo-secao .onda7-titulo-link{color:inherit;font-size:inherit;
  font-family:inherit;font-weight:inherit}
@media only screen and (max-width: 991px){
  .onda30-titulo-secao{font-size:34px !important;margin-bottom:22px !important}
}
@media only screen and (max-width: 767px){
  .onda30-titulo-secao{font-size:28px !important}
}"""

# o bloco da onda 22 fica so com o que e especifico de cada secao
CSS_ONDA22 = u"""/* ---- S-85 + S-86: a marca de secao como framework da home ---------------
   Nasceu do glifo que o tema desenhava ao lado de "PRATICAS"
   (.home-experience__title::after + ::before). Na v2 (S-86) e uma GRADE 2x2 de
   quatro blocos: o bloco do quadrante da secao fica maior e opaco, os outros
   tres pequenos e esmaecidos — "voce esta aqui" no mapa da home.
       [1] [2]     1 expertise   2 setores
       [3] [4]     3 lideres     4 reconhecimentos
   Navy fixo (#020E66) e float:left, a pedido: nos blocos de fundo escuro o
   marcador fica discreto de proposito.
   ATENCAO (S-110, onda 30): a tipografia dos 4 titulos NAO mora mais aqui — ela
   e da classe .onda30-titulo-secao. Nao reintroduzir regra por seletor. */
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

/* S-91: o "darken" ao rolar sai de cena. Como o tema fazia:
   `.home-experience::after` e um VEU CLARO (#A2BAE4) por cima da secao, e
   `.home-experience--dark-mode::after{opacity:0}` tirava o veu ao rolar — dai o
   fundo escurecer e o titulo navy sumir (era a S-87). Mantendo o veu sempre
   opaco, o fundo fica claro e o navy da classe funciona nos quatro blocos. */
.home-experience--dark-mode::after{opacity:1 !important}
/* o titulo de Reconhecimentos tinha uma linha decorativa que estica ao lado */
.certificates h2::after{display:none !important}

/* ---- textos que saem: "Praticas" e o super titulo "Lideres" -------------- */
.home-experience__title,.home-leaders__title{display:none !important}
/* sem a marca d'agua de 335px, a grade dos lideres sobe */
.home-leaders .container .row__titles{padding-top:0}

@media only screen and (max-width: 991px){
  .onda22-marca{width:22px;height:22px;gap:3px;margin:8px 12px 0 0}
  .onda22-marca i{width:6px;height:6px}
  .onda22-marca--1 i:nth-child(1),.onda22-marca--2 i:nth-child(2),
  .onda22-marca--3 i:nth-child(3),.onda22-marca--4 i:nth-child(4){
    width:10px;height:10px}
}"""


def ajustar(html):
    """Poe a classe e o data-aos nos 4 titulos; promove o de expertise a h2."""
    mudou = False
    for classe in TITULOS:
        pat = re.compile(r'<(?P<tag>h[1-6])(?P<attrs>[^>]*class="[^"]*'
                         + re.escape(classe) + r'[^"]*"[^>]*)>')
        m = pat.search(html)
        if not m:
            continue
        tag, attrs = m.group("tag"), m.group("attrs")
        novo_attrs = attrs
        if CLASSE not in novo_attrs:
            novo_attrs = re.sub(r'class="([^"]*)"',
                                lambda mm: 'class="%s %s"' % (mm.group(1), CLASSE),
                                novo_attrs, count=1)
        if 'data-aos=' not in novo_attrs:
            novo_attrs = ' data-aos="fade-up"' + novo_attrs
        nova_tag = "h2"          # os quatro sao titulos do mesmo nivel
        aberto = "<%s%s>" % (nova_tag, novo_attrs)
        if aberto == m.group(0) and tag == nova_tag:
            continue
        # fecha a tag junto, se a tag mudou
        ini, fim = m.start(), m.end()
        resto = html[fim:]
        if tag != nova_tag:
            j = resto.find("</%s>" % tag)
            if j < 0:
                continue
            resto = resto[:j] + "</%s>" % nova_tag + resto[j + len("</%s>" % tag):]
        html = html[:ini] + aberto + resto
        mudou = True
    return html, mudou


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    m1 = escrever_bloco_css(pub, "titulo-secao", CSS_ONDA30, onda="onda30")
    print("bloco onda30:titulo-secao %s" % ("gravado" if m1 else "ja estava igual"))
    m2 = escrever_bloco_css(pub, "marca-secoes", CSS_ONDA22, onda="onda22")
    print("bloco onda22:marca-secoes (sem tipografia) %s"
          % ("reescrito" if m2 else "ja estava igual"))

    n = 0
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if nome != "index.html":
                continue
            p = os.path.join(dirpath, nome)
            h = ler(p)
            if "onda18-orbe__titulo" not in h:      # só as homes têm os 4
                continue
            novo, mudou = ajustar(h)
            if mudou:
                gravar(p, novo)
                n += 1
                print("  4 titulos unificados: %s"
                      % os.path.relpath(p, pub).replace(os.sep, "/"))
    print("S-110 homes ajustadas: %d" % n)


if __name__ == "__main__":
    main()
