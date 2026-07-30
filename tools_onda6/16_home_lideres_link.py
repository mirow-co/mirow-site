# -*- coding: utf-8 -*-
"""
16_home_lideres_link.py — item 3 da lista do Mario (onda 7).

Uso:  python tools_onda6/16_home_lideres_link.py <raiz-que-contem-public>

A secao "Nossos Lideres" da home nao levava a lugar nenhum: os cards abrem modais
e nao havia caminho para a pagina de lideres. Aqui:
  - o subtitulo ("Nossos Lideres" / "Our Leaders" / "Unsere Fuehrungskraefte")
    vira link para a pagina de lideres do idioma da pagina;
  - abaixo dele entra um "ver todos" no padrao do tema (mesma seta usada nos
    cards de praticas da home, em branco por causa do fundo navy da secao).

Idempotente: marcadores <!-- onda7:lideres-link --> ... <!-- /onda7:lideres-link -->
e a classe onda7-titulo-link no subtitulo.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import (base_prefix, escrever_bloco_css, garantir_link_css,  # noqa: E402
                        gravar, ler, resolve_public)

MARK_INI = "<!-- onda7:lideres-link -->"
MARK_FIM = "<!-- /onda7:lideres-link -->"

SETA = (
    '<svg width="17" height="12" viewBox="0 0 17 12" fill="none" '
    'xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M9.79289 '
    '0.292893C10.1834 -0.0976309 10.8166 -0.0976312 11.2071 0.292893L16.2071 '
    '5.29289C16.3946 5.48043 16.5 5.73478 16.5 6C16.5 6.26521 16.3946 6.51957 '
    '16.2071 6.70711L11.2071 11.7071C10.8166 12.0976 10.1834 12.0976 9.7929 '
    '11.7071C9.40237 11.3166 9.40237 10.6834 9.7929 10.2929L13.0858 7L1.5 7C0.947715 '
    '7 0.5 6.55228 0.5 6C0.5 5.44771 0.947715 5 1.5 5L13.0858 5L9.79289 '
    '1.70711C9.40237 1.31658 9.40237 0.683418 9.79289 0.292893Z" fill="currentColor" /></svg>'
)

# idioma -> (href da pagina de lideres, rotulo do "ver todos")
DESTINO = {
    "pt": ("pt/sobre-nos/lideres/", u"Ver todos os líderes"),
    "en": ("en/about-us/leaders/", u"See all leaders"),
    "de": ("de/ueber-uns/fuehrungskraefte/", u"Alle Führungskräfte ansehen"),
}

HOMES = [
    ("pt/index.html", "pt"),
    ("en/index.html", "en"),
    ("en/homepage/index.html", "en"),
    ("de/index.html", "de"),
]

CSS = u"""/* onda7 — "Nossos Lideres" da home vira caminho para a pagina de lideres */
.home-leaders__subtitle .onda7-titulo-link{color:inherit;text-decoration:none;
  transition:color 300ms ease-in-out}
.home-leaders__subtitle .onda7-titulo-link:hover{color:#00ADEC}
.onda7-vertodos{display:inline-flex;align-items:center;gap:10px;
  color:var(--whiteColor,#fff);font-family:var(--fontFamily);font-size:16px;
  font-weight:700;text-decoration:none;margin-top:6px;
  transition:color 300ms ease-in-out}
.onda7-vertodos:hover{color:#00ADEC}
.onda7-vertodos svg{flex:none}
"""


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    if escrever_bloco_css(pub, "lideres-link", CSS):
        print("css onda7:lideres-link gravado")
    else:
        print("css onda7:lideres-link ja atualizado")

    alterados = 0
    for rel, idioma in HOMES:
        path = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(path):
            print("AVISO: nao existe %s" % rel)
            continue
        html = ler(path)
        orig = html
        prefix = base_prefix(html)
        href, rotulo = DESTINO[idioma]
        url = prefix + href

        html = garantir_link_css(html, prefix)

        # 1) subtitulo clicavel (idempotente: so envolve se ainda nao houver <a>)
        m = re.search(
            r'(<h2[^>]*class="home-leaders__subtitle"[^>]*>)(.*?)(</h2>)', html, re.S)
        if not m:
            print("AVISO: subtitulo de lideres nao encontrado em %s" % rel)
            continue
        if "onda7-titulo-link" not in m.group(2):
            html = (html[:m.start()] + m.group(1)
                    + '<a class="onda7-titulo-link" href="%s">%s</a>' % (url, m.group(2))
                    + m.group(3) + html[m.end():])

        # 2) link "ver todos" logo abaixo do subtitulo
        bloco = ('%s<a class="onda7-vertodos" href="%s" data-aos="fade-up">%s %s</a>%s'
                 % (MARK_INI, url, rotulo, SETA, MARK_FIM))
        if MARK_INI in html:
            html = re.sub(re.escape(MARK_INI) + r".*?" + re.escape(MARK_FIM),
                          lambda _m: bloco, html, flags=re.S)
        else:
            m2 = re.search(r'<h2[^>]*class="home-leaders__subtitle".*?</h2>', html, re.S)
            html = (html[:m2.end()] + "\n                " + bloco + "\n"
                    + html[m2.end():])

        if html != orig:
            gravar(path, html)
            alterados += 1
            print("link de lideres aplicado: %s (%s)" % (rel, idioma))
        else:
            print("sem mudanca: %s" % rel)

    print("\nresumo: %d arquivo(s) alterado(s)" % alterados)


if __name__ == "__main__":
    main()
