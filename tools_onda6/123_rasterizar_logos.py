# -*- coding: utf-8 -*-
"""Onda 61: rasteriza os dois logos-monstro para WebP, com fundo transparente.

POR QUE NAO DEU PARA SO "OTIMIZAR O SVG" (o 122 tentou, e a medida mostrou o limite):
    edp.svg        414 KB -> 149 KB   reduzindo os bitmaps embutidos... porque o
                                     "vetor" e na verdade 4 rasters colados
    mercedes.svg   298 KB -> 245 KB   arredondando 5 casas para 2 — e ainda sobram
                                     489 paths e 160 KB SO de coordenadas
Para um logo que a pagina exibe a 119x30 px, 489 paths e desproporcional. O formato
certo aqui e raster, no tamanho usado.

COMO: o Chrome carrega o SVG dentro de um HTML com o tamanho de destino e o
screenshot sai com FUNDO TRANSPARENTE (setDefaultBackgroundColorOverride com
alpha 0). Sem isso o logo ganharia um retangulo branco sobre a barra navy.
Conferido antes: o CSS da barra nao recolore o SVG (so `filter:grayscale` no
hover, que funciona igual em raster), entao rasterizar nao perde comportamento.

TAMANHO: 3x o exibido — cobre tela de DPR 3. Os .svg originais continuam no
historico do git, se algum dia a marca precisar aparecer grande.

Idempotente: nao refaz se o .webp existe e o HTML ja aponta para ele.
"""
import base64
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from _onda7_css import resolve_public

try:
    from PIL import Image
except ImportError:
    raise SystemExit("este script precisa do Pillow")

# (arquivo, largura do raster, altura do raster)
#
# AS DIMENSOES SAO A RAZAO EXATA DO ORIGINAL, nao "3x o exibido" (licao medida):
# depois do load, quem define a caixa do <img> e o ASPECTO REAL DO ARQUIVO — os
# atributos width/height do HTML sao so dica de pre-load. Com 243x90 (3x de 81x30)
# no lugar de um SVG de 3426x1263, a largura renderizada caiu de 81,38 para 81,00 px,
# e como a fileira e CENTRADA todos os 9 logos da linha andaram ~0,44px: o diff
# acusou mudanca de antialiasing em 7 logos que eu nunca toquei.
# Solucao: dividir o original pelo maximo divisor comum, o que da a MENOR dimensao
# com a razao identica — assim a caixa fica bit-identica.
#     edp            3426x1263  (gcd 3)  -> 1142x421
#     mercedes-benz  1400x354   (gcd 2)  ->  700x177
LOGOS = [
    ("wp-content/uploads/2026/07/clientes/edp.svg", 1142, 421),
    ("wp-content/uploads/2026/07/clientes/mercedes-benz.svg", 700, 177),
]
DPR = 1  # as dimensoes acima ja sao as finais


# NAO MEXER EM width/height DO HTML (licao medida na onda 61):
# eu havia reescrito os atributos com as dimensoes do arquivo novo. O aspecto muda na
# 3a casa (edp: 243/90 = 2,700 contra 3426/1263 = 2,712), e numa fileira CENTRADA isso
# redistribui todos os itens por fracoes de pixel — o diff acusou mudanca de
# antialiasing em 7 logos que eu nunca toquei. Os atributos sao dica de PROPORCAO, nao
# precisam casar com os pixels do arquivo: mantendo os originais, o layout fica
# bit-identico e so muda o pixel dos logos realmente trocados.

def main(raiz):
    pub = resolve_public(raiz)
    sys.path.insert(0, "tools")
    from verificacoes import ServidorLocal, Navegador

    # Duas listas, e a distincao importa: `pendentes` e o que falta RASTERIZAR;
    # a reescrita de referencia acontece para TODO logo que ja tem .webp, mesmo que
    # o raster tenha sido gerado num run anterior. Na primeira versao a idempotencia
    # olhava so o arquivo: o script gerou os .webp, quebrou antes de reescrever o
    # HTML, e o run seguinte disse "ja rasterizado" e nao consertou a referencia.
    pendentes = [(rel, w, h) for rel, w, h in LOGOS
                 if os.path.exists(os.path.join(pub, rel.replace("/", os.sep)))
                 and not os.path.exists(os.path.join(
                     pub, re.sub(r"\.svg$", ".webp", rel).replace("/", os.sep)))]
    prontos = [(rel, w, h) for rel, w, h in LOGOS
               if os.path.exists(os.path.join(
                   pub, re.sub(r"\.svg$", ".webp", rel).replace("/", os.sep)))]

    if pendentes:
        rasteriza(pub, pendentes)

    # reescreve as referencias de todos os que ja tem .webp
    trocar = prontos or pendentes
    tocados = reescreve(pub, trocar)
    print("%d pagina(s) com referencia reescrita" % tocados)


