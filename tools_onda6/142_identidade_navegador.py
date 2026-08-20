# -*- coding: utf-8 -*-
"""Onda 68 (#247) -- as 4 superficies de identidade que o site simplesmente nao tinha.

Medido nas 109 paginas de conteudo, TODAS as quatro ausentes:

    theme-color               barra de endereco do Chrome no Android e o
                              alternador de apps -- ficavam cinza de sistema
    msapplication-TileColor   o bloco do menu Iniciar do Windows tinha a imagem
                              certa (TileImage) e a cor de fundo do sistema
    mask-icon                 aba FIXADA do Safari -- sem isso o Safari desenha
                              uma letra generica em vez da marca
    manifest                  "adicionar a tela de inicio" no Android: sem
                              manifest nao ha nome curto nem icone de 512

Nenhuma delas e cara. Juntas, sao a diferenca entre o site parecer nosso e parecer
de ninguem em quatro lugares que o visitante ve.

O `mask-icon` REUSA o path do "m" e o `viewBox="0 0 101 102"` que o
`onda17-horizonte.js` ja estabeleceu na onda 34 -- nao redesenho nem re-derivo
caixa de marca. O Safari pede SVG de UMA cor e ele mesmo recolore pelo atributo
`color=` do link, entao o path vai com fill preto: nao e escolha estetica, e o
contrato do formato.

O icone de 512 sai da mesma fonte do favicon (`dados/marca-mirow-m-neg.png`), pela
mesma razao da onda 68: o que o Android desenha na tela de inicio e um glifo, nao
uma wordmark.

O manifest NAO declara `start_url` de proposito. O site tem tres idiomas e nenhum
e "o certo"; sem o campo, a especificacao usa a pagina de onde o visitante
instalou, o que faz um alemao instalar a versao alema. Fixar `/pt/` mandaria todos
para o portugues.

Idempotente: as tags sao removidas e reinseridas a partir das constantes, entao o
2o run produz texto identico. Confere o que gravou.

Uso:  python tools_onda6/142_identidade_navegador.py .
"""

from __future__ import print_function

import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image  # noqa: E402

from _onda7_css import ler, resolve_public  # noqa: E402

NAVY = "#020E66"
DESTINO = "wp-content/uploads/2026/08/onda68"
FONTE_MARCA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "dados", "marca-mirow-m-neg.png")
MARCA_SVG = "wp-content/uploads/2023/03/marca-mirow-co.svg"

MASK = "%s/marca-m-mask.svg" % DESTINO
ICONE512 = "%s/icone-mirow-512.png" % DESTINO
MANIFEST = "site.webmanifest"

VIEWBOX = "0 0 101 102"   # o mesmo do onda17-horizonte.js (onda 34)


def _sem_versao(txt):
    """O texto sem os carimbos `?v=N`, para comparar com o que o 27 ja carimbou."""
    return re.sub(r'\?v=\d+', '', txt)


