# -*- coding: utf-8 -*-
"""
42_separacao_cliente_candidato_carreiras.py — onda 11, issue S-12 (parte carreiras).

Uso:  python tools_onda6/42_separacao_cliente_candidato_carreiras.py <raiz-que-contem-public>

Pedido (issue mirow-co/mirow-marketing#61): separar claramente o "Fale Conosco"
de CLIENTE do de CANDIDATO. Achado ao investigar: o formulario de candidatura
da pagina de carreiras (secao <section class="job-contact">) usa o MESMO titulo
visivel "Fale Conosco" / "Contact Us" / "Kontaktieren Sie uns" que o formulario
de CLIENTE da pagina de contato — e essa e a causa provavel da confusao
reportada pelos estagiarios (o <legend> interno do form ja diz "Trabalhe
Conosco" / "Work with us" / "Arbeiten Sie mit uns" para leitor de tela; so o
<h2> visivel estava desalinhado).

Duas mudancas, ambas so-texto/so-HTML, zero CSS novo:

  1. Corrige o <h2 class="job-contact__title"> visivel para bater com o
     <legend> (candidato), tirando a ambiguidade com a pagina de contato.
  2. Preenche a <section class="links"> (hoje vazia, primeira secao depois do
     hero) com um card reciproco "Ja e cliente? Fale com nosso time",
     apontando para a pagina de contato — mesma classe `links__list-link--type2`
     ja usada pela barra equivalente da pagina de contato, so com outro
     background (`background-link-1.png`, mesmo asset do tema, ja usado em
     outras paginas) para diferenciar visualmente do card irmao.

Paginas atingidas: carreiras/, pt/carreiras/, en/careers/, de/karrieren/
(carreiras/ e copia identica de pt/carreiras/, mantida em sincronia).

Idempotente: titulo so troca se ainda estiver no texto antigo; o card do
CTA reciproco e removido pelo marcador antes de ser reinserido.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import gravar, idioma_da_pagina, ler, resolve_public  # noqa: E402

PAGINAS = [
    "carreiras/index.html",
    "pt/carreiras/index.html",
    "en/careers/index.html",
    "de/karrieren/index.html",
]

TITULO_ANTIGO = {
    "pt": u"Fale<br> Conosco",
    "en": u"Contact<br> Us",
    "de": u"Kontaktieren<br>Sie uns",
}
TITULO_NOVO = {
    "pt": u"Trabalhe<br> Conosco",
    "en": u"Work<br> With Us",
    "de": u"Arbeiten Sie<br>mit uns",
}

CONTATO_HREF = {
    "pt": u"/mirow-site/contato/",
    "en": u"/mirow-site/en/contact-us/",
    "de": u"/mirow-site/de/kontakt/",
}
CTA_TITULO = {
    "pt": u"Já é cliente?",
    "en": u"Already a client?",
    "de": u"Bereits Kunde?",
}
CTA_SUB = {
    "pt": u"Fale com nosso time",
    "en": u"Talk to our team",
    "de": u"Sprechen Sie mit unserem Team",
}

SETA_SVG = (u'<svg width="16" height="12" viewBox="0 0 16 12" fill="none" '
            u'xmlns="http://www.w3.org/2000/svg">'
            u'<path d="M9.29289 0.292893C9.68342 -0.0976309 10.3166 -0.0976312 10.7071 '
            u'0.292893L15.7071 5.29289C15.8946 5.48043 16 5.73478 16 6C16 6.26521 15.8946 '
            u'6.51957 15.7071 6.70711L10.7071 11.7071C10.3166 12.0976 9.68342 12.0976 9.2929 '
            u'11.7071C8.90237 11.3166 8.90237 10.6834 9.2929 10.2929L12.5858 7L1 7C0.447715 7 0 '
            u'6.55228 0 6C5.96046e-08 5.44771 0.447715 5 1 5L12.5858 5L9.29289 1.70711C8.90237 '
            u'1.31658 8.90237 0.683418 9.29289 0.292893Z" fill="white"/></svg>')

INI_CTA = u"<!-- onda11:s12-cta-cliente -->"
FIM_CTA = u"<!-- /onda11:s12-cta-cliente -->"

RE_LINKS_VAZIA = re.compile(
    r'(<section class="links">\s*<div class="container">\s*<div class="row">\s*'
    r'<div class="col">)(\s*)(</div>\s*</div>\s*</div>\s*</section>)',
    re.S,
)


def cta_html(idioma):
    href = CONTATO_HREF[idioma]
    return (u'%s<div class="links__list"><a class="links__list-link '
           u'links__list-link--type2" href="%s" '
           u'style="background-image:url(/mirow-site/wp-content/uploads/2023/02/'
           u'background-link-1.png)"><h3>%s</h3><span>%s%s</span></a></div>%s'
           % (INI_CTA, href, CTA_TITULO[idioma], CTA_SUB[idioma], SETA_SVG, FIM_CTA))


def aplicar_titulo(html, idioma):
    antigo = u'<h2 class="job-contact__title">%s</h2>' % TITULO_ANTIGO[idioma]
    novo = u'<h2 class="job-contact__title">%s</h2>' % TITULO_NOVO[idioma]
    if antigo in html:
        return html.replace(antigo, novo, 1), True
    return html, False


def aplicar_cta(html, idioma):
    if INI_CTA in html:
        html2 = re.sub(re.escape(INI_CTA) + r".*?" + re.escape(FIM_CTA), "__PLACEHOLDER__",
                       html, count=1, flags=re.S)
        html2 = html2.replace("__PLACEHOLDER__", cta_html(idioma), 1)
        return html2, html2 != html
    m = RE_LINKS_VAZIA.search(html)
    if not m:
        return html, False
    novo = html[:m.start()] + m.group(1) + cta_html(idioma) + m.group(3) + html[m.end():]
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
        idioma = idioma_da_pagina(html)
        antes = html
        html, ok1 = aplicar_titulo(html, idioma)
        if not ok1 and (u'<h2 class="job-contact__title">%s</h2>' % TITULO_NOVO[idioma]) not in html:
            print("AVISO: titulo job-contact nao encontrado em %s" % rel)
        html, ok2 = aplicar_cta(html, idioma)
        if not ok2 and INI_CTA not in html:
            print("AVISO: secao links vazia nao encontrada em %s" % rel)
        if html != antes:
            gravar(path, html)
            alterados += 1
            print("titulo candidato + CTA cliente (%s): %s" % (idioma, rel))
        else:
            print("sem mudanca: %s" % rel)

    print("\nresumo: %d arquivo(s) HTML alterado(s)" % alterados)


if __name__ == "__main__":
    main()
