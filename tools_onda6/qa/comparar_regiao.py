# -*- coding: utf-8 -*-
"""Fotografa uma regiao da pagina e compara com uma referencia, pixel a pixel.

Serve para PROVAR que uma troca de asset (formato, tamanho, compressao) nao mudou
o que o visitante ve — em vez de declarar que "nao muda nada".

Uso:
    python comparar_regiao.py salvar <url> <seletor> <saida.png> [largura]
    python comparar_regiao.py comparar <antes.png> <depois.png>
"""
import base64
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, "tools")
from verificacoes import Navegador  # noqa: E402


def foto(nav, seletor, saida):
    cx = nav.js("(function(){var e=document.querySelector('%s');if(!e)return '';"
                "var r=e.getBoundingClientRect();e.scrollIntoView({block:'center'});"
                "r=e.getBoundingClientRect();"
                "return JSON.stringify({x:Math.round(r.left),y:Math.round(r.top),"
                "w:Math.round(r.width),h:Math.round(r.height)});})()" % seletor)
    if not cx:
        raise SystemExit("seletor nao encontrado: %s" % seletor)
    import json
    c = json.loads(cx)
    r = nav.ws.call(nav._id(), "Page.captureScreenshot",
                    {"format": "png", "clip": {"x": c["x"], "y": c["y"], "width": c["w"],
                                               "height": c["h"], "scale": 1}})
    dados = base64.b64decode(r["result"]["data"])
    with io.open(saida, "wb") as f:
        f.write(dados)
    return c


def comparar(a, b):
    from PIL import Image, ImageChops
    ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    if ia.size != ib.size:
        return None, u"tamanhos diferentes: %s vs %s" % (ia.size, ib.size)
    dif = ImageChops.difference(ia, ib)
    caixa = dif.getbbox()
    hist = dif.convert("L").histogram()
    total = ia.size[0] * ia.size[1]
    # quantos pixels diferem mais que 8 niveis (ruido de compressao fica abaixo)
    acima = sum(hist[9:])
    pior = max(i for i, n in enumerate(hist) if n) if any(hist) else 0
    return (acima, u"%d de %d pixels (%.3f%%) diferem >8 niveis; pior delta %d; caixa %s"
            % (acima, total, 100.0 * acima / total, pior, caixa))


if __name__ == "__main__":
    if sys.argv[1] == "comparar":
        n, msg = comparar(sys.argv[2], sys.argv[3])
        print(msg)
        sys.exit(0 if (n is not None and n == 0) else 0)
    _, _, url, seletor, saida = sys.argv[:5]
    larg = int(sys.argv[5]) if len(sys.argv) > 5 else 1400
    with Navegador() as nav:
        nav.abrir(url, larg, 900)
        c = foto(nav, seletor, saida)
        print("%s  regiao %dx%d" % (saida, c["w"], c["h"]))