def path_do_m(pub):
    """Primeiro <path> da marca oficial: o glifo do 'm'. Lido, nao redigitado."""
    svg = ler(os.path.join(pub, MARCA_SVG.replace("/", os.sep)))
    m = re.search(r'<path[^>]*\sd="([^"]+)"', svg)
    if not m:
        raise SystemExit("nao achei o path da marca em %s" % MARCA_SVG)
    return m.group(1)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    dest = os.path.join(pub, DESTINO.replace("/", os.sep))
    if not os.path.isdir(dest):
        os.makedirs(dest)

    escritos = 0

    # --- 1. mask-icon do Safari ---
    d = path_do_m(pub)
    svg = (u'<svg xmlns="http://www.w3.org/2000/svg" viewBox="%s">'
           u'<path d="%s" fill="black"/></svg>\n' % (VIEWBOX, d))
    alvo = os.path.join(pub, MASK.replace("/", os.sep))
    if not os.path.exists(alvo) or ler(alvo) != svg:
        with io.open(alvo, "w", encoding="utf-8", newline="") as f:
            f.write(svg)
        escritos += 1

    # --- 2. icone de 512 para o manifest ---
    alvo512 = os.path.join(pub, ICONE512.replace("/", os.sep))
    fonte = Image.open(FONTE_MARCA).convert("RGB")
    novo = fonte.resize((512, 512), Image.LANCZOS)
    precisa = True
    if os.path.exists(alvo512):
        try:
            atual = Image.open(alvo512)
            atual.load()
            precisa = (atual.size != (512, 512)
                       or list(atual.convert("RGB").getdata())
                       != list(novo.getdata()))
        except Exception:
            precisa = True
    if precisa:
        buf = io.BytesIO()
        novo.save(buf, format="PNG", optimize=True)
        with open(alvo512, "wb") as f:
            f.write(buf.getvalue())
        escritos += 1

    # --- 3. manifest ---
    man = {
        "name": "Mirow & Co.",
        "short_name": "Mirow",
        "theme_color": NAVY,
        "background_color": NAVY,
        "display": "standalone",
        "icons": [
            {"src": "/wp-content/uploads/2023/04/cropped-favicon-mirow-192x192.png",
             "sizes": "192x192", "type": "image/png"},
            {"src": "/" + ICONE512, "sizes": "512x512", "type": "image/png"},
        ],
    }
    txt = json.dumps(man, indent=2, ensure_ascii=False) + u"\n"
    alvoman = os.path.join(pub, MANIFEST)
    if not os.path.exists(alvoman) or ler(alvoman) != txt:
        with io.open(alvoman, "w", encoding="utf-8", newline="") as f:
            f.write(txt)
        escritos += 1

    # --- confere o que gravou, antes de anunciar nas 109 paginas ---
    falhas = []
    im = Image.open(alvo512)
    im.load()
    if im.size != (512, 512):
        falhas.append("icone 512 saiu %dx%d" % im.size)
    s = ler(alvo)
    if "<path" not in s or VIEWBOX not in s:
        falhas.append("mask-icon sem path ou sem viewBox")
    j = json.loads(ler(alvoman))
    for ic in j["icons"]:
        fp = os.path.join(pub, ic["src"].lstrip("/").replace("/", os.sep))
        if not os.path.exists(fp):
            falhas.append("manifest aponta para %s, que nao existe" % ic["src"])
    if falhas:
        for f in falhas:
            print("  FALHA: %s" % f)
        raise SystemExit(1)

    # --- 4. as 4 tags nas paginas ---
    bloco = (
        u'\t<meta name="theme-color" content="%s" />\n'
        u'\t<meta name="msapplication-TileColor" content="%s" />\n'
        u'\t<link rel="mask-icon" href="/%s" color="%s" />\n'
        u'\t<link rel="manifest" href="/%s" />\n' % (NAVY, NAVY, MASK, NAVY, MANIFEST))

    remover = (
        r'[ \t]*<meta name="theme-color" content="[^"]*"\s*/?>\r?\n?',
        r'[ \t]*<meta name="msapplication-TileColor" content="[^"]*"\s*/?>\r?\n?',
        r'[ \t]*<link rel="mask-icon"[^>]*>\r?\n?',
        r'[ \t]*<link rel="manifest"[^>]*>\r?\n?',
    )

    alterados = 0
    semancora = []
    for dp, _dd, fs in os.walk(pub):
        for f in fs:
            if not f.endswith(".html"):
                continue
            fp = os.path.join(dp, f)
            h = ler(fp)
            # so paginas de conteudo: o stub de redirect nao precisa de identidade
            if not re.search(r'<meta name="msapplication-TileImage"', h):
                continue
            antes = h
            for rex in remover:
                h = re.sub(rex, '', h)
            anc = re.search(r'[ \t]*<meta name="msapplication-TileImage"'
                            r' content="[^"]*"\s*/?>\r?\n', h)
            if not anc:
                semancora.append(os.path.relpath(fp, pub))
                continue
            h = h[:anc.end()] + bloco + h[anc.end():]
            # Comparar IGNORANDO o `?v=`: o bloco daqui sai sem carimbo e o
            # 27_cache_busting o carimba depois. Comparando texto cru, os dois
            # scripts entravam em PINGUE-PONGUE -- o 142 tirava o `?v=83`, o 27
            # devolvia, e cada um relatava 106 mudancas em toda execucao, para
            # sempre. Nenhum dos dois estava errado isolado; a combinacao e que
            # nao convergia. Mesma classe do conflito entre o 111 e o 112, que o
            # docstring do 111 registra.
            if _sem_versao(h) != _sem_versao(antes):
                with io.open(fp, "w", encoding="utf-8", newline="") as fh:
                    fh.write(h)
                alterados += 1

    if semancora:
        print("  FALHA: %d pagina(s) sem ancora" % len(semancora))
        raise SystemExit(1)

    print("assets gravados: %d   paginas com as 4 tags: %d" % (escritos, alterados))
    print("\nresumo: %d arquivo(s) alterado(s)" % (escritos + alterados))


if __name__ == "__main__":
    main()
