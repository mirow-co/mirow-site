# -*- coding: utf-8 -*-
"""Onda 68 (#247) -- o cartao de preview de link, coerente nas 109 paginas.

RODA DEPOIS de 139 (cartoes de lider) e 140 (derivadas), porque normaliza o
`og:image` que aqueles dois deixaram apontado.

TRES DEFEITOS MEDIDOS, e o do meio e o pior:

1. **6 paginas sem `og:image` nenhuma** -- `/pt/imprensa/`, `/en/press/`,
   `/de/presse/` e as 3 politicas de privacidade. Compartilhadas no WhatsApp saiam
   sem imagem. A de imprensa e a que mais dói: e a pagina que se manda para
   jornalista, e a onda 65 acabou de leva-la de 29 para 43 materias.

2. **58 paginas com metadado MENTINDO sobre o proprio arquivo.** Quase todas
   declaravam `og:image:type = image/png` para arquivo que hoje e **WebP** --
   residuo das ondas 61/62c, que converteram a imagem e nao mexeram na tag. E as 3
   homes declaravam `og:image:width 663 / height 394` para o `og-mirow.png`, que e
   **1200x630**, com `type image/jpeg` para um **PNG**. Valor gemeo classico: a
   dimensao vivia em dois lugares e divergiu sem ninguem ver. O scraper do Facebook
   usa width/height declarados para decidir se desenha o cartao GRANDE -- 663x394
   esta abaixo do minimo, entao a home pedia cartao grande e se descrevia como
   pequena.

3. **`og:image:alt` em 0 de 109** e **`twitter:image` em 0 de 109**, apesar de
   todas as 109 declararem `twitter:card=summary_large_image`.

A CORRECAO E POR RECALCULO, NAO POR DIGITACAO: width, height e type saem do
arquivo ABERTO com o PIL, toda vez. Nao existe numero escrito a mao aqui, entao
esta classe de divergencia nao pode voltar -- se uma onda futura reconverter uma
imagem, a proxima execucao deste script reescreve as tags sozinha.

O `og:image:alt` sai do que a pagina ja diz: nome e cargo nas de lider, "Mirow &
Co." no cartao institucional, e o `og:title` sem o sufixo do site nas demais.
Nada inventado.

Idempotente: o bloco e RECONSTRUIDO a cada execucao a partir do arquivo, entao o
2o run produz texto identico e reporta 0 mudancas.

Uso:  python tools_onda6/141_cartao_de_link.py .
"""

from __future__ import print_function

import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image  # noqa: E402

from _onda7_css import ler, resolve_public  # noqa: E402

PADRAO = "wp-content/uploads/2026/07/onda6/og-mirow.png"
BASE = "https://mirow.com.br/"

MIME = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp",
        "GIF": "image/gif"}

# as tags que este script possui; sao removidas e reescritas a cada run
POSSUIDAS = ("og:image", "og:image:width", "og:image:height", "og:image:type",
             "og:image:alt")


def _alt(h, ref):
    """Texto do alt, sempre derivado do que a pagina ja afirma."""
    mn = re.search(r'<h1 class="blog-single__title">([^<]+)</h1>', h)
    mc = re.search(r'<p class="onda59-cargo"><strong>([^<]+)</strong></p>', h)
    if "og-lider-" in ref and mn and mc:
        return u"%s, %s — Mirow & Co." % (mn.group(1).strip(), mc.group(1).strip())
    if ref.endswith("og-mirow.png"):
        return u"Mirow & Co."
    mt = re.search(r'<meta property="og:title" content="([^"]+)"', h)
    if mt:
        t = mt.group(1)
        t = re.sub(r'\s*[-–—|]\s*Mirow\s*$', '', t).strip()
        if t:
            return t
    return u"Mirow & Co."


def _escapar(s):
    return (s.replace("&", "&amp;").replace('"', "&quot;")
            .replace("<", "&lt;").replace(">", "&gt;"))


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    sm = ler(os.path.join(pub, "sitemap.xml"))
    locs = re.findall(r'<loc>([^<]+)</loc>', sm)

    alterados = 0
    supridas = 0
    corrigidas = 0
    falhas = []

    for u in locs:
        p = u.replace(BASE, "").strip("/")
        fp = os.path.join(pub, *(p.split("/") + ["index.html"]))
        if not os.path.exists(fp):
            continue
        h = ler(fp)

        m = re.search(r'<meta property="og:image" content="([^"]+)"', h)
        ref = m.group(1).replace(BASE, "").lstrip("/") if m else PADRAO
        if not m:
            supridas += 1

        arq = os.path.join(pub, ref.replace("/", os.sep))
        if not os.path.exists(arq):
            falhas.append(u"%s aponta para %s, que nao existe" % (p, ref))
            continue
        im = Image.open(arq)
        larg, alt_px = im.size
        tipo = MIME.get(im.format)
        if not tipo:
            falhas.append(u"%s: formato %s sem mime conhecido" % (ref, im.format))
            continue

        alt_txt = _escapar(_alt(h, ref))

        # 1. remove tudo o que este script possui, para reconstruir
        antes = h
        for prop in POSSUIDAS:
            h = re.sub(r'[ \t]*<meta property="%s" content="[^"]*"\s*/?>\r?\n?'
                       % re.escape(prop), '', h)
        h = re.sub(r'[ \t]*<meta name="twitter:image" content="[^"]*"\s*/?>\r?\n?',
                   '', h)

        bloco = (
            u'\t<meta property="og:image" content="%s%s" />\n'
            u'\t<meta property="og:image:width" content="%d" />\n'
            u'\t<meta property="og:image:height" content="%d" />\n'
            u'\t<meta property="og:image:type" content="%s" />\n'
            u'\t<meta property="og:image:alt" content="%s" />\n'
            u'\t<meta name="twitter:image" content="%s%s" />\n'
            % (BASE, ref, larg, alt_px, tipo, alt_txt, BASE, ref))

        # 2. ancora: depois do og:site_name, que existe nas 109 (conferido).
        anc = re.search(r'[ \t]*<meta property="og:site_name" content="[^"]*"\s*/?>\r?\n',
                        h)
        if not anc:
            falhas.append(u"%s sem og:site_name -- nao sei onde ancorar" % p)
            continue
        h = h[:anc.end()] + bloco + h[anc.end():]

        if h != antes:
            with io.open(fp, "w", encoding="utf-8", newline="") as fh:
                fh.write(h)
            alterados += 1
            if m:
                corrigidas += 1

    if falhas:
        print("")
        for f in falhas[:10]:
            print("  FALHA: %s" % f)
        raise SystemExit(1)

    print("paginas que ganharam og:image (nao tinham): %d" % supridas)
    print("paginas com o bloco reescrito: %d" % corrigidas)
    print("\nresumo: %d arquivo(s) alterado(s)" % alterados)


if __name__ == "__main__":
    main()
