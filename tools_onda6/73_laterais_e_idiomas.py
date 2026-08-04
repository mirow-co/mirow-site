# -*- coding: utf-8 -*-
"""73 — onda 19, S-74 e S-76 (issues #132 e #134).

Uso:
    python tools_onda6/73_laterais_e_idiomas.py <raiz-que-contem-public>

S-74 — "nao consigo ver as linguas."
  Na onda 18 a lista de idiomas do rodape passou a abrir para cima (S-52), mas
  continuava cortada: nao e overflow: o rodape nao tinha contexto de empilhamento
  proprio, e a secao anterior (os cartoes de CTA) pintava por cima da lista.
  Correcao: o <footer> ganha position:relative + z-index, e o par
  .menu__languages / .menu__languages-list sobe acima disso.

S-76 — "adicione ao botao de subir a pagina tambem os botoes de comunicar com
  whatsapp e email na lateral."
  O botao solto da S-51 vira uma COLUNA fixa na direita com 3 acoes:
  WhatsApp · e-mail · voltar ao topo. WhatsApp e e-mail ficam sempre visiveis
  (sao canal de conversa — a metrica-mae do projeto); o de subir continua
  aparecendo so depois de 400px de rolagem.
  Os hrefs sao LIDOS do proprio header da pagina (fonte unica: o mesmo link e
  o mesmo texto-padrao de e-mail da S-72), nunca hardcoded aqui.

Idempotente: bloco entre marcadores (substitui o da S-51) e CSS em bloco marcado.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import (escrever_bloco_css, gravar, idioma_da_pagina, ler,  # noqa: E402
                        resolve_public)

MARK_INI = "<!-- onda18:voltar-topo -->"          # mesmo marcador da S-51
MARK_FIM = "<!-- /onda18:voltar-topo -->"

ROTULOS = {
    "pt": (u"Falar no WhatsApp", u"Enviar e-mail", u"Voltar ao início da página"),
    "en": (u"Chat on WhatsApp", u"Send e-mail", u"Back to top of page"),
    "de": (u"Per WhatsApp schreiben", u"E-Mail senden", u"Zurück zum Seitenanfang"),
}

SVG_WA = ('<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor"'
          ' d="M12.04 2C6.6 2 2.2 6.4 2.2 11.84c0 1.74.46 3.44 1.32 4.94L2.1 22l5.36-1.4a9.8 9.8'
          ' 0 0 0 4.58 1.15h.01c5.43 0 9.84-4.4 9.84-9.84C21.89 6.4 17.47 2 12.04 2Zm0 17.9h-.01a'
          '8.2 8.2 0 0 1-4.16-1.14l-.3-.18-3.1.81.83-3.02-.2-.31a8.14 8.14 0 0 1-1.25-4.35c0-4.5'
          ' 3.68-8.17 8.2-8.17 2.19 0 4.24.85 5.79 2.4a8.1 8.1 0 0 1 2.4 5.78c0 4.51-3.68 8.18-8.2'
          ' 8.18Zm4.5-6.12c-.25-.12-1.46-.72-1.68-.8-.23-.09-.39-.13-.55.12-.16.24-.63.79-.78.95-.14'
          '.17-.29.19-.53.06-.25-.12-1.04-.38-1.98-1.22-.73-.65-1.23-1.46-1.37-1.7-.14-.25-.02-.38.11'
          '-.5.11-.11.25-.29.37-.44.12-.15.16-.25.25-.42.08-.16.04-.31-.02-.43-.06-.12-.55-1.34-.76'
          '-1.83-.2-.48-.4-.41-.55-.42l-.47-.01c-.16 0-.43.06-.65.3-.22.25-.85.84-.85 2.05s.87 2.37'
          '.99 2.53c.12.17 1.71 2.62 4.15 3.67.58.25 1.03.4 1.39.51.58.19 1.11.16 1.53.1.47-.07 1.46'
          '-.6 1.66-1.18.21-.58.21-1.07.15-1.18-.06-.11-.22-.17-.47-.29Z"/></svg>')
SVG_MAIL = ('<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor"'
            ' d="M3 5h18a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Zm1.6 2L12'
            ' 12.3 19.4 7H4.6ZM20 8.9l-7.4 5.3a1 1 0 0 1-1.2 0L4 8.9V17h16V8.9Z"/></svg>')
SVG_TOPO = ('<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
            '<path fill="currentColor" d="M12 4.6l8.2 8.2-2.1 2.1L13.5 10.3V19.4h-3V10.3l-4.6 4.6'
            '-2.1-2.1z"/></svg>')

CSS = """/* ---- S-74: as 3 linguas do rodape aparecem inteiras ---------------------
   Nao era overflow: o rodape nao tinha contexto de empilhamento proprio e a
   secao anterior pintava por cima da lista que a S-52 fez abrir para cima. */
.footer{position:relative;z-index:20}
.rodape-barra .menu__languages{z-index:30}
.rodape-barra .menu__languages-list{z-index:40}