def rasteriza(pub, pendentes):
    sys.path.insert(0, "tools")
    from verificacoes import ServidorLocal, Navegador
    # pagina de apoio: um <img> por logo, no tamanho de destino
    apoio = os.path.join(pub, "_onda61_raster.html")
    partes = ["<!DOCTYPE html><html><head><meta charset='utf-8'>",
              "<style>html,body{margin:0;padding:0;background:transparent}",
              "img{display:block}</style></head><body>"]
    for i, (rel, w, h) in enumerate(pendentes):
        partes.append("<img id='L%d' src='/%s' style='width:%dpx;height:%dpx'>"
                      % (i, rel, w * DPR, h * DPR))
    partes.append("</body></html>")
    io.open(apoio, "w", encoding="utf-8", newline="").write("".join(partes))

    try:
        with ServidorLocal(pub) as srv, Navegador() as nav:
            nav.abrir("%s/_onda61_raster.html" % srv.base(), 1200, 800)
            nav.ws.call(nav._id(), "Emulation.setDefaultBackgroundColorOverride",
                        {"color": {"r": 0, "g": 0, "b": 0, "a": 0}})
            for i, (rel, w, h) in enumerate(pendentes):
                cx = nav.js("(function(){var e=document.getElementById('L%d');"
                            "var r=e.getBoundingClientRect();"
                            "return JSON.stringify({x:Math.round(r.left),"
                            "y:Math.round(r.top),w:Math.round(r.width),"
                            "h:Math.round(r.height)});})()" % i)
                c = json.loads(cx)
                r = nav.ws.call(nav._id(), "Page.captureScreenshot",
                                {"format": "png", "captureBeyondViewport": False,
                                 "clip": {"x": c["x"], "y": c["y"], "width": c["w"],
                                          "height": c["h"], "scale": 1}})
                dados = base64.b64decode(r["result"]["data"])
                im = Image.open(io.BytesIO(dados)).convert("RGBA")
                novo_rel = re.sub(r"\.svg$", ".webp", rel)
                destino = os.path.join(pub, novo_rel.replace("/", os.sep))
                im.save(destino, "WEBP", quality=92, method=6)
                antes = os.path.getsize(os.path.join(pub, rel.replace("/", os.sep)))
                depois = os.path.getsize(destino)
                # o alfa tem de existir de verdade, senao o logo vira caixa branca
                alfas = im.getchannel("A").getextrema()
                print("%-22s %6.0f KB -> %5.1f KB  %dx%d  alfa min/max %s"
                      % (os.path.basename(rel), antes / 1024.0, depois / 1024.0,
                         im.size[0], im.size[1], alfas))
                if alfas[0] == 255:
                    print("     ATENCAO: sem pixel transparente — conferir no diff visual")
    finally:
        if os.path.exists(apoio):
            os.remove(apoio)

def reescreve(pub, logos):
    """Troca .svg por .webp nas referencias. width/height ficam como estao."""
    tocados = 0
    for dp, _d, fs in os.walk(pub):
        if os.sep + ".git" in dp:
            continue
        for nome in fs:
            if not nome.endswith(".html"):
                continue
            fp = os.path.join(dp, nome)
            h = io.open(fp, encoding="utf-8").read()
            o = h
            for rel, w, hh in logos:
                novo_rel = re.sub(r"\.svg$", ".webp", rel)
                if rel not in h:
                    continue
                h = h.replace(rel, novo_rel)

            if h != o:
                io.open(fp, "w", encoding="utf-8", newline="").write(h)
                tocados += 1
    return tocados


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
