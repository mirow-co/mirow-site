# -*- coding: utf-8 -*-
"""31 — S-04 (issue #72): contraste dos icones de contato do header nos 2 estados.

Uso:
    python tools_onda6/31_header_contraste.py <raiz-que-contem-public>

O PROBLEMA
----------
Os 4 icones de contato do header (WhatsApp, e-mail, LinkedIn, Instagram) sao
brancos. A barra do header tem DOIS estados de fundo no tema:

  1. transparente  -> `.menu{background:rgba(0,0,0,0)}`             (padrao)
  2. BRANCA        -> `.menu:hover{background-color:var(--whiteColor)}`
                      `.single:not(.single-experience) .menu{...whiteColor}`

A onda 8.1 so tratou o estado 2 na variante "pagina de post"; no HOVER (que
acontece em TODAS as ~275 paginas, inclusive a home) os icones continuavam
brancos sobre fundo branco e sumiam.

O QUE ESTE SCRIPT FAZ
---------------------
So CSS, em bloco marcado (onda10:header-contraste) no onda6.css. Nenhum HTML
muda. O onda6.css carrega DEPOIS do CSS do tema, e as regras novas tem
especificidade maior que as da onda 8.1, entao vencem sem !important.

Cores escolhidas (contraste medido contra #ffffff, criterio WCAG 1.4.11 para
componente grafico = 3:1):

  #020e66 (navy Mirow) .............. 16.5:1  -> estado normal na barra branca
  #0e41a7 (azul do tema) ............  8.0:1  -> hover
  #128c7e (verde WhatsApp escuro) ...  4.0:1  -> hover do icone do WhatsApp

O ciano #00adec, usado no hover sobre a barra transparente, tem so 2.6:1 contra
branco — por isso ele NAO e reaproveitado no estado branco.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _onda7_css import escrever_bloco_css, resolve_public  # noqa: E402

CHAVE = "header-contraste"
ONDA = "onda10"

CSS = u"""
/* onda10 (S-04 / #72) — icones de contato legiveis nos 2 estados da barra */
@media only screen and (min-width: 992px){
  /* estado 1 — barra transparente sobre o hero: branco (como na onda 8.1) */
  .menu__contatos-link{color:#ffffff;opacity:.85}
  .menu__contatos-link:hover,.menu__contatos-link:focus-visible{color:#00adec;opacity:1}
  .menu__contatos-link--wa:hover,.menu__contatos-link--wa:focus-visible{color:#25d366}

  /* estado 2 — barra BRANCA: hover do header (todas as paginas) e paginas de
     post. Navy sobre branco = 16.5:1. */
  .menu:hover .menu__contatos-link,
  .single:not(.single-experience) .menu .menu__contatos-link{color:#020e66;opacity:1}
  .menu:hover .menu__contatos-link svg path,
  .single:not(.single-experience) .menu .menu__contatos-link svg path{
    fill:currentColor !important;stroke:none}
  .menu:hover .menu__contatos-link:hover,
  .menu:hover .menu__contatos-link:focus-visible,
  .single:not(.single-experience) .menu .menu__contatos-link:hover,
  .single:not(.single-experience) .menu .menu__contatos-link:focus-visible{color:#0e41a7}
  .menu:hover .menu__contatos-link--wa:hover,
  .menu:hover .menu__contatos-link--wa:focus-visible,
  .single:not(.single-experience) .menu .menu__contatos-link--wa:hover,
  .single:not(.single-experience) .menu .menu__contatos-link--wa:focus-visible{color:#128c7e}
}
"""


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])
    mudou = escrever_bloco_css(pub, CHAVE, CSS, onda=ONDA)
    print(u"bloco %s:%s %s" % (ONDA, CHAVE, u"gravado" if mudou else u"ja estava igual"))
    print(u"0 pagina(s) HTML alterada(s) — a entrega e so CSS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
