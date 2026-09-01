# -*- coding: utf-8 -*-
"""Onda 78: as instituicoes de cada lider aparecem no card, com icone.

Pedido do Mario em 31/08/2026: "coloque icones do lado das instituicoes e
empresas onde cada um dos lideres trabalhou. coloque icones para as faculdades
tambem. faca tudo isso caber, poder aumentar o tamanho dos cards de cada um".

De onde vem o dado
------------------
Das MESMAS constantes que alimentam o JSON-LD -- `ALUMNI` e `EXPERIENCIA` do
`111_geo_jsonld_lideres.py`, lidas do LinkedIn de cada um em 25/08 e conferidas
pelo Mario. Nada de lista nova: se o card e a ficha da maquina discordassem, um
dos dois estaria mentindo, e ninguem saberia qual (P3).

O que muda visualmente
----------------------
Entra uma faixa de "chips" no fim do conteudo do card, um por instituicao, cada
um com um icone que diz de que TIPO ela e: birrete para faculdade, predio para
empresa. O card cresce sozinho -- o tema usa `min-height`, nao altura fixa, entao
nada precisa ser forcado (e a Regra n. Zero segue intacta: o CSS novo e nosso, em
bloco marcado, por cima).

Sobre os icones
---------------
Sao dois SVG inline, monocromaticos, na cor da marca. NAO sao os logotipos das
instituicoes: logotipo de terceiro e marca registrada, sao ~25 arquivos para
buscar, e o uso e decisao do dono da marca -- perguntado ao Mario na mesma
mensagem. Trocar estes dois icones por logos reais depois e mudar o gerador de
chip, nao a estrutura.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_css = __import__("_onda7_css")
ler, gravar, escrever_bloco_css = _css.ler, _css.gravar, _css.escrever_bloco_css
_m111 = __import__("111_geo_jsonld_lideres")
_m153 = __import__("153_logos_instituicoes")

LOGOS_URL = "/wp-content/uploads/2026/08/onda79/logos/"


def arquivos_de_logo(pub):
    """slug -> nome do arquivo que existe no disco (a extensao veio dos BYTES)."""
    pasta = os.path.join(pub, "wp-content", "uploads", "2026", "08", "onda79", "logos")
    mapa = {}
    if os.path.isdir(pasta):
        for f in os.listdir(pasta):
            mapa[os.path.splitext(f)[0]] = f
    return mapa

LISTAGENS = ["pt/sobre-nos/lideres/index.html",
             "en/about-us/leaders/index.html",
             "de/ueber-uns/fuehrungskraefte/index.html"]

# nome longo (como esta na constante) -> nome curto para caber no chip
CURTO = {
    u"Universidade Técnica de Berlim": u"TU Berlin",
    u"Stevens Institute of Technology": u"Stevens Tech",
    u"University of Chicago": u"Univ. of Chicago",
    u"Fundação Getulio Vargas — EPGE": u"FGV EPGE",
    u"Pontifícia Universidade Católica do Rio de Janeiro (PUC-Rio)": u"PUC-Rio",
    u"Instituto Militar de Engenharia (IME)": u"IME",
    u"Universitat de Barcelona": u"Univ. de Barcelona",
    u"Universidade Federal do Rio de Janeiro (UFRJ)": u"UFRJ",
    u"Universität Karlsruhe": u"Univ. Karlsruhe",
    u"Universität Mannheim": u"Univ. Mannheim",
    u"Carnegie Mellon University — Tepper School of Business": u"Carnegie Mellon (Tepper)",
    u"Universidade de Brasília (UnB)": u"UnB",
    u"McKinsey & Company": u"McKinsey",
    u"Aracruz Celulose S.A.": u"Aracruz Celulose",
    u"Booz Allen Hamilton": u"Booz Allen",
    u"Monitor Deloitte": u"Monitor Deloitte",
    u"University of Chicago Booth School of Business": u"Chicago Booth",
    u"Innovative Management Partner (IMP)": u"IMP",
    u"Universität Bremen": u"Univ. Bremen",
    u"Malik Management": u"Malik",
    u"Arthur D. Little": u"Arthur D. Little",
    u"RC Alvarenga Engenharia e Construções": u"RC Alvarenga",
    u"Cam": u"Cam",
    u"Ampla": u"Ampla",
    u"Chilectra (Enel Distribución Chile)": u"Enel Chile",
    u"Arcoplan Construtora": u"Arcoplan",
    u"Catavento Consultoria": u"Catavento",
    u"Consórcio Integrador Rio de Janeiro (CIRJ)": u"Consórcio Rio (CIRJ)",
    u"Schlumberger": u"Schlumberger",
}

# birrete (formacao) e predio (empresa). 14x14, currentColor, sem fill externo.
ICONE_UNI = (u'<svg class="onda78-inst__icone" width="14" height="14" viewBox="0 0 20 20" '
             u'aria-hidden="true" focusable="false"><path fill="currentColor" '
             u'd="M10 3 1 7l9 4 7-3.1V13h1.6V7L10 3Zm-5.4 7.6v3C4.6 15 7 16.4 10 16.4'
             u's5.4-1.4 5.4-2.8v-3L10 13l-5.4-2.4Z"/></svg>')
ICONE_EMP = (u'<svg class="onda78-inst__icone" width="14" height="14" viewBox="0 0 20 20" '
             u'aria-hidden="true" focusable="false"><path fill="currentColor" '
             u'd="M3 17V4.6c0-.6.5-1.1 1.1-1.1h6.3c.6 0 1.1.5 1.1 1.1V8h4.4c.6 0 1.1.5 '
             u'1.1 1.1V17H3Zm2-2h2v-2H5v2Zm0-4h2V9H5v2Zm0-4h2V5H5v2Zm4 8h2v-2H9v2Zm0-4h2V9H9'
             u'v2Zm0-4h2V5H9v2Zm4 8h2v-2h-2v2Zm0-4h2v-2h-2v2Z"/></svg>')

def marca(curto, icone_generico, logos):
    """<img> com o logo real, ou o icone de tipo quando nao ha arquivo."""
    arq = logos.get(_m153.slug(curto))
    if not arq:
        return icone_generico
    # SEM loading="lazy": medido em 01/09, com lazy so 9 dos 26 logos chegavam a
    # carregar (os cards sao altos e a maioria nunca entra na viewport), e os que
    # carregavam apareciam com pop-in. Sao arquivos de 2 a 12 KB depois da
    # normalizacao -- o custo de baixar todos e menor que o de nao aparecerem.
    return (u'<img class="onda78-inst__logo" src="%s%s" alt="" '
            u'decoding="async">' % (LOGOS_URL, arq))


RE_CARD = re.compile(r'(<button class="page-leaders__list-item".*?)(</span><span class='
                     r'"page-leaders__list-item-more">)', re.S)
RE_NOME = re.compile(r'page-leaders__list-title">([^<]*?)(?:<small|</h3)')
RE_JA = re.compile(r'<ul class="onda78-inst">.*?</ul>', re.S)

ROTULO = {"pt": u"Formação e trajetória", "en": u"Education and career",
          "de": u"Ausbildung und Werdegang"}


def idioma(rel):
    return rel.split("/", 1)[0]


def chips(nome, logos=None):
    """(html, quantos) -- faculdades primeiro, depois empresas, sem repetir.

    Cada chip usa o LOGO REAL da instituicao quando o arquivo existe no disco; o
    icone generico de tipo (birrete/predio) ficou como FALLBACK para as cinco que
    nao tem logo verificavel. O `alt` fica vazio de proposito: o nome da
    instituicao ja esta no <span> ao lado, e repeti-lo no alt faria o leitor de
    tela dizer tudo duas vezes.
    """
    logos = logos or {}
    itens, vistos = [], set()
    for inst in _m111.ALUMNI.get(nome, []):
        curto = CURTO.get(inst, inst)
        if curto in vistos:
            continue
        vistos.add(curto)
        itens.append((marca(curto, ICONE_UNI, logos), curto, "uni"))
    for _cargo, org, _i, _f in _m111.EXPERIENCIA.get(nome, []):
        curto = CURTO.get(org, org)
        if curto in vistos:
            continue
        vistos.add(curto)
        itens.append((marca(curto, ICONE_EMP, logos), curto, "emp"))
    if not itens:
        return u"", 0
    li = u"".join(u'<li class="onda78-inst__item onda78-inst__item--%s">%s<span>%s</span></li>'
                  % (tipo, icone, texto) for icone, texto, tipo in itens)
    return u'<ul class="onda78-inst">%s</ul>' % li, len(itens)


def css():
    return u"""/* Onda 78 — as instituicoes de cada lider no card, com icone de tipo.
   O card cresce sozinho: o tema usa min-height, nao altura fixa. Os chips
   quebram em varias linhas (flex-wrap) e o tamanho e fluido, entao em tela
   grande eles ocupam o espaco que existe em vez de ficarem miudos. */
