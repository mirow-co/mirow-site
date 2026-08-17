# -*- coding: utf-8 -*-
"""99_remove_contato.py — tira a pagina de Contato do site.

Issue mirow-marketing#228. Idempotente: rodar 2x reporta 0 mudancas.

    python tools_onda6/99_remove_contato.py <raiz-que-contem-public> [--check]

Decisao do Mario (17/08):
  "nao sei se esta valendo a pena termos um formulario para contato no site. nao
   esta agregando a nada. ja tem mil outras formas de contato. remover a pagina
   de contato, ajustar a barra superior."

Contexto: o formulario ja estava morto — postava em admin-ajax.php, que responde
404 no site estatico (#226). Em vez de construir o backend, o Mario decidiu tirar
a pagina. Os canais que sobram e que ja existiam: as 4 pilulas do hero (WhatsApp,
e-mail, LinkedIn, Instagram), os 4 icones do header em toda pagina, e os botoes
de e-mail dos cards de lider.

O que faz
---------
1. As 3 paginas de conteudo (pt/contato, en/contact-us, de/kontakt) viram STUB DE
   REDIRECT para a home do MESMO idioma. Nao se apaga: elas tem ~195 views/mes
   (a maior intencao do site) e ha links externos e historico de busca apontando
   para la. 404 ali seria perder justamente quem ja queria falar.
2. Os stubs antigos que apontavam para elas (contato/, novo/contato/, etc.)
   passam a apontar DIRETO para a home — sem isso viraria redirect de redirect,
   que a S107 proibe (nenhum clique com 2 saltos).
3. O item "Contato" sai do menu — header e clone do rodape, nas 3 linguas.
4. O sitemap perde as 3 URLs (stub e noindex; listar noindex no sitemap e erro no
   Search Console — mesma razao da onda 33).

O que NAO faz
-------------
Nao mexe nas pilulas do hero nem nos icones do header: sao eles que passam a
carregar sozinhos o contato, e a V23/V14 ja os medem.
"""
from __future__ import unicode_literals

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public, ler, gravar  # noqa: E402

# pagina de conteudo -> home do mesmo idioma
DESTINO = {
    "pt/contato/index.html": "/pt/",
    "en/contact-us/index.html": "/en/",
    "de/kontakt/index.html": "/de/",
}
# caminhos antigos que redirecionavam para as de cima
CAMINHOS = ["/pt/contato/", "/en/contact-us/", "/de/kontakt/"]

STUB = (
    '<!DOCTYPE html><html lang="%(lang)s"><head><meta charset="utf-8">'
    '<meta http-equiv="refresh" content="0;url=%(destino)s">'
    '<meta name="robots" content="noindex,follow">'
    '<link rel="canonical" href="https://mirow.com.br%(destino)s">'
    '<title>Mirow &amp; Co.</title></head>'
    '<body><p>Redirecionando para <a href="%(destino)s">mirow.com.br%(destino)s</a>.</p>'
    '</body></html>\n'
)

# O item de menu, no header e no clone do rodape. O rotulo muda por idioma, o
# href nao — por isso a ancora e o href.
ITEM_MENU = re.compile(
    r'<div class="menu__nav-item"><a class="menu__nav-link[^"]*" '
    r'href="(?:/pt/contato/|/en/contact-us/|/de/kontakt/)"[^>]*>[^<]*</a></div>')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    pub = resolve_public(args[0])

    virou_stub = menus = religados = 0

    # 1) as 3 paginas de conteudo viram stub
    for rel, destino in DESTINO.items():
        caminho = os.path.join(pub, *rel.split("/"))
        if not os.path.exists(caminho):
            continue
        html = ler(caminho)
        novo = STUB % {"lang": rel.split("/")[0], "destino": destino}
        if html.strip() == novo.strip():
            continue
        if not check:
            gravar(caminho, novo)
        virou_stub += 1

    # 2) stubs antigos apontam direto para a home; 3) item de menu sai
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if not nome.endswith(".html"):
                continue
            caminho = os.path.join(dirpath, nome)
            rel = os.path.relpath(caminho, pub).replace("\\", "/")
            if rel in DESTINO:
                continue
            html = ler(caminho)
            novo = html

            # Redirect que apontava para uma pagina de contato: encurta o salto.
            eh_stub = ('http-equiv="refresh"' in novo
                       and '<footer class="footer">' not in novo)
            if eh_stub:
                for antigo in CAMINHOS:
                    if antigo in novo:
                        lang = antigo.strip("/").split("/")[0]
                        home = "/%s/" % ("pt" if lang == "pt" else lang)
                        novo = novo.replace(antigo, home)
                        religados += 1
                        break

            novo, n = ITEM_MENU.subn("", novo)
            menus += n

            if novo != html:
                if not check:
                    gravar(caminho, novo)

    print("paginas viraram stub:   %d" % virou_stub)
    print("itens de menu removidos: %d" % menus)
    print("stubs religados a home:  %d" % religados)
    print("mudancas: %d%s" % (virou_stub + menus + religados,
                              " (--check: nada escrito)" if check else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
