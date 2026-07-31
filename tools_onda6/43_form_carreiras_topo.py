# -*- coding: utf-8 -*-
"""
43_form_carreiras_topo.py — onda 11, issue S-13.

Uso:  python tools_onda6/43_form_carreiras_topo.py <raiz-que-contem-public>

Pedido (issue mirow-co/mirow-marketing#62): subir o formulario de inscricao de
carreiras para o TOPO da pagina — hoje fica escondido no fim (feedback dos
estagiarios). Depende da S-15 para o formulario de fato ENVIAR (troca de
backend) — isso e pendencia separada (issue #64); aqui so mexemos em POSICAO.

O que este script faz
----------------------
Move a <section class="job-contact"> (o form multi-pagina "work-with-us")
para ser a PRIMEIRA secao dentro de <div id="mainContent">, antes ate da
<section class="links"> (que a onda 11 / script 42 acabou de popular com o
CTA reciproco "Ja e cliente?"). Extracao/remocao respeita aninhamento de
<section> (mesma tecnica do 29_contato_enxuto.py), nunca regex guloso.

Aviso de CSS (NAO aplicado por este script — proposta em arquivo separado)
---------------------------------------------------------------------------
O tema estiliza `.job-contact{margin-top:-500px;padding:800px 0 100px}` — um
hack que pressupoe ~500-800px de conteudo ANTES da secao (no lugar antigo, ela
vinha depois do video de fundo da secao `career-path`). Movida para o topo,
sem essa pre-condicao, o layout quebra (a secao sobe por cima do hero).

Este script e proibido de editar
`public/wp-content/uploads/2026/07/onda6/onda6.css` (regra do processo desta
onda). Por isso ele so acrescenta a classe HTML `job-contact--topo` na secao
movida (marcador inerte, sem efeito visual sozinho) e deixa a REGRA CSS
correspondente como proposta em `tools_onda6/_css_pending_contato.css`, para
alguem com OK do Mario aplicar de vez em onda6.css. Ate isso acontecer, o
resultado visual desta secao no novo lugar fica quebrado (marcar S-13 como
"PRONTO (estrutura), aguardando aprovacao do CSS" — nao "NO AR").

Paginas atingidas: carreiras/, pt/carreiras/, en/careers/, de/karrieren/
(mesma lista do 42, por consistencia).

Idempotente: se a <section class="job-contact"> ja e a primeira depois de
<div id="mainContent">, nao faz nada.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, ler, resolve_public  # noqa: E402

PAGINAS = [
    "carreiras/index.html",
    "pt/carreiras/index.html",
    "en/careers/index.html",
    "de/karrieren/index.html",
]

MAIN = u'<div id="mainContent">'
ABERTURA = u'<section class="job-contact">'
ABERTURA_TOPO = u'<section class="job-contact job-contact--topo">'


def extrai_secao(html, abertura):
    """Devolve (antes, secao_completa, depois) respeitando aninhamento, ou None."""
    i = html.find(abertura)
    if i < 0:
        return None
    pos = i
    profundidade = 0
    while True:
        prox_abre = html.find("<section", pos + 1)
        prox_fecha = html.find("</section>", pos + 1)
        if prox_fecha < 0:
            raise SystemExit("HTML malformado: </section> nao encontrado")
        if 0 <= prox_abre < prox_fecha:
            profundidade += 1
            pos = prox_abre
            continue
        if profundidade == 0:
            fim = prox_fecha + len("</section>")
            break
        profundidade -= 1
        pos = prox_fecha
    return html[:i], html[i:fim], html[fim:]


def ja_no_topo(html):
    i = html.find(MAIN)
    if i < 0:
        return False
    resto = html[i + len(MAIN):].lstrip()
    return resto.startswith(ABERTURA) or resto.startswith(ABERTURA_TOPO)


def aplicar(html):
    if ja_no_topo(html):
        return html, False

    extraido = extrai_secao(html, ABERTURA)
    if extraido is None:
        # ja rodou antes e a secao ja tem a classe --topo mas nao esta no
        # comeco por algum motivo — tenta com o marcador tambem.
        extraido = extrai_secao(html, ABERTURA_TOPO)
        if extraido is None:
            return html, False
        antes, secao, depois = extraido
    else:
        antes, secao, depois = extraido
        secao = secao.replace(ABERTURA, ABERTURA_TOPO, 1)

    # tira a secao do lugar antigo
    html_sem = antes + depois

    # insere logo depois de <div id="mainContent">
    im = html_sem.find(MAIN)
    if im < 0:
        return html, False
    ponto = im + len(MAIN)
    novo = html_sem[:ponto] + u"\n" + secao + u"\n" + html_sem[ponto:]
    return novo, True


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    alterados = 0
    for rel in PAGINAS:
        path = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(path):
            print("AVISO: nao existe %s" % rel)
            continue
        html = ler(path)
        novo, ok = aplicar(html)
        if not ok:
            print("sem mudanca (ja no topo ou secao ausente): %s" % rel)
            continue
        gravar(path, novo)
        alterados += 1
        print("formulario de carreiras movido para o topo: %s" % rel)

    print("\nresumo: %d arquivo(s) HTML alterado(s)" % alterados)
    print(u"\nAVISO: o ajuste de CSS (margin/padding do .job-contact na nova "
         u"posicao) NAO foi aplicado — ver proposta em "
         u"tools_onda6/_css_pending_contato.css. Sem ela o bloco fica com "
         u"espacamento quebrado no topo da pagina.")


if __name__ == "__main__":
    main()
