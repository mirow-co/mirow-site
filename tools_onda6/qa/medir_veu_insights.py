# -*- coding: utf-8 -*-
"""Acha o veu MAIS LEVE que ainda mantem o titulo legivel sobre a foto.

    python tools_onda6/qa/medir_veu_insights.py

Pedido dos socios em 05/08 (issue #187): "Insights: melhorar contraste/cor das
fotos -- aparecem apagadas".

Medido: cada foto do card leva por cima um `::after` com
`linear-gradient(rgba(4,21,69,.78) 0%, rgba(4,21,69,.3) 45%, transparent 75%)`.
E o veu NAO e decoracao: o `<h3>` do card fica EM CIMA da foto, e sem ele o
titulo branco desaparece numa foto clara. Ou seja, o problema nao se resolve
apagando o veu -- se resolve achando o veu mais leve que ainda deixa o titulo
legivel na PIOR foto do acervo.

O que este script faz: para cada foto usada nos cards, recorta a faixa onde o
titulo cai, compoe com o navy do veu em varias opacidades, e calcula a razao de
contraste com o texto branco (formula WCAG 2.x). Reporta a menor opacidade que
mantem TODAS as fotos acima do alvo -- a pior foto governa, nao a media.

Alvo: 4,5:1 (AA para texto normal). Com folga de 0,3 porque o titulo cai em
posicao ligeiramente diferente conforme o numero de linhas.
"""
import io
import os
import re
import sys

from PIL import Image

NAVY = (4, 21, 69)          # a cor do veu, medida no computed style
TEXTO = (255, 255, 255)     # o titulo e branco
ALVO = 4.5                  # WCAG AA para texto normal
FOLGA = 0.3


def _canal(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminancia(rgb):
    r, g, b = (_canal(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a, b):
    la, lb = luminancia(a), luminancia(b)
    claro, escuro = max(la, lb), min(la, lb)
    return (claro + 0.05) / (escuro + 0.05)


def media_faixa(im, topo=0.0, base=0.45):
    """Cor media da faixa onde o titulo cai (o topo da foto)."""
    im = im.convert("RGB")
    w, h = im.size
    faixa = im.crop((0, int(h * topo), w, max(int(h * base), int(h * topo) + 1)))
    faixa = faixa.resize((40, 20))
    px = list(faixa.getdata())
    n = len(px)
    return (sum(p[0] for p in px) / n, sum(p[1] for p in px) / n, sum(p[2] for p in px) / n)


def compor(cor, alfa):
    return tuple(cor[i] * (1 - alfa) + NAVY[i] * alfa for i in range(3))


def fotos_dos_cards(pub):
    """As imagens que os cards de insight usam, lidas do HTML (nao adivinhadas)."""
    p = os.path.join(pub, "pt", "insights", "index.html")
    with io.open(p, encoding="utf-8", errors="replace") as f:
        h = f.read()
    urls = re.findall(r'page-insights__list-image[^>]*background-image:\s*url\(([^)]+)\)', h)
    if not urls:
        urls = re.findall(r'background-image:\s*url\(([^)]*uploads[^)]+)\)', h)
    fora, vistos = [], set()
    for u in urls:
        u = u.strip('\'" ').split("?")[0]
        cam = u.replace("/mirow-site", "", 1)
        if not cam.startswith("/"):
            continue
        disco = os.path.join(pub, cam.lstrip("/").replace("/", os.sep))
        if os.path.exists(disco) and disco not in vistos:
            vistos.add(disco)
            fora.append(disco)
    return fora


def main(raiz="."):
    pub = os.path.join(os.path.abspath(raiz), "public")
    fotos = fotos_dos_cards(pub)
    if not fotos:
        print(u"nenhuma foto de card encontrada no HTML")
        return 1
    print(u"%d foto(s) de card. Contraste do titulo branco por opacidade do veu:\n" % len(fotos))
    escala = [0.78, 0.70, 0.62, 0.55, 0.48, 0.40, 0.30, 0.0]
    print(u"%-40s %s" % ("foto", "  ".join("%.2f" % a for a in escala)))
    piores = {a: 99.0 for a in escala}
    for f in fotos:
        im = Image.open(f)
        cor = media_faixa(im)
        linha = []
        for a in escala:
            c = contraste(compor(cor, a), TEXTO)
            piores[a] = min(piores[a], c)
            linha.append("%5.1f" % c)
        print(u"%-40s %s" % (os.path.basename(f)[:40], " ".join(linha)))
    print(u"\n%-40s %s" % ("PIOR CASO", " ".join("%5.1f" % piores[a] for a in escala)))
    ok = [a for a in escala if piores[a] >= ALVO + FOLGA]
    if ok:
        print(u"\nMenor veu que mantem TODAS acima de %.1f:1 (com folga %.1f): "
              u"opacidade %.2f (hoje: 0.78)" % (ALVO, FOLGA, min(ok)))
    else:
        print(u"\nNenhuma opacidade testada mantem o alvo -- o veu de hoje ja e o minimo")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
