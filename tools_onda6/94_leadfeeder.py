# -*- coding: utf-8 -*-
"""94_leadfeeder.py — injeta o asset do Leadfeeder nas paginas de conteudo.

Issue mirow-marketing#222. Idempotente: rodar 2x reporta 0 mudancas.

    python tools_onda6/94_leadfeeder.py <raiz-que-contem-public> [--check]

Escreve UMA linha de <script> apontando para o nosso asset
wp-content/uploads/2026/07/onda6/onda54-leadfeeder.js logo depois do <meta charset>.
A URL do fornecedor NAO vive no HTML — vive dentro do asset, que decide se carrega
(interruptor ATIVO, opt-out, conta configurada).

Stubs de redirect ficam DE FORA: sao 173 paginas <meta refresh> sem corpo, das quais
o visitante sai em milissegundos. O criterio e o mesmo de Suite.eh_stub — se um
mudar, mudar o outro na mesma edicao (classe "valores gemeos" do P2.1).

A referencia sai SEM ?v=: o carimbo e do 27_cache_busting.py, que roda por ultimo.
"""
from __future__ import unicode_literals

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public, base_prefix, ler, gravar  # noqa: E402

ASSET = "wp-content/uploads/2026/07/onda6/onda54-leadfeeder.js"
MEDICAO = "wp-content/uploads/2026/07/onda6/onda31-medicao.js"

META_REFRESH = re.compile(r'<meta\s+http-equiv=["\']refresh["\']', re.I)

# Prefixo pela referencia do asset de MEDICAO, nao pelo base_prefix() generico.
#
# Achado real desta onda: base_prefix() devolve o prefixo da PRIMEIRA referencia a
# wp-content da pagina, e em 6 paginas de pratica a primeira e uma imagem legada em
# "/novo/wp-content/uploads/2023/04/...". O asset saia como /novo/... e 404ava — o
# mesmo bug da onda 33b, em que a medicao 404ou em 143 paginas por prefixo errado.
# A medicao serve de fonte porque a M01 garante que ela esta em toda pagina e a S123
# garante que o caminho dela resolve no disco.
PREFIXO_MEDICAO = re.compile(
    r'(?:src|href)="([^"]*?)' + re.escape(MEDICAO) + r'(?:\?[^"]*)?"')


def prefixo(html):
    m = PREFIXO_MEDICAO.search(html)
    return m.group(1) if m else base_prefix(html)


def eh_stub(rel, html):
    """Criterio COPIADO de Suite.eh_stub (tools/verificacoes.py)."""
    if rel == "index.html":
        return True
    return META_REFRESH.search(html) is not None and '<footer class="footer">' not in html


def bloco(prefix):
    return (
        "  <!-- Leadfeeder (nivel empresa) - issue mirow-marketing#222. "
        "Conta, opt-out e interruptor em %s -->\n"
        '  <script src="%s%s"></script>'
    ) % (ASSET, prefix, ASSET)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    pub = resolve_public(args[0])

    if not os.path.exists(os.path.join(pub, *ASSET.split("/"))):
        raise SystemExit("asset ausente: %s" % ASSET)

    injetados = ja_ok = stubs = 0
    problemas = []

    for dirpath, _dirs, files in os.walk(pub):
        for nome in files:
            if not nome.endswith(".html"):
                continue
            caminho = os.path.join(dirpath, nome)
            rel = os.path.relpath(caminho, pub).replace("\\", "/")
            html = ler(caminho)

            if ASSET in html:
                ja_ok += 1
                continue
            if rel == "404.html" or eh_stub(rel, html):
                stubs += 1
                continue

            # Ancora depois do <meta charset>: ele precisa caber nos primeiros
            # 1024 bytes, senao o navegador decide a codificacao antes de le-lo.
            anc = (re.search(r"<meta[^>]+charset[^>]*>", html, re.I)
                   or re.search(r"<head[^>]*>", html, re.I))
            if not anc:
                problemas.append(rel)
                continue

            novo = html[:anc.end()] + "\n" + bloco(prefixo(html)) + html[anc.end():]
            if not check:
                gravar(caminho, novo)
            injetados += 1

    print("injetado:          %d" % injetados)
    print("ja tinham o asset: %d" % ja_ok)
    print("stub/404 (fora):   %d" % stubs)
    if problemas:
        print("sem <head> nem charset: %d -> %s" % (len(problemas), ", ".join(problemas[:5])))
    print("mudancas: %d%s" % (injetados, " (--check: nada escrito)" if check else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
