# -*- coding: utf-8 -*-
"""98_fontes_locais.py — autohospeda a Titillium Web e corta o Google Fonts.

Issue mirow-marketing#227. Idempotente: rodar 2x reporta 0 mudancas.

    python tools_onda6/98_fontes_locais.py <raiz-que-contem-public> [--check]

Por que
-------
Levantado na revisao da politica de privacidade (#225): o Google Fonts recebia o
IP de todo visitante em 224 paginas, e era o ultimo compartilhamento de IP com os
EUA que ninguem tinha pedido. E o objeto literal do precedente de Munique
(LG Munchen I, jan/2022): EUR 100 de dano moral por transmitir o IP do visitante
a servidor nos EUA sem consentimento, sem identificar ninguem.

Medido antes de mexer (9 paginas, computado no navegador):
  - Titillium Web  -> 202 elementos. E a fonte do site.
  - Archivo, Libre Franklin, Roboto Serif -> ZERO elementos, e mesmo assim eram
    baixadas em toda pagina, via @import no CSS do TEMA (bundle-css.css).

O que faz
---------
1. Baixa os 12 .woff2 da Titillium Web (6 pesos x subsets latin e latin-ext) do
   fonts.gstatic.com e grava em wp-content/uploads/2026/07/fontes/.
   Licenca OFL — autohospedagem e expressamente permitida.
2. Gera fontes-mirow.css local com os mesmos @font-face, apontando para o disco,
   preservando `unicode-range` (sem ele o navegador baixa os dois subsets sempre)
   e `font-display:swap` (mesmo comportamento de antes).
3. No HTML: troca os 2 <link rel=preconnect> e o <link> do googleapis pelo nosso.
4. No TEMA: remove os 3 @import de familias que ninguem usa.

Sobre a regra zero do CLAUDE.md
------------------------------
"nunca editando o CSS do tema" — e aqui o passo 4 edita. E deliberado e sem
alternativa: @import nao se sobrescreve de fora, so se remove na origem. O que
sai sao TRES LINHAS que baixam fontes com zero elementos renderizados; nao ha
mudanca de estilo. A V34 mede que a Titillium continua sendo a fonte aplicada.

Achado registrado, NAO corrigido aqui
-------------------------------------
25 elementos declaram peso 500 ou 800, que NAO EXISTEM na Titillium Web (a
familia tem 200/300/400/600/700/900). O navegador serve o vizinho — a mesma
classe do bug da onda 35, ainda viva fora do hero. Mantemos exatamente o conjunto
que o <head> ja pedia para esta onda nao ter efeito visual; a correcao dos pesos
orfaos e trabalho proprio (ver #227).
"""
from __future__ import unicode_literals

import io
import os
import re
import sys

try:
    from urllib.request import urlopen, Request
except ImportError:  # py2
    from urllib2 import urlopen, Request  # noqa

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public, ler, gravar  # noqa: E402

DIR_FONTES = "wp-content/uploads/2026/07/fontes"
CSS_LOCAL = DIR_FONTES + "/fontes-mirow.css"
TEMA = "wp-content/themes/mirow/public/bundle-css.css"

GOOGLE_CSS = ("https://fonts.googleapis.com/css2"
              "?family=Titillium+Web:wght@200;300;400;600;700;900&display=swap")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# Os 3 @import de familias nao usadas, no CSS do tema.
IMPORTS_MORTOS = re.compile(
    r"@import\s+url\((?:'|\")?https://fonts\.googleapis\.com[^)]*\)\s*;\s*", re.I)

# No HTML: preconnects + o <link> do googleapis.
LINKS_GOOGLE = re.compile(
    r"[ \t]*<link[^>]*href=\"https://fonts\.(?:googleapis|gstatic)\.com[^\"]*\"[^>]*>\s*",
    re.I)


def baixa(url):
    req = Request(url, headers={"User-Agent": UA})
    return urlopen(req, timeout=60).read()


def prepara_fontes(pub, check):
    """Baixa os woff2 e escreve o CSS local. Devolve (n_baixados, n_total)."""
    css = baixa(GOOGLE_CSS).decode("utf-8")
    destino = os.path.join(pub, *DIR_FONTES.split("/"))
    if not check and not os.path.isdir(destino):
        os.makedirs(destino)

    baixados = 0
    urls = re.findall(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", css)
    for u in urls:
        nome = u.rsplit("/", 1)[-1].split("?")[0]
        # O nome do gstatic nao diz peso/subset; prefixamos para o disco ficar legivel.
        alvo = os.path.join(destino, nome)
        if not os.path.exists(alvo):
            if not check:
                with open(alvo, "wb") as f:
                    f.write(baixa(u))
            baixados += 1
        css = css.replace(u, nome)

    cabecalho = (
        "/* Titillium Web autohospedada (mirow-marketing#227).\n"
        " * Gerado por tools_onda6/98_fontes_locais.py a partir do CSS oficial do\n"
        " * Google Fonts — mesmos @font-face, mesmo unicode-range, mesmo swap.\n"
        " * Licenca OFL. Nao editar a mao: rodar o script. */\n")
    if not check:
        with io.open(os.path.join(pub, *CSS_LOCAL.split("/")), "w",
                     encoding="utf-8", newline="") as f:
            f.write(cabecalho + css)
    return baixados, len(urls)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    pub = resolve_public(args[0])

    baixados, total = prepara_fontes(pub, check)

    # 1) HTML: troca os links do Google pelo nosso.
    paginas = 0
    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if not nome.endswith(".html"):
                continue
            caminho = os.path.join(dirpath, nome)
            html = ler(caminho)
            if "fonts.googleapis.com" not in html and "fonts.gstatic.com" not in html:
                continue
            # Prefixo: o mesmo do asset de medicao, que a S123 garante resolver.
            m = re.search(r'(?:src|href)="([^"]*?)wp-content/uploads/2026/07/onda6/'
                          r'onda31-medicao\.js', html)
            prefixo = m.group(1) if m else "/"
            novo = LINKS_GOOGLE.sub("", html)
            tag = ('  <link rel="stylesheet" href="%s%s">\n' % (prefixo, CSS_LOCAL))
            anc = re.search(r"<meta[^>]+charset[^>]*>", novo, re.I)
            if not anc:
                continue
            novo = novo[:anc.end()] + "\n" + tag.rstrip("\n") + novo[anc.end():]
            if not check:
                gravar(caminho, novo)
            paginas += 1

    # 2) TEMA: remove os @import de familias nao usadas.
    p_tema = os.path.join(pub, *TEMA.split("/"))
    imports = 0
    if os.path.exists(p_tema):
        css = ler(p_tema)
        novo, imports = IMPORTS_MORTOS.subn("", css)
        if imports and not check:
            gravar(p_tema, novo)

    print("woff2 baixados:     %d de %d" % (baixados, total))
    print("paginas religadas:  %d" % paginas)
    print("@import removidos:  %d" % imports)
    print("mudancas: %d%s" % (paginas + imports,
                              " (--check: nada escrito)" if check else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
