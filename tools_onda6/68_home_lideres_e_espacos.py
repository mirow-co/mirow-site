# -*- coding: utf-8 -*-
"""68 — onda 18, S-50 e S-71 (issues #108 e #129): cards de lider e espacos da home.

Uso:
    python tools_onda6/68_home_lideres_e_espacos.py <raiz-que-contem-public>

S-50 — "ao clicar nessas fotos, chego na Bio do socio, nao no linkedin. aqui nao
  adianta ter o logo do linkedin."
  O card e um <button> que abre o modal da bio, e o icone "in" no canto e um SVG
  decorativo DENTRO do botao — clicar nele abre a bio. Como <a> nao pode morar
  dentro de <button>, o card ganha um wrapper posicionado
  (<div class="onda18-lider">) e o link do LinkedIn entra como IRMAO do botao,
  sobreposto exatamente ao icone. Foto/nome continuam abrindo a bio; o "in" vai
  para o perfil real.
  A URL de cada lider e LIDA do modal correspondente na propria pagina (fonte
  unica — nunca hardcoded aqui). Lider cujo modal nao tenha LinkedIn tem o icone
  decorativo escondido, para nao sobrar um logo que nao leva a nada.

S-71 — "vamos diminuir o espaco entre nossos lideres na pagina inicial e os
  reconhecimentos. o texto reconhecimentos so aparece se voce for la para baixo."
  O vao eram 200px: 100px de padding-bottom da grade de lideres + 100px de
  padding-top da secao de reconhecimentos. Caem para 40px + 48px (-112px), o que
  sobe o titulo "Reconhecimentos" na pagina.

Idempotente: o wrapper so entra se ainda nao existe; CSS em bloco marcado.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import escrever_bloco_css, gravar, ler, resolve_public  # noqa: E402

REX_CARD = re.compile(
    r'<button class="home-leaders__card"[^>]*data-bs-target="#(?P<modal>[^"]+)"[^>]*>'
    r'(?P<corpo>.*?)</button>', re.S)
REX_NOME = re.compile(r'<h4>(.*?)</h4>', re.S)

CSS = """/* ---- S-50: o icone "in" do card de lider vira link real do LinkedIn ----
   O card e um <button> (abre o modal da bio) — o <a> nao pode ficar dentro dele,
   entao mora num wrapper que herda a caixa do card e se sobrepoe ao icone. */
.onda18-lider{position:relative;display:flex;width:192px;max-width:45%}
.onda18-lider .home-leaders__card{width:100%;max-width:none;height:100%}
.onda18-lider__in{position:absolute;right:0;bottom:0;width:35px;height:35px;
  z-index:3;display:block;border-radius:3px;
  transition:background 200ms ease}
.onda18-lider__in:hover,.onda18-lider__in:focus-visible{
  background:rgba(0,173,236,.22);outline:none}
/* lider sem LinkedIn no modal: o logo decorativo sai (nao leva a lugar nenhum) */
.onda18-lider--sem-in .home-leaders__card>span>p>svg{display:none}

/* ---- S-71: menos vao entre "Nossos Lideres" e "Reconhecimentos" ----------
   Eram 100px (grade de lideres) + 100px (secao dos selos) = 200px. */
.home-leaders .container .row__content .col{padding-bottom:40px !important}
.certificates{padding-top:48px !important}
@media only screen and (max-width: 767px){
  .home-leaders .container .row__content .col{padding-bottom:28px !important}
  .certificates{padding-top:32px !important}
}"""


def linkedin_do_modal(html, modal_id):
    """URL do LinkedIn dentro do modal daquele lider (ou None)."""
    marca = 'id="%s"' % modal_id
    i = html.find(marca)
    if i < 0:
        return None
    # o modal seguinte delimita o trecho; senao vai ate o fim da secao
    j = html.find('class="modal fade"', i + len(marca))
    trecho = html[i:j if j > 0 else i + 20000]
    m = re.search(r'href="(https://[^"]*linkedin\.com/in/[^"]+)"', trecho)
    return m.group(1) if m else None


def envolver_cards(html):
    """Envolve cada card num wrapper com o link do LinkedIn ao lado."""
    feitos = {"link": 0, "sem_in": 0}

    def sub(m):
        card = m.group(0)
        modal = m.group("modal")
        nome_m = REX_NOME.search(m.group("corpo"))
        nome = re.sub(r"<[^>]+>", "", nome_m.group(1)).strip() if nome_m else ""
        url = linkedin_do_modal(html, modal)
        if url:
            feitos["link"] += 1
            link = ('<a class="onda18-lider__in" href="%s" target="_blank" '
                    'rel="noopener noreferrer" aria-label="LinkedIn de %s" '
                    'title="LinkedIn de %s"></a>' % (url, nome, nome))
            return '<div class="onda18-lider">%s%s</div>' % (card, link)
        feitos["sem_in"] += 1
        return '<div class="onda18-lider onda18-lider--sem-in">%s</div>' % card

    novo = REX_CARD.sub(sub, html)
    return novo, feitos


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    mudou = escrever_bloco_css(pub, "home-lideres", CSS, onda="onda18")
    print("bloco onda18:home-lideres %s" % ("gravado" if mudou else "ja estava igual"))

    alterados = 0
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if not n.endswith(".html"):
                continue
            p = os.path.join(dp, n)
            h = ler(p)
            if 'class="home-leaders__card"' not in h:
                continue
            rel = os.path.relpath(p, pub).replace(os.sep, "/")
            if 'class="onda18-lider' in h:
                print("  %s: wrapper ja aplicado" % rel)
                continue
            novo, feitos = envolver_cards(h)
            if novo != h:
                gravar(p, novo)
                alterados += 1
                print("  %s: %d card(s) com link do LinkedIn, %d sem (icone escondido)"
                      % (rel, feitos["link"], feitos["sem_in"]))
    print("resumo: %d home(s) alterada(s)" % alterados)


if __name__ == "__main__":
    main()
