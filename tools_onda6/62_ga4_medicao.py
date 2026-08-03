# -*- coding: utf-8 -*-
"""62_ga4_medicao.py — troca o gtag inline do espelho pelo asset de medicao.

Issue mirow-marketing#3. Idempotente: rodar 2x reporta 0 mudancas.

    python tools_onda6/62_ga4_medicao.py <raiz-que-contem-public> [--check]

O espelho do WordPress trouxe um bloco gtag inline em cada pagina, apontando para a
propriedade G-VK4QHHHS5X (herdada do site antigo, dono nao confirmado) e sem Consent
Mode. Este script troca esse bloco por uma referencia unica a
wp-content/uploads/2026/07/onda6/onda17-medicao.js, que configura as duas
propriedades da transicao, trata consentimento e instrumenta os eventos.

A referencia sai SEM ?v= de proposito: o carimbo e do 27_cache_busting.py, que roda
sempre por ultimo e e o unico lugar que versiona asset nosso.

Stub de redirect (public/index.html) fica de fora: o navegador sai antes de a
medicao valer e o pageview e contado na pagina de destino.
"""
from __future__ import unicode_literals

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public, base_prefix, ler, gravar  # noqa: E402

ASSET = "wp-content/uploads/2026/07/onda6/onda17-medicao.js"

# Bloco gtag inline que veio no espelho (identico nas 275 paginas).
GTAG_INLINE = re.compile(
    r"[ \t]*<!-- Google tag \(gtag\.js\) -->\s*"
    r"<script async src=\"https://www\.googletagmanager\.com/gtag/js\?id=G-[A-Z0-9]+\"></script>\s*"
    r"<script>.*?gtag\('config', 'G-[A-Z0-9]+'\);\s*</script>\s*",
    re.S,
)

# Bloco de medicao que a primeira versao deste script escreveu, quando o asset
# morava em assets/mirow-analytics.js, fora da convencao de asset de onda. Casado
# aqui para a migracao nao deixar duas medicoes na mesma pagina.
MEDICAO_ANTIGA = re.compile(
    r"[ \t]*<!-- Medicao Mirow \(GA4\)[^>]*-->\s*"
    r"<script src=\"[^\"]*assets/mirow-analytics\.js\"></script>\s*"
    r"<script async src=\"https://www\.googletagmanager\.com/gtag/js\?id=G-[A-Z0-9]+\"></script>\s*",
    re.S,
)


def bloco(prefix):
    return (
        "  <!-- Medicao Mirow (GA4) - issue mirow-marketing#3. Config e eventos em %s -->\n"
        '  <script src="%s%s"></script>\n'
        '  <script async src="https://www.googletagmanager.com/gtag/js?id=G-VK4QHHHS5X"></script>'
    ) % (ASSET, prefix, ASSET)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    pub = resolve_public(args[0])

    if not os.path.exists(os.path.join(pub, *ASSET.split("/"))):
        raise SystemExit("asset ausente: %s" % ASSET)

    trocados = injetados = ja_ok = redirect = migrados = 0
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

            if re.search(r'<meta\s+http-equiv=["\']refresh["\']', html, re.I) \
                    and "<head" not in html.lower():
                redirect += 1
                continue

            novo, n = GTAG_INLINE.subn("", html, count=1)
            novo, m = MEDICAO_ANTIGA.subn("", novo, count=1)
            # Ancora depois do <meta charset>: o charset tem que seguir dentro dos
            # primeiros 1024 bytes, senao o navegador decide a codificacao antes de
            # ler a declaracao.
            anc = (re.search(r"<meta[^>]+charset[^>]*>", novo, re.I)
                   or re.search(r"<head[^>]*>", novo, re.I))
            if not anc:
                problemas.append(rel)
                continue
            novo = novo[:anc.end()] + "\n" + bloco(base_prefix(novo)) + novo[anc.end():]
            if not check:
                gravar(caminho, novo)
            if m:
                migrados += 1
            elif n:
                trocados += 1
            else:
                injetados += 1

    print("gtag inline trocado: %d" % trocados)
    print("medicao migrada:     %d" % migrados)
    print("sem gtag, injetado:  %d" % injetados)
    print("ja tinham o asset:   %d" % ja_ok)
    print("stub de redirect:    %d" % redirect)
    if problemas:
        print("sem <head> nem charset: %d -> %s" % (len(problemas), ", ".join(problemas[:5])))
    print("mudancas: %d%s" % (trocados + migrados + injetados,
                              " (--check: nada escrito)" if check else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