.onda78-inst{list-style:none;display:flex;flex-wrap:wrap;gap:6px 8px;
  margin:14px 0 0;padding:0}
.onda78-inst__item{display:inline-flex;align-items:center;gap:5px;
  background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.18);
  border-radius:999px;padding:4px 10px;color:#fff;
  font-size:clamp(11px, .82vw, 13px);line-height:1.25;white-space:nowrap}
.onda78-inst__item--uni{background:rgba(0,173,236,.14);border-color:rgba(0,173,236,.35)}
.onda78-inst__icone{flex:0 0 auto;opacity:.9;font-family:inherit}
/* O <path> dentro do SVG herdava fonte do documento e caia em Times New Roman --
   a V11 ("uma fonte so renderizada") pegou no gate: 3 elementos, exatamente os 3
   <path> dos icones genericos. Nao muda um pixel do desenho (path nao tem texto),
   mas a assercao mede a FAMILIA COMPUTADA de todo elemento, e ela estava certa em
   reclamar: um <path> com Times declarado e uma fonte a mais carregavel na pagina. */
/* O tema tem um script que troca <img src="*.svg"> por <svg> INLINE (classes
   style-svg / replaced-svg). Tres desses arquivos declaram font-family dentro do
   proprio SVG, e o <path> resultante computava "Times New Roman" -- a V11 pegou
   no gate. O !important e necessario porque a declaracao vem de dentro do
   arquivo injetado, e nao de uma folha que a nossa possa simplesmente suceder.
   Nao muda um pixel: path nao desenha texto. */
