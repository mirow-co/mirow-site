# -*- coding: utf-8 -*-
"""
26_header_contatos.py — onda 8.1: contatos como icones na barra superior.

Uso:  python tools_onda6/26_header_contatos.py <raiz-que-contem-public>

Pedido do Mario: os mesmos 4 contatos do hero (WhatsApp do Andreas, e-mail,
LinkedIn e Instagram) presentes no header de TODAS as paginas do site, nao so
nas homes — discretos, brancos, do tamanho do menu, logo antes do seletor de
idioma.

Detalhes que importam
---------------------
- Idioma por pagina: a mensagem pre-preenchida do WhatsApp segue o cookie
  pll_language que o Polylang deixou no rodape (mesmo criterio das outras ondas),
  entao a pagina alema manda a mensagem em alemao.
- O tema pinta `path` de svg dentro do seletor de idioma
  (.menu__languages-button svg path{fill:var(--primaryColor)}). Por isso o icone
  aqui usa fill=currentColor + uma regra propria com !important, do mesmo jeito
  que resolveu nas bandeiras da onda 7 e nos pills do hero.
- Nos posts do blog o tema deixa o header BRANCO
  (.single:not(.single-experience) .menu{background-color:#fff}) — la os icones
  viram navy, senao sumiriam.
- Abaixo de 992px o header vira hamburguer e a barra nao tem espaco horizontal:
  os icones ficam ocultos nesse ponto (o hero das homes continua com os pills, e
  o rodape ja tem os contatos). Corte consciente, reportado ao Mario.
- O <link> do onda6.css passa a existir em TODAS as paginas (antes so nas homes
  e nas paginas de lideres), porque o estilo destes icones mora nele.

Idempotente.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import (base_prefix, escrever_bloco_css, garantir_link_css,  # noqa: E402
                        gravar, idioma_da_pagina, ler, resolve_public)
from _onda8_contatos import (ARIA, EMAIL, INSTAGRAM, LINKEDIN, ROTULOS,  # noqa: E402
                             SVG_IG, SVG_LI, SVG_MAIL, SVG_WA, url_whatsapp)

INI = u"<!-- onda8:menu-contatos -->"
FIM = u"<!-- /onda8:menu-contatos -->"
ANCORA = u'<div class="menu__languages">'

CSS = u"""/* onda8.1 — contatos como icones na barra superior (todas as paginas) */
.menu__contatos{display:none}
@media only screen and (min-width: 992px){
  /* o header era um space-between de 3 itens (logo | nav | idioma); com o 4o
     item a distribuicao mudaria de lugar, entao o nav fica centrado por margem
     automatica e o par contatos+idioma encosta na direita */
  .menu .container>.menu__nav{margin-left:auto;margin-right:auto}
  .menu__contatos{
    display:flex;align-items:center;gap:16px;order:3;
    margin-left:auto;padding-right:14px}
  .menu__contatos-link{
    display:inline-flex;align-items:center;justify-content:center;
    color:#fff;line-height:0;opacity:.85;
    transition:all 300ms ease-in-out}
  .menu__contatos-link svg{width:19px;height:19px}
  .menu__contatos-link svg path{fill:currentColor !important;stroke:none}
  .menu__contatos-link:hover,.menu__contatos-link:focus-visible{
    color:#00adec;opacity:1}
  .menu__contatos-link--wa:hover,.menu__contatos-link--wa:focus-visible{
    color:#25d366}
  /* nos posts o header do tema e branco — icone navy para nao sumir */
  .single:not(.single-experience) .menu__contatos-link{color:#020e66;opacity:.75}
}
"""


def bloco(idioma):
    lab_wa, lab_mail, lab_li, lab_ig = ROTULOS.get(idioma, ROTULOS["pt"])
    itens = [
        (u"menu__contatos-link menu__contatos-link--wa", url_whatsapp(idioma),
         SVG_WA, lab_wa, True),
        (u"menu__contatos-link", u"mailto:%s" % EMAIL, SVG_MAIL, lab_mail, False),
        (u"menu__contatos-link", LINKEDIN, SVG_LI, lab_li, True),
        (u"menu__contatos-link", INSTAGRAM, SVG_IG, lab_ig, True),
    ]
    links = []
    for cls, href, svg, rotulo, externo in itens:
        extra = u' target="_blank" rel="noopener noreferrer"' if externo else u""
        links.append(u'<a class="%s" href="%s"%s title="%s" aria-label="%s">%s</a>'
                     % (cls, href, extra, rotulo, rotulo, svg))
    return (u'%s<div class="menu__contatos" aria-label="%s">%s</div>%s'
            % (INI, ARIA.get(idioma, ARIA["pt"]), u"".join(links), FIM))


def aplicar(html, idioma):
    html = re.sub(re.escape(INI) + r".*?" + re.escape(FIM), "", html, flags=re.S)
    if ANCORA not in html:
        return html, False
    return html.replace(ANCORA, bloco(idioma) + ANCORA, 1), True


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    if escrever_bloco_css(pub, "menu-contatos", CSS, onda="onda8"):
        print("css onda8:menu-contatos gravado")
    else:
        print("css onda8:menu-contatos ja atualizado")

    alterados = 0
    vistos = 0
    por_idioma = {}
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if nome != "index.html":
                continue
            path = os.path.join(dirpath, nome)
            html = ler(path)
            if ANCORA not in html:
                continue
            vistos += 1
            idioma = idioma_da_pagina(html)
            por_idioma[idioma] = por_idioma.get(idioma, 0) + 1
            novo, ok = aplicar(html, idioma)
            if not ok:
                continue
            novo = garantir_link_css(novo, base_prefix(novo))
            if novo != html:
                gravar(path, novo)
                alterados += 1

    print("paginas com barra superior: %d  (%s)"
          % (vistos, ", ".join("%s=%d" % kv for kv in sorted(por_idioma.items()))))
    print("\nresumo: %d arquivo(s) HTML alterado(s)" % alterados)


if __name__ == "__main__":
    main()
