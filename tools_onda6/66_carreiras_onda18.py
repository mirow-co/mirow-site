# -*- coding: utf-8 -*-
"""66 — onda 18, S-55/S-63/S-64 (issues #113 #121 #122): pagina de carreiras.

Uso:
    python tools_onda6/66_carreiras_onda18.py <raiz-que-contem-public>

  S-55  "Trabalhe Conosco" (titulo do formulario) esta navy sobre navy — ilegivel.
        Passa a branco, junto das duas linhas tracejadas decorativas do col__title.
  S-63  sai o bloco "Ja e cliente?" (a <section class="links"> que carrega o
        marcador onda11:s12-cta-cliente) e o titulo seguinte perde o "para voce":
        "Temos uma proposta de valor unica para voce" -> "...unica"
  S-64  no fim da pagina entra um botao de inscricao que ancora no formulario do
        topo (a secao .job-contact--topo ganha id="inscricao")

Idempotente: remocao por marcador (se o bloco nao existe mais, 0 mudancas) e
botao entre marcadores.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import (escrever_bloco_css, gravar, idioma_da_pagina, ler,  # noqa: E402
                        resolve_public)

MARK_CTA = "onda11:s12-cta-cliente"
MARK_INI = "<!-- onda18:inscrever-fim -->"
MARK_FIM = "<!-- /onda18:inscrever-fim -->"

# S-63 — titulo sem "para voce"
TITULO_DE_PARA = [
    (u"Temos uma proposta de valor única para você", u"Temos uma proposta de valor única"),
    (u"We have a unique value proposition for you", u"We have a unique value proposition"),
    (u"Wir haben ein einzigartiges Wertangebot für Sie",
     u"Wir haben ein einzigartiges Wertangebot"),
]

# S-64 — rotulo do botao de inscricao no fim da pagina
BOTAO = {
    "pt": u"Quero me inscrever",
    "en": u"I want to apply",
    "de": u"Jetzt bewerben",
}

CSS = """/* S-55: o titulo do formulario de carreiras era navy sobre o gradiente navy
   do topo da secao — invisivel. Branco, junto das linhas tracejadas do tema. */
.job-contact--topo .job-contact__title{color:#fff !important}
.job-contact--topo .container .row .col__title::after{border-left-color:#fff !important}
.job-contact--topo .container .row .col__title::before{border-top-color:#fff !important}

/* S-64: botao de inscricao no fim da pagina, ancorando no formulario do topo */
.onda18-inscrever{padding:0 0 90px;text-align:center}
.onda18-inscrever__link{display:inline-block;background:#00ADEC;color:#020E66;
  font-weight:700;font-size:19px;letter-spacing:.02em;text-decoration:none;
  padding:18px 46px;transition:background 200ms ease,color 200ms ease}
.onda18-inscrever__link:hover,.onda18-inscrever__link:focus-visible{
  background:#020E66;color:#fff}
@media only screen and (max-width: 767px){
  .onda18-inscrever{padding:0 0 54px}
  .onda18-inscrever__link{font-size:17px;padding:16px 30px}
}"""


def remover_bloco_cliente(html):
    """S-63 — remove a <section class="links"> que contem o marcador do CTA."""
    if MARK_CTA not in html:
        return html
    pos = html.index(MARK_CTA)
    ini = html.rfind('<section class="links">', 0, pos)
    if ini < 0:
        return html
    fim = html.find("</section>", pos)
    if fim < 0:
        return html
    fim += len("</section>")
    return html[:ini] + "<!-- onda18:s63-cta-cliente-removido -->" + html[fim:]


def titulo_sem_para_voce(html):
    for de, para in TITULO_DE_PARA:
        if de in html:
            html = html.replace(de, para)
    return html


def botao_inscricao(html, lang):
    """S-64 — id no formulario do topo + botao ancorado no fim da pagina."""
    if 'class="job-contact job-contact--topo"' in html and 'id="inscricao"' not in html:
        html = html.replace('<section class="job-contact job-contact--topo">',
                            '<section class="job-contact job-contact--topo" id="inscricao">', 1)

    rotulo = BOTAO.get(lang, BOTAO["pt"])
    bloco = ('%s<section class="onda18-inscrever"><div class="container"><div class="row">'
             '<div class="col"><a class="onda18-inscrever__link" href="#inscricao">%s</a>'
             '</div></div></div></section>%s' % (MARK_INI, rotulo, MARK_FIM))

    if MARK_INI in html:
        velho = html[html.index(MARK_INI):html.index(MARK_FIM) + len(MARK_FIM)]
        return html.replace(velho, bloco, 1)
    # entra logo antes do fechamento do <main> da pagina de carreiras
    m = re.search(r'</main>', html)
    if not m:
        return html
    return html[:m.start()] + bloco + "\n    " + html[m.start():]


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    mudou = escrever_bloco_css(pub, "carreiras", CSS, onda="onda18")
    print("bloco onda18:carreiras %s" % ("gravado" if mudou else "ja estava igual"))

    tot = {"paginas": 0, "cta": 0, "titulo": 0, "botao": 0}
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if n != "index.html":
                continue
            p = os.path.join(dp, n)
            h = ler(p)
            if 'class="page-careers"' not in h:
                continue
            lang = idioma_da_pagina(h)
            orig = h

            antes = h
            h = remover_bloco_cliente(h)
            if h != antes:
                tot["cta"] += 1
            antes = h
            h = titulo_sem_para_voce(h)
            if h != antes:
                tot["titulo"] += 1
            antes = h
            h = botao_inscricao(h, lang)
            if h != antes:
                tot["botao"] += 1

            if h != orig:
                gravar(p, h)
                tot["paginas"] += 1
                print("  %s" % os.path.relpath(p, pub).replace(os.sep, "/"))

    print("resumo: %d pagina(s) de carreiras — cta removido %d, titulo %d, botao %d"
          % (tot["paginas"], tot["cta"], tot["titulo"], tot["botao"]))


if __name__ == "__main__":
    main()
