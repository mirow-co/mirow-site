# -*- coding: utf-8 -*-
"""Onda 80c: o logo raster entra no site em WebP, no tamanho em que e servido.

    python tools_onda6/157_logos_leves.py .

POR QUE
-------
O `153 --rebaixar` trouxe a Monitor Deloitte como PNG de 203 KB, e a S163 barrou
o deploy -- corretamente: a regra da onda 62c e que nenhum PNG passa de 120 KB,
porque WebP resolve. Um logo que o site desenha com 20px de altura nao tem por
que viajar em 203 KB; o arquivo grande e do jeito que a origem publica, nao do
jeito que a gente serve.

Isso ia se repetir a cada `--rebaixar` -- a origem nao muda de ideia. Entao a
normalizacao mora AQUI, no fim do pipeline de logo, e nao numa correcao manual
que a proxima execucao desfaz.

O QUE FAZ
---------
Para cada PNG/JPG da pasta de logos:
  - reamostra para no maximo 4x a altura de render (20px -> 80px de altura), o
    que da folga de sobra para tela retina 2x e ainda assim corta o peso;
  - grava WebP sem perdas quando ha transparencia (logo em cima de placa branca
    nao pode ganhar franja), com qualidade 90 quando nao ha;
  - APAGA o arquivo antigo -- deixar os dois lado a lado faria o 152 escolher por
    ordem de listagem do sistema de arquivos, que e a definicao de bug
    intermitente.

Nao mexe em SVG: la o peso ja e pequeno e o arquivo e vetor.

Idempotente: arquivo que ja e WebP e ja esta na altura alvo sai intacto.
"""
import io
import os
import sys

from PIL import Image

PASTA = os.path.join("wp-content", "uploads", "2026", "08", "onda79", "logos")
ALTURA_RENDER = 20      # o que o CSS da onda 78/80 usa
FATOR = 4               # folga para retina 2x, com sobra
ALTURA_MAX = ALTURA_RENDER * FATOR


def main(raiz):
    pasta = os.path.join(os.path.abspath(raiz), "public", PASTA)
    if not os.path.isdir(pasta):
        print(u"157: pasta de logos ausente")
        return 0
    convertidos, ja = 0, 0
    for nome in sorted(os.listdir(pasta)):
        base, ext = os.path.splitext(nome)
        if ext.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
            continue
        p = os.path.join(pasta, nome)
        antes = os.path.getsize(p)
        im = Image.open(p)
        larg, alt = im.size
        precisa_reduzir = alt > ALTURA_MAX
        if ext.lower() == ".webp" and not precisa_reduzir:
            ja += 1
            continue
        if precisa_reduzir:
            nova_larg = max(int(round(larg * ALTURA_MAX / float(alt))), 1)
            im = im.convert("RGBA").resize((nova_larg, ALTURA_MAX), Image.LANCZOS)
        else:
            im = im.convert("RGBA")
        # transparencia exige sem perdas: numa placa branca, o halo do lossy
        # aparece como franja cinza em volta da letra
        tem_alfa = im.getchannel("A").getextrema()[0] < 255
        destino = os.path.join(pasta, base + ".webp")
        im.save(destino, "WEBP", lossless=tem_alfa, quality=90, method=6)
        if os.path.abspath(destino) != os.path.abspath(p):
            os.remove(p)
        depois = os.path.getsize(destino)
        convertidos += 1
        print(u"  %-28s %6d -> %5d bytes  (%dx%d)"
              % (nome, antes, depois, im.size[0], im.size[1]))
    print(u"157: %d logo(s) raster normalizado(s), %d ja estava(m) ok" % (convertidos, ja))
    return convertidos


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