.onda78-inst svg, .onda78-inst svg *{font-family:inherit !important}
/* Onda 79 — o logo REAL da instituicao. A placa clara existe porque o card e
   escuro e a maioria destes logos e escura; os que ja sao brancos (UFRJ na
   versao negativa, Malik) entram sem placa, senao branco-sobre-branco os apaga.
   A classificacao saiu de MEDICAO de luminancia, nao de olhometro. */
.onda78-inst__logo{flex:0 0 auto;height:16px;width:auto;max-width:88px;
  object-fit:contain;background:#fff;border-radius:3px;padding:2px 4px}
.onda78-inst__logo--claro{background:transparent;padding:0}
/* no celular a lista pode ficar longa: rola na horizontal em vez de empurrar
   o card para baixo indefinidamente */
@media only screen and (max-width: 575px){
  .onda78-inst{flex-wrap:nowrap;overflow-x:auto;-webkit-overflow-scrolling:touch;
    scrollbar-width:none}
  .onda78-inst::-webkit-scrollbar{display:none}
}
"""


def main(raiz):
    pub = os.path.join(os.path.abspath(raiz), "public")
    logos = arquivos_de_logo(pub)
    total = 0
    for rel in LISTAGENS:
        p = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(p):
            continue
        h = ler(p)
        h = RE_JA.sub("", h)          # idempotencia: tira o que a run anterior pos
        novo, n = [], 0

        def troca(m):
            bloco = m.group(1)
            mn = RE_NOME.search(bloco)
            if not mn:
                return m.group(0)
            nome = mn.group(1).strip()
            html, quantos = chips(nome, logos)
            if not html:
                return m.group(0)
            novo.append(quantos)
            return bloco + html + m.group(2)

        h2 = RE_CARD.sub(troca, h)
        if h2 != h:
            gravar(p, h2)
            total += sum(novo)
            print(u"  %s: %d card(s), %d chip(s)" % (rel, len(novo), sum(novo)))
    mudou_css = escrever_bloco_css(pub, "instituicoes", css(), onda="onda78")
    print(u"152: %d chip(s) no total; css %s"
          % (total, "escrito" if mudou_css else "sem mudanca"))
    return total


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
