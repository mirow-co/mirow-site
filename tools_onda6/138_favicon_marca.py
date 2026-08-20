# -*- coding: utf-8 -*-
"""Onda 68 -- o favicon passa a ser a MARCA (o "m"), nao a wordmark inteira.

O PEDIDO (Mario, 20/08/2026, verbatim): "o favicon deveria ser baseado nesse, em
'C:\\Users\\admin\\OneDrive - Mirow\\Mirow & Co\\04_Qualifications and Visual\\
04_Logos e Cores\\01_New Mirow & Co\\PNG\\LogoNeg.png'. colocar no git do nosso
site um favicon baseado nisso". Ele chegou nisso perguntando que simbolo o Google
mostrava ao lado do dominio -- ou seja, o proprio dono da marca nao reconhecia o
icone do proprio site.

O QUE ESTAVA NO AR, MEDIDO (nao e opiniao de gosto, e tinta contada pixel a pixel):

    cropped-favicon-mirow-192x192.png   tinta branca = 0,29% do quadro
                                        caixa da marca = 125 x 11 px
    cropped-favicon-mirow-32x32.png     tinta branca = 0,00%
    themes/mirow/favicon.ico            16x16 -- abaixo do minimo do Google

O 32x32 nao tinha UM pixel acima de 200 de brilho: a wordmark "MIROW & CO." tem
11 caracteres, entao a 32px cada letra recebe ~3px e o antialias a apaga por
completo. O icone que o visitante via era um quadrado navy VAZIO, que o Google
ainda recorta em circulo. A marca nova tem 10,67% de tinta -- 37x mais.

A LICAO DE CLASSE: favicon nao aceita wordmark. O que cabe em 16px e UM glifo.
Nao e preferencia estetica, e aritmetica de pixel por caractere.

PROVENIENCIA DA FONTE. O arquivo do Mario foi copiado para
`tools_onda6/dados/marca-mirow-m-neg.png` (1150x1150, RGBA, alfa 255 em TODO
pixel -- conferido, nao presumido) e e DALI que este script le. O caminho do
OneDrive NAO entra no codigo: path absoluto de usuario em arquivo versionado e
antipadrao da R14, e o script tem de rodar na maquina de qualquer um.

Navy da fonte medido: (2, 14, 102) = #020E66, o navy oficial da casa (R4). Nao
foi preciso recolorir nada.

O QUE ESTE SCRIPT NAO FAZ, DE PROPOSITO: nao muda a moldura da marca. O "m"
ocupa 55% da largura do quadro no arquivo do Mario, com ~22% de respiro de cada
lado. Apertar esse respiro melhoraria a leitura a 16px, mas mexer no
enquadramento de uma marca e decisao de marca, nao de script -- vai como
alternativa para o Mario ver, nao como fato consumado.

CACHE. As 6 saidas entram na lista ASSETS do `27_cache_busting.py`, senao o
navegador (e o Google) serviriam o icone velho do cache e a troca "nao
funcionaria" no ar -- erro 6 e 9 da lista do CLAUDE.md. Favicon e o caso mais
agressivo de cache que existe.

Idempotente: roda 2x e o segundo run reporta 0 mudancas. Compara os PIXELS
decodificados antes de reescrever, nao os bytes -- versao diferente de Pillow
gera bytes diferentes para a mesma imagem, e sem isso o script "mudaria" tudo a
cada execucao em outra maquina.

VERIFICA O QUE GRAVOU. Depois de escrever, reabre cada arquivo e confere
dimensao e tinta. Sem isso este script seria o pixel vermelho da onda 60b outra
vez: escrever um asset e conferir apenas que ele existe.

Uso:  python tools_onda6/138_favicon_marca.py .
"""

from __future__ import print_function

import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image  # noqa: E402

from _onda7_css import resolve_public  # noqa: E402

FONTE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "dados", "marca-mirow-m-neg.png")

# Os 4 PNG mantem o nome que as 109 paginas ja referenciam: trocar o CONTEUDO
# custa 0 edicao de HTML. O nome "cropped-favicon-mirow-*" e heranca do
# WordPress e continua honesto -- sao favicons.
PNGS = [
    ("wp-content/uploads/2023/04/cropped-favicon-mirow-32x32.png", 32),
    ("wp-content/uploads/2023/04/cropped-favicon-mirow-180x180.png", 180),
    ("wp-content/uploads/2023/04/cropped-favicon-mirow-192x192.png", 192),
    ("wp-content/uploads/2023/04/cropped-favicon-mirow-270x270.png", 270),
]

# Multi-frame: 16 e 32 sao o que o navegador desenha na aba; 48 e o tamanho que
# o Google documenta como minimo para o icone do resultado de busca.
FRAMES_ICO = [(16, 16), (32, 32), (48, 48)]

# `themes/mirow/favicon.ico` e o que o <link rel="shortcut icon"> pede.
# `favicon.ico` na RAIZ nao e pedido por nenhuma tag: navegador e crawler batem
# em /favicon.ico por convencao, e hoje esse caminho nao existe no espelho
# (conferido no disco), ou seja responde 404 em producao.
ICOS = [
    "wp-content/themes/mirow/favicon.ico",
    "favicon.ico",
]

