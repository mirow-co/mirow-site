# -*- coding: utf-8 -*-
"""96_sem_addtoany.py — troca o widget AddToAny por links diretos.

Issue mirow-marketing#224. Idempotente: rodar 2x reporta 0 mudancas.

    python tools_onda6/96_sem_addtoany.py <raiz-que-contem-public> [--check]

Por que
-------
O AddToAny e um script de terceiro (static.addtoany.com, EUA) presente em 112
paginas so para desenhar tres botoes de compartilhar: e-mail, WhatsApp e LinkedIn.
Ele recebe o IP de todo visitante que abre um artigo, e os proprios <a> apontam
para redirects em addtoany.com — ou seja, quem clica passa por eles antes de
chegar ao destino.

Nada disso e necessario: os tres destinos tem URL publica e direta. Trocando,
o site perde um compartilhamento de IP com os EUA que ninguem pediu, perde uma
requisicao externa por pagina, e o botao continua fazendo exatamente a mesma
coisa. Levantado durante a revisao da politica de privacidade (#222), onde a
alternativa era ter de DECLARAR o AddToAny como operador.

O que muda no HTML
------------------
- `href` de cada <a> passa a apontar para o destino real (mailto:, wa.me,
  linkedin.com/sharing), com titulo e URL da propria pagina;
- o <a>, que era vazio (o script do fornecedor injetava o icone), recebe o SVG
  inline — os MESMOS tres icones ja usados nas pilulas de contato do hero, para
  nao introduzir um segundo jogo de icones no site;
- o <script> do addtoany sai.

Os icones vem do hero (onda 18/39): viewBox 24x24, `fill="currentColor"`, entao
herdam a cor que o CSS ja da ao botao — sem CSS novo.
"""
from __future__ import unicode_literals

import os
import re
import sys

try:
    from urllib.parse import quote
except ImportError:  # py2
    from urllib import quote  # noqa

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public, ler, gravar, escrever_bloco_css  # noqa: E402

# O fornecedor estilizava os botoes por conta propria. Sem ele, o <a> herdava o
# azul padrao do navegador/Bootstrap (rgb(13,110,253)) — fora da paleta Mirow.
# Medido apos a troca; por isso o bloco existe.
CSS = """.a2a_kit a{color:#020E66;display:inline-flex;align-items:center;
justify-content:center;width:32px;height:32px;transition:color .15s}
.a2a_kit a:hover,.a2a_kit a:focus{color:#00ADEC}"""

SITE = "https://mirow.com.br"

# Icones identicos aos das pilulas de contato do hero (onda 18/39).
ICONES = {
    "email": '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false">'
             '<path fill="currentColor" d="M2 5h20v14H2V5Zm2 2v.4l8 5 8-5V7H4Zm16 10v-7.2l-8 5-8-5V17h16Z"/></svg>',
    "whatsapp": '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false">'
                '<path fill="currentColor" d="M12 2a10 10 0 0 0-8.6 15L2 22l5.2-1.4A10 10 0 1 0 12 2Zm0 2a8 8 0 1 1-4.1 14.9l-.3-.2-3 .8.8-2.9-.2-.3A8 8 0 0 1 12 4Zm-3.4 4.3c-.2 0-.5.1-.7.4-.3.3-.9.9-.9 2.1s.9 2.4 1 2.6c.1.2 1.7 2.7 4.2 3.7 2 .8 2.4.6 2.9.6.4 0 1.4-.6 1.6-1.2.2-.6.2-1.1.1-1.2l-.6-.3-1.5-.7c-.2-.1-.4-.1-.5.1l-.7.9c-.1.2-.3.2-.5.1-.2-.1-1-.4-1.9-1.2-.7-.6-1.2-1.4-1.3-1.6-.1-.2 0-.3.1-.4l.4-.5.2-.4v-.4l-.7-1.6c-.2-.4-.4-.4-.5-.4h-.7Z"/></svg>',
    "linkedin": '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false">'
                '<path fill="currentColor" d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5ZM3 9h4v12H3V9Zm6 0h3.8v1.7h.1c.5-1 1.8-2 3.7-2 4 0 4.7 2.5 4.7 5.9V21h-4v-5.6c0-1.3 0-3-1.9-3s-2.2 1.4-2.2 2.9V21H9V9Z"/></svg>',
}

KIT = re.compile(
    r'<div class="a2a_kit[^"]*"([^>]*)>(.*?)</div>', re.S)
ANCORA = re.compile(
    r'<a class="a2a_button_(email|whatsapp|linkedin)"[^>]*?title="([^"]*)"[^>]*>\s*</a>', re.S)
ATTR_URL = re.compile(r'data-a2a-url="([^"]*)"')
ATTR_TITULO = re.compile(r'data-a2a-title="([^"]*)"')

# <script> do fornecedor, nas duas formas em que o espelho o traz.
SCRIPT = re.compile(
    r'[ \t]*<script[^>]*(?:static\.addtoany\.com|addtoany)[^>]*>\s*</script>\s*'
    r'|[ \t]*<script[^>]*>\s*(?:window\.)?a2a_config.*?</script>\s*', re.S | re.I)


def destino(rede, url, titulo):
    u, t = quote(url, safe=""), quote(titulo, safe="")
    if rede == "email":
        return "mailto:?subject=%s&amp;body=%s" % (t, u)
    if rede == "whatsapp":
        return "https://wa.me/?text=%s%%20%s" % (t, u)
    return "https://www.linkedin.com/sharing/share-offsite/?url=%s" % u


def converte_kit(m):
    attrs, corpo = m.group(1), m.group(2)
    mu, mt = ATTR_URL.search(attrs), ATTR_TITULO.search(attrs)
    caminho = mu.group(1) if mu else "/"
    titulo = (mt.group(1) if mt else "Mirow &amp; Co.").replace("&amp;", "&")
    url = SITE + caminho if caminho.startswith("/") else caminho

    def uma(a):
        rede, title = a.group(1), a.group(2)
        return ('<a class="a2a_button_%s" href="%s" title="%s" rel="noopener noreferrer"'
                ' target="_blank">%s</a>') % (rede, destino(rede, url, titulo), title,
                                              ICONES[rede])

    novo_corpo, n = ANCORA.subn(uma, corpo)
    if not n:
        return m.group(0)
    return '<div class="a2a_kit%s"%s>%s</div>' % (
        " onda56-share", attrs, novo_corpo)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    pub = resolve_public(args[0])

    kits = scripts = paginas = 0
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if not nome.endswith(".html"):
                continue
            caminho = os.path.join(dirpath, nome)
            html = ler(caminho)
            if "a2a_" not in html and "addtoany" not in html:
                continue

            novo, nk = KIT.subn(converte_kit, html)
            novo, ns = SCRIPT.subn("", novo)
            if novo != html:
                if not check:
                    gravar(caminho, novo)
                paginas += 1
                kits += nk
                scripts += ns

    if not check:
        escrever_bloco_css(pub, "share-direto", CSS, onda="onda56")

    print("paginas alteradas: %d" % paginas)
    print("kits convertidos:  %d" % kits)
    print("scripts removidos: %d" % scripts)
    print("mudancas: %d%s" % (paginas, " (--check: nada escrito)" if check else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
