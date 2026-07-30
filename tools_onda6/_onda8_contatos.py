# -*- coding: utf-8 -*-
"""Fonte unica dos contatos publicos usados na onda 8 (hero e barra superior).

Quem consome: 22_hero_contatos.py (pills no hero das 4 homes) e
26_header_contatos.py (icones no header de todas as paginas). Manter os dados
num lugar so evita que o numero do WhatsApp ou o e-mail divirjam entre os dois.

Nada aqui e segredo: sao os canais publicos da firma (R11 nao se aplica).
"""

WA_NUM = "5521999947429"          # WhatsApp direto do Andreas
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


def quote(texto):
    """percent-encode (RFC 3986) sem depender de locale nem de urllib."""
    seguro = u"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.~"
    out = []
    for ch in texto:
        if ch in seguro:
            out.append(ch)
        else:
            for b in ch.encode("utf-8"):
                out.append(u"%%%02X" % (b if isinstance(b, int) else ord(b)))
    return u"".join(out)


def url_whatsapp(idioma):
    return u"https://wa.me/%s?text=%s" % (WA_NUM, quote(MSG.get(idioma, MSG["pt"])))