TINTA_MINIMA = 4.0  # % de pixel claro; a wordmark antiga dava 0,29 e 0,00


def _pct_tinta(im):
    """Fracao de pixel claro (a 'tinta' branca da marca) sobre o quadro."""
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    n = 0
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if r > 200 and g > 200 and b > 200:
                n += 1
    return 100.0 * n / float(w * h)


def _mesmos_pixels(caminho, esperado):
    """True se o arquivo em disco ja tem exatamente a imagem esperada.

    Compara pixel decodificado, nao byte: encoder de Pillow diferente produz
    bytes diferentes para a mesma imagem, e comparar byte faria o script
    reescrever tudo a cada run em outra maquina (quebrando a idempotencia).
    """
    if not os.path.exists(caminho):
        return False
    try:
        atual = Image.open(caminho)
        atual.load()
    except Exception:
        return False
    if atual.size != esperado.size:
        return False
    return list(atual.convert("RGBA").getdata()) == \
        list(esperado.convert("RGBA").getdata())


def _gravar_png(caminho, im):
    d = os.path.dirname(caminho)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True)
    with open(caminho, "wb") as fh:
        fh.write(buf.getvalue())


def _gravar_ico(caminho, base):
    d = os.path.dirname(caminho)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    base.save(caminho, format="ICO", sizes=FRAMES_ICO)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    pub = resolve_public(sys.argv[1])

    if not os.path.exists(FONTE):
        raise SystemExit("fonte ausente: %s" % FONTE)

    fonte = Image.open(FONTE)
    fonte.load()
    if fonte.mode != "RGBA":
        fonte = fonte.convert("RGBA")

    # A fonte e opaca em todo pixel (conferido), entao nao ha composicao a fazer
    # -- mas se um dia entrar uma versao com alfa, achatar sobre o navy da
    # propria marca e o certo, nunca sobre branco.
    navy = fonte.convert("RGB").getpixel((0, 0))
    if fonte.getextrema()[3][0] < 255:
        fundo = Image.new("RGBA", fonte.size, navy + (255,))
        fundo.paste(fonte, mask=fonte)
        fonte = fundo

    print("fonte: %dx%d, navy %s, tinta %.2f%%"
          % (fonte.size[0], fonte.size[1], navy, _pct_tinta(fonte)))

    escritos = 0
    conferidos = []

    for rel, lado in PNGS:
        alvo = os.path.join(pub, rel.replace("/", os.sep))
        novo = fonte.resize((lado, lado), Image.LANCZOS).convert("RGB")
        if _mesmos_pixels(alvo, novo):
            continue
        _gravar_png(alvo, novo)
        escritos += 1

    base_ico = fonte.resize((256, 256), Image.LANCZOS).convert("RGBA")
    for rel in ICOS:
        alvo = os.path.join(pub, rel.replace("/", os.sep))
        precisa = True
        if os.path.exists(alvo):
            try:
                atual = Image.open(alvo)
                atual.load()
                tem = set(getattr(atual, "ico").sizes())
                precisa = (set(FRAMES_ICO) - tem) or _pct_tinta(atual) < TINTA_MINIMA
            except Exception:
                precisa = True
        if not precisa:
            continue
        _gravar_ico(alvo, base_ico)
        escritos += 1

    # --- confere o que gravou (o script NAO confia no proprio save) ---
    falhas = []
    for rel, lado in PNGS:
        alvo = os.path.join(pub, rel.replace("/", os.sep))
        im = Image.open(alvo)
        im.load()
        pct = _pct_tinta(im)
        conferidos.append((rel.split("/")[-1], "%dx%d" % im.size, pct,
                           os.path.getsize(alvo)))
        if im.size != (lado, lado):
            falhas.append("%s saiu %dx%d, esperado %dx%d"
                          % (rel, im.size[0], im.size[1], lado, lado))
        if pct < TINTA_MINIMA:
            falhas.append("%s tem so %.2f%% de tinta (minimo %.1f%%)"
                          % (rel, pct, TINTA_MINIMA))

    for rel in ICOS:
        alvo = os.path.join(pub, rel.replace("/", os.sep))
        im = Image.open(alvo)
        im.load()
        pct = _pct_tinta(im)
        try:
            tem = sorted(getattr(im, "ico").sizes())
        except Exception:
            tem = [im.size]
        conferidos.append((rel.split("/")[-1],
                           ",".join("%dx%d" % s for s in tem), pct,
                           os.path.getsize(alvo)))
        faltando = set(FRAMES_ICO) - set(tem)
        if faltando:
            falhas.append("%s sem os frames %s"
                          % (rel, sorted(faltando)))
        if pct < TINTA_MINIMA:
            falhas.append("%s tem so %.2f%% de tinta (minimo %.1f%%)"
                          % (rel, pct, TINTA_MINIMA))

    print("")
    for nome, dim, pct, tam in conferidos:
        print("  %-38s %-14s tinta %5.2f%%  %6.1f KB"
              % (nome, dim, pct, tam / 1024.0))

    if falhas:
        print("")
        for f in falhas:
            print("  FALHA: %s" % f)
        raise SystemExit(1)

    print("\nresumo: %d arquivo(s) alterado(s)" % escritos)


if __name__ == "__main__":
    main()
