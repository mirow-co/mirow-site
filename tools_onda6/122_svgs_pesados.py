# -*- coding: utf-8 -*-
"""Onda 61: os dois SVG de logo de cliente que pesam mais que a home toda.

MEDIDO:
    edp.svg            414 KB   natural 3426x1263, exibido 81x30
    mercedes-benz.svg  298 KB   natural 1400x354,  exibido 119x30

SAO PROBLEMAS DIFERENTES, e cada um pede uma correcao diferente:

1) edp.svg NAO e vetor: sao QUATRO bitmaps embutidos em base64 (o maior com
   244 KB), sobre uma estrutura de clipPath + path + linearGradient. Achatar tudo
   num raster exigiria re-render, e perderia a parte vetorial.
   CONSERTO: manter a estrutura intacta e reduzir SO OS PIXELS de cada bitmap
   embutido. O elemento <image> desenha o bitmap na largura/altura em unidades do
   SVG, independentemente de quantos pixels ele tem — trocar um PNG de 996x1263
   por um de 166x211 nao muda geometria nenhuma, so a resolucao da textura. Com o
   logo exibido a 81x30, sobra folga para tela de DPR 3.

2) mercedes-benz.svg E vetor de verdade: 489 paths com 5 casas decimais
   ("199.89024"). A 119x30 px de exibicao, a 3a casa decimal ja e invisivel.
   CONSERTO: arredondar os numeros para 2 casas e tirar metadados/comentarios.
   Nenhum ponto muda de lugar em nada que se veja.

PROVA: `tools_onda6/qa/comparar_regiao.py` fotografa a barra de logos antes e
depois e compara pixel a pixel. Sem o diff medido, a onda 61 nao fecha.

Idempotente: nao reprocessa arquivo que ja esta otimizado (marcador no SVG).
"""
import base64
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _onda7_css import resolve_public

try:
    from PIL import Image
except ImportError:
    raise SystemExit("este script precisa do Pillow")

MARCA = "<!--onda61:otimizado-->"
MAIOR_LADO_EMBUTIDO = 200   # pixels; o logo aparece a 81x30, isto e ~7x de folga


def otimiza_edp(caminho):
    s = io.open(caminho, encoding="utf-8", errors="ignore").read()
    if MARCA in s:
        return None
    antes = len(s)
    novos = []

    def troca(m):
        prefixo, b64 = m.group(1), m.group(2)
        raw = base64.b64decode(b64)
        im = Image.open(io.BytesIO(raw))
        w, h = im.size
        if max(w, h) > MAIOR_LADO_EMBUTIDO:
            esc = float(MAIOR_LADO_EMBUTIDO) / max(w, h)
            im = im.resize((max(1, int(round(w * esc))), max(1, int(round(h * esc)))),
                           Image.LANCZOS)
        buf = io.BytesIO()
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA")
        im.save(buf, "PNG", optimize=True)
        novo = base64.b64encode(buf.getvalue()).decode("ascii")
        novos.append((w, h, im.size, len(b64), len(novo)))
        return prefixo + novo

    s2 = re.sub(r'(data:image/png;base64,)([A-Za-z0-9+/=]+)', troca, s)
    s2 = s2.replace("<svg", MARCA + "<svg", 1)
    io.open(caminho, "w", encoding="utf-8", newline="").write(s2)
    for w, h, nova, a, b in novos:
        print("    bitmap %dx%d -> %dx%d  (base64 %.0f KB -> %.0f KB)"
              % (w, h, nova[0], nova[1], a / 1024.0, b / 1024.0))
    return antes, len(s2)


def otimiza_mercedes(caminho):
    s = io.open(caminho, encoding="utf-8", errors="ignore").read()
    if MARCA in s:
        return None
    antes = len(s)
    s2 = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s2 = re.sub(r"<(metadata|title|desc)\b.*?</\1>", "", s2, flags=re.S)
    # 5 casas -> 2. A 119x30 px de exibicao, a 3a casa e sub-pixel.
    s2 = re.sub(r"(-?\d+\.\d{3,})",
                lambda m: ("%.2f" % float(m.group(1))).rstrip("0").rstrip("."), s2)
    s2 = re.sub(r"[ \t]{2,}", " ", s2)
    s2 = re.sub(r"\n\s*\n+", "\n", s2)
    s2 = s2.replace("<svg", MARCA + "<svg", 1)
    io.open(caminho, "w", encoding="utf-8", newline="").write(s2)
    return antes, len(s2)


def main(raiz):
    pub = resolve_public(raiz)
    base = os.path.join(pub, "wp-content", "uploads", "2026", "07", "clientes")
    total_a = total_d = 0
    for nome, fn in (("edp.svg", otimiza_edp), ("mercedes-benz.svg", otimiza_mercedes)):
        p = os.path.join(base, nome)
        if not os.path.exists(p):
            print("  ausente: %s" % nome)
            continue
        print("%s:" % nome)
        r = fn(p)
        if r is None:
            print("    ja otimizado — 0 mudancas")
            continue
        a, d = r
        total_a += a
        total_d += d
        print("    arquivo: %.0f KB -> %.0f KB" % (a / 1024.0, d / 1024.0))
    if total_a:
        print("-" * 60)
        print("economia nos SVG: %.0f KB" % ((total_a - total_d) / 1024.0))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
