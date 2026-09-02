# -*- coding: utf-8 -*-
"""Onda 85: as fotos apagadas dos Insights ganham cor e contraste, medidos.

    python tools_onda6/160_fotos_insights.py .

Pedido dos socios em 05/08 (issue #187, item 2): "Insights: melhorar
contraste/cor das fotos -- aparecem apagadas".

COMO EU ERREI O ALVO PRIMEIRO, e vale registrar
------------------------------------------------
A primeira hipotese foi o veu: o tema cobre cada foto com
`linear-gradient(rgba(4,21,69,.78) ...)`, e a foto renderizada saia 23% mais
escura que o arquivo. Parecia obvio. Medi o veu mais leve que ainda mantem o
titulo legivel (0,62 -- ver `qa/medir_veu_insights.py`), apliquei, e fiz o A/B na
MESMA sessao: **+6% de luz e -4% de cor.** Nada que alguem veja.

Ou seja: o veu e real e nao e o problema. Medindo os ARQUIVOS, o problema
aparece -- 4 das 10 fotos sao apagadas na origem:

    Automotive-industry      saturacao 0,088   <- praticamente cinza
    iStock-1652035117        saturacao 0,101 e faixa de luminancia 88,7
    customer-experience      saturacao 0,214
    pricing                  faixa de luminancia 68,8   <- tudo no mesmo tom

Se eu tivesse parado no veu, teria fechado o item do #187 com uma mudanca de 6%
e a reclamacao dos socios continuaria valida na proxima vez que abrissem a
pagina.

O QUE ESTE SCRIPT FAZ
---------------------
Corrige SO as que estao abaixo do piso, e com teto no quanto pode mexer:

  - contraste: estica a faixa de luminancia ate o piso, no maximo x1,35;
  - cor: aumenta a saturacao ate o piso, no maximo x1,60.

Os tetos existem porque foto de banco de imagem sobre-processada fica com cara
de filtro de rede social -- o oposto do que um site de consultoria quer. A que
ja esta boa nao e tocada (idempotencia real: rodar 2x nao muda nada).

ONDE GRAVA, e por que nao por cima
-----------------------------------
Em `uploads/2026/09/onda85/fotos/`, NOSSA pasta, e a referencia no HTML e
reapontada. O original do WordPress fica intacto -- ele e o material que a firma
recebeu, e regravar por cima destruiria a unica copia fora do git.

A pasta entra nas PASTAS do 27_cache_busting: sem isso, trocar o conteudo de uma
foto no futuro nao chegaria a quem ja visitou (a licao da onda 82).
"""
import io
import os
import re
import sys

from PIL import Image, ImageEnhance

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "qa"))
_css = __import__("_onda7_css")
ler, gravar = _css.ler, _css.gravar

PISO_SAT = 0.30          # abaixo disso a foto le como lavada
PISO_FAIXA = 110.0       # p95 - p5 da luminancia; abaixo disso e "tudo no mesmo tom"
TETO_SAT = 1.60
TETO_CONTRASTE = 1.35
DESTINO = os.path.join("wp-content", "uploads", "2026", "09", "onda85", "fotos")

PAGINAS = ["pt/insights/index.html", "en/insights/index.html", "de/insights/index.html"]


def medir(im):
    import colorsys
    p = im.convert("RGB").resize((120, 120))
    px = list(p.getdata())
    n = len(px)
    sat = sum(colorsys.rgb_to_hsv(r / 255., g / 255., b / 255.)[1] for r, g, b in px) / n
    lums = sorted((0.2126 * r + 0.7152 * g + 0.0722 * b) for r, g, b in px)
    return sat, lums[int(n * .95)] - lums[int(n * .05)]


def corrigir(im):
    """Devolve (imagem, o que foi feito) ou (None, motivo) se ja estava boa."""
    sat, faixa = medir(im)
    fc = min(PISO_FAIXA / faixa, TETO_CONTRASTE) if faixa < PISO_FAIXA else 1.0
    fs = min(PISO_SAT / sat, TETO_SAT) if sat < PISO_SAT else 1.0
    if fc <= 1.001 and fs <= 1.001:
        return None, u"ja estava acima do piso"
    out = im.convert("RGB")
    if fc > 1.0:
        out = ImageEnhance.Contrast(out).enhance(fc)
    if fs > 1.0:
        out = ImageEnhance.Color(out).enhance(fs)
    return out, u"contraste x%.2f, cor x%.2f" % (fc, fs)


def fotos_no_html(pub, rel):
    p = os.path.join(pub, rel.replace("/", os.sep))
    if not os.path.exists(p):
        return None, []
    h = ler(p)
    urls = re.findall(r'background-image:\s*url\((/[^)]*?uploads/[^)]+?)\)', h)
    return h, [u.strip('\'" ').split("?")[0] for u in urls]


def main(raiz):
    pub = os.path.join(os.path.abspath(raiz), "public")
    saida = os.path.join(pub, DESTINO)
    if not os.path.isdir(saida):
        os.makedirs(saida)
    feitas, ja, trocas = {}, 0, 0
    for rel in PAGINAS:
        h, urls = fotos_no_html(pub, rel)
        if h is None:
            continue
        novo = h
        for u in dict.fromkeys(urls):
            if DESTINO.replace(os.sep, "/") in u:
                continue
            disco = os.path.join(pub, u.lstrip("/").replace("/", os.sep))
            if not os.path.exists(disco):
                continue
            nome = os.path.basename(disco)
            if nome not in feitas:
                im = Image.open(disco)
                corrigida, nota = corrigir(im)
                if corrigida is None:
                    feitas[nome] = None
                    ja += 1
                else:
                    base = os.path.splitext(nome)[0] + ".webp"
                    corrigida.save(os.path.join(saida, base), "WEBP", quality=88, method=6)
                    feitas[nome] = base
                    s0, f0 = medir(im)
                    s1, f1 = medir(corrigida)
                    print(u"  %-44s %s  (sat %.3f->%.3f, faixa %.0f->%.0f)"
                          % (nome[:44], nota, s0, s1, f0, f1))
            if feitas[nome]:
                alvo = "/" + DESTINO.replace(os.sep, "/") + "/" + feitas[nome]
                if u in novo:
                    novo = novo.replace(u, alvo)
                    trocas += 1
        if novo != h:
            gravar(os.path.join(pub, rel.replace("/", os.sep)), novo)
    print(u"160: %d foto(s) corrigida(s), %d ja estava(m) boa(s), %d referencia(s) reapontada(s)"
          % (len([v for v in feitas.values() if v]), ja, trocas))
    return trocas


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