/* ---- S-76: coluna fixa de acoes na lateral direita ---------------------- */
.onda19-lateral{position:fixed;right:22px;bottom:34px;z-index:900;
  display:flex;flex-direction:column;gap:12px;align-items:center}
.onda19-lateral__link{width:52px;height:52px;display:flex;align-items:center;
  justify-content:center;border-radius:50%;text-decoration:none;
  background:#020E66;border:2px solid #00ADEC;color:#fff;
  box-shadow:0 4px 14px rgba(2,14,102,.28);
  transition:background 200ms ease,color 200ms ease,border-color 200ms ease}
.onda19-lateral__link svg{width:22px;height:22px;display:block}
.onda19-lateral__link:hover,.onda19-lateral__link:focus-visible{
  background:#00ADEC;color:#020E66}
.onda19-lateral__link--wa:hover,.onda19-lateral__link--wa:focus-visible{
  background:#25D366;border-color:#25D366;color:#fff}
/* o de subir so aparece depois de rolar (herda o comportamento da S-51) */
.onda19-lateral__link--topo{opacity:0;visibility:hidden;transform:translateY(10px);
  transition:opacity 220ms ease,transform 220ms ease,visibility 220ms ease,
    background 200ms ease,color 200ms ease}
.onda19-lateral__link--topo.is-visivel{opacity:1;visibility:visible;transform:none}
@media only screen and (max-width: 767px){
  .onda19-lateral{right:12px;bottom:16px;gap:9px}
  .onda19-lateral__link{width:44px;height:44px}
  .onda19-lateral__link svg{width:19px;height:19px}
}
@media print{.onda19-lateral{display:none}}"""

JS = ("<script>(function(){var b=document.querySelector('.onda19-lateral__link--topo');"
      "if(!b)return;function t(){if(window.pageYOffset>400){b.classList.add('is-visivel');}"
      "else{b.classList.remove('is-visivel');}}"
      "window.addEventListener('scroll',t,{passive:true});t();})();</script>")


def hrefs_da_pagina(html):
    """Le os links de WhatsApp e e-mail do header da propria pagina (fonte unica)."""
    wa = re.search(r'class="menu__contatos-link menu__contatos-link--wa" href="([^"]+)"', html)
    mail = re.search(r'class="menu__contatos-link menu__contatos-link--mail" href="([^"]+)"', html)
    return (wa.group(1) if wa else None), (mail.group(1) if mail else None)


def bloco(lang, url_wa, url_mail):
    r_wa, r_mail, r_topo = ROTULOS.get(lang, ROTULOS["pt"])
    itens = []
    if url_wa:
        itens.append('<a class="onda19-lateral__link onda19-lateral__link--wa" href="%s" '
                     'target="_blank" rel="noopener noreferrer" aria-label="%s" title="%s">%s</a>'
                     % (url_wa, r_wa, r_wa, SVG_WA))
    if url_mail:
        itens.append('<a class="onda19-lateral__link onda19-lateral__link--mail" href="%s" '
                     'aria-label="%s" title="%s">%s</a>' % (url_mail, r_mail, r_mail, SVG_MAIL))
    itens.append('<a class="onda19-lateral__link onda19-lateral__link--topo" href="#topo" '
                 'aria-label="%s" title="%s">%s</a>' % (r_topo, r_topo, SVG_TOPO))
    return ('%s<div class="onda19-lateral" aria-label="Atalhos de contato">%s</div>%s%s'
            % (MARK_INI, "".join(itens), JS, MARK_FIM))


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    mudou = escrever_bloco_css(pub, "lateral-e-idiomas", CSS, onda="onda19")
    print("bloco onda19:lateral-e-idiomas %s" % ("gravado" if mudou else "ja estava igual"))

    alterados = 0
    sem_canal = 0
    for dp, _d, fs in os.walk(pub):
        for n in fs:
            if not n.endswith(".html"):
                continue
            p = os.path.join(dp, n)
            h = ler(p)
            if '<footer class="footer">' not in h:
                continue
            url_wa, url_mail = hrefs_da_pagina(h)
            if not url_wa and not url_mail:
                sem_canal += 1
            novo_bloco = bloco(idioma_da_pagina(h), url_wa, url_mail)

            if MARK_INI in h:
                velho = h[h.index(MARK_INI):h.index(MARK_FIM) + len(MARK_FIM)]
                novo = h.replace(velho, novo_bloco, 1)
            elif "</body>" in h:
                novo = h.replace("</body>", novo_bloco + "\n</body>", 1)
            else:
                continue
            if 'id="topo"' not in novo:
                novo = re.sub(r'(<body\b)', r'\1 id="topo"', novo, count=1)
            if novo != h:
                gravar(p, novo)
                alterados += 1
    print("resumo: %d pagina(s) com a coluna lateral, %d sem canal no header"
          % (alterados, sem_canal))


if __name__ == "__main__":
    main()
