# -*- coding: utf-8 -*-
"""
22_hero_contatos.py — onda 8, pedido 2 do Mario.

Uso:  python tools_onda6/22_hero_contatos.py <raiz-que-contem-public>

Adiciona, no hero das 4 homes (logo abaixo do subtitulo), uma linha discreta com
4 links de contato: WhatsApp direto do Andreas (com mensagem pre-preenchida por
idioma), e-mail, LinkedIn e Instagram.

Estetica: pills outline branco sobre o navy do hero, hover ciano Mirow; o pill do
WhatsApp usa o verde reconhecivel no hover. Icones SVG inline minimos, com
fill="currentColor" e uma regra explicita no nosso bloco de CSS, porque o tema
tem varias regras "svg path{fill:...}" escopadas em outros contextos.

O tema nao e alterado: HTML entra entre marcadores <!-- onda8:hero-contatos -->
e o CSS vai para um bloco marcado em wp-content/uploads/2026/07/onda6/onda6.css.

Idempotente: remove o bloco antigo antes de inserir o novo.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import (base_prefix, escrever_bloco_css, garantir_link_css,  # noqa: E402
                        gravar, idioma_da_pagina, ler, resolve_public)

HOMES = ["pt/index.html", "en/index.html", "en/homepage/index.html", "de/index.html"]

WA_NUM = "5521999947429"
EMAIL = "andreas.mirow@mirow.com.br"
LINKEDIN = "https://www.linkedin.com/company/mirow-co-/"
INSTAGRAM = "https://www.instagram.com/mirowandco"

MSG = {
    "pt": u"Olá! Vim pelo site da Mirow & Co. e gostaria de conversar.",
    "en": u"Hello, I found Mirow & Co. through the website and would like to talk.",
    "de": u"Hallo! Ich bin über die Website von Mirow & Co. auf Sie aufmerksam "
          u"geworden und würde gerne sprechen.",
}

ROTULOS = {
    "pt": (u"Falar no WhatsApp", u"E-mail", u"LinkedIn", u"Instagram"),
    "en": (u"WhatsApp us", u"E-mail", u"LinkedIn", u"Instagram"),
    "de": (u"Per WhatsApp schreiben", u"E-Mail", u"LinkedIn", u"Instagram"),
}

ARIA = {
    "pt": u"Contatos diretos",
    "en": u"Direct contacts",
    "de": u"Direkter Kontakt",
}

INI = u"<!-- onda8:hero-contatos -->"
FIM = u"<!-- /onda8:hero-contatos -->"

SVG_WA = (u'<svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true" '
          u'focusable="false"><path fill="currentColor" d="M12.04 2C6.6 2 2.2 6.4 2.2 11.84c0 '
          u'1.74.46 3.44 1.32 4.94L2.1 22l5.36-1.4a9.8 9.8 0 0 0 4.58 1.15h.01c5.43 0 9.84-4.4 '
          u'9.84-9.84C21.89 6.4 17.47 2 12.04 2Zm0 17.9h-.01a8.2 8.2 0 0 1-4.16-1.14l-.3-.18-3.1.81'
          u'.83-3.02-.2-.31a8.14 8.14 0 0 1-1.25-4.35c0-4.5 3.68-8.17 8.2-8.17 2.19 0 4.24.85 '
          u'5.79 2.4a8.1 8.1 0 0 1 2.4 5.78c0 4.51-3.68 8.18-8.2 8.18Zm4.5-6.12c-.25-.12-1.46-.72'
          u'-1.68-.8-.23-.09-.39-.13-.55.12-.16.24-.63.79-.78.95-.14.17-.29.19-.53.06-.25-.12-1.04'
          u'-.38-1.98-1.22-.73-.65-1.23-1.46-1.37-1.7-.14-.25-.02-.38.11-.5.11-.11.25-.29.37-.44.12'
          u'-.15.16-.25.25-.42.08-.16.04-.31-.02-.43-.06-.12-.55-1.34-.76-1.83-.2-.48-.4-.41-.55-.42'
          u'l-.47-.01c-.16 0-.43.06-.65.3-.22.25-.85.84-.85 2.05s.87 2.37.99 2.53c.12.17 1.71 2.62 '
          u'4.15 3.67.58.25 1.03.4 1.39.51.58.19 1.11.16 1.53.1.47-.07 1.46-.6 1.66-1.18.21-.58.21'
          u'-1.07.15-1.18-.06-.11-.22-.17-.47-.29Z"/></svg>')

SVG_MAIL = (u'<svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true" '
            u'focusable="false"><path fill="currentColor" d="M3 5h18a1 1 0 0 1 1 1v12a1 1 0 0 1-1 '
            u'1H3a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Zm1.6 2L12 12.3 19.4 7H4.6ZM20 8.9l-7.4 5.3a1 1 0 '
            u'0 1-1.2 0L4 8.9V17h16V8.9Z"/></svg>')

SVG_LI = (u'<svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true" '
          u'focusable="false"><path fill="currentColor" d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 '
          u'0 1 0-5ZM3 9h4v12H3V9Zm6 0h3.8v1.7h.05c.53-.95 1.83-1.95 3.76-1.95 4.02 0 4.76 2.5 '
          u'4.76 5.75V21h-4v-5.6c0-1.34-.02-3.06-1.9-3.06-1.9 0-2.19 1.45-2.19 2.96V21H9V9Z"/></svg>')

SVG_IG = (u'<svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true" '
          u'focusable="false"><path fill="currentColor" d="M7.8 2h8.4A5.8 5.8 0 0 1 22 7.8v8.4a5.8 '
          u'5.8 0 0 1-5.8 5.8H7.8A5.8 5.8 0 0 1 2 16.2V7.8A5.8 5.8 0 0 1 7.8 2Zm0 2A3.8 3.8 0 0 0 '
          u'4 7.8v8.4A3.8 3.8 0 0 0 7.8 20h8.4a3.8 3.8 0 0 0 3.8-3.8V7.8A3.8 3.8 0 0 0 16.2 4H7.8'
          u'ZM12 7a5 5 0 1 1 0 10 5 5 0 0 1 0-10Zm0 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6Zm5.4-2.6a1.1 1.1 '
          u'0 1 1 0 2.2 1.1 1.1 0 0 1 0-2.2Z"/></svg>')

CSS = u"""/* onda8 — linha de contatos no hero das homes */
.hero-contatos{list-style:none;margin:22px 0 0;padding:0;display:flex;flex-wrap:wrap;
  gap:10px;position:relative;z-index:5}
.hero-contatos__link{display:inline-flex;align-items:center;gap:8px;
  padding:8px 16px;border:1px solid rgba(255,255,255,.55);border-radius:999px;
  color:#fff;font-family:var(--secondaryFontFamily);font-size:15px;font-weight:400;
  line-height:1.2;text-decoration:none;background:rgba(2,14,102,.28);
  transition:all 300ms ease-in-out}
.hero-contatos__link svg{flex:none}
.hero-contatos__link svg path{fill:currentColor;stroke:none}
.hero-contatos__link:hover,.hero-contatos__link:focus-visible{
  color:#020e66;background:#00adec;border-color:#00adec;text-decoration:none}
.hero-contatos__link:hover svg path,.hero-contatos__link:focus-visible svg path{
  fill:currentColor}
.hero-contatos__link--wa:hover,.hero-contatos__link--wa:focus-visible{
  color:#fff;background:#25d366;border-color:#25d366}
@media only screen and (max-width: 767px){
  .hero-contatos{gap:8px;margin-top:18px}
  .hero-contatos__link{padding:7px 13px;font-size:14px}
}
"""


def bloco(idioma):
    lab_wa, lab_mail, lab_li, lab_ig = ROTULOS[idioma]
    wa = u"https://wa.me/%s?text=%s" % (WA_NUM, _quote(MSG[idioma]))
    itens = [
        (u"hero-contatos__link hero-contatos__link--wa", wa, SVG_WA, lab_wa, True),
        (u"hero-contatos__link", u"mailto:%s" % EMAIL, SVG_MAIL, lab_mail, False),
        (u"hero-contatos__link", LINKEDIN, SVG_LI, lab_li, True),
        (u"hero-contatos__link", INSTAGRAM, SVG_IG, lab_ig, True),
    ]
    lis = []
    for cls, href, svg, rotulo, externo in itens:
        extra = u' target="_blank" rel="noopener noreferrer"' if externo else u""
        lis.append(u'<li><a class="%s" href="%s"%s>%s<span>%s</span></a></li>'
                   % (cls, href, extra, svg, rotulo))
    return (u'%s\n                <ul class="hero-contatos" aria-label="%s">%s</ul>\n%s'
            % (INI, ARIA[idioma], u"".join(lis), FIM))


def _quote(texto):
    """percent-encode do texto da mensagem do WhatsApp (RFC 3986, sem depender de locale)."""
    seguro = u"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.~"
    out = []
    for ch in texto:
        if ch in seguro:
            out.append(ch)
        else:
            for b in ch.encode("utf-8"):
                out.append(u"%%%02X" % (b if isinstance(b, int) else ord(b)))
    return u"".join(out)


def aplicar(html, idioma):
    # 1) tira versao anterior do bloco (idempotencia)
    html = re.sub(r"\n[ \t]*" + re.escape(INI) + r".*?" + re.escape(FIM), "", html, flags=re.S)
    # 2) insere logo depois do subtitulo do hero
    m = re.search(r'<section class="banner">.*?</section>', html, re.S)
    if not m:
        return html, False
    banner = m.group(0)
    mp = re.search(r"</p>", banner)
    if not mp:
        return html, False
    novo_banner = banner[:mp.end()] + u"\n                " + bloco(idioma) + banner[mp.end():]
    return html[:m.start()] + novo_banner + html[m.end():], True


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    if escrever_bloco_css(pub, "hero-contatos", CSS, onda="onda8"):
        print("css onda8:hero-contatos gravado")
    else:
        print("css onda8:hero-contatos ja atualizado")

    alterados = 0
    for rel in HOMES:
        path = os.path.join(pub, rel.replace("/", os.sep))
        if not os.path.exists(path):
            print("AVISO: nao existe %s" % rel)
            continue
        html = ler(path)
        idioma = idioma_da_pagina(html)
        novo, ok = aplicar(html, idioma)
        if not ok:
            print("AVISO: hero nao encontrado em %s" % rel)
            continue
        novo = garantir_link_css(novo, base_prefix(novo))
        if novo != html:
            gravar(path, novo)
            alterados += 1
            print("contatos no hero (%s): %s" % (idioma, rel))
        else:
            print("sem mudanca: %s" % rel)

    print("\nresumo: %d arquivo(s) HTML alterado(s)" % alterados)


if __name__ == "__main__":
    main()
